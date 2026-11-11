#!/usr/bin/env python3
"""Sampel dan penilaian tinjauan label dataset dev.

    python3 eval/tools/tinjau_label.py sampel
    python3 eval/tools/tinjau_label.py nilai eval/tinjauan/t007-formulir-NAMA.csv
"""

from __future__ import annotations

import csv
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

import cek_dataset as v
import statistik

AKAR = Path(__file__).resolve().parents[2]
DEV = AKAR / "eval" / "dev" / "uji_pii_id.csv"
FOLDER = AKAR / "eval" / "tinjauan"
FORMULIR = FOLDER / "t007-formulir.csv"
KOLOM_FORMULIR = ["id", "teks", "label_penilai", "cakupan_penilai", "komentar"]
BENIH = 7


def label_baris(r: dict) -> str:
    if r["kategori"] in ("kredensial", "injeksi"):
        return r["diharapkan"]
    if r["diharapkan"] == "-":
        return "-"
    return "+".join(sorted({p.split(":", 1)[0] for p in r["diharapkan"].split(" | ")}))


def baca_dev() -> dict[str, dict]:
    with DEV.open(newline="", encoding="utf-8") as f:
        return {r["id"]: r for r in csv.DictReader(f)}


def sampel() -> list[dict]:
    rng = random.Random(BENIH)
    baris = list(baca_dev().values())
    terpilih: dict[str, dict] = {}

    def ambil(kandidat, n):
        kandidat = [r for r in kandidat if r["id"] not in terpilih]
        for r in rng.sample(kandidat, min(n, len(kandidat))):
            terpilih[r["id"]] = r

    for e in v.ENTITAS_P0 + v.ENTITAS_P1:
        n = 4 if e in v.ENTITAS_P0 else 3
        ambil([r for r in baris if r["kategori"] == "positif" and f"{e}:" in r["diharapkan"]], n)
        ambil([r for r in baris if r["kategori"] == "negatif" and r["catatan"].startswith(f"[{e}]")], n)
    for kategori in ("kredensial", "injeksi"):
        ambil([r for r in baris if r["kategori"] == kategori], 10)
    hasil = sorted(terpilih.values(), key=lambda r: int(r["id"][1:]))
    FOLDER.mkdir(parents=True, exist_ok=True)
    with FORMULIR.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=KOLOM_FORMULIR, lineterminator="\n")
        w.writeheader()
        for r in hasil:
            w.writerow({"id": r["id"], "teks": r["teks"], "label_penilai": "", "cakupan_penilai": "", "komentar": ""})
    return hasil


def nilai(path: Path) -> dict:
    dev = baca_dev()
    with path.open(newline="", encoding="utf-8") as f:
        isian = [r for r in csv.DictReader(f)]
    kosong = [r["id"] for r in isian if not r["label_penilai"].strip()]
    if kosong:
        raise SystemExit(f"{len(kosong)} baris belum diisi, misalnya {', '.join(kosong[:5])}")
    asli, penilai, beda, beda_cakupan = [], [], [], []
    for r in isian:
        d = dev[r["id"]]
        a = label_baris(d)
        p = "+".join(sorted(x.strip() for x in r["label_penilai"].split("+")))
        asli.append(a)
        penilai.append(p)
        if a != p:
            beda.append({"id": r["id"], "label_dataset": a, "label_penilai": p, "komentar": r["komentar"]})
        cak = r["cakupan_penilai"].strip()
        if cak and cak != d["cakupan_mvp"]:
            beda_cakupan.append({"id": r["id"], "dataset": d["cakupan_mvp"], "penilai": cak, "komentar": r["komentar"]})
    n = len(isian)
    sepakat = n - len(beda)
    lo, hi = statistik.wilson(len(beda), n)
    return {
        "berkas": str(path.relative_to(AKAR)),
        "n": n,
        "kesepakatan": round(sepakat / n, 4),
        "kappa": round(statistik.cohen_kappa(asli, penilai), 4),
        "ketidaksepakatan": {"k": len(beda), "nilai": round(len(beda) / n, 4), "ci95": [round(lo, 4), round(hi, 4)]},
        "per_label": dict(Counter(a for a, p in zip(asli, penilai) if a != p)),
        "beda_label": beda,
        "beda_cakupan": beda_cakupan,
    }


def markdown(h: dict) -> str:
    k = h["ketidaksepakatan"]
    baris = [
        f"# Hasil tinjauan label: `{h['berkas']}`",
        "",
        f"- Baris dinilai: {h['n']}",
        f"- Kesepakatan label baris: {h['kesepakatan']:.3f}",
        f"- Kappa Cohen: {h['kappa']:.3f} (target ≥ 0,8)",
        f"- Ketidaksepakatan: {k['k']} baris, {k['nilai']:.3f} ({k['ci95'][0]:.3f}–{k['ci95'][1]:.3f}); "
        "batas atas tingkat kesalahan sebelum adjudikasi (target ≤ 0,05)",
        "",
        "| ID | Label dataset | Label penilai | Komentar |",
        "| --- | --- | --- | --- |",
    ]
    for b in h["beda_label"]:
        baris.append(f"| {b['id']} | `{b['label_dataset']}` | `{b['label_penilai']}` | {b['komentar'] or '—'} |")
    if h["beda_cakupan"]:
        baris += ["", "| ID | `cakupan_mvp` dataset | Penilai | Komentar |", "| --- | --- | --- | --- |"]
        for b in h["beda_cakupan"]:
            baris.append(f"| {b['id']} | {b['dataset']} | {b['penilai']} | {b['komentar'] or '—'} |")
    return "\n".join(baris) + "\n"


def main(argv: list[str]) -> int:
    if argv == ["sampel"]:
        hasil = sampel()
        print(f"{len(hasil)} baris ditulis ke {FORMULIR.relative_to(AKAR)}")
        print(dict(Counter(r["kategori"] for r in hasil)))
        return 0
    if len(argv) == 2 and argv[0] == "nilai":
        path = Path(argv[1]).resolve()
        h = nilai(path)
        nama = re.sub(r"^t007-formulir-?", "", path.stem) or "penilai"
        keluar = AKAR / "eval" / "results" / f"t007-{nama}"
        keluar.with_suffix(".json").write_text(json.dumps(h, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        keluar.with_suffix(".md").write_text(markdown(h), encoding="utf-8")
        print(markdown(h))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
