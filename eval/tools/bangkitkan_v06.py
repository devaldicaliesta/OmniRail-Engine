#!/usr/bin/env python3
"""Pembangkit baris dataset v0.6: konteks lintas pesan (PRD PII-10) dan angka terucap (PII-11).

Baris v0.1 s.d. v0.5 belum punya pembangkit di repo (T-008). Skrip ini hanya
mencakup baris yang ditambahkan di v0.6 (D2362-D2506, H1010-H1072).

    python3 eval/tools/bangkitkan_v06.py          # cek: baris di repo identik dengan hasil pembangkit
    python3 eval/tools/bangkitkan_v06.py --tulis  # tambahkan baris bila belum ada
"""
import csv
import random
import sys
from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]
rng = random.Random(20261111)

PROV = [11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 31, 32, 33, 34, 35, 36, 51, 52, 53,
        61, 62, 63, 64, 65, 71, 72, 73, 74, 75, 76, 81, 82, 91, 92]
KATA = ["nol", "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan", "sembilan"]
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus",
         "September", "Oktober", "November", "Desember"]
dipakai = set()


def unik(f):
    while True:
        v = f()
        if v not in dipakai:
            dipakai.add(v)
            return v


def wilayah():
    return f"{rng.choice(PROV):02d}{rng.randint(1, 79):02d}{rng.randint(1, 40):02d}"


def nik():
    hr = rng.randint(1, 28) + (40 if rng.random() < 0.5 else 0)
    return unik(lambda: f"{wilayah()}{hr:02d}{rng.randint(1, 12):02d}{rng.randint(60, 99):02d}{rng.randint(1, 120):04d}")


def kk():
    return unik(lambda: f"{wilayah()}{rng.randint(1, 28):02d}{rng.randint(1, 12):02d}{rng.randint(5, 24):02d}{rng.randint(1, 3000):04d}")


def angka(n):
    # Digit pertama 1, 7, atau 9: tidak diawali 0/62 (nomor HP) dan bukan prefix kartu.
    return rng.choice("179") + "".join(str(rng.randint(0, 9)) for _ in range(n - 1))


def rekening():
    return unik(lambda: angka(rng.choice([10, 10, 12, 13, 15])))


def paspor():
    huruf = "ABCEX"
    return unik(lambda: rng.choice(["", rng.choice(huruf)]) + rng.choice(huruf) + str(rng.randint(10**6, 10**7 - 1)))


def bpjs():
    n = rng.choice([13, 13, 11, 16])
    return unik(lambda: "000" + angka(10) if n == 13 and rng.random() < 0.5 else angka(n))


def tgl_lahir(gaya=None):
    th, bl, hr = rng.randint(1950, 2005), rng.randint(1, 12), rng.randint(1, 28)
    gaya = gaya or rng.choice(["dmy/", "dmy-", "nama"])
    if gaya == "dmy/":
        return f"{hr:02d}/{bl:02d}/{th}"
    if gaya == "dmy-":
        return f"{hr:02d}-{bl:02d}-{th}"
    return f"{hr} {BULAN[bl - 1]} {th}"


def hp():
    return unik(lambda: "08" + rng.choice(["12", "13", "21", "52", "57", "77", "78", "95", "96", "81", "38"]) + "".join(str(rng.randint(0, 9)) for _ in range(rng.choice([7, 8]))))


def eja(digits, campur=False, kosong=False):
    kata = []
    for i, d in enumerate(digits):
        w = KATA[int(d)]
        if d == "0" and kosong and rng.random() < 0.6:
            w = "kosong"
        kata.append(w)
    if campur:
        return digits[:4] + " " + " ".join(kata[4:])
    return " ".join(kata)


# ---------------------------------------------------------------- lintas pesan
DEV_LP = [
    # (entitas, pertanyaan asisten, pembangkit, bentuk jawaban)
    ("bank_account", "Baik Kak, untuk proses refund boleh dibantu nomor rekeningnya?", rekening),
    ("bank_account", "Silakan kirim no rek tujuan transfer ya.", rekening),
    ("bank_account", "Pengembalian dana dikirim ke rekening. Nomornya berapa Kak?", rekening),
    ("passport_id", "Untuk tiket internasional, mohon cantumkan nomor paspor penumpang.", paspor),
    ("passport_id", "Boleh dibantu nomor passport sesuai halaman identitas?", paspor),
    ("bpjs", "Boleh disebutkan nomor kartu BPJS Kesehatan Bapak?", bpjs),
    ("bpjs", "Nomor KPJ peserta berapa Bu?", bpjs),
    ("birth_date", "Untuk verifikasi data, tanggal lahir Kakak kapan?", tgl_lahir),
    ("birth_date", "Mohon konfirmasi tgl lahir pemegang polis.", tgl_lahir),
    ("kk", "Untuk pendaftaran anggota keluarga, mohon kirim nomor Kartu Keluarga.", kk),
    ("kk", "No. KK-nya boleh diketik di sini?", kk),
]
DEV_JAWAB = ["{v}", "{v} kak", "ini {v}", "{v}, makasih", "oke {v}", "{v} ya mbak"]

