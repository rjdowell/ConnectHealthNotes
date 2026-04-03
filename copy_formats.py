"""
Transform generated text for Teams (plain) and Email.

Differentiates AI Notes (markdown) vs CRM (plain record). No second model call.
"""

from __future__ import annotations

import re
from typing import Final

COPY_TEAMS_PLAIN: Final = "Teams / Plain Text"
COPY_EMAIL: Final = "Email Format"

COPY_OPTIONS: tuple[str, ...] = (COPY_TEAMS_PLAIN, COPY_EMAIL)

_SUMMARY = "summary"
_KEY_DETAILS = "key details"
_ACTIONS = "action items"
_OPEN_Q = "open questions"


def _strip_md_bold(s: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"\1", s)


def _flatten_bullet_line(s: str) -> str:
    """Single line for Teams: no internal newlines, no markdown, single spaces only."""
    t = _strip_md_bold(s.strip())
    t = re.sub(r"[\r\n]+", " ", t)
    t = re.sub(r"[ \t]+", " ", t)
    return t.strip()


def _split_markdown_sections(md: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    title: str | None = None
    buf: list[str] = []
    for line in md.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line.strip())
        if m:
            if title is not None:
                sections.append((title.lower(), "\n".join(buf).strip()))
            title = m.group(1).strip().lower()
            buf = []
        else:
            buf.append(line)
    if title is not None:
        sections.append((title.lower(), "\n".join(buf).strip()))
    return sections


def _is_empty_section_body(body: str) -> bool:
    b = body.strip()
    if not b:
        return True
    if b.rstrip(".").lower() in ("none", "n/a", "—", "-"):
        return True
    return False


def _bullet_lines(body: str) -> list[str]:
    out: list[str] = []
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"^[\-\*]\s+", "", line)
        line = _strip_md_bold(line).strip()
        if line:
            out.append(line)
    return out


def _summary_lines(body: str) -> list[str]:
    """Up to 3 summary lines: prefer model bullets, else sentence split."""
    text = _strip_md_bold(body.strip())
    if not text:
        return []
    bullets: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"^[\-\*]\s+(.+)$", line)
        if m:
            bullets.append(m.group(1).strip())
    if bullets:
        return bullets[:3]
    parts = re.split(r"(?<=[.!?])\s+", text)
    lines = [p.strip() for p in parts if p.strip()]
    return lines[:3] if len(lines) > 3 else lines


def _norm_phrase(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower().strip().rstrip("."))


def _dedupe_against_summary(summary_lines: list[str], items: list[str]) -> list[str]:
    """Drop detail/question lines already covered by any summary line."""
    if not summary_lines:
        return items
    blobs = [_norm_phrase(x) for x in summary_lines if x.strip()]
    joined = " ".join(blobs)
    joined_dots = joined.replace(".", "")
    out: list[str] = []
    for it in items:
        tl = _norm_phrase(it)
        tl_dots = tl.replace(".", "")
        if len(tl) >= 8 and (tl in joined or tl_dots in joined_dots):
            continue
        skip = False
        for b in blobs:
            bd = b.replace(".", "")
            if len(tl) >= 8 and (tl in b or tl_dots in bd or (len(b) >= 12 and b in tl)):
                skip = True
                break
        if skip:
            continue
        out.append(it)
    return out


def _looks_like_crm_plain(text: str) -> bool:
    t = text.strip()
    return bool(t) and t.upper().startswith("RECORD")


def _crm_field_lines(text: str) -> list[str]:
    out: list[str] = []
    pending_label: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        line = _strip_md_bold(line)
        if line.upper().startswith("MISSING:"):
            out.append(line)
            pending_label = None
            continue
        if line.isupper() and len(line) <= 32 and ":" not in line:
            pending_label = line.title()
            out.append(line)
            continue
        if ":" in line:
            out.append(line)
            pending_label = None
        elif pending_label:
            out.append(f"{pending_label}: {line}")
            pending_label = None
        elif out:
            out[-1] = f"{out[-1]} {line}".strip()
        else:
            out.append(line)
    return out


def _crm_extract_name(text: str) -> str:
    m = re.search(r"(?mi)^Name:\s*(.+)$", text)
    if m:
        v = m.group(1).strip()
        if v and not re.match(r"^not stated", v, re.I):
            return v[:60]
    return ""


def _sections_from_text(text: str) -> tuple[str, list[tuple[str, str]]]:
    if _looks_like_crm_plain(text):
        return "crm", []
    secs = _split_markdown_sections(text)
    if secs:
        return "markdown", [(h, b) for h, b in secs if not _is_empty_section_body(b)]
    return "markdown", [("body", text.strip())]


