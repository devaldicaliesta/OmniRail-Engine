# OmniRail Engine — Rincian task MVP

Turunan dari [PRD MVP v1.0](PRD.md). Satu task berarti satu PR dengan kriteria selesai yang bisa diperiksa. Kode requirement (misalnya `PII-04`) merujuk ke PRD bagian 7.

**Cara memakai:** kerjakan berurutan per tahap, centang task yang selesai, dan tulis keputusan baru di bagian "Catatan keputusan" di bawah. Task di satu tahap boleh dikerjakan paralel bila kolom "Butuh" sudah terpenuhi.

---

## Tahap 0 — Validasi (maks. 2 minggu)

| | ID | Task | Requirement | Selesai bila | Butuh |
| --- | --- | --- | --- | --- | --- |
| [x] | T-001 | Draf dataset `eval/{dev,holdout}/uji_pii_id.csv` | EVAL-01 | 106 baris dev dan 47 holdout, format terdokumentasi di `eval/README.md` | — |
| [x] | T-002 | Lengkapi dataset sampai ≥ 50 positif dan ≥ 50 negatif per entitas MVP | EVAL-01, Q1 | Hitungan per entitas memenuhi target, dan holdout ≥ 30% dari total | T-001 |
| [ ] | T-003 | Tetapkan kriteria angka keputusan "lanjut, pivot, berhenti" | Q2 | Kriteria tertulis di catatan keputusan **sebelum** T-004 dijalankan | — |
| [ ] | T-004 | Jalankan dataset (dev) terhadap Presidio dengan recognizer Indonesia sederhana (regex tanpa validator) | Tahap 0 | Recall, precision, dan false positive per entitas tercatat di `eval/results/` | T-002, T-003 |
| [ ] | T-005 | Uji LiteLLM + guardrail Presidio sebagai proxy: pemulihan token (`output_parse_pii`), blokir credentials, dan overhead latensi. Cek juga status bug pemulihan di jalur Anthropic ([BerriAI/litellm#22821](https://github.com/BerriAI/litellm/issues/22821)) | Tahap 0 | Laporan singkat: fitur yang benar-benar ada, celahnya, dan cara memasangnya | — |
| [ ] | T-007 | Tinjau sampel label dataset oleh orang kedua: 5 sampai 10 baris per entitas dan kategori (± 120 baris), dev saja | EVAL-01, Q1 | Label keliru diperbaiki; tingkat kesalahan sampel tercatat. Bila > 5%, tinjau ulang entitas yang bermasalah | T-002 |
| [ ] | T-008 | (Opsional) Simpan pembangkit dataset di `eval/tools/` agar dataset bisa diperbanyak ulang secara konsisten | EVAL-01 | Menjalankan pembangkit menghasilkan berkas yang identik dengan yang di repo | — |
| [ ] | T-006 | Keputusan Tahap 0 | Tahap 0 | Catatan keputusan berisi angka T-004 dan T-005 dibandingkan dengan kriteria T-003 | T-004, T-005 |

Bila keputusannya **pivot**, Tahap 1 dan 2 diganti dengan plugin untuk LiteLLM atau Presidio, sedangkan Tahap 3 (entitas, validator, pack, dan eval) tetap dipakai.

## Tahap 1 — Kerangka proxy

| | ID | Task | Requirement | Selesai bila | Butuh |
| --- | --- | --- | --- | --- | --- |
| [ ] | T-101 | Inisialisasi workspace Rust: crate `omnirail-core` (pustaka, tanpa HTTP) dan `omnirail` (binary), CI (fmt, clippy, test) | — | `cargo test` hijau di CI; `omnirail-core` tidak bergantung pada axum | T-006 |
| [ ] | T-102 | Skema dan pemuat `omnirail.yaml`: validasi, substitusi `${ENV}`, default aman | CFG-01, CFG-02, CFG-06 | Konfigurasi salah menghentikan start dengan pesan berisi kunci yang salah; variabel kosong ditolak | T-101 |
| [ ] | T-103 | Server axum: `POST /v1/chat/completions` (non-streaming), `/healthz`, `/readyz`, batas body, field yang didukung | API-01, API-04, API-07, POL-01 | Request valid diteruskan ke handler; body > `max_body_bytes` mendapat 413 | T-101 |
| [ ] | T-104 | Autentikasi kunci OmniRail secara *constant-time* | CFG-07 | Kunci salah mendapat 401; kunci provider tidak pernah muncul di log, error, atau `/readyz` | T-103 |
| [ ] | T-105 | Kontrak error format OpenAI dan header `x-omnirail-request-id` | Bagian 8 | Semua kode error di PRD bagian 8 punya test | T-103 |
| [ ] | T-106 | Tolak fitur yang belum didukung: `stream`, `tools`/`functions`, konten non-teks | API-02 | Ketiganya mendapat 400 `omnirail_unsupported_feature` tanpa memanggil upstream | T-105 |
| [ ] | T-107 | Format internal dan adapter Ollama; resolusi rute dari `routes` | UP-01, UP-02 | SDK OpenAI Python dan Node mendapat jawaban dari Ollama lewat proxy | T-103 |

## Tahap 2 — Jalur provider

| | ID | Task | Requirement | Selesai bila | Butuh |
| --- | --- | --- | --- | --- | --- |
| [ ] | T-201 | Mock server upstream untuk Anthropic, Gemini, dan OpenAI | — | Test adapter berjalan tanpa jaringan dan tanpa biaya token | T-107 |
| [ ] | T-202 | Adapter Anthropic Messages API | UP-05, UP-06 | Pemetaan system, `max_tokens` default, `finish_reason`, dan `usage` lulus di mock; uji integrasi nyata lulus | T-201 |
| [ ] | T-203 | Cek ulang format Gemini API ke dokumentasi resmi | Q7 | Catatan perbedaan (bila ada) dengan blueprint tertulis | — |
| [ ] | T-204 | Adapter Gemini API | UP-05, UP-06 | Sama seperti T-202, termasuk `assistant` → `model` dan `systemInstruction` | T-201, T-203 |
| [ ] | T-205 | Adapter OpenAI (passthrough) | UP-05, UP-06 | Sama seperti T-202 | T-201 |
| [ ] | T-206 | `allowed_providers`, timeout upstream, dan penyaringan body error provider | UP-03, UP-04, UP-07, POL-03 | Provider terlarang gagal saat start dan mendapat 403 saat request; timeout mendapat 504; body error provider tidak muncul di respons maupun log | T-202 |

## Verifikasi format (sebelum atau paralel dengan T-302)

Tindak lanjut keterbatasan K1 s.d. K5 di PRD Lampiran A. T-302 boleh dimulai dengan asumsi sementara. Task ini dianggap selesai bila hasilnya tercatat di Lampiran A dan dataset diperbarui bila perlu.

| | ID | Task | Requirement | Selesai bila | Butuh |
| --- | --- | --- | --- | --- | --- |
| [ ] | T-321 | Cari daftar prefix (BIN) kartu GPN; putuskan jalur deteksi kartu debit GPN | K1, Q5 | Daftar prefix bersumber resmi, **atau** keputusan tertulis memakai Luhn + kata konteks; baris dataset kartu GPN ditambahkan | — |
| [ ] | T-322 | Konfirmasi kode provinsi Papua Selatan, Papua Tengah, Papua Pegunungan, dan Papua Barat Daya | K2, Q5 | Kode dicocokkan dengan tabel Kemendagri; validator NIK/KK dan dataset disesuaikan | — |
| [ ] | T-323 | Pastikan panjang nomor BPJS Ketenagakerjaan (11 atau 16 digit) | K3, Q11 | Format bersumber resmi atau dari contoh calon pengguna (bukan data asli); spesifikasi `bpjs` diperbarui | — |
| [ ] | T-324 | Cek format nomor paspor ke sumber Imigrasi, termasuk dampak paspor tunggal 2027 | K4, Q11 | Pola `passport_id` bersumber Imigrasi, atau catatan bahwa sumber resmi tidak tersedia | — |
| [ ] | T-325 | Buka ulang sumber yang tidak bisa diakses (NI PPPK, kode plat, token Telegram) dari jaringan tanpa batasan | K5, Q10, Q12 | Tingkat keyakinan di Lampiran A diperbarui berdasarkan sumber primer | — |

## Tahap 3 — PII, credentials, kebijakan, dan audit

| | ID | Task | Requirement | Selesai bila | Butuh |
| --- | --- | --- | --- | --- | --- |
| [ ] | T-301 | Normalisasi teks (NFKC, casefold, hapus karakter lebar-nol) dengan peta posisi ke teks asli | POL-02 | Rentang temuan pada teks normal bisa dipetakan kembali ke teks asli; test Unicode lulus | T-101 |
| [ ] | T-302 | Validator: Luhn + prefix kartu, struktur NIK, KK, dan NIP, nomor HP, NPWP, paspor, BPJS, tanggal | PII-01, bagian 7.10 | Test unit memakai semua baris dev yang relevan; asumsi yang belum terverifikasi (K1 s.d. K5) ditandai di kode agar mudah diganti | T-301 (T-321 s.d. T-325 bila sudah selesai) |
| [ ] | T-303 | Detektor entitas, kata konteks wajib, dan aturan prioritas tumpang tindih | PII-01, PII-07 | D050 terdeteksi sebagai `nik`, D051 sebagai `credit_card`; `kk`, `passport_id`, `bpjs`, `birth_date`, dan `bank_account` tanpa konteks tidak terdeteksi | T-302 |
| [ ] | T-304 | Tokenisasi dan pemulihan: token konsisten, lompati token yang sudah ada di input, tabel hanya di memori | PII-02 s.d. PII-06 | Kriteria terima PII di PRD 7.4 lulus | T-303 |
| [ ] | T-305 | Detektor credentials dan pengecualian placeholder | CRED-01 s.d. CRED-03 | Semua baris `kredensial` dev dengan `cakupan_mvp = ya` lulus | T-301 |
| [ ] | T-306 | Kebijakan: `max_input_chars`, `deny_patterns`, dan `blocked_keywords` per kata utuh | POL-01, POL-02 | Baris `injeksi` dev dengan `cakupan_mvp = ya` lulus; `politikus` tidak tertangkap oleh kata kunci `politik` | T-301 |
| [ ] | T-307 | Rangkai alur request dan response sesuai urutan PRD 7.1, termasuk pemeriksaan semua peran pesan dan riwayat | Bagian 7.1, API-03 | Test integrasi membuktikan request yang diblokir tidak pernah ditokenisasi dan tidak memanggil upstream | T-304, T-305, T-306, T-206 |
| [ ] | T-308 | Mode `enforce` dan `shadow`, serta `fail_mode` per rute | POL-04, POL-05 | Tabel semantik shadow di PRD 7.6 lulus baris per baris | T-307 |
| [ ] | T-309 | Pack `id-general` dibundel; pemuat pack mewajibkan tes; urutan prioritas konfigurasi | CFG-03 s.d. CFG-05 | Pack tanpa `tests/` ditolak; override di `omnirail.yaml` menang | T-306 |
| [ ] | T-310 | `omnirail test --pack` | EVAL-03 | Gagal bila ada satu baris `should_detect` terlewat atau satu baris `should_ignore` tertangkap | T-309 |
| [ ] | T-311 | Audit log JSON per request, beserta `policy_version` dan `policy_hash` | AUD-01 s.d. AUD-03 | Field sesuai PRD 7.7; hash berubah bila kebijakan berubah dan tetap bila hanya kunci rahasia yang berubah; tidak ada nilai PII di log | T-307 |
| [ ] | T-312 | Metrik OpenTelemetry (OTLP) | AUD-04 | Metrik di PRD AUD-04 terlihat di collector lokal | T-307 |
| [ ] | T-313 | `omnirail eval`: metrik per entitas, hasil JSON bernomor versi, dan ringkasan Markdown | EVAL-02 | Menghitung metrik sesuai aturan `eval/README.md` | T-303, T-305, T-306 |
| [ ] | T-314 | Baseline dan ambang CI | EVAL-04 | Baseline dev tercatat; CI gagal bila recall turun atau false positive naik melewati ambang; target PRD bagian 9 direvisi tertulis | T-313, T-310 |
| [ ] | T-316 | Fungsi `inspect` di `omnirail-core`, endpoint `POST /omnirail/v1/inspect` dan `GET /omnirail/v1/packs` | PG-01, PG-02 | Respons berisi keputusan, temuan berupa posisi (tanpa nilai), teks bertoken, versi dan hash kebijakan; mock upstream membuktikan provider tidak dipanggil; `grep` nilai uji pada body respons kosong | T-307, T-309 |
| [ ] | T-317 | CLI `omnirail inspect "<teks>"` dan `--file` | EVAL-06 | Keluaran sama dengan endpoint T-316 untuk input yang sama; kode keluar bukan nol bila diblokir | T-316 |
| [ ] | T-318 | `omnirail validate --config`, contoh `CODEOWNERS` dan workflow CI untuk repo pengguna, dan berkas contoh `omnirail.example.yaml` dari PRD 7.14 | CFG-10, bagian 7.14 | Konfigurasi atau tes pack yang gagal menghasilkan kode keluar bukan nol; kunci tak dikenal ditolak; contoh 7.14 lolos validasi | T-309, T-310 |
| [ ] | T-315 | Entitas P1 `vehicle_plate` dan `ip_address`, mati secara default | PII-01b | Baris dev kedua entitas lulus saat diaktifkan; tidak memengaruhi metrik MVP saat mati | T-303 |

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
| [ ] | T-506 | Konfigurasi `playground` (enabled, admin_keys, allowed_routes, datasets), kunci admin terpisah, dan penyajian berkas statis tertanam dengan CSP | PG-04, PG-05 | Default 404; bukan loopback tanpa `admin_keys` gagal start; kunci aplikasi mendapat 403 `omnirail_admin_required`; ukuran berkas ≤ 200 KB | T-316 |
| [ ] | T-507 | Tab Coba mode periksa saja: input, pilihan pack dan mode, sorotan entitas berlabel, tabel temuan tersamarkan, teks bertoken, keputusan, waktu, versi dan hash kebijakan | PG-03, PG-06, PG-07 | Hasil identik dengan audit log jalur proxy; tidak ada teks di `localStorage`/`sessionStorage`; berfungsi tanpa internet | T-506 |
| [ ] | T-508 | Aksesibilitas dan uji E2E tab Coba | PG-03, kriteria 7.13 | Bisa dipakai penuh dengan keyboard; kontras WCAG 2.1 AA; satu uji E2E (Playwright) untuk alur tempel teks → periksa → lihat temuan | T-507 |
| [ ] | T-509 | `SECURITY.md`, `CONTRIBUTING.md`, dan `CODEOWNERS` untuk repo OmniRail | DIST-05 | Ada jalur pelaporan kerentanan privat; folder `policy-packs/` wajib ditinjau pemilik | — |
| [ ] | T-505 | 5 sampai 10 wawancara calon pengguna | G5 | Ringkasan tertulis menentukan prioritas setelah MVP, dan Q3, Q8, Q9 terjawab; tugas "coba pack lalu jelaskan satu temuan" diukur di tampilan uji (target bagian 9) | T-507 |

---

## Setelah rilis awal (P1, urutan ditentukan umpan balik)

| | ID | Task | Requirement | Selesai bila | Butuh |
| --- | --- | --- | --- | --- | --- |
| [ ] | T-601 | Kirim ke provider dari tab Coba: tampilan berdampingan teks bertoken, jawaban provider, dan jawaban setelah dipulihkan; dibatasi `allowed_routes` | PG-08 | Rute di luar daftar ditolak; nilai asli tidak pernah dikirim ke provider | T-507 |
| [ ] | T-602 | Bandingkan `enforce` dan `shadow` dalam satu tampilan | PG-09 | Perbedaan keputusan per aturan terlihat untuk teks yang sama | T-507 |
| [ ] | T-603 | Override entitas sementara | PG-10 | Override tidak tersimpan, ditandai jelas, dan menghasilkan hash kebijakan sementara | T-507 |
| [ ] | T-604 | Tab Evaluasi: metrik per entitas, selisih dengan baseline, kasus gagal yang bisa disaring, unduh JSON/Markdown | PG-11 | Hasil sama dengan `omnirail eval` untuk dataset dan pack yang sama | T-313, T-507 |
| [ ] | T-605 | Kunci holdout di tab Evaluasi | PG-12 | Membuka holdout butuh konfirmasi dan tercatat di audit log | T-604 |
| [ ] | T-606 | Backlog P1 lain dari PRD: `GET /v1/models` (API-05), ekspor ringkasan audit (AUD-05), reload konfigurasi via SIGHUP (CFG-08), deteksi secret entropi tinggi (CRED-04), contoh pemasangan di depan LiteLLM (DIST-04), `response_format` dari klien dan retry JSON (JSON-05, JSON-06), entitas kustom (PII-08) | API-05, AUD-05, CFG-08, CRED-04, DIST-04, JSON-05, JSON-06, PII-08 | Dipecah menjadi task sendiri saat diprioritaskan | — |

## Catatan keputusan

| Tanggal | Keputusan |
| --- | --- |
| 9 Nov 2026 | Dataset dipisah per folder (`eval/dev/`, `eval/holdout/`) dengan nama berkas dan kolom yang sama, bukan kolom `split` tambahan |
| 9 Nov 2026 | Bila satu nilai lolos validator NIK dan kartu sekaligus, kata konteks menentukan jenisnya; tanpa konteks, dipakai urutan prioritas PII-07 |
| 9 Nov 2026 | Dataset v0.2: 701 baris dev dan 307 holdout. Template kalimat dev dan holdout dipisah. Baris negatif menandai entitas yang dijebak di `catatan` (`[nik]`, `[email]`, dan seterusnya) |
| 9 Nov 2026 | Terbuka (PRD Q13): apakah nama bank (BCA, BRI, dan seterusnya) dijadikan kata konteks `bank_account`? Sekarang baris seperti itu ditandai `cakupan_mvp = tidak` |
| 9 Nov 2026 | Entitas ditambah (PRD v1.2): `nip`, `kk`, `passport_id`, `bpjs`, `birth_date` masuk P0; `vehicle_plate` dan `ip_address` P1. Dataset v0.3: 1.276 baris dev dan 549 holdout |
| 9 Nov 2026 | Format diverifikasi (PRD Lampiran A). NI PPPK ditambahkan ke validator `nip` (digit 13-14 bernilai 21 s.d. 29), paspor diperluas menjadi 1-2 huruf + 6-7 digit, BPJS Ketenagakerjaan 16 digit ditambahkan, kode plat disesuaikan Perpol 7/2021. Baris hasil template dibangkitkan ulang; baris tulisan tangan (D001-D106, H001-H047) tidak berubah |
| 9 Nov 2026 | Crosscheck kesiapan (PRD v1.5): semua requirement P0 kini punya task; ditambah T-007 (tinjau label), T-008, T-318 (`omnirail validate`), T-509 (`SECURITY.md`), dan T-606 (backlog P1) |
| 9 Nov 2026 | Tampilan uji (PRD 7.13): endpoint `inspect` dan CLI di Tahap 3, tab Coba mode periksa saja di Tahap 5, fitur lain setelah rilis. Tampilan uji dipakai dalam wawancara Tahap 5 |
| 9 Nov 2026 | Dataset v0.5: 2.361 baris dev dan 1.009 holdout. Ditambah bingkai teks (prompt LLM, chat, email, tabel, YAML, JSON, pesan terusan) dan gaya ketik (singkatan, voice-to-text). Jenis nomor BPJS kini dicocokkan dengan kalimatnya (Kesehatan 13 digit, Ketenagakerjaan 11 atau 16 digit), sehingga baris v0.3/v0.4 hasil template untuk entitas baru dibangkitkan ulang. Baris v0.1/v0.2 tidak berubah |
| 9 Nov 2026 | Pola plat mewajibkan huruf akhiran, dan IP ≥ 224 dikecualikan. Keduanya ditemukan saat pemeriksaan silang dataset ("gate A1", "Vitamin B 12", subnet mask) |
