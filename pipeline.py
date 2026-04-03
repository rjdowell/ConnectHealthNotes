"""
Prepare raw notes for the model: always clean and structure, then build context string.
"""

from __future__ import annotations

from cleaning import clean_notes
from structuring import build_ai_context, structure_notes


def prepare_context_for_model(raw: str) -> str:
    """
    Run basic cleaning and structuring, then return the combined context
    passed to the AI (same shape as before: cleaned + structured blocks).
    """
    text = raw.strip()
    if not text:
        return ""

    cleaned = clean_notes(text)
    structured = structure_notes(cleaned)
    return build_ai_context(cleaned, structured)
