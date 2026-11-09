# OmniRail Engine — Rincian task MVP

Turunan dari [PRD MVP v1.0](PRD.md). Satu task berarti satu PR dengan kriteria selesai yang bisa diperiksa. Kode requirement (misalnya `PII-04`) merujuk ke PRD bagian 7.

**Cara memakai:** kerjakan berurutan per tahap, centang task yang selesai, dan tulis keputusan baru di bagian "Catatan keputusan" di bawah. Task di satu tahap boleh dikerjakan paralel bila kolom "Butuh" sudah terpenuhi.

---

## Tahap 0 — Validasi (maks. 2 minggu)

| | ID | Task | Requirement | Selesai bila | Butuh |
| --- | --- | --- | --- | --- | --- |
| [x] | T-001 | Draf dataset `eval/{dev,holdout}/uji_pii_id.csv` | EVAL-01 | 106 baris dev dan 47 holdout, format terdokumentasi di `eval/README.md` | — |
| [ ] | T-002 | Lengkapi dataset sampai ≥ 50 positif dan ≥ 50 negatif per entitas MVP | EVAL-01, Q1 | Hitungan per entitas memenuhi target, dan holdout ≥ 30% dari total | T-001 |
| [ ] | T-003 | Tetapkan kriteria angka keputusan "lanjut, pivot, berhenti" | Q2 | Kriteria tertulis di catatan keputusan **sebelum** T-004 dijalankan | — |
| [ ] | T-004 | Jalankan dataset (dev) terhadap Presidio dengan recognizer Indonesia sederhana (regex tanpa validator) | Tahap 0 | Recall, precision, dan false positive per entitas tercatat di `eval/results/` | T-002, T-003 |
| [ ] | T-005 | Uji LiteLLM + guardrail Presidio sebagai proxy: pemulihan token (`output_parse_pii`), blokir credentials, dan overhead latensi | Tahap 0 | Laporan singkat: fitur yang benar-benar ada, celahnya, dan cara memasangnya | — |
| [ ] | T-006 | Keputusan Tahap 0 | Tahap 0 | Catatan keputusan berisi angka T-004 dan T-005 dibandingkan dengan kriteria T-003 | T-004, T-005 |

Bila keputusannya **pivot**, Tahap 1 dan 2 diganti dengan plugin untuk LiteLLM atau Presidio, sedangkan Tahap 3 (entitas, validator, pack, dan eval) tetap dipakai.

## Tahap 1 — Kerangka proxy

| | ID | Task | Requirement | Selesai bila | Butuh |
| --- | --- | --- | --- | --- | --- |
| [ ] | T-101 | Inisialisasi workspace Rust: crate `omnirail-core` (pustaka, tanpa HTTP) dan `omnirail` (binary), CI (fmt, clippy, test) | — | `cargo test` hijau di CI; `omnirail-core` tidak bergantung pada axum | T-006 |
| [ ] | T-102 | Skema dan pemuat `omnirail.yaml`: validasi, substitusi `${ENV}`, default aman | CFG-01, CFG-02, CFG-06 | Konfigurasi salah menghentikan start dengan pesan berisi kunci yang salah; variabel kosong ditolak | T-101 |
| [ ] | T-103 | Server axum: `POST /v1/chat/completions` (non-streaming), `/healthz`, `/readyz`, batas body | API-01, API-04, POL-01 | Request valid diteruskan ke handler; body > `max_body_bytes` mendapat 413 | T-101 |
| [ ] | T-104 | Autentikasi kunci OmniRail secara *constant-time* | CFG-07 | Kunci salah mendapat 401; kunci provider tidak pernah muncul di log, error, atau `/readyz` | T-103 |
| [ ] | T-105 | Kontrak error format OpenAI dan header `x-omnirail-request-id` | Bagian 8 | Semua kode error di PRD bagian 8 punya test | T-103 |
| [ ] | T-106 | Tolak fitur yang belum didukung: `stream`, `tools`/`functions`, konten non-teks | API-02 | Ketiganya mendapat 400 `omnirail_unsupported_feature` tanpa memanggil upstream | T-105 |
| [ ] | T-107 | Format internal dan adapter Ollama; resolusi rute dari `model_map` | UP-01, UP-02 | SDK OpenAI Python dan Node mendapat jawaban dari Ollama lewat proxy | T-103 |

