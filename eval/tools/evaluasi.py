#!/usr/bin/env python3
"""Evaluasi detektor PII pada split dev.

    python3 eval/tools/evaluasi.py jalan prototipe|presidio
    python3 eval/tools/evaluasi.py banding prototipe presidio
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Callable

import cek_dataset as v
import statistik

AKAR = Path(__file__).resolve().parents[2]
DEV = AKAR / "eval" / "dev" / "uji_pii_id.csv"
HASIL = AKAR / "eval" / "results"
ENTITAS = v.ENTITAS_P0
ENTITAS_T003 = ["nik", "kk", "credit_card", "bpjs", "bank_account"]
LANGSUNG = ["nik", "kk", "nip", "npwp", "passport_id", "bpjs", "credit_card",
            "bank_account", "email", "phone_id"]
KUASI = ["birth_date"]

Detektor = Callable[[list[tuple[str, str]]], list[tuple[str, str]]]


def pesan_dari_teks(teks: str) -> list[tuple[str, str]]:
    if not teks.startswith("<<"):
        return [("user", teks)]
    bagian = re.split(r"^<<(\w+)>> ", teks, flags=re.M)[1:]
    return [(bagian[i], bagian[i + 1].rstrip("\n")) for i in range(0, len(bagian), 2)]


def normal(nilai: str) -> str:
    return re.sub(r"[\s.\-]", "", nilai)


def muat_detektor(nama: str) -> tuple[Detektor, dict]:
    if nama == "prototipe":
        import prototipe_detektor as p

        def jalankan(pesan):
            return [(t.jenis, t.nilai) for daftar in p.deteksi(pesan) for t in daftar]

        return jalankan, {"keterangan": "prototipe referensi OmniRail (regex + validator + kata konteks, PRD 7.10)"}
    if nama == "presidio":
        import baseline_presidio as b

        return b.detektor(), b.KONFIGURASI
    raise SystemExit(f"detektor tidak dikenal: {nama}")


def evaluasi(detektor: Detektor) -> dict:
    with DEV.open(newline="", encoding="utf-8") as f:
        baris = [r for r in csv.DictReader(f)
                 if r["kategori"] in ("positif", "negatif") and r["cakupan_mvp"] == "ya"]
    tp, fn, fp = Counter(), Counter(), Counter()
    neg_total, neg_kotor = Counter(), Counter()
    butir: dict[str, int] = {}
    gagal = []
    for r in baris:
        temuan = [(j, normal(n)) for j, n in detektor(pesan_dari_teks(r["teks"])) if j in ENTITAS]
        harap = [] if r["diharapkan"] == "-" else [
            (j, normal(n)) for j, n in (p.split(":", 1) for p in r["diharapkan"].split(" | "))
            if j in ENTITAS]
        sisa = Counter(temuan)
        for i, (j, n) in enumerate(harap):
            ok = sisa[(j, n)] > 0
            if ok:
                sisa[(j, n)] -= 1
                tp[j] += 1
            else:
                fn[j] += 1
                gagal.append({"id": r["id"], "jenis": "terlewat", "entitas": j})
            butir[f"pos:{r['id']}:{i}:{j}"] = int(ok)
        for (j, _), k in sisa.items():
            if k > 0:
                fp[j] += k
                gagal.append({"id": r["id"], "jenis": "salah tandai", "entitas": j})
        if r["kategori"] == "negatif":
            jebak = re.match(r"\[([a-z_]+)\]", r["catatan"])
            e = jebak[1] if jebak else "lain"
            neg_total[e] += 1
            bersih = not temuan
            neg_kotor[e] += 0 if bersih else 1
            butir[f"neg:{r['id']}"] = int(bersih)

    def ringkas(tp_, fn_, fp_, nt, nk):
        hasil = {}
        if tp_ + fn_:
            hasil["recall"] = _angka(tp_, tp_ + fn_)
        if tp_ + fp_:
            hasil["precision"] = _angka(tp_, tp_ + fp_)
        if nt:
            hasil["false_positive"] = _angka(nk, nt)
        hasil.update({"tp": tp_, "fn": fn_, "fp": fp_})
        return hasil

    per = {e: ringkas(tp[e], fn[e], fp[e], neg_total[e], neg_kotor[e]) for e in ENTITAS}

    def gabung(daftar):
        return ringkas(sum(tp[e] for e in daftar), sum(fn[e] for e in daftar),
                       sum(fp[e] for e in daftar), sum(neg_total[e] for e in daftar),
                       sum(neg_kotor[e] for e in daftar))

    return {
        "per_entitas": per,
        "gabungan": {
            "semua_p0": ringkas(sum(tp.values()), sum(fn.values()), sum(fp.values()),
                                sum(neg_total.values()), sum(neg_kotor.values())),
            "t003": gabung(ENTITAS_T003),
            "identifier_langsung": gabung(LANGSUNG),
            "identifier_kuasi": gabung(KUASI),
        },
        "butir": butir,
        "kasus_gagal": gagal,
    }


def _angka(k: int, n: int) -> dict:
    lo, hi = statistik.wilson(k, n)
    return {"nilai": round(k / n, 4), "k": k, "n": n, "ci95": [round(lo, 4), round(hi, 4)]}


def _commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=AKAR,
                              capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "tidak diketahui"


def _fmt(x: dict | None) -> str:
    if not x:
        return "—"
    return f"{x['nilai']:.3f} ({x['ci95'][0]:.3f}–{x['ci95'][1]:.3f})"


def markdown(nama: str, hasil: dict) -> str:
    m = hasil["meta"]
    baris = [
        f"# Hasil evaluasi dev: {nama}",
        "",
        f"Dataset `{m['dataset']}`, commit `{m['commit']}`, waktu {m['waktu']}. "
        "Angka dalam kurung adalah interval Wilson 95%.",
        "",
        f"Konfigurasi: {m['konfigurasi'].get('keterangan', '-')}",
        "",
        "| Entitas | Recall | Precision | False positive (baris negatif) | TP | FN | FP |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for e, x in hasil["per_entitas"].items():
        baris.append(f"| `{e}` | {_fmt(x.get('recall'))} | {_fmt(x.get('precision'))} | "
                     f"{_fmt(x.get('false_positive'))} | {x['tp']} | {x['fn']} | {x['fp']} |")
    baris += ["", "| Gabungan | Recall | Precision | False positive |", "| --- | --- | --- | --- |"]
    for g, x in hasil["gabungan"].items():
        baris.append(f"| {g} | {_fmt(x.get('recall'))} | {_fmt(x.get('precision'))} | "
                     f"{_fmt(x.get('false_positive'))} |")
    return "\n".join(baris) + "\n"


def jalan(nama: str) -> dict:
    detektor, konfig = muat_detektor(nama)
    hasil = evaluasi(detektor)
    hasil["meta"] = {
        "sistem": nama,
        "commit": _commit(),
        "dataset": "eval/dev/uji_pii_id.csv v0.6",
        "waktu": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "konfigurasi": konfig,
    }
    HASIL.mkdir(parents=True, exist_ok=True)
    (HASIL / f"dev-{nama}.json").write_text(json.dumps(hasil, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (HASIL / f"dev-{nama}.md").write_text(markdown(nama, hasil), encoding="utf-8")
    return hasil


def banding(a: str, b: str) -> str:
    ha = json.loads((HASIL / f"dev-{a}.json").read_text(encoding="utf-8"))
    hb = json.loads((HASIL / f"dev-{b}.json").read_text(encoding="utf-8"))
    ba, bb = ha["butir"], hb["butir"]

    def uji(awalan: str, entitas: list[str] | None) -> tuple[int, int, int, float]:
        kunci = [k for k in ba if k.startswith(awalan) and k in bb]
        if entitas is not None:
            kunci = [k for k in kunci if k.rsplit(":", 1)[-1] in entitas]
        hanya_a = sum(1 for k in kunci if ba[k] and not bb[k])
        hanya_b = sum(1 for k in kunci if bb[k] and not ba[k])
        return len(kunci), hanya_a, hanya_b, statistik.mcnemar_eksak(hanya_a, hanya_b)

    baris = [f"# Perbandingan dev: {a} lawan {b}", "",
             f"Uji McNemar eksak per butir. Kolom \"hanya {a}\" = butir yang benar di {a} tetapi salah di {b}.", "",
             f"| Ukuran | Butir | Hanya {a} | Hanya {b} | p |", "| --- | --- | --- | --- | --- |"]
    for label, awalan, ent in [
        ("Recall, lima entitas T-003", "pos:", ENTITAS_T003),
        ("Recall, semua entitas P0", "pos:", None),
    ]:
        n, x, y, p = uji(awalan, ent)
        baris.append(f"| {label} | {n} | {x} | {y} | {p:.4g} |")
    kunci_neg = [k for k in ba if k.startswith("neg:") and k in bb]
    x = sum(1 for k in kunci_neg if ba[k] and not bb[k])
    y = sum(1 for k in kunci_neg if bb[k] and not ba[k])
    baris.append(f"| Baris negatif bersih, semua | {len(kunci_neg)} | {x} | {y} | {statistik.mcnemar_eksak(x, y):.4g} |")
    baris += ["", "| Gabungan T-003 | " + a + " | " + b + " |", "| --- | --- | --- |"]
    for uk in ("recall", "precision", "false_positive"):
        baris.append(f"| {uk} | {_fmt(ha['gabungan']['t003'].get(uk))} | {_fmt(hb['gabungan']['t003'].get(uk))} |")
    teks = "\n".join(baris) + "\n"
    (HASIL / f"banding-{a}-{b}.md").write_text(teks, encoding="utf-8")
    return teks


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] == "jalan":
        print(markdown(argv[1], jalan(argv[1])))
        return 0
    if len(argv) == 3 and argv[0] == "banding":
        print(banding(argv[1], argv[2]))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
