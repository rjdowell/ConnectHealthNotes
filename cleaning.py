"""Basic text cleaning (Python only, no API)."""

import re
from typing import Dict, List

# Lowercase keys only. Each token is replaced by the canonical phrase (whole-word, case-insensitive).
# Extend this dict to add terms; longer keys are applied first to avoid substring collisions.
ABBREVIATIONS: Dict[str, str] = {
    "icu": "Intensive Care Unit",
    "peds": "Pediatrics",
    "ans": "Anesthesiology",
    "em": "Emergency Medicine",
    "er": "Emergency Room",
}

# Precompiled patterns: longest abbreviations first so e.g. "icu" wins over any future shorter key.
_ABBR_PATTERNS: List[tuple[re.Pattern[str], str]] = []
for _abbr in sorted(ABBREVIATIONS.keys(), key=len, reverse=True):
    _ABBR_PATTERNS.append(
        (re.compile(rf"\b{re.escape(_abbr)}\b", re.IGNORECASE), ABBREVIATIONS[_abbr])
    )


def expand_abbreviations(text: str) -> str:
    """
    Replace known shorthand with full phrases. Whole words only; unknown tokens unchanged.

    Matching is case-insensitive; replacement always uses the canonical value from ABBREVIATIONS
    so the same abbreviation expands the same way every time.
    """
    if not text:
        return ""
    result = text
    for pattern, expansion in _ABBR_PATTERNS:
        result = pattern.sub(expansion, result)
    return result


FILLER_PATTERN = re.compile(
    r"\b(um|uh|like|you know|kind of|sort of)\b",
    re.IGNORECASE,
)

REPEATED_PUNCT = re.compile(r"([!?.,])\1+")


def _normalize_line(line: str) -> str:
    line = FILLER_PATTERN.sub("", line)
    line = re.sub(r"\s+", " ", line).strip()
    line = REPEATED_PUNCT.sub(r"\1", line)
    return line


def _standardize_bullet(line: str) -> str:
    s = line.strip()
    if not s:
        return ""
    bullet_chars = ("•", "·", "▪", "‣", "◦", "*")
    for b in bullet_chars:
        if s.startswith(b):
            s = s[len(b) :].strip()
            return f"- {s}"
    if re.match(r"^[\-\–\—]\s*", s):
        rest = re.sub(r"^[\-\–\—]\s*", "", s)
        return f"- {rest}"
    return s


def clean_notes(text: str) -> str:
    """
    Expand known abbreviations, remove filler words, normalize spacing, collapse blank lines,
    standardize bullets to '- ', clean repeated punctuation.
    """
    if not text or not text.strip():
        return ""

    text = expand_abbreviations(text)

    lines: List[str] = []
    for raw in text.splitlines():
        raw = _normalize_line(raw)
        if not raw:
            continue
        raw = _standardize_bullet(raw)
        if raw:
            lines.append(raw)

    out = "\n".join(lines)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()
