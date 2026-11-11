#!/usr/bin/env python3
"""Baseline Presidio untuk Tahap 0 (T-004). Bukan bagian dari CI.

Butuh `pip install presidio-analyzer` (diuji dengan presidio-analyzer 2.2.366
dan spaCy 3.8). Tidak butuh model spaCy terunduh: dipakai pipeline kosong
bahasa Indonesia dengan lemma = huruf kecil, agar peningkatan skor kata
konteks Presidio (LemmaContextAwareEnhancer) bisa bekerja.

Konfigurasi, sesuai definisi T-004 "recognizer Indonesia sederhana (regex
tanpa validator)":

- recognizer bawaan Presidio untuk email, kartu kredit (dengan Luhn bawaan
  Presidio), dan nomor telepon (pustaka phonenumbers, region ID);
- PatternRecognizer regex sederhana tanpa validator untuk NIK, KK, NPWP, NIP,
  rekening, paspor, BPJS, dan tanggal lahir, dengan kata konteks PRD 7.10;
- skor pola 0,5 untuk entitas yang di PRD tidak mewajibkan konteks, 0,3 untuk
  yang mewajibkan; ambang 0,4; konteks menambah skor 0,35 (default Presidio);
- setiap pesan dianalisis terpisah, seperti guardrail Presidio di LiteLLM;
- rentang yang tumpang tindih: skor tertinggi menang, lalu yang terpanjang,
  lalu urutan prioritas PII-07 (sama dengan prototipe, agar adil).
"""

from __future__ import annotations

import tempfile

KONFIGURASI = {
    "keterangan": (
        "Presidio Analyzer + recognizer bawaan (email, kartu dengan Luhn, telepon region ID) "
        "+ regex Indonesia sederhana tanpa validator dengan kata konteks; ambang 0,4"
    ),
    "ambang": 0.4,
}

PRIORITAS = ["credit_card", "nip", "nik", "npwp", "bpjs", "bank_account",
             "phone_id", "passport_id", "birth_date", "email", "kk"]

PETA = {
    "EMAIL_ADDRESS": "email", "CREDIT_CARD": "credit_card", "PHONE_NUMBER": "phone_id",
    "ID_NIK": "nik", "ID_KK": "kk", "ID_NPWP": "npwp", "ID_NIP": "nip",
    "ID_BANK_ACCOUNT": "bank_account", "ID_PASSPORT": "passport_id", "ID_BPJS": "bpjs",
    "ID_BIRTH_DATE": "birth_date",
}

BULAN = ("januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|"
         "desember|jan|feb|mar|apr|jun|jul|agu|agt|ags|sep|okt|nov|des")


def _mesin():
    import spacy
    import tldextract

    # EmailRecognizer memakai tldextract. Pakai daftar sufiks bawaan paket,
    # tanpa mengunduh dari internet, agar hasil bisa diulang tanpa jaringan.
    tldextract.extract = tldextract.TLDExtract(suffix_list_urls=())
    from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer, RecognizerRegistry
    from presidio_analyzer.nlp_engine import SpacyNlpEngine
    from presidio_analyzer.predefined_recognizers import (
        CreditCardRecognizer, EmailRecognizer, PhoneRecognizer)
    from spacy.language import Language

    if "lemma_huruf_kecil" not in Language.factories:
        @Language.component("lemma_huruf_kecil")
        def _lemma(doc):
            for t in doc:
                t.lemma_ = t.lower_
            return doc

    folder = tempfile.mkdtemp(prefix="spacy-id-")
    nlp = spacy.blank("id")
    nlp.add_pipe("lemma_huruf_kecil")
    nlp.to_disk(folder)
    mesin_nlp = SpacyNlpEngine(models=[{"lang_code": "id", "model_name": folder}])

    def pola(nama, daftar, konteks):
        return PatternRecognizer(
            supported_entity=nama, supported_language="id", context=konteks,
            patterns=[Pattern(f"{nama}_{i}", rx, skor) for i, (rx, skor) in enumerate(daftar)])

    registri = RecognizerRegistry(supported_languages=["id"])
    registri.add_recognizer(EmailRecognizer(supported_language="id"))
    registri.add_recognizer(CreditCardRecognizer(supported_language="id"))
    registri.add_recognizer(PhoneRecognizer(supported_language="id", supported_regions=("ID",),
                                            context=["hp", "telp", "telepon", "wa", "whatsapp"]))
    registri.add_recognizer(pola("ID_NIK", [(r"\b\d{16}\b", 0.5)], ["nik", "ktp", "induk"]))
    registri.add_recognizer(pola("ID_KK", [(r"\b\d{16}\b", 0.3)], ["kk", "keluarga"]))
    registri.add_recognizer(pola("ID_NPWP", [(r"\b\d{2}\.\d{3}\.\d{3}\.\d-\d{3}\.\d{3}\b", 0.5),
                                             (r"\b\d{15,16}\b", 0.3)], ["npwp", "pajak"]))
    registri.add_recognizer(pola("ID_NIP", [(r"\b\d{8} ?\d{6} ?\d ?\d{3}\b", 0.5)],
                                 ["nip", "pns", "asn", "pegawai"]))
    registri.add_recognizer(pola("ID_BANK_ACCOUNT", [(r"\b\d{8,16}\b", 0.3), (r"\b\d+(?:-\d+){1,4}\b", 0.3)],
                                 ["rekening", "rek", "norek", "account"]))
    registri.add_recognizer(pola("ID_PASSPORT", [(r"\b[A-Z]{1,2} ?\d{6,7}\b", 0.3)], ["paspor", "passport"]))
    registri.add_recognizer(pola("ID_BPJS", [(r"\b(?:\d{11}|\d{13}|\d{16})\b", 0.3)],
                                 ["bpjs", "kis", "jkn", "kpj"]))
    registri.add_recognizer(pola("ID_BIRTH_DATE", [
        (r"\b\d{2}[-/.]\d{2}[-/.]\d{4}\b", 0.3), (r"\b\d{4}-\d{2}-\d{2}\b", 0.3),
        (rf"(?i)\b\d{{1,2}} (?:{BULAN}) \d{{4}}\b", 0.3)],
        ["lahir", "ttl", "dob", "birth", "kelahiran"]))
    return AnalyzerEngine(registry=registri, nlp_engine=mesin_nlp, supported_languages=["id"])


def _pilih(teks, hasil):
    calon = []
    for h in hasil:
        jenis = PETA.get(h.entity_type)
        if jenis and h.score >= KONFIGURASI["ambang"]:
            urut = PRIORITAS.index(jenis) if jenis in PRIORITAS else len(PRIORITAS)
            calon.append((-h.score, -(h.end - h.start), urut, h.start, h.end, jenis))
    calon.sort()
    terpilih = []
    for *_, mulai, akhir, jenis in calon:
        if all(akhir <= a or mulai >= b for a, b, _ in terpilih):
            terpilih.append((mulai, akhir, jenis))
    return [(jenis, teks[a:b]) for a, b, jenis in sorted(terpilih)]


def detektor():
    mesin = _mesin()

    def jalankan(pesan):
        temuan = []
        for _, teks in pesan:
            temuan += _pilih(teks, mesin.analyze(text=teks, language="id"))
        return temuan

    return jalankan


if __name__ == "__main__":
    import sys

    print(detektor()([("user", " ".join(sys.argv[1:]))]))
