"""Pembangun chart Altair yang dipakai lebih dari satu halaman.

Hanya bentuk yang berulang yang ditaruh di sini (heatmap berlabel, bullet chart,
skala kelompok rekrutmen). Chart yang khas satu halaman tetap ditulis di halamannya
supaya berkas halaman bisa dibaca dari atas ke bawah.
"""

from __future__ import annotations

import altair as alt
import pandas as pd

from core import theme
from core.format import angka

KELOMPOK = ["Terbuka", "Afirmasi", "RBB"]


def skala_kelompok() -> alt.Scale:
    """Warna tetap per kelompok rekrutmen, tidak pernah berganti saat filter mengurangi seri."""
    return alt.Scale(domain=KELOMPOK, range=theme.seri()[:3])


def warna_kelompok(legend: bool = True) -> alt.Color:
    return alt.Color(
        "kelompok:N",
        scale=skala_kelompok(),
        legend=alt.Legend(title=None, orient="top") if legend else None,
    )


def heatmap(
    df: pd.DataFrame,
    x: str,
    y: str,
    nilai: str,
    *,
    urutan_x: list | None = None,
    urutan_y: list | None = None,
    domain: tuple[float, float] | None = None,
    format_label: str = ".0f",
    tinggi_baris: int = 34,
    tooltip: list | None = None,
    label: bool = True,
    sudut_label_x: int = 0,
) -> alt.LayerChart | alt.Chart:
    """Heatmap satu hue dengan angka di tiap sel. Tinta putih di sel gelap."""
    t = theme.token()
    batas = domain or (0, float(df[nilai].max() or 1))
    ambang = batas[0] + 0.55 * (batas[1] - batas[0])
    dasar = alt.Chart(df).encode(
        x=alt.X(
            f"{x}:N",
            sort=urutan_x,
            title=None,
            axis=alt.Axis(
                # Label miring ditaruh di BAWAH dan condong ke kiri: label miring di atas
                # menjorok ke kanan melewati plot, lalu Vega mengecilkan seluruh heatmap.
                labelAngle=sudut_label_x,
                labelAlign="right" if sudut_label_x else "center",
                labelLimit=150,
                orient="bottom" if sudut_label_x else "top",
                labelOverlap=False,
                ticks=False,
                domain=False,
            ),
        ),
        y=alt.Y(f"{y}:N", sort=urutan_y, title=None, axis=alt.Axis(ticks=False, domain=False, labelLimit=180, labelOverlap=False)),
    )
    sel = dasar.mark_rect(cornerRadius=3, stroke=t["surface_card"], strokeWidth=2).encode(
        color=alt.Color(f"{nilai}:Q", scale=alt.Scale(domain=list(batas), range=theme.RAMP), legend=None),
        tooltip=tooltip or [f"{y}:N", f"{x}:N", alt.Tooltip(f"{nilai}:Q", format=format_label)],
    )
    n_baris = df[y].nunique()
    # Selalu dikembalikan sebagai layer: chart tunggal bersumbu x diskret dirender dengan
    # lebar tetap 20px per kolom, sedangkan layer ikut melebar ke kontainer.
    teks = dasar.mark_text(fontSize=11, fontWeight=600, opacity=1 if label else 0).encode(
        text=alt.Text(f"{nilai}:Q", format=format_label),
        color=alt.condition(f"datum.{nilai} > {ambang}", alt.value("#FFFFFF"), alt.value("#103A5D")),
    )
    return (sel + teks).properties(height=max(tinggi_baris * n_baris, 100))


def bullet(
    df: pd.DataFrame,
    kategori: str,
    target: str,
    capaian: str,
    *,
    label_target: str,
    label_capaian: str,
    horizontal: bool = False,
    tinggi: int = 260,
) -> alt.LayerChart:
    """Bullet chart: batang lebar pucat = target, batang sempit pekat = capaian, persen di ujung.

    Pengganti sumbu ganda untuk "rencana vs realisasi": satu skala, dua ketebalan.
    """
    t = theme.token()
    warna = theme.seri()[0]
    data = df.copy()
    data["_pct"] = (100 * data[capaian] / data[target]).round(0)
    data["_label"] = data["_pct"].map(lambda v: f"{v:.0f}%")
    data["_target_teks"] = data[target].map(angka)
    data["_capaian_teks"] = data[capaian].map(angka)
    tooltip = [
        alt.Tooltip(f"{kategori}:N", title=kategori.capitalize()),
        alt.Tooltip("_target_teks:N", title=label_target),
        alt.Tooltip("_capaian_teks:N", title=label_capaian),
        alt.Tooltip("_label:N", title="Capaian"),
    ]
    # Capaian bisa melampaui target (pemenuhan >100%). Skala dan titik jangkar label
    # karena itu memakai yang terbesar di antara keduanya, bukan target saja — kalau
    # tidak, batang capaian keluar dari domain dan labelnya tertimpa batang itu sendiri.
    data["_ujung"] = data[[target, capaian]].max(axis=1)
    puncak = float(data["_ujung"].max()) * 1.15
    if horizontal:
        pos_k = alt.Y(f"{kategori}:N", title=None, sort=None)
        skala = alt.X(f"{target}:Q", title=None, scale=alt.Scale(domain=[0, puncak]), axis=alt.Axis(format="~s", tickCount=4))
        isi = alt.X(f"{capaian}:Q")
        belakang = alt.Chart(data).mark_bar(color=t["netral"], opacity=0.45, cornerRadiusTopRight=4, cornerRadiusBottomRight=4, height=22)
        depan = alt.Chart(data).mark_bar(color=warna, cornerRadiusTopRight=3, cornerRadiusBottomRight=3, height=9)
        teks = alt.Chart(data).mark_text(align="left", dx=6, fontSize=12, color=t["text_secondary"]).encode(
            y=pos_k, x=alt.X("_ujung:Q"), text="_label:N"
        )
        return (
            belakang.encode(y=pos_k, x=skala, tooltip=tooltip)
            + depan.encode(y=pos_k, x=isi, tooltip=tooltip)
            + teks
        ).properties(height=tinggi)
    pos_k = alt.X(f"{kategori}:O", title=None, axis=alt.Axis(labelAngle=0))
    skala = alt.Y(f"{target}:Q", title=None, scale=alt.Scale(domain=[0, puncak]), axis=alt.Axis(format="~s", tickCount=4))
    belakang = alt.Chart(data).mark_bar(color=t["netral"], opacity=0.45, cornerRadiusTopLeft=4, cornerRadiusTopRight=4, width={"band": 0.7})
    depan = alt.Chart(data).mark_bar(color=warna, cornerRadiusTopLeft=3, cornerRadiusTopRight=3, width={"band": 0.3})
    teks = alt.Chart(data).mark_text(dy=-8, fontSize=12, color=t["text_secondary"]).encode(
        x=pos_k, y=alt.Y("_ujung:Q"), text="_label:N"
    )
    return (
        belakang.encode(x=pos_k, y=skala, tooltip=tooltip)
        + depan.encode(x=pos_k, y=alt.Y(f"{capaian}:Q"), tooltip=tooltip)
        + teks
    ).properties(height=tinggi)
