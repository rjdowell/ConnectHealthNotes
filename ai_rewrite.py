"""OpenAI API: single-output generation for AI Notes or CRM Format."""

from __future__ import annotations

import os
from typing import Optional, Tuple

from output_cleanup import finalize_generated_output
from recruiter_prompts import (
    OUTPUT_CRM_FORMAT,
    system_prompt_ai_notes,
    system_prompt_crm_format,
)

DEFAULT_MODEL = "gpt-4o-mini"
# Fixed seed improves repeatability on models that support it (best-effort per API).
_DETERMINISTIC_SEED = 42


def _complete(
    system_prompt: str,
    user_content: str,
    model: str = DEFAULT_MODEL,
) -> Tuple[str, Optional[str]]:
    """Run one chat completion; returns (text, error_message)."""
    key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not key:
        return "", "The AI service is not configured."

    if not user_content.strip():
        return "", "No content to process."

    try:
        from openai import OpenAI

        client = OpenAI(api_key=key)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            seed=_DETERMINISTIC_SEED,
        )
        text = (resp.choices[0].message.content or "").strip()
        return text, None
    except Exception as e:  # noqa: BLE001
        return "", str(e)


def generate_output(
    context: str,
    output_type: str,
    model: str = DEFAULT_MODEL,
) -> Tuple[str, Optional[str]]:
    """
    Produce the final user-facing text for the selected output mode.

    output_type must be OUTPUT_AI_NOTES ("AI Notes") or OUTPUT_CRM_FORMAT ("CRM Format").
    """
    if output_type == OUTPUT_CRM_FORMAT:
        text, err = _complete(
            system_prompt_crm_format(),
            f"Build the CRM record from these notes:\n\n{context}",
            model=model,
        )
        if not err and text:
            text = finalize_generated_output(text, OUTPUT_CRM_FORMAT)
        return text, err

    return _complete(
        system_prompt_ai_notes(),
        f"Transform the following notes according to the instructions:\n\n{context}",
        model=model,
    )


def format_crm_record(context: str, model: str = DEFAULT_MODEL) -> Tuple[str, Optional[str]]:
    """Thin wrapper for tests or future reuse; same as CRM branch of generate_output."""
    return generate_output(context, OUTPUT_CRM_FORMAT, model=model)
