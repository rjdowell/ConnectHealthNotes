"""
Post-process model output before display (no UI). Keeps CRM records readable.
"""

from __future__ import annotations

import re

from recruiter_prompts import OUTPUT_CRM_FORMAT


def consolidate_crm_missing_fields(text: str) -> str:
    """
    Replace many 'Label: Not stated' lines with a single MISSING: line.
    Preserves an existing MISSING: line by merging labels.
    """
    if not (text or "").strip():
        return text

    lines = text.splitlines()
    kept: list[str] = []
    missing: list[str] = []
    pending_section: str | None = None

    for line in lines:
        s = line.strip()
        if not s:
            kept.append(line)
            continue

        if s.upper().startswith("MISSING:"):
            rest = s.split(":", 1)[1].strip()
            if rest:
                missing.extend(x.strip() for x in rest.split(",") if x.strip())
            continue

        if s.isupper() and len(s) <= 32 and ":" not in s:
            pending_section = s.title()
            kept.append(line)
            continue

        m = re.match(r"^([^:]+):\s*(Not stated\.?|N/A|—)\s*$", s, re.I)
        if m:
            missing.append(m.group(1).strip())
            pending_section = None
            continue

        if re.match(r"^(Not stated\.?|N/A|—)\s*$", s, re.I):
            if pending_section:
                if kept and kept[-1].strip().isupper() and ":" not in kept[-1]:
                    kept.pop()
                missing.append(pending_section)
            pending_section = None
            continue

        pending_section = None
        kept.append(line)

    out = "\n".join(kept)
    out = re.sub(r"\n{3,}", "\n\n", out).strip()

    if missing:
        uniq: list[str] = []
        for x in missing:
            if x not in uniq:
                uniq.append(x)
        merged = ", ".join(uniq)
        if "\nMISSING:" in out or out.rstrip().endswith("MISSING:") or re.search(
            r"(?m)^MISSING:\s*.+$", out
        ):
            out = re.sub(r"(?m)^MISSING:\s*.+$", "", out).strip()
        out = f"{out}\n\nMISSING: {merged}" if out else f"MISSING: {merged}"

    return out.strip()


def finalize_generated_output(text: str, output_type: str) -> str:
    if output_type != OUTPUT_CRM_FORMAT:
        return text
    return consolidate_crm_missing_fields(text)
