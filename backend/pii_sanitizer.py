import re
from typing import Dict, Any, List

class PIISanitizer:
    """
    Zero-Trust PII Masking Engine for Zepto Reviews AI.
    Redacts phone numbers, emails, order IDs, addresses, and sensitive account details
    from raw review text before storing or sending to external LLM APIs.
    """

    REDACTION_TAGS = {
        "PHONE": "[PHONE_REDACTED]",
        "EMAIL": "[EMAIL_REDACTED]",
        "ORDER_ID": "[ORDER_ID_REDACTED]",
        "CARD": "[CARD_REDACTED]",
        "ADDRESS": "[ADDRESS_REDACTED]",
        "PINCODE": "[PINCODE_REDACTED]"
    }

    # Number word mapping for word-based digit obfuscation (e.g. "nine eight seven six...")
    WORD_TO_DIGIT = {
        "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
        "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9"
    }

    # Regex patterns
    EMAIL_PATTERN = re.compile(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        re.IGNORECASE
    )

    # Indian Mobile Phone pattern: starts with +91/0 or 6-9, followed by 9 digits with optional spaces/hyphens
    PHONE_PATTERN = re.compile(
        r'\b(?:\+?91[\-\s.]*|0)?[6-9](?:[\-\s.]*\d){9}\b'
    )

    # Order ID patterns (e.g. ORD-123456, Order #991823, ZEPTO-99182) - requires digits or explicit ORD prefix
    ORDER_ID_PATTERN = re.compile(
        r'\b(?:ORD|ORDER)[\s\-\#]*[A-Z0-9]{4,12}\b|\bZEPTO[\s\-\#]*\d{4,12}\b',
        re.IGNORECASE
    )

    # Card pattern (13 to 19 digits with optional spaces or hyphens)
    CARD_PATTERN = re.compile(
        r'\b(?:\d[ -]*?){13,19}\b'
    )

    # Pincode pattern (Indian 6-digit pin codes starting with 1-9)
    PINCODE_PATTERN = re.compile(
        r'\b[1-9]\d{5}\b'
    )

    # Indian Address Patterns (e.g. Flat 402, House No 12, HSR Layout, Sector 4)
    ADDRESS_PATTERN = re.compile(
        r'\b(?:flat|house\s+no|h\.no|apartment|apt|sector|block|layout|stage|phase)\s+[a-z0-9\-\/,\s]{2,20}\b',
        re.IGNORECASE
    )

    @classmethod
    def normalize_word_digits(cls, text: str) -> str:
        """Converts written number words ('nine eight seven...') to digits for PII detection."""
        words = text.split()
        normalized_words = []
        for word in words:
            clean_word = word.lower().strip(",.")
            if clean_word in cls.WORD_TO_DIGIT:
                normalized_words.append(cls.WORD_TO_DIGIT[clean_word])
            else:
                normalized_words.append(word)
        return " ".join(normalized_words)

    @classmethod
    def sanitize_text(cls, text: str) -> Dict[str, Any]:
        """
        Redacts PII elements from review text.
        Returns a dict with sanitized text and metadata on what PII was scrubbed.
        """
        if not text or not text.strip():
            return {
                "sanitized_text": "",
                "pii_detected": False,
                "redaction_counts": {}
            }

        original_text = text
        sanitized = text
        redaction_counts: Dict[str, int] = {}

        # 1. Scrub Emails
        emails = cls.EMAIL_PATTERN.findall(sanitized)
        if emails:
            redaction_counts["EMAIL"] = len(emails)
            sanitized = cls.EMAIL_PATTERN.sub(cls.REDACTION_TAGS["EMAIL"], sanitized)

        # 2. Scrub Order IDs
        orders = cls.ORDER_ID_PATTERN.findall(sanitized)
        if orders:
            redaction_counts["ORDER_ID"] = len(orders)
            sanitized = cls.ORDER_ID_PATTERN.sub(cls.REDACTION_TAGS["ORDER_ID"], sanitized)

        # 3. Scrub Address patterns
        addresses = cls.ADDRESS_PATTERN.findall(sanitized)
        if addresses:
            redaction_counts["ADDRESS"] = len(addresses)
            sanitized = cls.ADDRESS_PATTERN.sub(cls.REDACTION_TAGS["ADDRESS"], sanitized)

        # 4. Check for phone numbers (including word-based digits)
        normalized_pass = cls.normalize_word_digits(sanitized)
        phones_in_norm = cls.PHONE_PATTERN.findall(normalized_pass)
        phones_in_orig = cls.PHONE_PATTERN.findall(sanitized)

        if phones_in_orig:
            redaction_counts["PHONE"] = len(phones_in_orig)
            sanitized = cls.PHONE_PATTERN.sub(cls.REDACTION_TAGS["PHONE"], sanitized)
        elif phones_in_norm:
            redaction_counts["PHONE"] = len(phones_in_norm)
            sanitized = cls.PHONE_PATTERN.sub(cls.REDACTION_TAGS["PHONE"], normalized_pass)

        # 5. Scrub Pincodes (if not part of phone or already redacted tag)
        pincodes = cls.PINCODE_PATTERN.findall(sanitized)
        if pincodes:
            valid_pincodes = [p for p in pincodes if not any(tag in p for tag in cls.REDACTION_TAGS.values())]
            if valid_pincodes:
                redaction_counts["PINCODE"] = len(valid_pincodes)
                for pin in valid_pincodes:
                    sanitized = sanitized.replace(pin, cls.REDACTION_TAGS["PINCODE"])

        pii_detected = len(redaction_counts) > 0

        return {
            "raw_text": original_text,
            "sanitized_text": sanitized,
            "pii_detected": pii_detected,
            "redaction_counts": redaction_counts
        }

    @classmethod
    def sanitize_user_name(cls, user_name: str) -> str:
        """Anonymizes user names for Play Store reviews (e.g. 'Rahul Sharma' -> 'Rahul S.')."""
        if not user_name or user_name.lower().strip() in ["a google user", "anonymous", "zepto user"]:
            return "Zepto User"

        parts = user_name.strip().split()
        if len(parts) == 1:
            return parts[0][0].upper() + "."
        return f"{parts[0]} {parts[-1][0].upper()}."