HOLD_LP = [
    ("bank_account", "Could you share the account number for the refund?", rekening),
    ("bank_account", "Data yang kami perlukan: nama bank dan norek penerima.", rekening),
    ("passport_id", "Sesuai syarat visa, isi nomor paspor yang masih berlaku.", paspor),
    ("bpjs", "Untuk klaim, kami butuh nomor JKN atau KIS peserta.", bpjs),
    ("birth_date", "Please confirm your date of birth for verification.", tgl_lahir),
    ("birth_date", "Data diri belum lengkap. TTL sesuai KTP?", tgl_lahir),
    ("kk", "Lampirkan juga nomor kartu keluarga calon peserta.", kk),
]
HOLD_JAWAB = ["{v}", "sudah saya cek, {v}", "{v} (sesuai dokumen)", "nomornya {v}"]

DEV_LP_NEG = [
    ("bank_account", "Boleh minta nomor pesanannya Kak?", rekening, "pesan sebelumnya meminta nomor pesanan, bukan rekening"),
    ("bank_account", "Nomor rekening tidak perlu dikirim lewat chat ya Kak, cukup nomor resi saja. Terima kasih sudah menghubungi kami dan semoga harinya menyenangkan selalu bersama keluarga.", rekening, "kata rekening jauh dari akhir pesan sebelumnya (> 15 kata)"),
    ("birth_date", "Tanggal pengiriman yang Kakak inginkan kapan?", lambda: f"{rng.randint(1, 28):02d}/{rng.randint(1, 12):02d}/2026", "pesan sebelumnya menanyakan tanggal pengiriman"),
    ("passport_id", "Kode voucher yang tertera di email berapa?", paspor, "pesan sebelumnya meminta kode voucher; bentuk mirip paspor"),
    ("bpjs", "Nomor tiket keluhan Bapak berapa?", lambda: angka(13), "pesan sebelumnya meminta nomor tiket"),
]
HOLD_LP_NEG = [
    ("bank_account", "Please send the order ID so we can track it.", rekening, "pesan sebelumnya meminta order ID"),
    ("birth_date", "Kapan jadwal servis yang diinginkan?", lambda: f"{rng.randint(1, 28):02d}-{rng.randint(1, 12):02d}-2026", "pesan sebelumnya menanyakan jadwal servis"),
    ("passport_id", "Nomor kursi pesawatnya mau di mana?", lambda: rng.choice("ABCDEF") + str(rng.randint(100000, 999999)), "pesan sebelumnya soal nomor kursi"),
]


