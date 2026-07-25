import datetime
from typing import AsyncGenerator
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from backend.config import settings

Base = declarative_base()

class PlayStoreReview(Base):
    __tablename__ = "playstore_reviews"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    review_id = Column(String(255), unique=True, index=True, nullable=False)
    user_name_sanitized = Column(String(255), nullable=True)
    rating_stars = Column(Integer, nullable=False, index=True)
    raw_text = Column(Text, nullable=False)
    sanitized_text = Column(Text, nullable=False)
    app_version = Column(String(50), nullable=True, index=True)
    thumbs_up_count = Column(Integer, default=0)
    language_code = Column(String(20), default="unknown")
    overall_sentiment = Column(Float, nullable=True)
    urgency_level = Column(String(20), default="MEDIUM")
    review_created_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    aspects = relationship("AspectSentiment", back_populates="review", cascade="all, delete-orphan")
    replies = relationship("DeveloperReply", back_populates="review", cascade="all, delete-orphan")

class AspectSentiment(Base):
    __tablename__ = "aspect_sentiments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    playstore_review_id = Column(Integer, ForeignKey("playstore_reviews.id"), nullable=False)
    aspect_category = Column(String(100), nullable=False, index=True)
    sentiment_score = Column(Float, nullable=False)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    review = relationship("PlayStoreReview", back_populates="aspects")

class DeveloperReply(Base):
    __tablename__ = "developer_replies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    playstore_review_id = Column(Integer, ForeignKey("playstore_reviews.id"), nullable=False)
    draft_reply_text = Column(Text, nullable=False)
    published_reply_text = Column(Text, nullable=True)
    status = Column(String(50), default="DRAFT", index=True)  # DRAFT, APPROVED, PUBLISHED, REJECTED
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)
    published_at = Column(DateTime, nullable=True)

    review = relationship("PlayStoreReview", back_populates="replies")

class VersionAnomaly(Base):
    __tablename__ = "version_anomalies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    app_version = Column(String(50), nullable=False, index=True)
    aspect_category = Column(String(100), nullable=False)
    z_score = Column(Float, nullable=False)
    defect_count = Column(Integer, nullable=False)
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)

# Engine & Session setup
engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
