"""Detect actions and questions; format Summary / Action Items / Open Questions."""

import re
from typing import List

ACTION_KEYWORDS = re.compile(
    r"\b(action|follow\s*up|send|build|check|owner|next\s*step)\b",
    re.IGNORECASE,
)
QUESTION_PHRASES = re.compile(
    r"\b(need\s+to\s+confirm|open\s+item)\b",
    re.IGNORECASE,
)


def _is_action_line(line: str) -> bool:
    return bool(ACTION_KEYWORDS.search(line))


def _is_question_line(line: str) -> bool:
    if "?" in line:
        return True
    return bool(QUESTION_PHRASES.search(line))


def _bullet(line: str) -> str:
    s = line.strip()
    if s.startswith("- "):
        return s
    return f"- {s}"


def structure_notes(text: str) -> str:
    """
    Split content into summary bullets, action items, and open questions.
    Lines matching action/question heuristics are excluded from summary.
    """
    if not text or not text.strip():
        return ""

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    summary: List[str] = []
    actions: List[str] = []
    questions: List[str] = []

    for line in lines:
        # Strip leading bullet for classification
        content = re.sub(r"^-\s*", "", line).strip()
        if _is_action_line(content):
            actions.append(content)
        elif _is_question_line(content):
            questions.append(content)
        else:
            summary.append(content)

    parts: List[str] = []

    parts.append("Summary")
    parts.append("")
    if summary:
        for s in summary:
            parts.append(_bullet(s))
    else:
        parts.append("- (No general summary lines detected; see actions and questions below.)")
    parts.append("")

    parts.append("Action Items")
    parts.append("")
    if actions:
        for a in actions:
            parts.append(_bullet(a))
    else:
        parts.append("- (None detected.)")
    parts.append("")

    parts.append("Open Questions")
    parts.append("")
    if questions:
        for q in questions:
            parts.append(_bullet(q))
    else:
        parts.append("- (None detected.)")

    return "\n".join(parts).strip()


def build_ai_context(cleaned_text: str, structured_text: str) -> str:
    """Single string passed to the model as source material."""
    return (
        "--- Cleaned notes ---\n"
        f"{cleaned_text}\n\n"
        "--- Structured outline ---\n"
        f"{structured_text}"
    )
