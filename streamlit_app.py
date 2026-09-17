"""Dashboard Rekrutmen PLN v2 — titik masuk aplikasi.

Menyusun navigasi, elemen lintas halaman (sakelar mode analis, tanggal potong),
lalu menjalankan halaman terpilih. Logika data ada di `core/`, tampilan di
`components/`, isi halaman di `app_pages/`.
"""

from __future__ import annotations

import streamlit as st

from chat import chat_store, chat_ui
from chat.chatbot import list_llm_profiles
from components import ui
from core import theme
from core.db import TANGGAL_POTONG

st.set_page_config(
    page_title="Dashboard Rekrutmen PLN",
    page_icon=":material/bolt:",
    layout="wide",
    initial_sidebar_state="collapsed",  # navigasi ada di atas, sidebar tidak dipakai
)

HALAMAN = [
    st.Page("app_pages/ringkasan.py", title="Ringkasan", icon=":material/dashboard:", default=True),
    st.Page("app_pages/perencanaan.py", title="Perencanaan", icon=":material/event_upcoming:"),
    st.Page("app_pages/corong.py", title="Tahapan seleksi", icon=":material/filter_alt:"),
    st.Page("app_pages/pasca.py", title="Pasca-seleksi & OJT", icon=":material/school:"),
    st.Page("app_pages/penempatan.py", title="Penempatan", icon=":material/location_on:"),
    st.Page("app_pages/kandidat.py", title="Kandidat", icon=":material/groups:"),
    st.Page("app_pages/kualitas.py", title="Kualitas data", icon=":material/fact_check:"),
    st.Page("app_pages/chatbot.py", title="RecruitMan", icon=":material/chat:"),
]

ui.gaya_global()

halaman = st.navigation(HALAMAN, position="top")

# Nav pindah ke atas, jadi sidebar kosong dan tak perlu dibuka. Sakelar mode analis
# dan keterangan potongan data ikut naik ke baris tepat di bawah nav, rata kanan,
# supaya tetap satu tempat untuk semua halaman.
with st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="center"):
    st.caption(
        f"Data per {TANGGAL_POTONG.strftime('%d %B %Y')}, gelombang 2019-2025, PLN Group"
    )
    ui.sakelar_mode_analis()

# ── Popover RecruitMan mengambang (semua halaman kecuali halaman RecruitMan
# sendiri) — port dari recruitment_dashboard/app.py. Tombol posisi tetap di pojok
# kanan bawah lewat CSS (.st-key-floating_chatbot), supaya bisa tanya tanpa
# pindah halaman. Riwayat percakapan dibagi dengan halaman RecruitMan penuh lewat
# session_state["active_conversation_id"] yang sama.
t = theme.token()
st.html(
    f"""
    <style>
      .st-key-floating_chatbot {{
        position: fixed;
        right: 28px;
        bottom: 28px;
        z-index: 999999;
      }}
      .st-key-floating_chatbot button {{
        border-radius: 999px !important;
        background: {t['brand_blue']} !important;
        color: white !important;
        border: none !important;
        padding: 12px 22px !important;
        box-shadow: 0 10px 28px {t['shadow']} !important;
      }}
    </style>
    """
)

if halaman.title != "RecruitMan":
    with st.popover("RecruitMan", icon=":material/chat:", key="floating_chatbot"):
        llm_profiles = list_llm_profiles()
        if llm_profiles:
            with st.container(border=True):
                selected_profile = chat_ui.render_model_status_selector(
                    llm_profiles, show_new_chat_button=True, auto_check=False
                )
        else:
            selected_profile = None
            st.caption("Mode demo tanpa API: belum ada profil LLM di secrets.toml")

        active_conversation_id = st.session_state.setdefault("active_conversation_id", None)

        typed_question = st.chat_input("Tanya mengenai rekrutmen...", key="copilot_question")
        just_answered = False
        if typed_question and typed_question.strip():
            active_conversation_id = chat_ui.submit_question(
                active_conversation_id, typed_question, selected_profile, key_prefix="popover"
            )
            just_answered = True

        history = chat_store.load_turns(active_conversation_id)
        indexed_history = list(enumerate(history))
        # Giliran yang baru dijawab sudah digambar langsung oleh submit_question, tepat
        # di atas sini — dibuang di sini supaya tidak digambar dua kali.
        if just_answered:
            indexed_history = indexed_history[:-1]
        recent = indexed_history[-2:]
        older = indexed_history[:-2]

        for idx, (question, response, answer_icon, created_at) in reversed(recent):
            chat_ui.render_turn(
                question, response, answer_icon, idx, key_prefix="popover", created_at=created_at
            )

        if older:
            with st.expander(f"Riwayat sebelumnya ({len(older)})"):
                for idx, (question, response, answer_icon, created_at) in reversed(older):
                    chat_ui.render_turn(
                        question, response, answer_icon, idx, key_prefix="popover", created_at=created_at
                    )

halaman.run()
