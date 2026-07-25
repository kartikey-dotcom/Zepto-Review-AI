import pytest
from backend.developer_reply_generator import DeveloperReplyGenerator

def test_developer_reply_character_limit_enforced():
    reply_obj = DeveloperReplyGenerator.generate_reply(
        review_text="App crash on payment screen after update v4.12.0!",
        rating=1,
        primary_aspect="App UX & Technical Performance"
    )
    assert reply_obj["is_valid_length"] is True
    assert reply_obj["character_count"] <= 350
    assert len(reply_obj["developer_reply"]) <= 350

def test_developer_reply_tone_for_5_stars():
    reply_obj = DeveloperReplyGenerator.generate_reply(
        review_text="Super fast delivery in 7 minutes! Fresh milk delivered safely.",
        rating=5,
        primary_aspect="Delivery Speed & Rider Behavior"
    )
    assert "Thank you so much" in reply_obj["developer_reply"]
    assert reply_obj["character_count"] <= 350

def test_developer_reply_no_pii_leakage():
    reply_obj = DeveloperReplyGenerator.generate_reply(
        review_text="Charged twice for Order [ORDER_ID_REDACTED]! Call [PHONE_REDACTED]",
        rating=1,
        primary_aspect="Pricing, Surge & Refund Delays"
    )
    reply_text = reply_obj["developer_reply"]
    assert "[PHONE_REDACTED]" not in reply_text
    assert "9876543210" not in reply_text
    assert reply_obj["character_count"] <= 350
