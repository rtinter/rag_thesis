from pathlib import Path

import httpx
import streamlit as st

from api import post_question
from components import render_chat, render_panel

st.set_page_config(page_title="HAW Modul Chatbot", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_source" not in st.session_state:
    st.session_state.active_source = None


def load_css() -> None:
    css_path = Path(__file__).parent / "theme.css"
    st.markdown(
        f"<style>{css_path.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )
load_css()

st.markdown(
    '<div class="app-header">'
        '<div class="app-logo"></div>'
        "<div>"
            '<div class="app-title">Modul-Assistent</div>'
            '<div class="app-sub">Maschinelles Lernen &middot; SS 2026</div>'
        "</div>"
    "</div>",
    unsafe_allow_html=True,
)

question = st.chat_input("Stell mir eine Frage zu den Vorlesungsunterlagen ..")

_space_left, chat_col, _space_right, panel_col = st.columns([3, 6, 1, 5.5], gap="small")

if question:
    st.session_state.messages.append({"role": "user", "content": question})

with chat_col:
    render_chat()

    if question:
        try:
            with st.spinner("Ich suche nach einer passenden Antwort in den Modulunterlagen ... gib mir einen Moment."):
                data = post_question(question)

            st.session_state.messages.append(
                {
                    "role": "llm",
                    "content": data["answer"],
                    "sources": data["sources"],
                }
            )
            st.session_state.active_source = None
            st.rerun()

        except httpx.HTTPStatusError as error:
            st.error(error.response.json()["detail"])
        except httpx.RequestError:
            st.error("Das Backend ist gerade nicht erreichbar. Läuft es?")
        except Exception:
            st.error("Unerwarteter Fehler. Bitte erneut versuchen.")

with panel_col:
    with st.container(key="slide_panel", border=True):
        render_panel()
