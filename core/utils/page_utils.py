"""Page numbering and roman/arabic numeral validation utilities."""

from __future__ import annotations

import re

ROMAN_LOWER_MAP = {
    1: "i", 2: "ii", 3: "iii", 4: "iv", 5: "v",
    6: "vi", 7: "vii", 8: "viii", 9: "ix", 10: "x",
    11: "xi", 12: "xii", 13: "xiii", 14: "xiv", 15: "xv",
    16: "xvi", 17: "xvii", 18: "xviii", 19: "xix", 20: "xx"
}
REV_ROMAN_LOWER = {v: k for k, v in ROMAN_LOWER_MAP.items()}


def is_roman_lower(text: str) -> bool:
    """Check if text is a valid lowercase roman numeral."""
    t = text.strip().lower()
    return bool(re.fullmatch(r"m{0,4}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})", t)) and len(t) > 0


def is_arabic_num(text: str) -> bool:
    """Check if text is an arabic number."""
    return text.strip().isdigit()


def parse_page_num(text: str) -> tuple[int | None, str]:
    """Parse page string into integer value and numeral type ('arabic', 'roman_lower', 'unknown')."""
    t = text.strip()
    if is_arabic_num(t):
        return int(t), "arabic"
    if is_roman_lower(t.lower()):
        # Calculate roman value
        val = roman_to_int(t.lower())
        return val, "roman_lower"
    return None, "unknown"


def roman_to_int(s: str) -> int:
    roman_values = {'i': 1, 'v': 5, 'x': 10, 'l': 50, 'c': 100, 'd': 500, 'm': 1000}
    total = 0
    prev_val = 0
    for char in reversed(s.lower()):
        val = roman_values.get(char, 0)
        if val >= prev_val:
            total += val
        else:
            total -= val
        prev_val = val
    return total
