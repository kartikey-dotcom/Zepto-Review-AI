import pytest
from backend.data_normalizer import DataNormalizer

def test_short_review_rejected():
    text = "Bad app service"  # 3 words
    valid, reason, _ = DataNormalizer.validate_and_normalize(text)
    assert valid is False
    assert "word_count_too_short" in reason

def test_seven_words_review_rejected():
    text = "This app is very bad and slow"  # 7 words
    valid, reason, _ = DataNormalizer.validate_and_normalize(text)
    assert valid is False
    assert "word_count_too_short" in reason

def test_eight_words_review_accepted():
    text = "This app is very bad slow and not working"  # 8 words
    valid, reason, _ = DataNormalizer.validate_and_normalize(text)
    assert valid is True
    assert reason == "valid"

def test_review_with_emojis_rejected():
    text = "Awesome delivery in 7 minutes flat! Love Zepto service very much 👏🔥"
    valid, reason, _ = DataNormalizer.validate_and_normalize(text)
    assert valid is False
    assert reason == "contains_emojis"

def test_review_with_devanagari_hindi_rejected():
    text = "ऐप बहुत खराब है delivery rider was extremely delayed and rude"
    valid, reason, _ = DataNormalizer.validate_and_normalize(text)
    assert valid is False
    assert reason == "contains_non_latin_script"

def test_valid_hinglish_review_accepted():
    text = "App crash ho raha hai pe payment screen pe after latest update v4.12.0 for refund."
    valid, reason, _ = DataNormalizer.validate_and_normalize(text)
    assert valid is True
    assert reason == "valid"
