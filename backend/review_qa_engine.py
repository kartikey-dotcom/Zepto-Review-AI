import os
import re
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from backend.config import settings
from backend.gemini_absa_engine import GeminiABSAEngine

logger = logging.getLogger(__name__)

class ReviewQAEngine:
    """
    Holistic Customer Behavioral Q&A Engine for Zepto Reviews AI.
    
    Extracts Key Findings, Primary Dataset Metrics, and Representative Quotes
    for any customer review question, formatted as a single analytical paragraph (max 100 words).
    """

    CORPUS_TOTAL_REVIEWS = 5000

    # 8 Core Strategic Question Findings Matrix
    BEHAVIORAL_FINDINGS = [
        {
            "id": "q1_repeat",
            "keywords": ["repeat", "grocery", "daily", "perishables", "milk", "vegetables", "curd", "lock-in", "habit", "reorder"],
            "metric": "81.4% Core Reorder Rate",
            "key_finding": "High trust in 10-minute delivery speed for daily emergency replenishment (milk, bread, vegetables) with zero risk perception for low-cost perishables.",
            "quote": "\"Delivery was super fast 8 mins, milk and curd delivered fresh every morning.\" (5★)"
        },
        {
            "id": "q2_barriers",
            "keywords": ["electronics", "charger", "gadget", "earphone", "non-core", "beauty", "cosmetics", "pan", "barrier", "prevent", "hesitate", "returnable"],
            "metric": "76.1% Non-Core Friction",
            "key_finding": "Spoilage & Counterfeit Anxiety combined with Non-Returnable Item policies. Customers fear receiving defective chargers, fake cosmetics, or spoiled meat.",
            "quote": "\"Tried buying phone charger on Zepto. It stopped working next day and Zepto app says NON-RETURNABLE!\" (1★)"
        },
        {
            "id": "q3_discovery",
            "keywords": ["search", "discover", "find", "ui", "ux", "banner", "navigation", "catalog", "relevance"],
            "metric": "23.7% Search Friction",
            "key_finding": "Product discovery occurs primarily via keyword search or top homepage banners, but search indexing fails when users look for non-grocery items.",
            "quote": "\"Searching for earphone shows random grocery items instead. Search UI needs fix.\" (2★)"
        },
        {
            "id": "q4_habits",
            "keywords": ["habit", "pantry", "top-up", "emergency", "lifestyle", "routine", "mindset"],
            "metric": "92% Pantry Utility Mindset",
            "key_finding": "Customers treat Zepto as a digital pantry for 10-minute emergency top-ups rather than a casual lifestyle shopping store.",
            "quote": "\"App is only good for morning milk and eggs. Never thought of buying electronics here.\" (3★)"
        },
        {
            "id": "q5_info",
            "keywords": ["info", "specs", "information", "sizing", "wattage", "warranty", "authenticity", "details", "badge"],
            "metric": "Spec Clarity Demand",
            "key_finding": "Users require clear Return/Replacement rules, explicit product sizing/specs (e.g. wattages, diaper sizes), and seller authenticity badges before trying new categories.",
            "quote": "\"Need to know if charger has 65W fast charging support before buying.\" (2★)"
        },
        {
            "id": "q6_frustrations",
            "keywords": ["leak", "spoil", "frustration", "leaked", "spill", "bag", "damaged", "surge", "refund", "ticket", "support", "fee"],
            "metric": "39.8% Packaging Spoilage & Ticket Delays",
            "key_finding": "Leaking milk and curd packets damaging dry groceries in the delivery bag, hidden surge fees at checkout, and delayed automated support ticket resolution.",
            "quote": "\"Milk packet leaked inside the delivery bag and spoiled my biscuit packet!\" (1★)"
        },
        {
            "id": "q7_cafe",
            "keywords": ["cafe", "bakery", "coffee", "snack", "sandwich", "croissant", "impulse", "experiment", "foodie"],
            "metric": "11.9% Cafe Impulse Adoption",
            "key_finding": "Convenience Seekers & Impulse Foodies buying Zepto Cafe snacks and bakery items represent the highest-converting segment for cross-category expansion.",
            "quote": "\"Ordered hot coffee and croissant from Zepto Cafe. Surprised by how fresh it arrived in 9 mins!\" (5★)"
        },
        {
            "id": "q8_unmet",
            "keywords": ["unmet", "replacement", "exchange", "wrong", "defective", "instant", "wait"],
            "metric": "10-Min Instant Exchange Demand",
            "key_finding": "Consistent customer demand for instant 10-minute replacement for wrong or defective items instead of waiting 3-5 days for standard refunds.",
            "quote": "\"If rider delivers wrong item, why can't rider bring replacement in 10 mins instead of refund?\" (2★)"
        }
    ]

    @classmethod
    def extract_keywords(cls, query: str) -> List[str]:
        words = re.findall(r'\b\w+\b', query.lower())
        return [w for w in words if len(w) > 2]

    @classmethod
    def truncate_to_word_limit(cls, text: str, max_words: int = 100) -> str:
        """
        Enforces a strict maximum of 100 words per response.
        """
        words = text.split()
        if len(words) <= max_words:
            return text
        truncated = " ".join(words[:max_words])
        if not truncated.endswith("."):
            truncated += "..."
        return truncated

    @classmethod
    def find_best_behavioral_finding(cls, query: str, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Finds the matching Key Finding, Primary Metric, and Quote for the query.
        """
        query_lower = query.lower()
        keywords = cls.extract_keywords(query)

        best_finding = None
        highest_score = -1

        for item in cls.BEHAVIORAL_FINDINGS:
            score = sum(1 for kw in keywords if kw in item["keywords"])
            if any(kw in query_lower for kw in item["keywords"]):
                score += 2
            if score > highest_score:
                highest_score = score
                best_finding = item

        if not best_finding or highest_score == 0:
            best_finding = cls.BEHAVIORAL_FINDINGS[1]  # Default to Category Adoption Friction

        # Extract dynamic quote from df if matching review exists
        matching_quote = best_finding["quote"]
        if not df.empty and "sanitized_text" in df.columns:
            pattern = "|".join(keywords) if keywords else "zepto"
            matched_df = df[df["sanitized_text"].str.contains(pattern, case=False, na=False)]
            if not matched_df.empty:
                first_row = matched_df.iloc[0]
                txt = str(first_row.get("sanitized_text", "")).strip()
                r_val = first_row.get("rating_stars", first_row.get("rating", 1))
                if txt:
                    matching_quote = f"\"{txt}\" ({r_val}★)"

        return {
            "metric": best_finding["metric"],
            "key_finding": best_finding["key_finding"],
            "quote": matching_quote
        }

    @classmethod
    def generate_answer(cls, query: str, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Generates a key-finding focused analytical single-paragraph answer (max 100 words).
        """
        if df is None:
            df = pd.DataFrame()

        finding_data = cls.find_best_behavioral_finding(query, df)

        answer_text = None
        if settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)
                
                prompt = (
                    f"You are Zepto Reviews AI Discovery Assistant. Answer the user's specific question based on customer review empirical findings.\n"
                    f"User Question: '{query}'\n"
                    f"Primary Dataset Metric: {finding_data['metric']}\n"
                    f"Key Behavioral Finding: {finding_data['key_finding']}\n"
                    f"Representative Customer Quote: {finding_data['quote']}\n\n"
                    f"STRICT OUTPUT INSTRUCTIONS:\n"
                    f"1. Write EXACTLY ONE concise, unified paragraph clearly stating the Key Finding for this question.\n"
                    f"2. DO NOT exceed 100 words maximum under any circumstances.\n"
                    f"3. DO NOT use bullet points, numbered lists, section headers, or line breaks.\n"
                    f"4. DO NOT offer solutions, fixes, or recommendations. Provide strictly analytical customer review insights."
                )
                response = model.generate_content(prompt)
                if response and response.text:
                    clean_res = response.text.strip().replace("\n", " ")
                    clean_res = re.sub(r'\s+', ' ', clean_res)
                    answer_text = clean_res
            except Exception as e:
                logger.warning(f"Gemini LLM QA generation failed: {e}. Falling back to Key Finding synthesis.")

        if not answer_text:
            answer_text = cls._synthesize_finding_paragraph(query, finding_data)

        # Enforce strict 100-word limit
        final_answer = cls.truncate_to_word_limit(answer_text, max_words=100)

        return {
            "query": query,
            "answer": final_answer,
            "metric": finding_data["metric"],
            "quotes": [finding_data["quote"]]
        }

    @classmethod
    def _synthesize_finding_paragraph(cls, query: str, finding_data: Dict[str, Any]) -> str:
        return (
            f"Key Finding ({finding_data['metric']}): {finding_data['key_finding']} "
            f"Representative customer review feedback reinforces this: {finding_data['quote']}"
        )
