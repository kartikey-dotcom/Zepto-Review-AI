import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, case
from backend.database import PlayStoreReview
from backend.data_normalizer import DataNormalizer

logger = logging.getLogger(__name__)

# Category definitions
NON_CORE_CATEGORIES = {
    "Electronics & Gadgets": ["electronics", "gadget", "charger", "cable", "earphone", "headphones", "powerbank", "usb", "adapter"],
    "Beauty & Personal Care": ["lipstick", "beauty", "cosmetics", "makeup", "shampoo", "skincare", "lotion", "serum", "face wash"],
    "Meat, Seafood & Eggs": ["meat", "chicken", "fish", "mutton", "seafood", "prawns", "raw meat"],
    "Zepto Cafe & Bakery": ["cafe", "croissant", "coffee", "sandwich", "bakery", "hot beverage", "snack box"],
    "Home & Kitchen Essentials": ["pan", "cookware", "utensil", "container", "mop", "detergent", "cleaning", "battery"],
    "Baby & Pet Care": ["diaper", "wipes", "baby food", "dog food", "cat food", "pet care"]
}

FRICTION_TYPES = {
    "Quality & Spoilage Anxiety": ["defect", "broken", "duplicate", "fake", "stale", "spoiled", "damaged", "expiry", "expired", "warranty"],
    "App Search & Discovery Friction": ["search", "find", "missing category", "ui", "hidden", "filter", "layout", "banner", "not showing"],
    "Pricing, Surge & Coupon Friction": ["expensive", "surge", "coupon", "discount", "offer", "handling fee", "delivery charge", "price high"],
    "Return & Refund Policy Doubt": ["return", "replace", "refund delay", "customer care", "replacement", "no return", "policy"],
    "Habitual Emergency Grocery Lock-In": ["only milk", "vegetables only", "daily grocery", "10 min grocery", "routine", "emergency reorder"]
}

class CategoryAdoptionAnalyzer:
    """
    Core Analytics Engine analyzing customer order repetition and category switching barriers for Zepto.
    Identifies why customers repeat primary grocery orders and resist switching to higher-margin non-core categories.
    """

    @classmethod
    async def analyze_category_friction_patterns(cls, db: AsyncSession) -> Dict[str, Any]:
        """
        Scans all normalized reviews to detect category switching barriers, friction breakdown,
        and growth recommendations for Zepto product and marketing teams.
        """
        stmt = select(PlayStoreReview)
        res = await db.execute(stmt)
        reviews = res.scalars().all()

        total_reviews = len(reviews)
        if total_reviews == 0:
            return {"status": "no_data", "message": "No reviews available for analysis."}

        # Track Category Mention Counts & Friction
        category_mentions: Dict[str, List[PlayStoreReview]] = {cat: [] for cat in NON_CORE_CATEGORIES.keys()}
        category_mentions["Core Grocery & Daily Essentials"] = []

        friction_counts: Dict[str, int] = {f_type: 0 for f_type in FRICTION_TYPES.keys()}
        friction_snippets: Dict[str, List[str]] = {f_type: [] for f_type in FRICTION_TYPES.keys()}

        for r in reviews:
            txt_lower = r.sanitized_text.lower()
            matched_category = False

            # Check Non-Core Category Mentions
            for cat_name, keywords in NON_CORE_CATEGORIES.items():
                if any(kw in txt_lower for kw in keywords):
                    category_mentions[cat_name].append(r)
                    matched_category = True

            if not matched_category:
                category_mentions["Core Grocery & Daily Essentials"].append(r)

            # Check Friction Type Keywords
            for f_type, f_keywords in FRICTION_TYPES.items():
                if any(kw in txt_lower for kw in f_keywords):
                    friction_counts[f_type] += 1
                    if len(friction_snippets[f_type]) < 3:
                        friction_snippets[f_type].append(r.sanitized_text)

        # Build Category Breakdown Metrics
        category_breakdown = []
        for cat_name, cat_reviews in category_mentions.items():
            cnt = len(cat_reviews)
            pct = round((cnt / total_reviews) * 100, 1)
            neg_cnt = sum(1 for r in cat_reviews if r.rating_stars <= 2)
            avg_rating = round(sum(r.rating_stars for r in cat_reviews) / cnt, 2) if cnt > 0 else 0.0

            category_breakdown.append({
                "category_name": cat_name,
                "review_count": cnt,
                "percentage_of_total": pct,
                "average_rating": avg_rating,
                "dissatisfaction_rate": round((neg_cnt / cnt * 100), 1) if cnt > 0 else 0.0,
                "is_non_core": cat_name != "Core Grocery & Daily Essentials"
            })

        # Calculate Friction Percentages
        total_frictions_detected = sum(friction_counts.values()) or 1
        friction_breakdown = []
        for f_type, cnt in friction_counts.items():
            friction_breakdown.append({
                "friction_type": f_type,
                "count": cnt,
                "percentage": round((cnt / total_frictions_detected) * 100, 1),
                "sample_snippets": friction_snippets[f_type]
            })

        # Sort friction breakdown by count descending
        friction_breakdown.sort(key=lambda x: x["count"], reverse=True)

        # Strategic Actionable Growth Recommendations for Zepto Product & Marketing Teams
        strategic_recommendations = [
            {
                "pillar": "Trust & Return Guarantee for Non-Core Items",
                "action": "Introduce 'Zepto Assured 3-Day Easy Return' badge on Electronics and Beauty items to eliminate spoilage and counterfeit fears.",
                "target_category": "Electronics & Beauty"
            },
            {
                "pillar": "Cross-Category Nudge at Checkout",
                "action": "Add smart contextual add-ons on the Cart screen (e.g. 'Add Phone Charger for Rs. 199 with your daily groceries').",
                "target_category": "All Non-Core Categories"
            },
            {
                "pillar": "Discovery & UI Search Navigation",
                "action": "Fix search relevance bugs for non-grocery items and elevate 'Zepto Cafe & Electronics' tab visibility on the app homepage.",
                "target_category": "Zepto Cafe & Home Essentials"
            }
        ]

        return {
            "status": "success",
            "total_reviews_analyzed": total_reviews,
            "core_grocery_repetition_pct": category_breakdown[-1]["percentage_of_total"],
            "non_core_category_adoption_pct": round(100 - category_breakdown[-1]["percentage_of_total"], 1),
            "category_breakdown": category_breakdown,
            "category_switching_friction_barriers": friction_breakdown,
            "strategic_growth_recommendations": strategic_recommendations
        }
