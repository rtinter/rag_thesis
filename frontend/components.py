import html

import streamlit as st

from api import build_slide_url
from formatting import highlight_citations, normalize_math


@st.dialog("Folienansicht", width="large")
def enlarge_slide(url: str, title: str) -> None:
    st.markdown(f"**{title}**")
    st.image(url, width="stretch")


def render_chat() -> None:
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            st.markdown(
                f'<div class="user-row"><div class="user-bubble">'
                f'{html.escape(msg["content"])}</div></div>',
                unsafe_allow_html=True,
            )
        else:
            with st.chat_message("llm", avatar=":material/robot_2:"):
                st.markdown(highlight_citations(normalize_math(msg["content"])))
            render_source_chips(i, msg["sources"])


def render_chip_row(msg_index: int, sources: list[dict]) -> None:
    with st.container(horizontal=True):
        for src in sources:
            page = src["page_numbers"][0] if src["page_numbers"] else "-"
            source_id = (msg_index, src["cite_nr"])
            is_active = source_id == st.session_state.active_source
            if st.button(
                f'{src["cite_nr"]} · Folie {page}',
                key=f'chip_{msg_index}_{src["cite_nr"]}',
                type="primary" if is_active else "secondary",
            ):
                st.session_state.active_source = source_id
                st.rerun()


def render_source_chips(msg_index: int, sources: list[dict]) -> None:
    if not sources:
        return

    cited = [s for s in sources if s["cited"]]
    others = [s for s in sources if not s["cited"]]

    if cited:
        st.markdown('<div class="sources-label">Quellen</div>', unsafe_allow_html=True)
        render_chip_row(msg_index, cited)

    if others:
        with st.expander(f"Zusätzliches Material ({len(others)})", type="compact"):
            render_chip_row(msg_index, others)


def active_source() -> dict | None:
    if st.session_state.active_source is None:
        return None

    msg_index, cite_nr = st.session_state.active_source
    sources = st.session_state.messages[msg_index]["sources"]

    for s in sources:
        if s["cite_nr"] == cite_nr:
            return s
    return None


def render_panel() -> None:
    source = active_source()

    if source is None:
        st.markdown(
            '<div class="panel-empty">Klicke eine Quelle an,<br>'
            "um die zugehörige Folie zu sehen.</div>",
            unsafe_allow_html=True,
        )
        return

    head, close = st.columns([5, 1])
    head.markdown(
        f'<div class="panel-title">[{source["cite_nr"]}] '
        f'{html.escape(source["title"])}</div>',
        unsafe_allow_html=True,
    )
    if close.button("✕", key="close_panel"):
        st.session_state.active_source = None
        st.rerun()

    url = build_slide_url(source)
    if url:
        st.image(url, width="stretch")
        if st.button("⤢ Vergrößern", key="enlarge", width="stretch"):
            enlarge_slide(url, source["title"])
    else:
        st.markdown(source["page_content"])

    pages = ", ".join(str(p) for p in source["page_numbers"])
    st.markdown(
        f'<div class="source-row"><span class="source-label">Modul</span>'
        f'<span class="source-value">{html.escape(source["modul"])}</span></div>'
        f'<div class="source-row"><span class="source-label">Vorlesung</span>'
        f'<span class="source-value">{html.escape(source["lecture"])}</span></div>'
        f'<div class="source-row"><span class="source-label">Folie</span>'
        f'<span class="source-value">{pages}</span></div>',
        unsafe_allow_html=True,
    )
