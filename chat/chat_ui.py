"""Komponen UI chatbot — port dari recruitment_dashboard/chat_ui.py (v1).

Perubahan dari v1:
- Parameter `dataframes` dibuang di semua fungsi — v2 tidak memuat DataFrame ke
  memori; `run_sql_for_export` (chat/chatbot.py) membuka koneksi read-only sendiri
  langsung ke berkas .duckdb.
- Trik prefill pertanyaan lewat `st.components.v1.html` (v1) **dihapus** — API itu
  deprecated (lihat skill developing-with-streamlit § best practices). Diganti:
  klik saran langsung mengirim pertanyaan (submit_question dengan render_live=False),
  bukan menyalin teks ke kotak input.
- Emoji dekoratif (🔍📊⬇️🗑🔄✅🤖😊🟢🔴⚠️💬) diganti ikon Material atau teks polos (D6).
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Iterator
from zoneinfo import ZoneInfo

import streamlit as st

from chat import chat_store
from chat.chatbot import (
    answer_question,
    build_conversation_context,
    check_llm_connection,
    pesan_aman,
    run_sql_for_export,
    update_chat_summary,
)

LLM_STATUS_TTL_SECONDS = 300

SUGGESTIONS = [
    "Tahap mana yang paling banyak menggugurkan kandidat?",
    "Sebutkan 5 unit induk dengan gap FTK terbesar",
    "Berapa persen jalur RBB yang berjejak di sistem PLN?",
    "Berapa orang yang sedang OJT sekarang?",
]


def get_selected_profile(llm_profiles: list[dict[str, str]]) -> dict[str, str] | None:
    if not llm_profiles:
        return None
    profile_by_id = {p["id"]: p for p in llm_profiles}
    selected_id = st.session_state.get("copilot_llm_profile")
    if selected_id not in profile_by_id:
        selected_id = llm_profiles[0]["id"]
    return profile_by_id[selected_id]


def render_model_status_selector(
    llm_profiles: list[dict[str, str]],
    show_new_chat_button: bool = False,
    auto_check: bool = True,
) -> dict[str, str] | None:
    """Selectbox + status/recheck, dipakai bersama oleh popover mengambang (lintas
    halaman) dan halaman RecruitMan sendiri — satu sumber kebenaran untuk model aktif.
    Popover mengambang juga dapat tombol "Percakapan baru" ringkas di sebelah tombol
    cek ulang (halaman RecruitMan penuh sudah punya tombol lebar sendiri di sidebar,
    jadi tidak perlu yang kedua di sini).

    `auto_check=False` (dipakai popover mengambang) mematikan ping otomatis saat
    status basi/kosong — isi `with st.popover(...):` DIEKSEKUSI di server pada
    SETIAP render halaman, bukan cuma saat popover-nya benar-benar dibuka (ini
    terukur menambah ~5 detik ke SETIAP navigasi halaman, karena tiap sesi baru
    langsung memicu ping jaringan nyata ke API LLM). Dengan auto_check=False,
    status cuma tampil dari cache sesi kalau ada (mis. sudah dicek dari halaman
    RecruitMan penuh) atau "belum dicek" — ping baru terjadi saat pengguna
    menekan tombol cek ulang sendiri."""
    if not llm_profiles:
        st.caption("Mode demo tanpa API: belum ada profil LLM di secrets.toml")
        return None

    profile_by_id = {p["id"]: p for p in llm_profiles}
    if show_new_chat_button:
        status_col, recheck_col, new_chat_col = st.columns([4, 1, 1], vertical_alignment="bottom")
    else:
        status_col, recheck_col = st.columns([5, 1], vertical_alignment="bottom")
    with status_col:
        selected_id = st.selectbox(
            "Model LLM",
            list(profile_by_id.keys()),
            format_func=lambda pid: f"{profile_by_id[pid]['icon']} {profile_by_id[pid]['label']}",
            key="copilot_llm_profile",
            label_visibility="collapsed",
        )
    selected_profile = profile_by_id[selected_id]

    status_cache = st.session_state.setdefault("copilot_llm_status", {})
    cached = status_cache.get(selected_id)
    stale = cached is None or (time.time() - cached["checked_at"] > LLM_STATUS_TTL_SECONDS)
    with recheck_col:
        force_recheck = st.button(
            "", icon=":material/refresh:", key=f"copilot_recheck_{selected_id}", help="Cek ulang koneksi"
        )
    if show_new_chat_button:
        with new_chat_col:
            if st.button("", icon=":material/add:", key="popover_new_chat", help="Percakapan baru"):
                st.session_state["active_conversation_id"] = None
                st.rerun()

    if force_recheck or (auto_check and stale):
        with st.spinner("Mengecek koneksi..."):
            ok, detail = check_llm_connection(selected_profile)
        status_cache[selected_id] = {"ok": ok, "detail": detail, "checked_at": time.time()}
        cached = status_cache[selected_id]

    note = f" · {selected_profile['note']}" if selected_profile.get("note") else ""
    if cached is None:
        st.badge("Belum dicek", icon=":material/help:", color="gray")
    elif cached["ok"]:
        st.badge(f"Terhubung{note}", icon=":material/check_circle:", color="green")
    else:
        st.badge(f"Gagal terhubung{note}", icon=":material/error:", color="red")
        st.caption(cached["detail"][:150])
    return selected_profile


def _format_turn_time(created_at: str | None) -> str:
    if not created_at:
        return ""
    try:
        dt = datetime.fromisoformat(created_at)
    except ValueError:
        return ""
    tz_name = st.context.timezone
    if tz_name:
        try:
            dt = dt.astimezone(ZoneInfo(tz_name))
        except Exception:
            pass
    return dt.strftime("%d/%m/%Y %H:%M")


def _render_export_button(block: dict[str, Any], export_key: str) -> None:
    """Tombol "unduh semua baris" — hanya muncul kalau tabel yang ditampilkan
    memang terpotong dari total baris hasil query."""
    total_rows = block.get("total_rows")
    table = block.get("table")
    if not total_rows or table is None or total_rows <= len(table) or not block.get("sql"):
        return

    if export_key not in st.session_state:
        if st.button(
            f"Siapkan semua {total_rows:,} baris (CSV)".replace(",", "."),
            key=f"{export_key}_prepare",
            icon=":material/download:",
        ):
            with st.spinner("Menyiapkan file..."):
                try:
                    full_table = run_sql_for_export(block["sql"])
                    st.session_state[export_key] = full_table.to_csv(index=False).encode("utf-8")
                except Exception as exc:
                    st.error(f"Gagal menyiapkan file: {pesan_aman(exc)}")
                    return
            st.rerun()
    else:
        st.download_button(
            f"Unduh semua {total_rows:,} baris (CSV)".replace(",", "."),
            data=st.session_state[export_key],
            file_name=f"{export_key}.csv",
            mime="text/csv",
            key=f"{export_key}_download",
            icon=":material/download:",
        )


def _render_result_blocks(response: dict[str, Any], idx: int, key_prefix: str) -> None:
    for block_idx, block in enumerate(response.get("results") or []):
        if block.get("sql"):
            if st.checkbox("Lihat SQL", key=f"{key_prefix}_sql_{idx}_{block_idx}"):
                st.code(block["sql"], language="sql")
        if block.get("table") is not None:
            st.dataframe(block["table"], width="stretch", hide_index=True)
            _render_export_button(block, f"{key_prefix}_export_{idx}_{block_idx}")
        if block.get("chart") is not None:
            st.plotly_chart(block["chart"], width="stretch", key=f"{key_prefix}_chart_{idx}_{block_idx}")


def _typewriter_chunks(text: str, target_chunks: int = 60, delay: float = 0.02) -> Iterator[str]:
    words = text.split(" ")
    if not words:
        return
    chunk_size = max(1, len(words) // target_chunks)
    for i in range(0, len(words), chunk_size):
        piece = " ".join(words[i : i + chunk_size])
        yield piece + (" " if i + chunk_size < len(words) else "")
        time.sleep(delay)


def render_turn(
    question: str,
    response: dict[str, Any],
    answer_icon: str,
    idx: int,
    key_prefix: str,
    created_at: str | None = None,
) -> None:
    with st.chat_message("user"):
        st.markdown(question)
        time_label = _format_turn_time(created_at)
        if time_label:
            st.caption(time_label)
    with st.chat_message("assistant", avatar=answer_icon):
        _render_result_blocks(response, idx, key_prefix)
        st.markdown(response["text"])


def submit_question(
    conversation_id: int | None,
    question: str,
    profile: dict[str, str] | None,
    key_prefix: str = "live",
    render_live: bool = True,
) -> int:
    if conversation_id is None:
        conversation_id = chat_store.create_conversation()
        st.session_state["active_conversation_id"] = conversation_id

    conv = chat_store.get_conversation(conversation_id) or {"chat_summary": "", "summary_upto": 0}
    history_before = chat_store.load_turns(conversation_id)
    buffer_turns = [(q, r) for q, r, _icon, _created_at in history_before[-2:]]
    summary = conv.get("chat_summary") or ""
    conversation_context = build_conversation_context(summary, buffer_turns)
    new_turn_idx = len(history_before)

    if render_live:
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant", avatar=profile["icon"] if profile else ":material/smart_toy:"):
            steps: list[str] = []
            status_box = st.status("Memproses pertanyaan...", expanded=True)
            with status_box:
                def on_step(msg: str) -> None:
                    steps.append(msg)
                    st.write(msg)

                response = answer_question(
                    question,
                    profile=profile,
                    conversation_context=conversation_context,
                    on_step=on_step,
                )
            status_box.update(
                label="Selesai" if steps else "Jawaban siap",
                state="complete",
                expanded=False,
            )
            _render_result_blocks(response, new_turn_idx, key_prefix)
            st.write_stream(_typewriter_chunks(response["text"]))
    else:
        response = answer_question(question, profile=profile, conversation_context=conversation_context)

    if response.get("kind") == "llm" and profile:
        answer_icon = profile["icon"]
    else:
        answer_icon = ":material/smart_toy:"
    chat_store.append_turn(conversation_id, question, response, answer_icon)

    history_after = chat_store.load_turns(conversation_id)
    summarized_upto = conv.get("summary_upto") or 0
    foldable_end = len(history_after) - 2
    if foldable_end > summarized_upto:
        new_turns = [(q, r) for q, r, _icon, _created_at in history_after[summarized_upto:foldable_end]]
        new_summary = update_chat_summary(summary, new_turns, profile)
        chat_store.update_summary(conversation_id, new_summary, foldable_end)

    return conversation_id
