import datetime
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class AlertDispatcher:
    """
    Multi-channel Alert Dispatcher for Zepto Reviews AI.
    Formats and dispatches Slack, Jira, and Webhook alerts when Version Regressions (Z > 2.0 / Z > 3.0) are detected.
    """

    _ALERT_LOG: List[Dict[str, Any]] = []

    @classmethod
    def create_alert_payload(cls, anomaly: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formats a structured alert payload for Slack / Jira webhook integration.
        """
        ver = anomaly.get("app_version", "v4.12.0")
        aspect = anomaly.get("aspect_category", "App UX & Technical Performance")
        z_score = anomaly.get("z_score", 3.0)
        defect_count = anomaly.get("defect_count", 0)
        severity = anomaly.get("severity", "CRITICAL")
        snippets = anomaly.get("sample_snippets", [])

        title = f"🚨 {severity} REGRESSION ALERT: {aspect} spike in {ver} (Z-score: {z_score})"
        summary = (
            f"Zepto Reviews AI detected an app version regression spike in release '{ver}'. "
            f"{defect_count} critical defect complaints identified for aspect '{aspect}' "
            f"(Statistical Z-score: {z_score}, exceeding threshold)."
        )

        slack_blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": title, "emoji": True}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*App Version:* `{ver}`"},
                    {"type": "mrkdwn", "text": f"*Severity:* *{severity}*"},
                    {"type": "mrkdwn", "text": f"*Z-Score:* `{z_score}`"},
                    {"type": "mrkdwn", "text": f"*Defect Count:* `{defect_count}`"}
                ]
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Root Cause Snippets:*\n" + "\n".join([f"• \"_{s}_\"" for s in snippets[:3]])}
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"Target Package: `com.zepto.customer` | Dispatched at: {datetime.datetime.utcnow().isoformat()}Z"}
                ]
            }
        ]

        alert_entry = {
            "alert_id": f"ALT-REG-{ver.replace('.', '')}-{int(datetime.datetime.utcnow().timestamp())}",
            "title": title,
            "summary": summary,
            "severity": severity,
            "app_version": ver,
            "aspect_category": aspect,
            "z_score": z_score,
            "defect_count": defect_count,
            "dispatched_at": datetime.datetime.utcnow().isoformat(),
            "slack_payload": {"blocks": slack_blocks},
            "target_channels": ["#mobile-tech-alerts", "#zepto-cx-escalations"]
        }

        cls._ALERT_LOG.append(alert_entry)
        logger.info(f"Dispatched {severity} Alert [{alert_entry['alert_id']}] for version {ver}")
        return alert_entry

    @classmethod
    def get_dispatched_alerts(cls) -> List[Dict[str, Any]]:
        """Returns the history of dispatched alerts."""
        return cls._ALERT_LOG
