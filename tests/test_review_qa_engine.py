import pytest
import pandas as pd
from backend.review_qa_engine import ReviewQAEngine

def test_retrieve_matching_reviews():
    data = [
        {"rating_stars": 1, "sanitized_text": "Charger stopped working on Zepto app", "primary_aspect": "Non-Core"},
        {"rating_stars": 5, "sanitized_text": "Milk delivered super fast in 8 mins", "primary_aspect": "Delivery"}
    ]
    df = pd.DataFrame(data)

    matched = ReviewQAEngine.retrieve_matching_reviews("milk delivery speed", df)
    assert not matched.empty
    assert len(matched) >= 1

def test_generate_answer_dynamic_distinct():
    data = [
        {"rating_stars": 1, "sanitized_text": "Tried buying phone charger on Zepto. Non-returnable!", "primary_aspect": "Non-Core Category Adoption Friction"},
        {"rating_stars": 1, "sanitized_text": "Milk packet leaked inside delivery bag", "primary_aspect": "Product Quality & Packaging Spoilage"},
        {"rating_stars": 2, "sanitized_text": "App crash during checkout when applying promo code", "primary_aspect": "App UX & Technical Performance"}
    ]
    df = pd.DataFrame(data)

    ans_elec = ReviewQAEngine.generate_answer("Why do electronics fail?", df)
    ans_milk = ReviewQAEngine.generate_answer("What about milk leakage?", df)

    assert isinstance(ans_elec["answer"], str)
    assert len(ans_elec["answer"]) > 20

    # Must be strictly 100 words maximum
    words_count = len(ans_elec["answer"].split())
    assert words_count <= 100

    # Must not contain bullet points or section segment markers
    assert "•" not in ans_elec["answer"]
    assert "\n" not in ans_elec["answer"]
    assert "Recommended Action" not in ans_elec["answer"]

    # Answers must be distinct per topic
    assert ans_elec["answer"] != ans_milk["answer"]
