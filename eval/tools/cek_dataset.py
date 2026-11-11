#!/usr/bin/env python3
"""Pemeriksa konsistensi dataset uji.

    python3 eval/tools/cek_dataset.py [--ringkasan] [--ketat]
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import ipaddress
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]
BERKAS = {
    "dev": AKAR / "eval" / "dev" / "uji_pii_id.csv",
    "holdout": AKAR / "eval" / "holdout" / "uji_pii_id.csv",
}
README_EVAL = AKAR / "eval" / "README.md"

KOLOM = ["id", "kategori", "teks", "diharapkan", "cakupan_mvp", "catatan"]
PREFIX_ID = {"dev": "D", "holdout": "H"}
KATEGORI = {"positif", "negatif", "kredensial", "injeksi"}
CAKUPAN = {"ya", "tidak"}

ENTITAS_P0 = [
    "email", "phone_id", "credit_card", "nik", "npwp", "bank_account",
    "nip", "kk", "passport_id", "bpjs", "birth_date",
]
ENTITAS_P1 = ["vehicle_plate", "ip_address"]
ENTITAS_NER = ["nama", "alamat"]
ENTITAS = ENTITAS_P0 + ENTITAS_P1 + ENTITAS_NER

JENIS_KREDENSIAL = {"api_key", "jwt", "private_key", "connection_string", "password_assignment", "-"}
JENIS_INJEKSI = {"deny", "-"}

TARGET_MIN_PER_ENTITAS = 50
TARGET_RASIO_HOLDOUT = 0.30

KODE_PROVINSI = {
    11, 12, 13, 14, 15, 16, 17, 18, 19, 21,
    31, 32, 33, 34, 35, 36,
    51, 52, 53,
    61, 62, 63, 64, 65,
    71, 72, 73, 74, 75, 76,
    81, 82,
    91, 92, 93, 94, 95, 96,
}

BULAN_ID = {
    "januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "agustus": 8, "september": 9, "oktober": 10, "november": 11, "desember": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7,
    "agu": 8, "agt": 8, "ags": 8, "sep": 9, "okt": 10, "nov": 11, "des": 12,
}


KATA_DIGIT = {
    "nol": "0", "kosong": "0", "satu": "1", "dua": "2", "tiga": "3", "empat": "4",
    "lima": "5", "enam": "6", "tujuh": "7", "delapan": "8", "sembilan": "9",
}

PENANDA_PERAN = re.compile(r"^<<(\w+)>> ", re.M)
PERAN = {"system", "user", "assistant"}


def kata_ke_digit(nilai: str) -> str | None:
    token = re.findall(r"[A-Za-z]+|\d+|\+", nilai)
    if not any(t.lower() in KATA_DIGIT for t in token):
        return None
    hasil = []
    for t in token:
        if t.lower() in KATA_DIGIT:
            hasil.append(KATA_DIGIT[t.lower()])
        elif t.isdigit() or t == "+":
            hasil.append(t)
        elif t.lower() == "plus":
            hasil.append("+")
        else:
            return ""
    return "".join(hasil)


def digit(nilai: str) -> str:
    return re.sub(r"[\s.\-]", "", nilai)


def tanggal_valid(tahun: int, bulan: int, hari: int) -> bool:
    try:
        dt.date(tahun, bulan, hari)
    except ValueError:
        return False
    return True


def luhn(angka: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(angka)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def prefix_kartu(angka: str) -> str | None:
    n = len(angka)
    if angka.startswith("4") and n in (13, 16, 19):
        return "visa"
    if n == 16 and (51 <= int(angka[:2]) <= 55 or 2221 <= int(angka[:4]) <= 2720):
        return "mastercard"
    if n == 15 and angka[:2] in ("34", "37"):
        return "amex"
    if 16 <= n <= 19 and 3528 <= int(angka[:4]) <= 3589:
        return "jcb"
    return None


def cek_email(v: str) -> str | None:
    if len(v) > 254:
        return "panjang > 254"
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[A-Za-z]{2,}", v):
        return "bukan bentuk email dengan TLD >= 2 huruf"
    return None


def cek_phone_id(v: str) -> str | None:
    if not re.fullmatch(r"\+?[0-9][0-9 .\-]*", v):
        return "memuat karakter selain digit, spasi, titik, tanda hubung"
    d = digit(v).lstrip("+")
    if d.startswith("62"):
        d = "0" + d[2:]
    if not d.startswith("08"):
        return "bukan nomor seluler (harus diawali 08/+628/628)"
    if not 10 <= len(d) <= 13:
        return f"panjang setelah normalisasi {len(d)}, harus 10 s.d. 13"
    return None


def cek_credit_card(v: str) -> str | None:
    if not re.fullmatch(r"[0-9][0-9 \-]*", v):
        return "memuat karakter selain digit, spasi, tanda hubung"
    d = digit(v)
    if not 13 <= len(d) <= 19:
        return f"{len(d)} digit, harus 13 s.d. 19"
    if not luhn(d):
        return "gagal Luhn"
    if prefix_kartu(d) is None:
        return "prefix/panjang jaringan tidak dikenal (Visa, Mastercard, Amex, JCB)"
    return None


def _cek_wilayah_tanggal(d: str, boleh_perempuan: bool) -> str | None:
    if len(d) != 16 or not d.isdigit():
        return f"harus 16 digit, didapat {len(d)}"
    if int(d[:2]) not in KODE_PROVINSI:
        return f"kode provinsi {d[:2]} tidak dikenal"
    hari, bulan = int(d[6:8]), int(d[8:10])
    if boleh_perempuan and 41 <= hari <= 71:
        hari -= 40
    if not (1 <= hari <= 31 and 1 <= bulan <= 12):
        return f"tanggal {d[6:12]} tidak valid"
    if d[12:] == "0000":
        return "nomor urut 0000"
    return None


def cek_nik(v: str) -> str | None:
    return _cek_wilayah_tanggal(digit(v), boleh_perempuan=True)


def cek_kk(v: str) -> str | None:
    return _cek_wilayah_tanggal(digit(v), boleh_perempuan=False)


def cek_npwp(v: str) -> str | None:
    if re.fullmatch(r"\d{2}\.\d{3}\.\d{3}\.\d-\d{3}\.\d{3}", v):
        return None
    d = digit(v)
    if not d.isdigit() or len(d) not in (15, 16):
        return "harus 15 digit berformat, atau 15/16 digit"
    return None


def cek_bank_account(v: str) -> str | None:
    d = digit(v)
    if not d.isdigit() or not 8 <= len(d) <= 16:
        return "harus 8 s.d. 16 digit"
    return None


def cek_nip(v: str) -> str | None:
    if not re.fullmatch(r"[0-9 ]+", v):
        return "memuat karakter selain digit dan spasi"
    d = v.replace(" ", "")
    if len(d) != 18:
        return f"harus 18 digit, didapat {len(d)}"
    th, bl, hr = int(d[0:4]), int(d[4:6]), int(d[6:8])
    if not (1940 <= th <= 2008 and tanggal_valid(th, bl, hr)):
        return f"tanggal lahir {d[:8]} tidak valid (1940 s.d. 2008)"
    th_angkat, kode = int(d[8:12]), int(d[12:14])
    if th_angkat < th + 18:
        return "tahun pengangkatan < tahun lahir + 18"
    if not (1 <= kode <= 12 or 21 <= kode <= 29):
        return f"digit 13-14 = {d[12:14]}, harus bulan 01-12 (PNS) atau 21-29 (PPPK)"
    if d[14] not in "12":
        return "digit ke-15 (jenis kelamin) harus 1 atau 2"
    if d[15:] == "000":
        return "nomor urut 000"
    return None


def cek_passport_id(v: str) -> str | None:
    if not re.fullmatch(r"[A-Z]{1,2} ?\d{6,7}", v):
        return "harus 1-2 huruf kapital + 6-7 digit"
    return None


def cek_bpjs(v: str) -> str | None:
    d = digit(v)
    if not d.isdigit() or len(d) not in (11, 13, 16):
        return "harus 11, 13, atau 16 digit"
    return None


def cek_birth_date(v: str) -> str | None:
    tahun_ini = dt.date.today().year
    m = re.fullmatch(r"(\d{2})[-/.](\d{2})[-/.](\d{4})", v)
    if m:
        hr, bl, th = map(int, m.groups())
    elif m := re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", v):
        th, bl, hr = map(int, m.groups())
    elif m := re.fullmatch(r"(\d{1,2}) ([A-Za-z]+) (\d{4})", v):
        hr, nama_bulan, th = int(m[1]), m[2].lower(), int(m[3])
        if nama_bulan not in BULAN_ID:
            return f"nama bulan '{m[2]}' tidak dikenal"
        bl = BULAN_ID[nama_bulan]
    else:
        return "format tanggal tidak dikenal"
    if not (1900 <= th <= tahun_ini and tanggal_valid(th, bl, hr)):
        return "tanggal tidak valid atau di luar 1900 s.d. tahun berjalan"
    return None


def cek_vehicle_plate(v: str) -> str | None:
    if not re.fullmatch(r"[A-Z]{1,2} ?\d{1,4} ?[A-Z]{1,3}", v):
        return "harus kode wilayah + 1-4 digit + 1-3 huruf kapital"
    return None


IPV4_DIKECUALIKAN = [
    ipaddress.ip_network(n)
    for n in ("0.0.0.0/8", "10.0.0.0/8", "127.0.0.0/8", "169.254.0.0/16",
              "172.16.0.0/12", "192.168.0.0/16", "224.0.0.0/3")
]
IPV6_DIKECUALIKAN = [ipaddress.ip_network(n) for n in ("::1/128", "fe80::/10", "fc00::/7", "ff00::/8")]


def cek_ip_address(v: str) -> str | None:
    try:
        ip = ipaddress.ip_address(v)
    except ValueError:
        return "bukan alamat IP yang valid (atau oktet bernol di depan)"
    daftar = IPV4_DIKECUALIKAN if ip.version == 4 else IPV6_DIKECUALIKAN
    if any(ip in n for n in daftar):
        return "IP privat, loopback, link-local, atau >= 224 (dikecualikan PRD 7.10)"
    return None


VALIDATOR = {
    "email": cek_email,
    "phone_id": cek_phone_id,
    "credit_card": cek_credit_card,
    "nik": cek_nik,
    "kk": cek_kk,
    "npwp": cek_npwp,
    "bank_account": cek_bank_account,
    "nip": cek_nip,
    "passport_id": cek_passport_id,
    "bpjs": cek_bpjs,
    "birth_date": cek_birth_date,
    "vehicle_plate": cek_vehicle_plate,
    "ip_address": cek_ip_address,
}


@dataclass
class Laporan:
    error: list[str] = field(default_factory=list)
    peringatan: list[str] = field(default_factory=list)

    def err(self, lokasi: str, pesan: str) -> None:
        self.error.append(f"{lokasi}: {pesan}")

    def warn(self, lokasi: str, pesan: str) -> None:
        self.peringatan.append(f"{lokasi}: {pesan}")


@dataclass
class Hitungan:
    baris: Counter = field(default_factory=Counter)
    positif: Counter = field(default_factory=Counter)
    positif_luar: Counter = field(default_factory=Counter)
    negatif: Counter = field(default_factory=Counter)
    kredensial: int = 0
    injeksi: int = 0
    ner: int = 0


def urai_diharapkan(nilai: str) -> list[tuple[str, str]] | None:
    if nilai == "-":
        return []
    hasil = []
    for bagian in nilai.split(" | "):
        if ":" not in bagian:
            return None
        jenis, isi = bagian.split(":", 1)
        hasil.append((jenis, isi))
    return hasil


def periksa_baris(split: str, nomor: int, r: dict, lap: Laporan, hit: Hitungan) -> None:
    lok = f"{split}:{r['id'] or f'baris {nomor}'}"
    kat, cak = r["kategori"], r["cakupan_mvp"]

    if kat not in KATEGORI:
        lap.err(lok, f"kategori '{kat}' tidak dikenal")
        return
    if cak not in CAKUPAN:
        lap.err(lok, f"cakupan_mvp '{cak}' harus 'ya' atau 'tidak'")
    if not r["teks"].strip():
        lap.err(lok, "teks kosong")
    peran = PENANDA_PERAN.findall(r["teks"])
    if peran or "<<" in r["teks"]:
        if not r["teks"].startswith("<<"):
            lap.err(lok, "teks multi-pesan harus diawali penanda peran, misalnya <<user>>")
        salah = [p for p in peran if p not in PERAN]
        if salah:
            lap.err(lok, f"penanda peran tidak dikenal: {', '.join(salah)}")
        if len(peran) < 2:
            lap.err(lok, "teks multi-pesan harus memuat minimal dua pesan")

    if kat == "kredensial":
        hit.kredensial += 1
        if r["diharapkan"] not in JENIS_KREDENSIAL:
            lap.err(lok, f"diharapkan '{r['diharapkan']}' bukan jenis kredensial yang dikenal")
        return
    if kat == "injeksi":
        hit.injeksi += 1
        if r["diharapkan"] not in JENIS_INJEKSI:
            lap.err(lok, f"diharapkan '{r['diharapkan']}' harus 'deny' atau '-'")
        return

    pasangan = urai_diharapkan(r["diharapkan"])
    if pasangan is None:
        lap.err(lok, "diharapkan harus '-' atau daftar 'jenis:nilai' dipisah ' | '")
        return

    if kat == "positif" and not pasangan:
        lap.err(lok, "baris positif tanpa entitas")
    if kat == "negatif":
        if pasangan:
            lap.err(lok, "baris negatif tidak boleh memuat entitas di diharapkan")
        m = re.match(r"\[([a-z_]+)\]", r["catatan"])
        if not m:
            lap.err(lok, "catatan baris negatif harus diawali entitas yang dijebak, misalnya [nik]")
        elif m[1] not in ENTITAS:
            lap.err(lok, f"entitas [{m[1]}] di catatan tidak dikenal")
        else:
            hit.negatif[m[1]] += 1

    jumlah = Counter(pasangan)
    for (jenis, isi), kali in jumlah.items():
        if jenis not in ENTITAS:
            lap.err(lok, f"jenis entitas '{jenis}' tidak dikenal")
            continue
        if not isi:
            lap.err(lok, f"nilai {jenis} kosong")
            continue
        muncul = r["teks"].count(isi)
        if muncul < kali:
            lap.err(lok, f"{jenis}:{isi!r} ditulis {kali}x tetapi muncul {muncul}x di teks")
        if jenis in ENTITAS_NER and cak == "ya":
            lap.err(lok, f"entitas {jenis} butuh NER, harus cakupan_mvp = tidak")
        if jenis in ENTITAS_P1 and cak == "ya":
            lap.err(lok, f"entitas P1 {jenis} harus cakupan_mvp = tidak di baris positif")
        validator = VALIDATOR.get(jenis)
        terucap = kata_ke_digit(isi) if validator else None
        if terucap == "":
            alasan = "angka terucap memuat kata selain kata bilangan satu digit"
        else:
            alasan = validator(terucap or isi) if validator else None
            if alasan and terucap:
                alasan = f"{alasan} (angka terucap dibaca sebagai {terucap})"
        if alasan:
            pesan = f"{jenis}:{isi!r} gagal validator: {alasan}"
            (lap.err if cak == "ya" else lap.warn)(lok, pesan)

        if jenis in ENTITAS_NER:
            hit.ner += kali
        elif cak == "ya" or jenis in ENTITAS_P1:
            hit.positif[jenis] += kali
        else:
            hit.positif_luar[jenis] += kali


def baca(split: str, path: Path, lap: Laporan, hit: Hitungan) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        data = f.read()
    if "\r" in data:
        lap.err(split, "berkas memuat CR (\\r); gunakan akhir baris LF")
    pembaca = csv.DictReader(data.splitlines(keepends=True))
    if pembaca.fieldnames != KOLOM:
        lap.err(split, f"header harus {','.join(KOLOM)}, didapat {pembaca.fieldnames}")
        return []
    baris = []
    id_terlihat: dict[str, int] = {}
    pola_id = re.compile(rf"{PREFIX_ID[split]}\d{{3,}}")
    for nomor, r in enumerate(pembaca, start=2):
        if None in r or any(v is None for v in r.values()):
            lap.err(f"{split}:baris {nomor}", "jumlah kolom tidak sesuai header")
            continue
        if not pola_id.fullmatch(r["id"]):
            lap.err(f"{split}:baris {nomor}", f"id '{r['id']}' harus berbentuk {PREFIX_ID[split]}001")
        elif r["id"] in id_terlihat:
            lap.err(f"{split}:{r['id']}", f"id ganda (juga di baris {id_terlihat[r['id']]})")
        else:
            id_terlihat[r["id"]] = nomor
        hit.baris[split] += 1
        periksa_baris(split, nomor, r, lap, hit)
        baris.append(r)
    return baris


def periksa_kebocoran(dev: list[dict], holdout: list[dict], lap: Laporan) -> None:
    teks_dev = defaultdict(list)
    for r in dev:
        teks_dev[r["teks"].strip()].append(r["id"])
    for r in holdout:
        if (sama := teks_dev.get(r["teks"].strip())):
            lap.err(f"holdout:{r['id']}", f"teks identik dengan dev {', '.join(sama)} (kebocoran holdout)")


def periksa_target(hit: Hitungan, lap: Laporan) -> None:
    total = sum(hit.baris.values())
    if total:
        rasio = hit.baris["holdout"] / total
        if rasio < TARGET_RASIO_HOLDOUT - 0.005:
            lap.err("target", f"holdout {rasio:.1%} dari total, target >= {TARGET_RASIO_HOLDOUT:.0%}")
    for e in ENTITAS_P0 + ENTITAS_P1:
        if hit.positif[e] < TARGET_MIN_PER_ENTITAS:
            lap.err("target", f"{e}: {hit.positif[e]} positif, target >= {TARGET_MIN_PER_ENTITAS}")
        if hit.negatif[e] < TARGET_MIN_PER_ENTITAS:
            lap.err("target", f"{e}: {hit.negatif[e]} negatif, target >= {TARGET_MIN_PER_ENTITAS}")


def angka_id(teks: str) -> int:
    return int(teks.replace(".", ""))


def periksa_readme(hit: Hitungan, lap: Laporan) -> None:
    if not README_EVAL.exists():
        lap.warn("README", f"{README_EVAL} tidak ditemukan")
        return
    isi = README_EVAL.read_text(encoding="utf-8")
    for split in ("dev", "holdout"):
        m = re.search(rf"\| `{split}/uji_pii_id\.csv` \| ([\d.]+) \|", isi)
        if not m:
            lap.warn("README", f"baris jumlah untuk {split} tidak ditemukan")
        elif angka_id(m[1]) != hit.baris[split]:
            lap.err("README", f"{split}: README menulis {m[1]} baris, sebenarnya {hit.baris[split]}")
    for e in ENTITAS_P0 + ENTITAS_P1:
        m = re.search(rf"^\| `{e}` \| P\d \| ([\d.]+) \| ([\d.]+) \|", isi, re.M)
        if not m:
            lap.warn("README", f"baris tabel untuk {e} tidak ditemukan")
            continue
        pos, neg = angka_id(m[1]), angka_id(m[2])
        if (pos, neg) != (hit.positif[e], hit.negatif[e]):
            lap.err(
                "README",
                f"{e}: README menulis {pos} positif/{neg} negatif, "
                f"sebenarnya {hit.positif[e]}/{hit.negatif[e]}",
            )


def cetak_ringkasan(hit: Hitungan) -> None:
    total = sum(hit.baris.values())
    print("\n## Ringkasan dataset\n")
    print("| Berkas | Baris |\n| --- | --- |")
    for split in ("dev", "holdout"):
        print(f"| `{split}/uji_pii_id.csv` | {hit.baris[split]} |")
    if total:
        print(f"\nHoldout: {hit.baris['holdout'] / total:.1%} dari {total} baris.\n")
    print("| Entitas | Prioritas | Positif | Negatif | Positif di luar cakupan |")
    print("| --- | --- | --- | --- | --- |")
    for e in ENTITAS_P0 + ENTITAS_P1:
        prio = "P0" if e in ENTITAS_P0 else "P1"
        luar = hit.positif_luar[e] or "—"
        print(f"| `{e}` | {prio} | {hit.positif[e]} | {hit.negatif[e]} | {luar} |")
    print(f"\nKredensial: {hit.kredensial} baris. Injeksi: {hit.injeksi} baris. "
          f"Nama dan alamat (NER): {hit.ner} kemunculan.")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ringkasan", action="store_true", help="cetak tabel jumlah per entitas")
    ap.add_argument("--ketat", action="store_true", help="peringatan juga dianggap error")
    args = ap.parse_args(argv)

    lap, hit = Laporan(), Hitungan()
    data = {split: baca(split, path, lap, hit) for split, path in BERKAS.items()}
    periksa_kebocoran(data["dev"], data["holdout"], lap)
    periksa_target(hit, lap)
    periksa_readme(hit, lap)

    for p in lap.peringatan:
        print(f"PERINGATAN {p}")
    for e in lap.error:
        print(f"ERROR {e}")
    if args.ringkasan:
        cetak_ringkasan(hit)

    gagal = bool(lap.error) or (args.ketat and bool(lap.peringatan))
    print(
        f"\n{sum(hit.baris.values())} baris diperiksa: "
        f"{len(lap.error)} error, {len(lap.peringatan)} peringatan."
    )
    return 1 if gagal else 0


if __name__ == "__main__":
    sys.exit(main())