## Tahap 2 — Jalur provider

| | ID | Task | Requirement | Selesai bila | Butuh |
| --- | --- | --- | --- | --- | --- |
| [ ] | T-201 | Mock server upstream untuk Anthropic, Gemini, dan OpenAI | — | Test adapter berjalan tanpa jaringan dan tanpa biaya token | T-107 |
| [ ] | T-202 | Adapter Anthropic Messages API | UP-05, UP-06 | Pemetaan system, `max_tokens` default, `finish_reason`, dan `usage` lulus di mock; uji integrasi nyata lulus | T-201 |
| [ ] | T-203 | Cek ulang format Gemini API ke dokumentasi resmi | Q7 | Catatan perbedaan (bila ada) dengan blueprint tertulis | — |
| [ ] | T-204 | Adapter Gemini API | UP-05, UP-06 | Sama seperti T-202, termasuk `assistant` → `model` dan `systemInstruction` | T-201, T-203 |
| [ ] | T-205 | Adapter OpenAI (passthrough) | UP-05, UP-06 | Sama seperti T-202 | T-201 |
| [ ] | T-206 | `allowed_providers`, timeout upstream, dan penyaringan body error provider | UP-03, UP-04, UP-07 | Provider terlarang gagal saat start dan mendapat 403 saat request; timeout mendapat 504; body error provider tidak muncul di respons maupun log | T-202 |

## Tahap 3 — PII, credentials, kebijakan, dan audit

| | ID | Task | Requirement | Selesai bila | Butuh |
| --- | --- | --- | --- | --- | --- |
| [ ] | T-301 | Normalisasi teks (NFKC, casefold, hapus karakter lebar-nol) dengan peta posisi ke teks asli | POL-02 | Rentang temuan pada teks normal bisa dipetakan kembali ke teks asli; test Unicode lulus | T-101 |
| [ ] | T-302 | Validator: Luhn + prefix kartu, struktur NIK, nomor HP, NPWP | PII-01, bagian 7.10 | Test unit memakai semua baris dev yang relevan | T-301 |
| [ ] | T-303 | Detektor entitas dan aturan prioritas tumpang tindih | PII-01, PII-07 | D050 terdeteksi sebagai `nik`, D051 sebagai `credit_card`; `bank_account` tanpa konteks tidak terdeteksi | T-302 |
| [ ] | T-304 | Tokenisasi dan pemulihan: token konsisten, lompati token yang sudah ada di input, tabel hanya di memori | PII-02 s.d. PII-06 | Kriteria terima PII di PRD 7.4 lulus | T-303 |
| [ ] | T-305 | Detektor credentials dan pengecualian placeholder | CRED-01 s.d. CRED-03 | Semua baris `kredensial` dev dengan `cakupan_mvp = ya` lulus | T-301 |
| [ ] | T-306 | Kebijakan: `max_input_chars`, `deny_patterns`, dan `blocked_keywords` per kata utuh | POL-01, POL-02 | Baris `injeksi` dev dengan `cakupan_mvp = ya` lulus; `politikus` tidak tertangkap oleh kata kunci `politik` | T-301 |
| [ ] | T-307 | Rangkai alur request dan response sesuai urutan PRD 7.1 | Bagian 7.1 | Test integrasi membuktikan request yang diblokir tidak pernah ditokenisasi dan tidak memanggil upstream | T-304, T-305, T-306, T-206 |
| [ ] | T-308 | Mode `enforce` dan `shadow`, serta `fail_mode` per rute | POL-04, POL-05 | Tabel semantik shadow di PRD 7.6 lulus baris per baris | T-307 |
| [ ] | T-309 | Pack `id-general` dibundel; pemuat pack mewajibkan tes; urutan prioritas konfigurasi | CFG-03 s.d. CFG-05 | Pack tanpa `tests/` ditolak; override di `omnirail.yaml` menang | T-306 |
| [ ] | T-310 | `omnirail test --pack` | EVAL-03 | Gagal bila ada satu baris `should_detect` terlewat atau satu baris `should_ignore` tertangkap | T-309 |
| [ ] | T-311 | Audit log JSON per request, beserta `policy_version` dan `policy_hash` | AUD-01 s.d. AUD-03 | Field sesuai PRD 7.7; hash berubah bila kebijakan berubah dan tetap bila hanya kunci rahasia yang berubah; tidak ada nilai PII di log | T-307 |
| [ ] | T-312 | Metrik OpenTelemetry (OTLP) | AUD-04 | Metrik di PRD AUD-04 terlihat di collector lokal | T-307 |
| [ ] | T-313 | `omnirail eval`: metrik per entitas, hasil JSON bernomor versi, dan ringkasan Markdown | EVAL-02 | Menghitung metrik sesuai aturan `eval/README.md` | T-303, T-305, T-306 |
| [ ] | T-314 | Baseline dan ambang CI | EVAL-04 | Baseline dev tercatat; CI gagal bila recall turun atau false positive naik melewati ambang; target PRD bagian 9 direvisi tertulis | T-313, T-310 |

