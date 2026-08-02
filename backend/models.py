import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class IngestReviewRequest(BaseModel):
    review_id: str = Field(..., description="Unique Play Store review ID (e.g. gp:AOqpTOE_...)")
    user_name: Optional[str] = Field("Google User", description="Reviewer name on Play Store")
    rating: int = Field(..., ge=1, le=5, description="Star rating 1 to 5")
    review_text: str = Field(..., description="Raw text content of the review")
    app_version: Optional[str] = Field("v4.12.0", description="Zepto app version string")
    platform: Optional[str] = Field("play_store", description="Source platform: play_store, app_store, or reddit")
    thumbs_up_count: Optional[int] = Field(0, description="Number of thumbs up on Play Store")
    review_timestamp: Optional[str] = Field(None, description="ISO format creation timestamp")

class IngestBatchRequest(BaseModel):
    reviews: List[IngestReviewRequest]

class ScrapeRequest(BaseModel):
    count: int = Field(20, ge=1, le=200, description="Number of Play Store reviews to fetch")

class ReviewResponse(BaseModel):
    id: int
    review_id: str
    user_name_sanitized: Optional[str]
    rating_stars: int
    raw_text: str
    sanitized_text: str
    app_version: Optional[str]
    platform: str = "play_store"
    thumbs_up_count: int
    language_code: str
    pii_detected: bool = False
    redaction_summary: Dict[str, int] = {}
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class PaginatedReviewResponse(BaseModel):
    total_count: int
    page: int
    page_size: int
    reviews: List[ReviewResponse]

class SystemHealthResponse(BaseModel):
    status: str
    project_name: str
    target_package: str
    database_status: str
    total_reviews_ingested: int
    timestamp: datetime.datetime

class VersionAnomalyResponse(BaseModel):
    app_version: str
    aspect_category: str
    defect_count: int
    mean_defects: float
    std_dev: float
    z_score: float
    severity: str
    total_version_reviews: int
    defect_percentage: float
    sample_snippets: List[str] = []

class AnomalyDetectionSummary(BaseModel):
    status: str
    total_reviews_analyzed: int
    app_versions_scanned: int
    anomalies_detected_count: int
    anomalies: List[VersionAnomalyResponse]
