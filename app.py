"""
Notes Cleaner Pro — production-oriented Streamlit UI.
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

_ENV_FILE = Path(__file__).resolve().parent / ".env"
load_dotenv(_ENV_FILE, encoding="utf-8-sig", override=True)

import streamlit as st

from ai_rewrite import generate_output
from copy_formats import COPY_OPTIONS, format_for_copy
from pipeline import prepare_context_for_model
from recruiter_prompts import OUTPUT_OPTIONS


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
            .main .block-container { padding-top: 1.25rem; padding-bottom: 2rem; max-width: 1200px; }
            h1 { font-weight: 600; font-size: 1.75rem; margin-bottom: 0.25rem; }
            div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stMarkdown"]) h3 {
                font-size: 1rem; font-weight: 600; margin-top: 0; margin-bottom: 0.5rem;
                color: #31333F;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="ConnectHealth Notes",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _inject_styles()

    st.title("ConnectHealth Notes")
    st.caption("Polished notes or CRM records—generate once, copy for Microsoft Teams or email.")

    if "last_output" not in st.session_state:
        st.session_state["last_output"] = None
    if "last_output_error" not in st.session_state:
        st.session_state["last_output_error"] = None
    if "generating" not in st.session_state:
        st.session_state["generating"] = False

    col_in, col_out = st.columns([1, 1], gap="large")

    with col_in:
        st.markdown("### Your notes")
        raw = st.text_area(
            "Notes input",
            height=440,
            label_visibility="collapsed",
            placeholder=(
                "Drop in rough notes, transcript snippets, or bullets—no need to clean them up.\n\n"
                "Tip: include names, role/title, comp or level if mentioned, dates for follow-ups, "
                "and who owns next steps."
            ),
            key="raw_notes",
        )
        st.caption(
            "Do not include sensitive personal data (SSN, DOB, full addresses, etc.)"
        )

        output_type = st.selectbox(
            "Output Type",
            OUTPUT_OPTIONS,
            index=0,
        )

        st.write("")
        gen_pending = st.button(
            "Generate Output",
            type="primary",
            use_container_width=True,
            disabled=st.session_state["generating"],
        )

        copy_as = st.selectbox(
            "Copy as",
            COPY_OPTIONS,
            index=0,
        )

        btn_copy, btn_clear = st.columns(2, gap="small")
        with btn_copy:
            copy_clicked = st.button("Copy Output", use_container_width=True)
        with btn_clear:
            clear_clicked = st.button("Clear Input", use_container_width=True)

        if clear_clicked:
            st.session_state["raw_notes"] = ""
            st.session_state["last_output"] = None
            st.session_state["last_output_error"] = None
            st.session_state["generating"] = False
            st.rerun()

        if gen_pending:
            if not raw.strip():
                st.warning("Add notes before generating.")
                st.session_state["last_output"] = None
                st.session_state["last_output_error"] = None
            else:
                st.session_state["generating"] = True
                st.session_state["_gen_output_type"] = output_type
                st.rerun()

    with col_out:
        st.markdown("### Output")

        if st.session_state["generating"]:
            otype = st.session_state.get("_gen_output_type", OUTPUT_OPTIONS[0])
            with st.spinner("Generating your output…"):
                ctx = prepare_context_for_model(raw)
                text, err = generate_output(ctx, otype)
                if err:
                    st.session_state["last_output_error"] = err
                    st.session_state["last_output"] = None
                else:
                    st.session_state["last_output_error"] = None
                    st.session_state["last_output"] = text
            st.session_state["generating"] = False
            if "_gen_output_type" in st.session_state:
                del st.session_state["_gen_output_type"]
            st.rerun()

        err = st.session_state.get("last_output_error")
        out_text = st.session_state.get("last_output")

        if err:
            st.error(err)
        elif out_text:
            st.text_area(
                "Generated output",
                value=out_text,
                height=520,
                label_visibility="collapsed",
                disabled=True,
            )
        else:
            st.info("Choose **AI Notes** or **CRM Format**, then click **Generate Output**.")

        if copy_clicked:
            import pyperclip

            raw_out = st.session_state.get("last_output") or ""
            if not (raw_out or "").strip():
                st.warning("Generate output first, then copy.")
            else:
                payload = format_for_copy(raw_out, copy_as)
                try:
                    pyperclip.copy(payload)
                    st.toast("Copied to clipboard.")
                except Exception:
                    st.warning("Copy failed. Select the text and use Ctrl+C.")


if __name__ == "__main__":
    main()
