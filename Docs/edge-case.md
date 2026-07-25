# Zepto Reviews AI — Edge-Case & Boundary Scenario Analysis

**Project Title:** Zepto Reviews AI  
**Domain:** Quick Commerce (Q-Commerce) / AI System Reliability & Edge-Case Governance  
**Active Build Scope:** Google Play Store Reviews (Phase 1 Focus)  
**Document Version:** 1.1.0  
**Status:** Approved Technical Risk & Edge-Case Reference  
**Reference Documents:**  
* [ProblemStatement.md](file:///c:/Users/DELL/OneDrive/Desktop/Krishna/Zepto%20Reviews%20AI/Docs/ProblemStatement.md)  
* [Architecture.md](file:///c:/Users/DELL/OneDrive/Desktop/Krishna/Zepto%20Reviews%20AI/Docs/Architecture.md)  
* [PhasewiseImplementation.md](file:///c:/Users/DELL/OneDrive/Desktop/Krishna/Zepto%20Reviews%20AI/Docs/PhasewiseImplementation.md)  

---

## 1. Executive Overview

This document provides a comprehensive analysis of **Edge-Case Scenarios**, failure modes, and automated safeguards specifically engineered for processing **Google Play Store Reviews** for Zepto.

---

## 2. Play Store Edge-Case Taxonomy & Safeguards

### Category 1: Play Store Platform & API Constraints

#### E1.1 Play Store Developer Reply Character Limit Violation
* **Scenario:** Generated AI developer reply draft exceeds the strict Google Play Developer Console limit of **350 characters**.
* **Risk:** API reject error when publishing response to Play Store console.
* **System Safeguard:**
  * **Prompt Hard Constraint & Post-Truncation Guard:** Prompt includes explicit constraint: `"Maximum response length: 300 characters"`. Post-processor validates `len(reply_text) <= 350` before queuing for console API dispatch.

#### E1.2 Play Store Scraper IP Rate-Limiting & Anti-Bot Blocking
* **Scenario:** Polling Google Play Store scraper hits HTTP 429 / 403 Rate Limit during high-frequency review ingestion.
* **Risk:** Ingestion stream drops review updates for hours.
* **System Safeguard:**
  * **Proxy Rotation & Fallback to Developer API:** Implement proxy pool with residential IP rotation; fallback to official Google Play Developer API (OAuth Service Account) whenever scraper rate limits occur.

#### E1.3 Edited / Updated Play Store Reviews
* **Scenario:** Customer updates an existing Play Store review from 1 star (*"App crashed"*) to 5 stars (*"Issue fixed, great service!"*).
* **Risk:** Duplicate database entries; outdated negative sentiment score remaining in metrics.
* **System Safeguard:**
  * **Upsert on `review_id`:** Database uses `ON CONFLICT (review_id) DO UPDATE` to re-run ABSA and recalculate overall app sentiment when a review is modified.

---

### Category 2: Linguistic & Technical Edge Cases

#### E2.1 App Version Regression Spike (New Release Bug)
* **Scenario:** Zepto releases `app_version: v4.12.0`. Within 1 hour, 150 1-star reviews complain *"Payment screen black screen crash"*.
* **Risk:** App rating tanks; slow developer awareness.
* **System Safeguard:**
  * **Version Regression Alerting:** Sliding window Z-score per `app_version`. When $Z > 3.0$ on *App UX & Technical Performance*, immediately dispatch P0 Slack alert to Mobile Tech Lead with aggregated crash review snippets.

#### E2.2 Obfuscated PII in Public Play Store Comments
* **Scenario:** User posts review: *"My phone number is 9876543210 refund my order ORD-99128 fast!"*.
* **Risk:** Customer PII exposed publicly on internal BI dashboards.
* **System Safeguard:**
  * **Dual-Pass PII Masking:** Regex + SpaCy Indian NER redacts phone numbers, emails, and order IDs before dashboard rendering or external LLM invocation.

#### E2.3 Sarcasm & Contradictory Play Store Ratings
* **Scenario:** 5-star review: *"Best app ever! Charged money 3 times and didn't deliver food! 👏"*.
* **Risk:** Misclassified as positive feedback.
* **System Safeguard:**
  * **Star-Text Discrepancy Tagging:** If rating $= 5$ stars BUT text sentiment $< -0.50$, tag review as `CONTRADICTORY_RATING` and prioritize for human CX review.

---

## 3. Automated Edge-Case Safeguard Matrix

| Edge-Case ID | Category | Scenario | Automated Safeguard |
|---|---|---|---|
| **E1.1** | API Limit | Developer reply $> 350$ chars | Strict prompt constraint + pre-publish length truncation guard ($\le 350$). |
| **E1.2** | Streaming | Play Store Scraper 429 Block | Proxy rotation + Fallback to official Google Play Developer API. |
| **E1.3** | Persistence | Customer edits 1-star to 5-star | DB `UPSERT` on `review_id` to re-run ABSA & update sentiment score. |
| **E2.1** | Tech Ops | App Update (`v4.12.0`) Crash Spike | Z-score spike detector ($Z > 3.0$) dispatches P0 Slack alert to Mobile Team. |
| **E2.2** | Privacy | PII in public review text | Dual-pass Regex + SpaCy NER redacts phone/order IDs before storage. |
| **E2.3** | AI Model | Sarcastic 5-star complaint | Text sentiment overrides star rating; applies `CONTRADICTORY_RATING` tag. |

---

## 4. Conclusion

This edge-case analysis guarantees that **Zepto Reviews AI** handles all Google Play Store platform constraints, character limits, scraper rate limits, app update regression spikes, and PII masking requirements with enterprise-grade reliability.
