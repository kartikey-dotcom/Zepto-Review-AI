import re
from typing import Tuple, Dict, Any

class DataNormalizer:
    """
    Phase 1 Data Normalization Engine for Zepto Reviews AI.
    
    Rules:
    1. Filter out reviews with fewer than 8 words.
    2. Filter out reviews containing emojis.
    3. Filter out reviews written in non-Latin scripts / foreign languages (e.g. Devanagari, Tamil, Telugu).
    """

    MIN_WORD_COUNT = 8

    # Emoji Unicode Range Regex
    EMOJI_PATTERN = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Symbols & Pictographs
        "\U0001F680-\U0001F6FF"  # Transport & Map Symbols
        "\U0001F700-\U0001F77F"  # Alchemical Symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U000025B6"  # Shapes
        "\U00002600-\U000026FF"  # Miscellaneous Symbols
        "]+",
        flags=re.UNICODE
    )

    # Non-Latin Script Regex (Devanagari, Tamil, Kannada, Bengali, Arabic, etc.)
    NON_LATIN_PATTERN = re.compile(
        r'[\u0900-\u097F\u0B80-\u0BFF\u0C80-\u0CFF\u0980-\u09FF\u0A80-\u0AFF\u0C00-\u0C7F\u0600-\u06FF\u0400-\u04FF]',
        re.UNICODE
    )

    @classmethod
    def get_word_count(cls, text: str) -> int:
        """Counts total words in the text."""
        if not text or not text.strip():
            return 0
        return len(text.strip().split())

    @classmethod
    def contains_emojis(cls, text: str) -> bool:
        """Checks if text contains emojis."""
        if not text:
            return False
        return bool(cls.EMOJI_PATTERN.search(text))

    @classmethod
    def contains_non_latin_script(cls, text: str) -> bool:
        """Checks if text contains non-Latin scripts (e.g. Devanagari Hindi, Tamil, Kannada)."""
        if not text:
            return False
        return bool(cls.NON_LATIN_PATTERN.search(text))

    @classmethod
    def validate_and_normalize(cls, text: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validates review text against Phase 1 normalization rules.
        
        Returns:
            Tuple[is_valid: bool, rejection_reason: str, metadata: dict]
        """
        if not text or not text.strip():
            return False, "empty_text", {"word_count": 0, "has_emojis": False, "has_non_latin": False}

        word_count = cls.get_word_count(text)
        has_emojis = cls.contains_emojis(text)
        has_non_latin = cls.contains_non_latin_script(text)

        metadata = {
            "word_count": word_count,
            "has_emojis": has_emojis,
            "has_non_latin": has_non_latin
        }

        # Rule 1: Minimum 8 words
        if word_count < cls.MIN_WORD_COUNT:
            return False, f"word_count_too_short ({word_count} < 8 words)", metadata

        # Rule 2a: No emojis
        if has_emojis:
            return False, "contains_emojis", metadata

        # Rule 2b: Latin script only (English / Hinglish)
        if has_non_latin:
            return False, "contains_non_latin_script", metadata

        return True, "valid", metadata
