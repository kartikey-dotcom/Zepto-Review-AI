import pytest
from backend.pii_sanitizer import PIISanitizer

def test_pii_phone_number_redaction():
    text = "App crashed! Call me on 9876543210 for refund."
    res = PIISanitizer.sanitize_text(text)
    assert res["pii_detected"] is True
    assert "[PHONE_REDACTED]" in res["sanitized_text"]
    assert "9876543210" not in res["sanitized_text"]

def test_pii_email_redaction():
    text = "Charged twice for order. Send receipt to rahul.s@gmail.com please."
    res = PIISanitizer.sanitize_text(text)
    assert res["pii_detected"] is True
    assert "[EMAIL_REDACTED]" in res["sanitized_text"]
    assert "rahul.s@gmail.com" not in res["sanitized_text"]

def test_pii_order_id_redaction():
    text = "Order ORD-991823 was delayed by 45 mins. Spoiled milk received."
    res = PIISanitizer.sanitize_text(text)
    assert res["pii_detected"] is True
    assert "[ORDER_ID_REDACTED]" in res["sanitized_text"]
    assert "ORD-991823" not in res["sanitized_text"]

def test_pii_address_redaction():
    text = "Rider dropped items at Flat 402 Sector 4 HSR Layout without calling."
    res = PIISanitizer.sanitize_text(text)
    assert res["pii_detected"] is True
    assert "[ADDRESS_REDACTED]" in res["sanitized_text"]

def test_pii_word_digit_normalization():
    text = "Call me on nine eight seven six five four three two one zero"
    res = PIISanitizer.sanitize_text(text)
    assert res["pii_detected"] is True
    assert "[PHONE_REDACTED]" in res["sanitized_text"]

def test_clean_review_no_pii():
    text = "Zepto delivery is super fast! Got fresh milk in 8 minutes."
    res = PIISanitizer.sanitize_text(text)
    assert res["pii_detected"] is False
    assert res["sanitized_text"] == text

def test_user_name_anonymization():
    assert PIISanitizer.sanitize_user_name("Rahul Sharma") == "Rahul S."
    assert PIISanitizer.sanitize_user_name("A Google User") == "Zepto User"
    assert PIISanitizer.sanitize_user_name("Ankit") == "A."
