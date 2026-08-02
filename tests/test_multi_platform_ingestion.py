import pytest
from backend.appstore_scraper import AppStoreScraperConnector
from backend.reddit_scraper import RedditScraperConnector

def test_appstore_scraper_synthetic():
    reviews = AppStoreScraperConnector.get_synthetic_appstore_reviews(50)
    assert len(reviews) == 50
    for r in reviews:
        assert r["platform"] == "app_store"
        assert "review_id" in r
        assert "review_text" in r
        assert r["rating"] >= 1 and r["rating"] <= 5

def test_reddit_scraper_synthetic():
    discussions = RedditScraperConnector.get_synthetic_reddit_discussions(50)
    assert len(discussions) == 50
    for d in discussions:
        assert d["platform"] == "reddit"
        assert "review_id" in d
        assert "review_text" in d
        assert d["rating"] >= 1 and d["rating"] <= 5
