import pytest
from backend.gemini_absa_engine import GeminiABSAEngine

def test_absa_aspect_classification_app_ux():
    text = "App crash ho raha hai payment screen pe after latest update v4.12.0 for refund."
    res = GeminiABSAEngine.classify_aspect_rule_based(text, rating=1)
    assert res["primary_aspect"] == "App UX & Technical Performance"
    assert res["sentiment_score"] < 0
    assert res["is_critical"] is True

def test_absa_aspect_classification_delivery():
    text = "Delivery took 45 minutes instead of 10 mins! Rider was rude and dropped items."
    res = GeminiABSAEngine.classify_aspect_rule_based(text, rating=1)
    assert res["primary_aspect"] == "Delivery Speed & Rider Behavior"

def test_absa_aspect_classification_quality():
    text = "Curd packet was torn and leaked over bread and eggs in my bag!"
    res = GeminiABSAEngine.classify_aspect_rule_based(text, rating=1)
    assert res["primary_aspect"] == "Product Quality & Packaging Spoilage"

def test_absa_aspect_classification_category_adoption():
    text = "Ordered raw chicken from Zepto Meat section. Blood leaked all over my milk."
    res = GeminiABSAEngine.classify_aspect_rule_based(text, rating=1)
    assert res["primary_aspect"] == "Non-Core Category Adoption Friction"

@pytest.mark.asyncio
async def test_absa_batch_analysis():
    batch = [
        {"review_id": "gp:101", "sanitized_text": "Super fast 7 minute delivery! Fresh milk delivered.", "rating": 5},
        {"review_id": "gp:102", "sanitized_text": "App crash on payment screen refund pending.", "rating": 1}
    ]
    results = await GeminiABSAEngine.analyze_batch(batch)
    assert len(results) == 2
    assert results[0]["review_id"] == "gp:101"
    assert results[0]["primary_aspect"] == "Delivery Speed & Rider Behavior"
