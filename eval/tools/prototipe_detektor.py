#!/usr/bin/env python3
"""Prototipe detektor referensi.

    python3 eval/tools/prototipe_detektor.py "NIK saya 3273011503900001"
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass

import cek_dataset as v

ENTITAS_P0 = v.ENTITAS_P0

PRIORITAS = [
    "credit_card", "nip", "nik", "npwp", "bpjs", "bank_account",
    "phone_id", "passport_id", "birth_date", "email",
]
KONTEKS_WAJIB = {"kk", "passport_id", "bpjs", "birth_date", "bank_account"}

KONTEKS: dict[str, list[tuple[str, ...]]] = {
    "nik": [("nik",), ("ktp",), ("no", "induk"), ("nomor", "induk"), ("induk", "kependudukan")],
    "npwp": [("npwp",), ("nomor", "pokok", "wajib", "pajak")],
    "bank_account": [("rekening",), ("rek",), ("norek",), ("a", "n"), ("account",)],
    "nip": [("nip",), ("pns",), ("asn",), ("pegawai",)],
    "kk": [("kk",), ("kartu", "keluarga")],
    "passport_id": [("paspor",), ("passport",)],
    "bpjs": [("bpjs",), ("kis",), ("jkn",), ("kpj",)],
    "birth_date": [("lahir",), ("tgl", "lahir"), ("tanggal", "lahir"), ("ttl",), ("dob",),
                   ("birth",), ("kelahiran",)],
    "credit_card": [("kartu",), ("card",), ("cc",), ("kredit",), ("debit",), ("visa",),
                    ("mastercard",)],
    "phone_id": [("hp",), ("telp",), ("telepon",), ("wa",), ("whatsapp",), ("sms",),
                 ("ponsel",), ("handphone",)],
}
JARAK_KONTEKS = 5
LINTAS_AWAL = 10
LINTAS_EKOR = 15

BULAN = "|".join(sorted(v.BULAN_ID, key=len, reverse=True))
EKSTENSI_BERKAS = {"png", "jpg", "jpeg", "gif", "svg", "webp", "pdf", "ico", "bmp"}

POLA: list[tuple[str, re.Pattern[str]]] = [
    ("email", re.compile(r"(?<![\w.+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")),
    ("phone_id", re.compile(r"(?<![\w+])(?:\+62[ .\-]?|62|0)8(?:[ .\-]?\d){7,12}(?![\w])")),
    ("credit_card", re.compile(r"(?<![\w.])\d(?:[ \-]?\d){12,18}(?![\w])")),
    ("nik", re.compile(r"(?<![\w.])\d{16}(?![\w])")),
    ("kk", re.compile(r"(?<![\w.])\d{16}(?![\w])")),
    ("npwp", re.compile(r"(?<![\w.])(?:\d{2}\.\d{3}\.\d{3}\.\d-\d{3}\.\d{3}|\d{15,16})(?![\w])")),
    ("nip", re.compile(r"(?<![\w.])\d{8} ?\d{6} ?\d ?\d{3}(?![\w])")),
    ("bank_account", re.compile(r"(?<![\w.])\d(?:[ \-]?\d){7,15}(?![\w])")),
    ("passport_id", re.compile(r"(?<![\w])[A-Z]{1,2} ?\d{6,7}(?![\w])")),
    ("bpjs", re.compile(r"(?<![\w.])(?:\d{16}|\d{13}|\d{11})(?![\w])")),
    ("birth_date", re.compile(
        rf"(?<![\w])(?:\d{{2}}[-/.]\d{{2}}[-/.]\d{{4}}|\d{{4}}-\d{{2}}-\d{{2}}|\d{{1,2}} (?:{BULAN}) \d{{4}})(?![\w])",
        re.IGNORECASE)),
]

VALIDATOR = {
    "email": v.cek_email, "phone_id": v.cek_phone_id, "credit_card": v.cek_credit_card,
    "nik": v.cek_nik, "kk": v.cek_kk, "npwp": v.cek_npwp, "nip": v.cek_nip,
    "bank_account": v.cek_bank_account, "passport_id": v.cek_passport_id,
    "bpjs": v.cek_bpjs, "birth_date": v.cek_birth_date,
}


@dataclass(frozen=True)
class Temuan:
    jenis: str
    nilai: str
    mulai: int
    akhir: int


@dataclass
class _Token:
    teks: str
    mulai: int
    akhir: int


def _dasar(kata: str) -> str:
    for akhiran in ("nya", "ku", "mu"):
        if kata.endswith(akhiran) and len(kata) - len(akhiran) >= 3:
            return kata[: -len(akhiran)]
    return kata


def _token(teks: str) -> list[_Token]:
    return [_Token(m.group().lower(), m.start(), m.end()) for m in re.finditer(r"[A-Za-z]+|\d+", teks)]


def _posisi_konteks(token: list[_Token], jenis: str) -> list[tuple[int, int]]:
    hasil = []
    kata = [t.teks for t in token]
    for frasa in KONTEKS.get(jenis, []):
        n = len(frasa)
        for i in range(len(kata) - n + 1):
            potong = kata[i:i + n]
            if tuple(potong) != frasa and tuple(potong[:-1] + [_dasar(potong[-1])]) != frasa:
                continue
            if jenis == "birth_date" and frasa == ("lahir",):
                if kata[i + 1:i + 3] == ["dan", "batin"] or (i > 0 and kata[i - 1] == "hari"):
                    continue
            hasil.append((i, i + n - 1))
    return hasil


def _indeks_token(token: list[_Token], mulai: int, akhir: int) -> tuple[int, int]:
    dalam = [i for i, t in enumerate(token) if t.mulai >= mulai and t.akhir <= akhir]
    if dalam:
        return dalam[0], dalam[-1]
    sebelum = [i for i, t in enumerate(token) if t.akhir <= mulai]
    i = sebelum[-1] + 1 if sebelum else 0
    return i, i - 1


def _jarak_konteks(jenis: str, token: list[_Token], awal: int, ujung: int,
                   token_lalu: list[_Token] | None) -> float | None:
    terbaik = None
    for a, b in _posisi_konteks(token, jenis):
        if b < awal:
            jarak = awal - b - 1
        elif a > ujung:
            jarak = a - ujung - 1 + 0.5
        else:
            continue
        if jarak <= JARAK_KONTEKS and (terbaik is None or jarak < terbaik):
            terbaik = jarak
    if terbaik is None and token_lalu is not None and awal < LINTAS_AWAL:
        n = len(token_lalu)
        for a, b in _posisi_konteks(token_lalu, jenis):
            if b >= n - LINTAS_EKOR:
                jarak = (n - 1 - b) + awal + JARAK_KONTEKS + 1
                if terbaik is None or jarak < terbaik:
                    terbaik = jarak
    return terbaik


def _lolos_tambahan(jenis: str, teks: str, mulai: int, akhir: int, nilai: str) -> bool:
    if jenis == "email":
        if re.match(r":[^\s]", teks[akhir:akhir + 2]):
            return False
        if nilai.rsplit(".", 1)[-1].lower() in EKSTENSI_BERKAS:
            return False
    if jenis in {"bank_account", "credit_card", "nik", "kk", "bpjs", "npwp"}:
        if re.search(r"rp\.?\s*$", teks[max(0, mulai - 4):mulai], re.IGNORECASE):
            return False
    if jenis == "npwp" and not re.fullmatch(r"\d{2}\.\d{3}\.\d{3}\.\d-\d{3}\.\d{3}", nilai):
        return True
    return True


def deteksi_pesan(teks: str, teks_lalu: str | None = None) -> list[Temuan]:
    token = _token(teks)
    token_lalu = _token(teks_lalu) if teks_lalu is not None else None
    kandidat: dict[tuple[int, int], list[tuple[str, int | None]]] = {}
    for jenis, pola in POLA:
        for m in pola.finditer(teks):
            nilai, mulai, akhir = m.group(), m.start(), m.end()
            if VALIDATOR[jenis](nilai) is not None or not _lolos_tambahan(jenis, teks, mulai, akhir, nilai):
                continue
            awal, ujung = _indeks_token(token, mulai, akhir)
            jarak = _jarak_konteks(jenis, token, awal, ujung, token_lalu)
            npwp_polos = jenis == "npwp" and "." not in nilai
            if (jenis in KONTEKS_WAJIB or npwp_polos) and jarak is None:
                continue
            kandidat.setdefault((mulai, akhir), []).append((jenis, jarak))

    pilihan = []
    for (mulai, akhir), daftar in kandidat.items():
        berkonteks = [(j, d) for j, d in daftar if d is not None]
        if berkonteks:
            jenis = min(berkonteks, key=lambda x: (x[1], _urutan(x[0])))[0]
        else:
            jenis = min((j for j, _ in daftar), key=_urutan)
        pilihan.append(Temuan(jenis, teks[mulai:akhir], mulai, akhir))

    pilihan.sort(key=lambda t: (-(t.akhir - t.mulai), t.mulai))
    hasil: list[Temuan] = []
    for t in pilihan:
        if all(t.akhir <= h.mulai or t.mulai >= h.akhir for h in hasil):
            hasil.append(t)
    return sorted(hasil, key=lambda t: t.mulai)


def _urutan(jenis: str) -> int:
    return PRIORITAS.index(jenis) if jenis in PRIORITAS else len(PRIORITAS)


def deteksi(pesan: list[tuple[str, str]]) -> list[list[Temuan]]:
    hasil = []
    for i, (_, teks) in enumerate(pesan):
        lalu = pesan[i - 1][1] if i > 0 else None
        hasil.append(deteksi_pesan(teks, lalu))
    return hasil


if __name__ == "__main__":
    for t in deteksi_pesan(" ".join(sys.argv[1:])):
        print(f"{t.jenis}\t{t.nilai}\t[{t.mulai}:{t.akhir}]")