## Tahap 4 — Validasi JSON

| | ID | Task | Requirement | Selesai bila | Butuh |
| --- | --- | --- | --- | --- | --- |
| [ ] | T-401 | Schema per rute di konfigurasi | JSON-01 | Rute tanpa schema tidak divalidasi | T-307 |
| [ ] | T-402 | Perbaikan sintaks lokal | JSON-02 | Pagar markdown, koma ekstra, kurung yang tidak tertutup, dan kutip tunggal diperbaiki; test per kasus | T-401 |
| [ ] | T-403 | Urutan perbaiki → parse → pulihkan → validasi; `fail_mode.egress` | JSON-03, JSON-04 | Kriteria terima PRD 7.8 lulus | T-402, T-304 |
| [ ] | T-404 | Set uji JSON rusak dan metriknya di `omnirail eval` | Bagian 9 | Persentase JSON valid setelah perbaikan tercatat | T-403, T-313 |

## Tahap 5 — Rilis awal

| | ID | Task | Requirement | Selesai bila | Butuh |
| --- | --- | --- | --- | --- | --- |
| [ ] | T-501 | Benchmark latensi dengan mock upstream (1 rb, 5 rb, dan 20 rb karakter) | EVAL-05 | p50 dan p99 overhead tercatat dan dibandingkan dengan target | T-307 |
| [ ] | T-502 | Build rilis: Linux x86_64 dan arm64, macOS arm64, image container minimal | DIST-01, DIST-02 | Artefak terlampir di GitHub Release bertag | T-314, T-403 |
| [ ] | T-503 | README rilis: quickstart ≤ 5 langkah, batas klaim, dan hasil benchmark | DIST-03, bagian 10 | 3 orang baru berhasil mengirim request pertama dalam ≤ 10 menit | T-501, T-502 |
| [ ] | T-504 | Jalankan holdout sebelum rilis | EVAL-01 | Hasil holdout tercatat; penurunan dibanding dev dijelaskan | T-314 |
| [ ] | T-505 | 5 sampai 10 wawancara calon pengguna | G5 | Ringkasan tertulis menentukan prioritas setelah MVP, dan Q3, Q8, Q9 terjawab | — |

---

## Catatan keputusan

| Tanggal | Keputusan |
| --- | --- |
| 9 Nov 2026 | Dataset dipisah per folder (`eval/dev/`, `eval/holdout/`) dengan nama berkas dan kolom yang sama, bukan kolom `split` tambahan |
| 9 Nov 2026 | Bila satu nilai lolos validator NIK dan kartu sekaligus, kata konteks menentukan jenisnya; tanpa konteks, dipakai urutan prioritas PII-07 |
