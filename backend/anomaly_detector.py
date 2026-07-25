import math
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.database import PlayStoreReview, AspectSentiment, VersionAnomaly
from backend.gemini_absa_engine import GeminiABSAEngine

logger = logging.getLogger(__name__)

class VersionAnomalyDetector:
    """
    App Version Regression & Statistical Anomaly Detector for Zepto Reviews AI.
    
    Calculates sliding-window Z-scores per app_version and aspect_category.
    Formula: Z = (x - mu) / sigma
    Threshold Rule: Z > 3.0 triggers P0 Critical Alert, Z > 2.0 triggers P1 High Alert.
    """

    CRITICAL_Z_THRESHOLD = 3.0
    HIGH_Z_THRESHOLD = 2.0

    @classmethod
    def calculate_z_score(cls, count: float, mean: float, std_dev: float) -> float:
        """Calculates statistical Z-score with division by zero safety."""
        if std_dev == 0.0 or math.isnan(std_dev):
            if count > mean:
                return 2.5 if count > mean * 1.5 else 1.5
            return 0.0
        return round((count - mean) / std_dev, 2)

    @classmethod
    async def detect_anomalies_from_db(cls, db: AsyncSession, min_samples: int = 5) -> Dict[str, Any]:
        """
        Scans all ingested reviews, groups defects by app_version and aspect_category,
        calculates statistical Z-scores across versions, and identifies anomalies.
        """
        # Fetch all reviews
        stmt = select(PlayStoreReview)
        res = await db.execute(stmt)
        reviews = res.scalars().all()

        if not reviews:
            return {"status": "no_data", "total_reviews": 0, "anomalies": []}

        # Build Version -> Aspect -> Defect Count mapping
        # A review is a "defect" if rating <= 2 or sentiment_score < 0
        version_aspect_counts: Dict[str, Dict[str, int]] = {}
        version_total_reviews: Dict[str, int] = {}
        version_aspect_snippets: Dict[str, Dict[str, List[str]]] = {}

        for r in reviews:
            ver = r.app_version or "v4.12.0"
            version_total_reviews[ver] = version_total_reviews.get(ver, 0) + 1

            # Rule-based aspect resolution for consistent detection
            analysis = GeminiABSAEngine.classify_aspect_rule_based(r.sanitized_text, r.rating_stars)
            aspect = analysis["primary_aspect"]

            if ver not in version_aspect_counts:
                version_aspect_counts[ver] = {}
                version_aspect_snippets[ver] = {}

            if aspect not in version_aspect_counts[ver]:
                version_aspect_counts[ver][aspect] = 0
                version_aspect_snippets[ver][aspect] = []

            if r.rating_stars <= 2 or analysis["sentiment_score"] < 0:
                version_aspect_counts[ver][aspect] += 1
                if len(version_aspect_snippets[ver][aspect]) < 3:
                    version_aspect_snippets[ver][aspect].append(r.sanitized_text)

        all_versions = list(version_aspect_counts.keys())
        all_aspects = list(set(
            aspect for ver_data in version_aspect_counts.values() for aspect in ver_data.keys()
        ))

        detected_anomalies = []

        # Calculate Z-score per aspect across all versions
        for aspect in all_aspects:
            counts_by_ver = {ver: version_aspect_counts[ver].get(aspect, 0) for ver in all_versions}
            counts_list = list(counts_by_ver.values())

            if not counts_list:
                continue

            mean_val = sum(counts_list) / len(counts_list)
            variance = sum((x - mean_val) ** 2 for x in counts_list) / len(counts_list)
            std_dev = math.sqrt(variance)

            for ver in all_versions:
                count = counts_by_ver[ver]
                z_score = cls.calculate_z_score(count, mean_val, std_dev)

                if z_score >= cls.HIGH_Z_THRESHOLD:
                    severity = "CRITICAL" if z_score >= cls.CRITICAL_Z_THRESHOLD else "HIGH"
                    snippets = version_aspect_snippets.get(ver, {}).get(aspect, [])

                    anomaly_data = {
                        "app_version": ver,
                        "aspect_category": aspect,
                        "defect_count": count,
                        "mean_defects": round(mean_val, 2),
                        "std_dev": round(std_dev, 2),
                        "z_score": z_score,
                        "severity": severity,
                        "total_version_reviews": version_total_reviews.get(ver, 0),
                        "defect_percentage": round((count / version_total_reviews.get(ver, 1)) * 100, 1),
                        "sample_snippets": snippets
                    }
                    detected_anomalies.append(anomaly_data)

                    # Persist anomaly into DB table
                    db_anomaly = VersionAnomaly(
                        app_version=ver,
                        aspect_category=aspect,
                        z_score=z_score,
                        defect_count=count
                    )
                    db.add(db_anomaly)

        await db.commit()

        # Sort anomalies by Z-score descending
        detected_anomalies.sort(key=lambda x: x["z_score"], reverse=True)

        logger.info(f"Anomaly Detection Completed. Found {len(detected_anomalies)} version regression anomalies.")

        return {
            "status": "success",
            "total_reviews_analyzed": len(reviews),
            "app_versions_scanned": len(all_versions),
            "anomalies_detected_count": len(detected_anomalies),
            "anomalies": detected_anomalies
        }
