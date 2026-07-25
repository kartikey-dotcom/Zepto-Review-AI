import pytest
from backend.anomaly_detector import VersionAnomalyDetector
from backend.alert_dispatcher import AlertDispatcher

def test_z_score_calculation():
    # Test normal count
    z1 = VersionAnomalyDetector.calculate_z_score(count=10, mean=10.0, std_dev=2.0)
    assert z1 == 0.0

    # Test spike count (Z = (30 - 10) / 5 = 4.0)
    z2 = VersionAnomalyDetector.calculate_z_score(count=30, mean=10.0, std_dev=5.0)
    assert z2 == 4.0

    # Test zero std_dev handling
    z3 = VersionAnomalyDetector.calculate_z_score(count=20, mean=10.0, std_dev=0.0)
    assert z3 > 0.0

def test_alert_dispatcher_payload():
    anomaly = {
        "app_version": "v4.12.0",
        "aspect_category": "App UX & Technical Performance",
        "defect_count": 150,
        "mean_defects": 40.0,
        "std_dev": 25.0,
        "z_score": 4.4,
        "severity": "CRITICAL",
        "sample_snippets": ["App crash ho raha hai pe payment screen pe!"]
    }

    alert = AlertDispatcher.create_alert_payload(anomaly)
    assert "ALT-REG-v4120" in alert["alert_id"]
    assert alert["severity"] == "CRITICAL"
    assert alert["z_score"] == 4.4
    assert len(alert["slack_payload"]["blocks"]) >= 3
    assert alert in AlertDispatcher.get_dispatched_alerts()