def _ai_gather(
    sections: list[tuple[str, str]],
) -> tuple[list[str], list[str], list[str], list[str]]:
    summary_lines: list[str] = []
    details: list[str] = []
    actions: list[str] = []
    questions: list[str] = []
    for heading, body in sections:
        if _is_empty_section_body(body):
            continue
        if heading == _SUMMARY:
            summary_lines = _summary_lines(body)
        elif heading == _KEY_DETAILS:
            details.extend(_bullet_lines(body))
        elif heading == _ACTIONS:
            actions.extend(_bullet_lines(body))
        elif heading == _OPEN_Q:
            questions.extend(_bullet_lines(body))
        elif heading == "body":
            summary_lines = _summary_lines(body) or ([body.strip()[:500]] if body.strip() else [])
    details = _dedupe_against_summary(summary_lines, details)
    questions = _dedupe_against_summary(summary_lines, questions)
    return summary_lines, details, actions, questions


def to_teams_plain_text(text: str) -> str:
    """
    Plain text for Microsoft Teams: hyphen bullets, single-line items,
    no markdown, pastes cleanly.
    """
    if not text:
        return ""
    kind, sections = _sections_from_text(text)

    if kind == "crm":
        lines = _crm_field_lines(text)
        missing = [ln for ln in lines if ln.upper().startswith("MISSING:")]
        rest = [ln for ln in lines if not ln.upper().startswith("MISSING:")]
        parts: list[str] = []
        for ln in rest:
            if not ln.strip():
                continue
            if ln.isupper() and len(ln) <= 32 and ":" not in ln:
                parts.append(ln)
                continue
            raw = ln[2:].strip() if ln.startswith("- ") else ln
            parts.append(f"- {_flatten_bullet_line(raw)}")
        body = "\n".join(parts).strip()
        if missing:
            mline = _flatten_bullet_line(missing[0])
            body = f"{body}\n\n- {mline}" if body else f"- {mline}"
        return body

    if not sections:
        t = _strip_md_bold(text).strip()
        return "\n".join(
            f"- {_flatten_bullet_line(ln.removeprefix('- '))}" for ln in t.splitlines() if ln.strip()
        )

    summary_lines, details, actions, questions = _ai_gather(sections)
    parts: list[str] = []

    if summary_lines:
        parts.append("Summary")
        for s in summary_lines:
            parts.append(f"- {_flatten_bullet_line(s)}")
        parts.append("")

    if details:
        parts.append("Details")
        for d in details:
            parts.append(f"- {_flatten_bullet_line(d)}")
        parts.append("")

    if actions:
        parts.append("Actions")
        for a in actions:
            parts.append(f"- {_flatten_bullet_line(a)}")
        parts.append("")

    if questions:
        parts.append("Open questions")
        for q in questions:
            parts.append(f"- {_flatten_bullet_line(q)}")

    return "\n".join(parts).strip()


def to_email(text: str) -> str:
    """Forwardable email: Subject line + short labeled sections, hyphen bullets."""
    if not text:
        return ""
    kind, sections = _sections_from_text(text)

    if kind == "crm":
        name = _crm_extract_name(text)
        subj = f"CRM — {name}" if name else "CRM — candidate record"
        lines = _crm_field_lines(text)
        body_lines: list[str] = []
        for ln in lines:
            if ln.isupper() and len(ln) <= 32 and ":" not in ln:
                body_lines.append("")
                body_lines.append(ln)
                continue
            body_lines.append(_flatten_bullet_line(ln))
        body = "\n".join(body_lines).strip()
        return f"Subject: {subj}\n\n{body}"

    if not sections:
        return f"Subject: Notes\n\n{_flatten_bullet_line(_strip_md_bold(text))}"

    summary_lines, details, actions, questions = _ai_gather(sections)
    summary_text = " ".join(summary_lines).strip()
    subj = summary_text[:72] if len(summary_text) > 10 else "Notes update"
    subj = _strip_md_bold(subj).strip()
    if len(subj) > 58:
        subj = subj[:55].rstrip() + "…"

    parts: list[str] = [f"Subject: {subj}", "", "Hi —", ""]
    if summary_lines:
        parts.append("Summary")
        parts.extend(f"- {_flatten_bullet_line(s)}" for s in summary_lines)
        parts.append("")
    if details:
        parts.append("Details")
        parts.extend(f"- {_flatten_bullet_line(d)}" for d in details)
        parts.append("")
    if actions:
        parts.append("Next steps")
        parts.extend(f"- {_flatten_bullet_line(a)}" for a in actions)
        parts.append("")
    if questions:
        parts.append("Open questions")
        parts.extend(f"- {_flatten_bullet_line(q)}" for q in questions)
    parts.append("")
    parts.append("—")
    return "\n".join(parts).strip()


def format_for_copy(text: str, copy_as: str) -> str:
    if copy_as == COPY_EMAIL:
        return to_email(text)
    return to_teams_plain_text(text)