def baris_lp(templat, jawab, n_pos, n_neg, neg_templat):
    out = []
    for i in range(n_pos):
        ent, tanya, gen = templat[i % len(templat)]
        v = gen()
        balas = jawab[(i // len(templat)) % len(jawab)].format(v=v)
        teks = f"<<assistant>> {tanya}\n<<user>> {balas}"
        out.append(("positif", teks, f"{ent}:{v}", "ya", "lintas pesan: kata konteks hanya ada di pesan asisten sebelumnya (PII-10)"))
    for i in range(n_neg):
        ent, tanya, gen, alasan = neg_templat[i % len(neg_templat)]
        v = gen()
        balas = jawab[i % len(jawab)].format(v=v)
        teks = f"<<assistant>> {tanya}\n<<user>> {balas}"
        out.append(("negatif", teks, "-", "ya", f"[{ent}] lintas pesan: {alasan}"))
    return out


# ---------------------------------------------------------------- angka terucap
DEV_UCAP = [
    ("phone_id", "[transkrip panggilan] pelanggan: iya mbak nomor hp saya {v} bisa dihubungi kapan saja", lambda: hp(), "eja"),
    ("phone_id", "agen: baik nomornya pelanggan: {v} itu wa juga", lambda: hp(), "kosong"),
    ("phone_id", "Tolong ringkas transkrip berikut: pelanggan menyebut nomor {v} untuk konfirmasi pengiriman.", lambda: hp(), "campur"),
    ("nik", "pelanggan: nik saya {v} sesuai ktp", nik, "eja"),
    ("bank_account", "pelanggan: transfer ke rekening saya {v} atas nama sendiri", rekening, "eja"),
    ("kk", "pelanggan: nomor kartu keluarga {v}", kk, "kosong"),
]
HOLD_UCAP = [
    ("phone_id", "[rekaman CS 14.05] customer bilang nomornya {v} tolong dicatat", lambda: hp(), "kosong"),
    ("phone_id", "Ringkas: penelepon minta dihubungi balik di {v}.", lambda: hp(), "campur"),
    ("nik", "penelepon menyebut nomor induk kependudukan {v} untuk verifikasi", nik, "eja"),
    ("bank_account", "dana mohon dikembalikan ke no rek {v} ya pak", rekening, "kosong"),
]
DEV_UCAP_NEG = [
    ("phone_id", "pelanggan: saya pesan dua tiga kardus kirim ke lantai delapan ya", "bilangan terucap bukan nomor"),
    ("phone_id", "agen: harganya tiga ratus lima puluh ribu termasuk ongkir", "nominal harga terucap"),
    ("nik", "pelanggan: tadi saya hitung satu dua tiga empat lima enam tujuh delapan sembilan sepuluh barangnya pas", "menghitung barang, bukan NIK"),
    ("bank_account", "pelanggan: saya transfer jam sembilan lewat lima belas menit ke rekening toko", "waktu terucap dekat kata rekening"),
    ("phone_id", "Ringkas transkrip: pelanggan menunggu di gate dua kursi nomor empat belas", "nomor gate dan kursi terucap"),
    ("phone_id", "agen: mohon ditunggu satu dua menit ya pak sistem sedang lambat", "satu dua menit"),
    ("phone_id", "pelanggan: ukuran sepatu saya empat dua kalau tidak ada empat tiga juga boleh", "ukuran sepatu terucap"),
    ("bank_account", "pelanggan: cicilan rekening koran saya tinggal enam bulan lagi dari dua belas", "jumlah bulan terucap dekat kata rekening"),
    ("nik", "agen: alamat pengiriman RT nol tiga RW nol lima sudah benar ya bu", "RT/RW terucap"),
    ("kk", "pelanggan: anggota kartu keluarga saya ada lima orang dua anak", "jumlah anggota keluarga terucap"),
    ("phone_id", "Ringkas: pelanggan pesan nasi goreng dua es teh tiga untuk meja tujuh", "jumlah pesanan dan nomor meja terucap"),
    ("bank_account", "pelanggan: no rek nya nanti saya kirim lewat email saja ya jangan di telepon", "kata no rek tanpa nilai"),
]
HOLD_UCAP_NEG = [
    ("phone_id", "[rekaman CS] customer minta paket nomor tiga dan lima dikirim besok jam delapan", "nomor paket dan jam terucap"),
    ("bank_account", "penelepon bilang saldo rekening tinggal dua juta tujuh ratus ribu", "nominal saldo terucap dekat kata rekening"),
    ("nik", "penelepon membaca kode kupon satu satu dua dua tiga tiga", "kode kupon terucap"),
    ("phone_id", "Ringkas: customer komplain lampu kamar nomor dua satu nol mati sejak jam tujuh", "nomor kamar dan jam terucap"),
    ("bank_account", "penelepon tanya bunga deposito tiga persen untuk tenor enam bulan", "persentase dan tenor terucap"),
    ("kk", "customer bilang di kartu keluarganya baru ada tiga nama", "jumlah nama terucap"),
]


def baris_ucap(templat, n_pos, n_neg, neg_templat):
    out = []
    for i in range(n_pos):
        ent, kalimat, gen, gaya = templat[i % len(templat)]
        d = gen()
        v = eja(d, campur=(gaya == "campur"), kosong=(gaya == "kosong"))
        out.append(("positif", kalimat.format(v=v), f"{ent}:{v}", "tidak",
                    f"angka terucap ({d}); PII-11 P1, ditunda dari MVP"))
    for i in range(n_neg):
        ent, kalimat, alasan = neg_templat[i % len(neg_templat)]
        out.append(("negatif", kalimat, "-", "ya", f"[{ent}] angka terucap: {alasan}"))
    return out


dev = baris_lp(DEV_LP, DEV_JAWAB, 66, 25, DEV_LP_NEG) + baris_ucap(DEV_UCAP, 42, len(DEV_UCAP_NEG), DEV_UCAP_NEG)
hold = baris_lp(HOLD_LP, HOLD_JAWAB, 28, 9, HOLD_LP_NEG) + baris_ucap(HOLD_UCAP, 20, len(HOLD_UCAP_NEG), HOLD_UCAP_NEG)


AWAL = {"D": 2362, "H": 1010}


def jadi_baris(prefix, baris):
    return [[f"{prefix}{i:03d}", kat, teks, harap, cak, cat]
            for i, (kat, teks, harap, cak, cat) in enumerate(baris, start=AWAL[prefix])]


def main(argv):
    hasil = {
        AKAR / "eval" / "dev" / "uji_pii_id.csv": jadi_baris("D", dev),
        AKAR / "eval" / "holdout" / "uji_pii_id.csv": jadi_baris("H", hold),
    }
    beda = 0
    for path, baru in hasil.items():
        with path.open(newline="", encoding="utf-8") as f:
            ada = {r[0]: r for r in csv.reader(f)}
        if "--tulis" in argv:
            sisa = [r for r in baru if r[0] not in ada]
            with path.open("a", newline="", encoding="utf-8") as f:
                csv.writer(f, lineterminator="\n").writerows(sisa)
            print(f"{path.name} ({path.parent.name}): {len(sisa)} baris ditambahkan")
            continue
        for r in baru:
            if ada.get(r[0]) != r:
                beda += 1
                print(f"BEDA {r[0]}")
    if "--tulis" not in argv:
        print("identik" if not beda else f"{beda} baris berbeda")
    return 1 if beda else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
