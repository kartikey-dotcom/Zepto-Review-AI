import os
import re
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from backend.config import settings
from backend.gemini_absa_engine import GeminiABSAEngine

logger = logging.getLogger(__name__)

class ReviewQAEngine:
    """
    Production RAG (Retrieval-Augmented Generation) Engine for Zepto Customer Reviews.
    
    Architecture:
    1. Vector Retrieval: TF-IDF & Cosine Similarity Semantic Vector Search over 5,000 reviews.
    2. Context Augmentation: Formats retrieved review chunks & empirical metrics.
    3. Single-Paragraph Analytical Generation: Gemini LLM / Dynamic RAG Synthesizer.
    """

    STOPWORDS = {
        "what", "why", "how", "when", "where", "who", "does", "do", "are", "is", "the", "and", "about",
        "for", "with", "tell", "show", "give", "many", "much", "can", "you", "zepto", "app", "review",
        "reviews", "customer", "customers", "user", "users", "there", "their", "have", "has", "had",
        "please", "some", "more", "say", "saying", "said", "think", "people"
    }

    @classmethod
    def extract_keywords(cls, query: str) -> List[str]:
        words = re.findall(r'\b\w+\b', query.lower())
        return [w for w in words if len(w) > 2 and w not in cls.STOPWORDS]

    @classmethod
    def vector_search(cls, query: str, df: pd.DataFrame, top_k: int = 30) -> pd.DataFrame:
        """
        Semantic TF-IDF & Cosine Similarity Vector Search over review text corpus.
        """
        if df.empty or "sanitized_text" not in df.columns:
            return pd.DataFrame()

        reviews_list = df["sanitized_text"].astype(str).tolist()

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=10000)
            tfidf_matrix = vectorizer.fit_transform(reviews_list)
            query_vec = vectorizer.transform([query])

            scores = cosine_similarity(query_vec, tfidf_matrix).flatten()
            top_indices = scores.argsort()[::-1][:top_k]
            
            # Filter matches with positive similarity score
            valid_indices = [idx for idx in top_indices if scores[idx] > 0.01]

            if valid_indices:
                matched_df = df.iloc[valid_indices].copy()
                matched_df["similarity_score"] = scores[valid_indices]
                return matched_df
        except Exception as e:
            logger.warning(f"TF-IDF vector search fallback to keyword matching: {e}")

        # Fallback Keyword Search
        keywords = cls.extract_keywords(query)
        if not keywords:
            return df.head(top_k)

        pattern = "|".join(keywords)
        matched_df = df[df["sanitized_text"].str.contains(pattern, case=False, na=False)]

        if matched_df.empty:
            return df.head(top_k)

        return matched_df.head(top_k)

    @classmethod
    def generate_answer(cls, query: str, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Generates an accurate RAG single-paragraph analytical response strictly based on customer reviews.
        """
        if df is None or df.empty:
            df = pd.DataFrame([
                {"rating_stars": 1, "sanitized_text": "Tried buying phone charger on Zepto. It stopped working next day and Zepto app says NON-RETURNABLE!", "primary_aspect": "Non-Core Category Adoption Friction"},
                {"rating_stars": 1, "sanitized_text": "Milk packet leaked inside the delivery bag and spoiled my biscuit packet!", "primary_aspect": "Product Quality & Packaging Spoilage"},
                {"rating_stars": 5, "sanitized_text": "Delivery was super fast 8 mins, milk and curd delivered fresh every morning.", "primary_aspect": "Delivery Speed & Rider Behavior"},
                {"rating_stars": 2, "sanitized_text": "Searching for earphone shows random grocery items instead. Search UI needs fix.", "primary_aspect": "App UX & Technical Performance"},
                {"rating_stars": 1, "sanitized_text": "Applied promo coupon but discount not credited. Support closed my ticket without response.", "primary_aspect": "Pricing, Surge & Refund Delays"},
                {"rating_stars": 5, "sanitized_text": "Ordered hot coffee and croissant from Zepto Cafe. Surprised by how fresh it arrived in 9 mins!", "primary_aspect": "Non-Core Category Adoption Friction"},
                {"rating_stars": 1, "sanitized_text": "Tomatoes were soft and bruised. Quality check before delivery is badly needed.", "primary_aspect": "Product Quality & Packaging Spoilage"}
            ])

        if "rating_stars" not in df.columns and "rating" in df.columns:
            df["rating_stars"] = df["rating"]

        # Step 1: RAG Vector & Keyword Search
        matched_df = cls.vector_search(query, df, top_k=30)
        total_matched = len(matched_df)
        avg_rating = float(matched_df["rating_stars"].mean()) if total_matched > 0 and "rating_stars" in matched_df.columns else 0.0

        # Step 2: Extract Aspect Distribution
        aspect_counts = {}
        for _, row in matched_df.iterrows():
            aspect = row.get("primary_aspect")
            if not aspect or aspect == "Core Grocery & Perishables":
                analysis = GeminiABSAEngine.classify_aspect_rule_based(
                    str(row.get("sanitized_text", "")),
                    int(row.get("rating_stars", 1))
                )
                aspect = analysis["primary_aspect"]
            aspect_counts[aspect] = aspect_counts.get(aspect, 0) + 1

        # Step 3: Extract Representative RAG Review Chunks
        quotes = []
        seen_texts = set()
        for _, row in matched_df.iterrows():
            text = str(row.get("sanitized_text", "")).strip()
            if text and text not in seen_texts:
                seen_texts.add(text)
                rating_val = row.get("rating_stars", row.get("rating", 1))
                quotes.append(f"\"{text}\" ({rating_val}★)")
            if len(quotes) >= 3:
                break

        # Step 4: RAG Generation (Gemini LLM or RAG Fallback Synthesizer)
        answer_text = None
        if settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)
                
                context_str = "\n".join(quotes)
                prompt = (
                    f"You are Zepto Reviews AI Discovery Assistant. Answer the user's question using the retrieved customer review context below.\n"
                    f"User Question: '{query}'\n"
                    f"Retrieved Reviews Count: {total_matched}\n"
                    f"Average Rating for Topic: {avg_rating:.2f}/5.0\n"
                    f"Retrieved Customer Review Chunks:\n{context_str}\n\n"
                    f"STRICT RAG FORMAT INSTRUCTIONS:\n"
                    f"1. Write EXACTLY ONE short, cohesive paragraph summarizing the review analysis.\n"
                    f"2. DO NOT use bullet points, numbered lists, segment headers, or line breaks.\n"
                    f"3. Provide STRICTLY review data analysis (ratings, customer sentiment, exact quotes). DO NOT suggest solutions or fix recommendations."
                )
                response = model.generate_content(prompt)
                if response and response.text:
                    clean_res = response.text.strip().replace("\n", " ")
                    clean_res = re.sub(r'\s+', ' ', clean_res)
                    answer_text = clean_res
            except Exception as e:
                logger.warning(f"Gemini RAG LLM generation failed: {e}. Falling back to RAG synthesizer.")

        if not answer_text:
            answer_text = cls.synthesize_rag_fallback(query, total_matched, avg_rating, aspect_counts, quotes)

        return {
            "query": query,
            "answer": answer_text,
            "total_matched": total_matched,
            "avg_rating": round(avg_rating, 2),
            "quotes": quotes[:2]
        }

    @classmethod
    def synthesize_rag_fallback(cls, query: str, count: int, avg_rating: float, aspects: Dict[str, int], quotes: List[str]) -> str:
        keywords = cls.extract_keywords(query)
        kw_str = ", ".join(keywords[:2]) if keywords else "this query"
        top_aspect = max(aspects, key=aspects.get) if aspects else "App Experience & Quality"

        sentiment_label = "strong customer dissatisfaction" if avg_rating <= 1.8 else (
            "mixed customer feedback" if avg_rating <= 3.5 else "mostly positive customer sentiment"
        )

        quote_text = f" as highlighted by customer feedback: {quotes[0]}." if quotes else "."

        return (
            f"Analysis of {count:,} customer reviews relating to '{kw_str}' reveals an average score of {avg_rating:.2f}/5.0★ with {sentiment_label}. "
            f"Primary discussions focus on {top_aspect}{quote_text}"
        )
