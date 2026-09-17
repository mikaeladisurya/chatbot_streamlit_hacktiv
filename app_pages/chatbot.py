"""Halaman 8 — Chatbot.

Port dari recruitment_dashboard/app_pages/chatbot.py (v1), termasuk trik JS untuk
mengisi kotak tanya saat saran diklik (lihat komentar di blok "kanan" di bawah —
st.chat_input tidak punya parameter isi awal, jadi tanpa trik ini klik saran
harus langsung mengirim). Beda dari v1: tidak ada parameter `dataframes` —
chat/chatbot.py membuka koneksi read-only sendiri ke berkas .duckdb tiap giliran.
"""

from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components

from chat import chat_store, chat_ui
from chat.chatbot import list_llm_profiles
from components import ui

ui.judul_halaman("RecruitMan")

# Tinggi dinamis mengikuti viewport (bukan px tetap) — sama seperti v1
# (recruitment_dashboard/app.py). st.container(height=N) yang tetap membuat kotak
# terasa "kurang ke bawah" di layar besar; calc(100vh - Npx) mengisi sampai
# mentok bawah dan tetap scroll internal sendiri kalau isinya lebih panjang.
st.html(
    """
    <style>
      .st-key-chatpage_history_box {
        max-height: calc(100vh - 520px);
        min-height: 160px;
        overflow-y: auto;
        padding-right: 4px;
      }
      .st-key-chatpage_answers_box {
        max-height: calc(100vh - 300px);
        min-height: 300px;
        overflow-y: auto;
        padding-right: 4px;
      }
    </style>
    """
)

llm_profiles = list_llm_profiles()
active_id = st.session_state.setdefault("active_conversation_id", None)

kiri, kanan = st.columns([1, 3])

with kiri:
    with st.container(border=True):
        if st.button("Percakapan baru", width="stretch", icon=":material/add:"):
            st.session_state["active_conversation_id"] = None
            st.rerun()
        selected_profile = chat_ui.render_model_status_selector(llm_profiles)

    st.markdown("**Riwayat**")
    with st.container(key="chatpage_history_box", border=True):
        for conv in chat_store.list_conversations():
            is_active = conv["id"] == active_id
            label_col, menu_col = st.columns([5, 1], vertical_alignment="center")
            label = conv["title"] or "Percakapan baru"
            with label_col:
                if st.button(
                    label,
                    key=f"chatpage_conv_{conv['id']}",
                    width="stretch",
                    type="primary" if is_active else "secondary",
                ):
                    st.session_state["active_conversation_id"] = conv["id"]
                    st.rerun()
            with menu_col:
                with st.popover("", key=f"chatpage_menu_{conv['id']}"):
                    new_title = st.text_input(
                        "Ubah judul",
                        value=label,
                        key=f"chatpage_rename_{conv['id']}",
                        label_visibility="collapsed",
                    )
                    if st.button("Simpan judul", key=f"chatpage_rename_save_{conv['id']}", width="stretch"):
                        chat_store.update_title(conv["id"], new_title.strip() or "Percakapan baru")
                        st.rerun()
                    if st.button(
                        "Hapus percakapan",
                        key=f"chatpage_del_{conv['id']}",
                        width="stretch",
                        icon=":material/delete:",
                    ):
                        chat_store.delete_conversation(conv["id"])
                        if is_active:
                            st.session_state["active_conversation_id"] = None
                        st.rerun()

with kanan:
    typed_question = st.chat_input("Tanya mengenai rekrutmen...", key="chatpage_question")
    just_answered = False

    prefill = st.session_state.pop("chatpage_prefill", None)
    if prefill:
        # st.chat_input tidak punya parameter `value`/default (bukan keterbatasan
        # buatan v2 — API bawaan Streamlit memang tidak menyediakannya), jadi klik
        # saran tidak bisa native mengisi kotaknya. Trik ini menaruh teksnya
        # langsung ke elemen <textarea> lewat JS (window.parent.document, sama
        # seperti shortcut Ctrl+/ v1) — TIDAK mengirim apa pun, kotak tetap bisa
        # diedit, pengguna sendiri yang menekan Enter.
        components.html(
            """
            <script>
            (function() {
                const doc = window.parent.document;
                const text = __TEXT_JSON__;
                let attempts = 0;
                function trySet() {
                    const textarea = Array.from(doc.querySelectorAll('textarea')).find(
                        (el) => el.placeholder === 'Tanya mengenai rekrutmen...'
                    );
                    if (textarea) {
                        const setter = Object.getOwnPropertyDescriptor(
                            window.parent.HTMLTextAreaElement.prototype, 'value'
                        ).set;
                        setter.call(textarea, text);
                        textarea.dispatchEvent(new Event('input', { bubbles: true }));
                        textarea.focus();
                        return;
                    }
                    attempts += 1;
                    if (attempts < 20) {
                        setTimeout(trySet, 50);
                    }
                }
                trySet();
            })();
            </script>
            """.replace("__TEXT_JSON__", json.dumps(prefill)),
            height=0,
        )

    with st.container(key="chatpage_answers_box", border=True):
        if typed_question and typed_question.strip():
            active_id = chat_ui.submit_question(
                active_id, typed_question, selected_profile, key_prefix="chatpage"
            )
            just_answered = True

        turns = chat_store.load_turns(active_id)
        if not turns:
            st.markdown("##### Tanyakan apa saja tentang data rekrutmen PLN")
            st.caption("Atau klik salah satu contoh di bawah untuk mengisi kotak tanya.")
            saran_row = st.container(horizontal=True, horizontal_alignment="center")
            for i, saran in enumerate(chat_ui.SUGGESTIONS):
                if saran_row.button(saran, key=f"chatpage_suggestion_{i}"):
                    # Hanya mengisi — pertanyaan baru terkirim saat pengguna menekan
                    # Enter sendiri di kotak (lihat blok prefill JS di atas).
                    st.session_state["chatpage_prefill"] = saran
                    st.rerun()
        else:
            history_to_draw = turns[:-1] if just_answered else turns
            for idx, (question, response, answer_icon, created_at) in reversed(list(enumerate(history_to_draw))):
                chat_ui.render_turn(
                    question, response, answer_icon, idx, key_prefix="chatpage", created_at=created_at
                )
