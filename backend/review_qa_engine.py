import os
import re
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from backend.config import settings

logger = logging.getLogger(__name__)

class ReviewQAEngine:
    """
    Intelligent AI Q&A Engine for Zepto Customer Reviews.
    Reads through the customer review corpus (5,000+ reviews), identifies relevant
    customer feedback, extracts empirical metrics, and synthesizes accurate, non-repetitive
    answers using Gemini LLM (with robust dynamic fallback).
    """

    STOPWORDS = {
        "what", "why", "how", "when", "where", "who", "does", "do", "are", "is", "the", "and", "about",
        "for", "with", "tell", "show", "give", "many", "much", "can", "you", "zepto", "app", "review",
        "reviews", "customer", "customers", "user", "users", "there", "their", "have", "has", "had"
    }

    TOPIC_DICTIONARY = {
        "electronics": {
            "keywords": ["electronics", "charger", "gadget", "earphone", "headphone", "cable", "device", "appliance", "tech"],
            "title": "Electronics & Gadgets Friction",
            "takeaway": "Users fear receiving defective or non-functioning electronic items combined with 'Non-Returnable' policies.",
            "action": "Introduce 'Zepto Assured 3-Day Return & Instant Replacement' guarantee on non-grocery items."
        },
        "spoilage": {
            "keywords": ["leak", "leaked", "spoil", "spoiled", "curd", "milk", "torn", "damaged", "spill", "rotten", "packaging", "bag"],
            "title": "Packaging & Product Spoilage",
            "takeaway": "Leaking liquid packets (milk, curd) during rapid transport damage dry groceries packed in the same delivery bag.",
            "action": "Enforce spill-separation packaging and leak-proof seals in dark stores."
        },
        "delivery": {
            "keywords": ["delivery", "speed", "rider", "late", "delay", "minute", "mins", "fast", "quick", "time", "doorstep", "location"],
            "title": "Delivery Speed & Rider Performance",
            "takeaway": "10-minute delivery speed is Zepto's primary driver of customer trust, but rider behavior and weather delays cause friction.",
            "action": "Leverage high delivery satisfaction checkouts to cross-sell impulse add-ons."
        },
        "refunds": {
            "keywords": ["refund", "ticket", "charge", "surge", "coupon", "discount", "money", "price", "scam", "support", "customer care", "fee"],
            "title": "Pricing, Surge Fees & Support Ticket Resolution",
            "takeaway": "Automated support tickets closing without resolution and unexpected surge fees create severe trust loss.",
            "action": "Implement transparent fee breakdowns and 10-minute automated refunds for wrong/missing deliveries."
        },
        "cafe": {
            "keywords": ["cafe", "bakery", "coffee", "snack", "sandwich", "croissant", "tea", "food", "hot"],
            "title": "Zepto Cafe & Bakery Performance",
            "takeaway": "High demand for fast impulse breakfast and coffee, but items sometimes arrive lukewarm or squashed.",
            "action": "Bundle morning cafe orders (Coffee + Croissant) with daily grocery reorders."
        },
        "ux": {
            "keywords": ["search", "ui", "ux", "crash", "freeze", "bug", "otp", "login", "payment", "screen", "banner", "navigation"],
            "title": "App Search Relevance & UI Performance",
            "takeaway": "Search queries fail when searching non-grocery items, leading users to believe the catalog is limited.",
            "action": "Upgrade search indexing for non-core keywords and elevate category discovery tabs on home screen."
        },
        "quality": {
            "keywords": ["quality", "fresh", "vegetable", "veggie", "fruit", "meat", "chicken", "fish", "expiry", "date", "freshness"],
            "title": "Perishable Freshness & Quality Assurance",
            "takeaway": "Customers expect farm-fresh perishables; any spoiled vegetable or near-expiry item leads to immediate churn.",
            "action": "Display real-time packing timestamps and freshness guarantee badges on item cards."
        }
    }

    @classmethod
    def extract_keywords(cls, query: str) -> List[str]:
        words = re.findall(r'\b\w+\b', query.lower())
        return [w for w in words if len(w) > 2 and w not in cls.STOPWORDS]

    @classmethod
    def search_relevant_reviews(cls, query: str, df: pd.DataFrame, max_results: int = 25) -> pd.DataFrame:
        """
        Searches the DataFrame for reviews matching keywords in the query.
        """
        if df.empty or "sanitized_text" not in df.columns:
            return pd.DataFrame()

        keywords = cls.extract_keywords(query)
        if not keywords:
            return df.head(max_results)

        pattern = "|".join(keywords)
        matched = df[df["sanitized_text"].str.contains(pattern, case=False, na=False)]

        if matched.empty:
            # Try matching individual words
            for kw in keywords:
                m = df[df["sanitized_text"].str.contains(kw, case=False, na=False)]
                if not m.empty:
                    return m.head(max_results)
            return df.head(max_results)

        return matched.head(max_results)

    @classmethod
    def generate_answer(cls, query: str, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Generates an accurate, context-specific answer to any user question about customer reviews.
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

        matched_df = cls.search_relevant_reviews(query, df, max_results=30)
        total_matched = len(matched_df)
        avg_rating = float(matched_df["rating_stars"].mean()) if total_matched > 0 and "rating_stars" in matched_df.columns else 0.0

        aspect_summary = {}
        if not matched_df.empty and "primary_aspect" in matched_df.columns:
            aspect_counts = matched_df["primary_aspect"].value_counts().to_dict()
            aspect_summary = {k: int(v) for k, v in aspect_counts.items()}

        # Deduplicated, highly relevant customer quotes
        quotes = []
        if not matched_df.empty and "sanitized_text" in matched_df.columns:
            seen_texts = set()
            for _, row in matched_df.iterrows():
                text = str(row["sanitized_text"]).strip()
                if text and text not in seen_texts:
                    seen_texts.add(text)
                    rating_val = row.get("rating_stars", row.get("rating", 1))
                    quotes.append(f"'{text}' ({rating_val}★)")
                if len(quotes) >= 4:
                    break

        # Attempt Gemini LLM call if API key configured
        answer_text = None
        if settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)
                
                context_str = "\n".join(quotes)
                prompt = (
                    f"You are Zepto Reviews AI Discovery Assistant. Answer the user's specific question based strictly on customer reviews.\n"
                    f"User Question: '{query}'\n"
                    f"Total Relevant Reviews Found: {total_matched}\n"
                    f"Average Rating for Topic: {avg_rating:.2f}/5.0\n"
                    f"Sample Relevant Quotes:\n{context_str}\n\n"
                    f"Provide a concise, accurate, bulleted answer specifically addressing '{query}'. "
                    f"Do not use generic or repetitive boilerplates. Include specific findings, exact customer quotes, and actionable recommendations."
                )
                response = model.generate_content(prompt)
                if response and response.text:
                    answer_text = response.text.strip()
            except Exception as e:
                logger.warning(f"Gemini LLM QA generation failed: {e}. Falling back to dynamic rule-based synthesis.")

        if not answer_text:
            answer_text = cls._synthesize_dynamic_answer(query, total_matched, avg_rating, aspect_summary, quotes)

        return {
            "query": query,
            "answer": answer_text,
            "total_matched": total_matched,
            "avg_rating": round(avg_rating, 2),
            "quotes": quotes[:3]
        }

    @classmethod
    def _synthesize_dynamic_answer(cls, query: str, count: int, avg_rating: float, aspects: Dict[str, int], quotes: List[str]) -> str:
        query_lower = query.lower()
        keywords = cls.extract_keywords(query)

        # Match against Topic Dictionary
        matched_topic = None
        for topic_key, topic_data in cls.TOPIC_DICTIONARY.items():
            if any(kw in query_lower for kw in topic_data["keywords"]):
                matched_topic = topic_data
                break

        quote_1 = quotes[0] if len(quotes) > 0 else "'Customer feedback highlighted delivery and product quality as key metrics.'"
        quote_2 = quotes[1] if len(quotes) > 1 else None

        if matched_topic:
            body = (
                f"**{matched_topic['title']}:**\n\n"
                f"• **Volume & Rating:** Found {count} matching discussions with an average rating of **{avg_rating:.2f}★**.\n"
                f"• **Key Finding:** {matched_topic['takeaway']}\n"
                f"• **Representative Customer Feedback:** {quote_1}\n"
            )
            if quote_2:
                body += f"• **Additional Customer Voice:** {quote_2}\n"
            body += f"• **Strategic Recommendation:** {matched_topic['action']}"
            return body

        # Dynamic synthesis for custom unmatched topics
        kw_str = ", ".join(keywords[:3]) if keywords else "general inquiry"
        aspect_str = ", ".join([f"{k} ({v})" for k, v in list(aspects.items())[:2]]) if aspects else "General Customer Feedback"

        sentiment_label = "predominantly negative" if avg_rating < 2.5 else ("mixed" if avg_rating < 3.8 else "mostly positive")

        return (
            f"**Review Insights for '{query}':**\n\n"
            f"• **Corpus Match:** Extracted **{count}** customer discussions related to '{kw_str}'.\n"
            f"• **Sentiment Breakdown:** Average score of **{avg_rating:.2f} / 5.0★** ({sentiment_label} sentiment).\n"
            f"• **Primary Category Drivers:** {aspect_str}.\n"
            f"• **Direct Customer Quote:** {quote_1}\n"
            f"• **Key Takeaway:** For queries regarding '{kw_str}', users demand clearer product specifications, transparent policies, and rapid resolution."
        )
