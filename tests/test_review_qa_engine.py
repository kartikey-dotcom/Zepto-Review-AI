import pytest
import pandas as pd
from backend.review_qa_engine import ReviewQAEngine

def test_search_relevant_reviews():
    data = [
        {"rating_stars": 1, "sanitized_text": "Charger stopped working on Zepto app", "primary_aspect": "Non-Core"},
        {"rating_stars": 5, "sanitized_text": "Milk delivered super fast in 8 mins", "primary_aspect": "Delivery"},
        {"rating_stars": 1, "sanitized_text": "Milk leaked inside the delivery bag", "primary_aspect": "Spoilage"}
    ]
    df = pd.DataFrame(data)

    matched = ReviewQAEngine.search_relevant_reviews("milk leak", df)
    assert not matched.empty
    assert len(matched) >= 1

def test_generate_answer_rule_based():
    data = [
        {"rating_stars": 1, "sanitized_text": "Tried buying phone charger on Zepto. Non-returnable!", "primary_aspect": "Non-Core Category Adoption Friction"},
        {"rating_stars": 5, "sanitized_text": "Delivery fresh milk every morning", "primary_aspect": "Delivery Speed & Rider Behavior"}
    ]
    df = pd.DataFrame(data)

    res = ReviewQAEngine.generate_answer("Why do electronics fail?", df)
    assert res["query"] == "Why do electronics fail?"
    assert "Non-Core" in res["answer"]
    assert res["total_matched"] >= 1
