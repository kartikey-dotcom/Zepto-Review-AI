import pytest
import pandas as pd
from backend.review_qa_engine import ReviewQAEngine

def test_find_best_behavioral_finding():
    data = [
        {"rating_stars": 1, "sanitized_text": "Charger stopped working on Zepto app", "primary_aspect": "Non-Core"},
        {"rating_stars": 5, "sanitized_text": "Milk delivered super fast in 8 mins", "primary_aspect": "Delivery"}
    ]
    df = pd.DataFrame(data)

    finding = ReviewQAEngine.find_best_behavioral_finding("milk repeat reorder speed", df)
    assert "81.4%" in finding["metric"]
    assert "Key Finding" not in finding["metric"]

def test_generate_answer_key_finding_format():
    data = [
        {"rating_stars": 1, "sanitized_text": "Tried buying phone charger on Zepto. Non-returnable!", "primary_aspect": "Non-Core Category Adoption Friction"},
        {"rating_stars": 1, "sanitized_text": "Milk packet leaked inside delivery bag", "primary_aspect": "Product Quality & Packaging Spoilage"},
        {"rating_stars": 2, "sanitized_text": "App crash during checkout when applying promo code", "primary_aspect": "App UX & Technical Performance"}
    ]
    df = pd.DataFrame(data)

    ans_elec = ReviewQAEngine.generate_answer("Why do users hesitate to buy electronics?", df)
    ans_milk = ReviewQAEngine.generate_answer("What causes milk leakage packaging issues?", df)

    assert isinstance(ans_elec["answer"], str)
    assert len(ans_elec["answer"]) > 20

    # Must be Key Finding focused
    assert "Key Finding" in ans_elec["answer"] or "76.1%" in ans_elec["answer"]

    # Must be strictly 100 words maximum
    words_count = len(ans_elec["answer"].split())
    assert words_count <= 100

    # Must not contain bullet points or line breaks
    assert "•" not in ans_elec["answer"]
    assert "\n" not in ans_elec["answer"]

    # Answers must be distinct per topic
    assert ans_elec["answer"] != ans_milk["answer"]
