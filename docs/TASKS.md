# OmniRail Engine — Rincian task MVP

Turunan dari [PRD MVP v1.7.2](PRD.md). Dasar metode tiap task ada di [Landasan metode](LANDASAN_METODE.md). Satu task berarti satu PR dengan kriteria selesai yang bisa diperiksa. Kode requirement (misalnya `PII-04`) merujuk ke PRD bagian 7.

**Cara memakai:** kerjakan berurutan per tahap, centang task yang selesai (`[-]` berarti ditutup tanpa dikerjakan penuh, dengan alasan di catatan keputusan), dan tulis keputusan baru di bagian "Catatan keputusan" di bawah. Task di satu tahap boleh dikerjakan paralel bila kolom "Butuh" sudah terpenuhi.

**Tentang ID task (v1.6):** tahap disusun ulang mengikuti pembagian rilis α dan β di PRD bagian 11. ID task lama dipertahankan agar rujukan di commit dan dokumen tidak putus, jadi angka ratusan pada ID tidak lagi menunjukkan tahap.

| Rilis | Tahap | Isi singkat |
| --- | --- | --- |
| — | 0 | Validasi dan keputusan lanjut, pivot, atau berhenti |
| α (periksa) | 1, 2 | `omnirail-core`, CLI `inspect`/`eval`/`scan`, demo web WASM, wawancara pertama |
| β (proxy, rilis publik pertama) | 3, 4, 5 | Proxy dengan pseudo-streaming, Ollama + satu provider cloud, mode shadow, audit log, laporan paparan |

---

## Tahap 0 — Validasi (maks. 2 minggu)

| | ID | Task | Requirement | Selesai bila | Butuh |
| --- | --- | --- | --- | --- | --- |
| [x] | T-001 | Draf dataset `eval/{dev,holdout}/uji_pii_id.csv` | EVAL-01 | 106 baris dev dan 47 holdout, format terdokumentasi di `eval/README.md` | — |
| [x] | T-002 | Lengkapi dataset sampai ≥ 50 positif dan ≥ 50 negatif per entitas MVP | EVAL-01, Q1 | Hitungan per entitas memenuhi target, dan holdout ≥ 30% dari total | T-001 |
| [x] | T-003 | Tetapkan kriteria angka keputusan "lanjut, pivot, berhenti" | Q2 | Kriteria tertulis di catatan keputusan **sebelum** T-004 dijalankan | — |
| [x] | T-004 | Jalankan dataset (dev) terhadap Presidio dengan recognizer Indonesia sederhana (regex tanpa validator) | Tahap 0 | Recall, precision, dan false positive per entitas tercatat di `eval/results/` | T-002, T-003 |
| [x] | T-011 | Prototipe detektor referensi di `eval/tools/` (Python, regex + validator + kata konteks sesuai PRD 7.10, memakai validator `cek_dataset.py`) sebagai angka pembanding pendekatan OmniRail | Tahap 0, Q2 | Recall, precision, dan false positive per entitas di dev tercatat di `eval/results/` dengan format yang sama dengan T-004; ditandai bukan kode produk. Nanti dipakai sebagai acuan uji silang untuk implementasi Rust | T-009 |
| [x] | T-005 | Uji LiteLLM + guardrail Presidio sebagai proxy: pemulihan token (`output_parse_pii`), blokir credentials, dan overhead latensi. Cek juga status bug pemulihan di jalur Anthropic ([BerriAI/litellm#22821](https://github.com/BerriAI/litellm/issues/22821)) | Tahap 0 | Laporan singkat: fitur yang benar-benar ada, celahnya, dan cara memasangnya | — |
| [ ] | T-007 | Tinjau sampel label dataset oleh orang kedua: 5 sampai 10 baris per entitas dan kategori (± 120 baris), dev saja | EVAL-01, Q1 | Label keliru diperbaiki; tingkat kesalahan sampel dan kappa Cohen tercatat (`eval/tools/statistik.py`, target κ ≥ 0,8). Bila kesalahan > 5% atau κ < 0,8, tinjau ulang entitas yang bermasalah | T-002 |
| [x] | T-009 | Pemeriksa konsistensi dataset `eval/tools/cek_dataset.py` dan CI | EVAL-01 | Format, label, validator struktur PRD 7.10, kebocoran dev ke holdout, target jumlah, dan tabel `eval/README.md` dicek di setiap pull request | T-002 |
| [x] | T-010 | Dataset v0.6: baris percakapan multi-pesan dan angka terucap | PII-10, PII-11 | Baris lintas pesan (positif dan negatif) dan angka terucap ada di dev dan holdout dengan template terpisah; pemeriksa dataset lulus | T-009 |
| [x] | T-012 | Pustaka statistik evaluasi `eval/tools/statistik.py`: interval Wilson, uji McNemar eksak, kappa Cohen | EVAL-09 | Diuji terhadap nilai rujukan; tabel lebar interval untuk ukuran dataset sekarang tercatat di Landasan metode bagian 1 | — |
| [x] | T-013 | Datasheet dataset `eval/DATASHEET.md` (Gebru dkk., 2021) | EVAL-01 | Motivasi, komposisi, proses, pelabelan, pemakaian, distribusi, dan pemeliharaan terdokumentasi, termasuk risiko nilai rekaan yang kebetulan sama dengan nomor asli | T-010 |
| [-] | T-008 | (Opsional, ditutup) Simpan pembangkit dataset di `eval/tools/` agar dataset bisa diperbanyak ulang secara konsisten | EVAL-01 | Menjalankan pembangkit menghasilkan berkas yang identik dengan yang di repo | — |
| [x] | T-006 | Keputusan Tahap 0 | Tahap 0 | Catatan keputusan berisi angka T-004, T-005, dan T-011 dibandingkan dengan kriteria T-003 | T-004, T-005, T-011 |

Bila keputusannya **pivot**, Tahap 3 dan 4 (proxy) diganti dengan plugin untuk LiteLLM atau Presidio, sedangkan Tahap 1 dan 2 (inti deteksi, pack, eval, `scan`, dan demo) tetap dipakai.

## Verifikasi format (sebelum atau paralel dengan T-302)

Tindak lanjut keterbatasan K1 s.d. K5 di PRD Lampiran A. T-302 boleh dimulai dengan asumsi sementara. Task ini dianggap selesai bila hasilnya tercatat di Lampiran A dan dataset diperbarui bila perlu.

| | ID | Task | Requirement | Selesai bila | Butuh |
| --- | --- | --- | --- | --- | --- |
| [ ] | T-321 | Cari daftar prefix (BIN) kartu GPN; putuskan jalur deteksi kartu debit GPN | K1, Q5 | Daftar prefix bersumber resmi, **atau** keputusan tertulis memakai Luhn + kata konteks; baris dataset kartu GPN ditambahkan | — |
| [ ] | T-322 | Konfirmasi kode provinsi Papua Selatan, Papua Tengah, Papua Pegunungan, dan Papua Barat Daya | K2, Q5 | Kode dicocokkan dengan tabel Kemendagri; validator NIK/KK dan dataset disesuaikan | — |
| [ ] | T-323 | Pastikan panjang nomor BPJS Ketenagakerjaan (11 atau 16 digit) | K3, Q11 | Format bersumber resmi atau dari contoh calon pengguna (bukan data asli); spesifikasi `bpjs` diperbarui | — |
| [ ] | T-324 | Cek format nomor paspor ke sumber Imigrasi, termasuk dampak paspor tunggal 2027 | K4, Q11 | Pola `passport_id` bersumber Imigrasi, atau catatan bahwa sumber resmi tidak tersedia | — |
| [ ] | T-325 | Buka ulang sumber yang tidak bisa diakses (NI PPPK, kode plat, token Telegram) dari jaringan tanpa batasan | K5, Q10, Q12 | Tingkat keyakinan di Lampiran A diperbarui berdasarkan sumber primer | — |
| [ ] | T-326 | Verifikasi format credentials ekosistem lokal: token gateway WhatsApp (Fonnte, Wablas), DOKU, iPaymu, OY!, Flip, RajaOngkir, Biteship | CRED-05 | Format setiap layanan bersumber dokumentasi resmi dan tercatat di Lampiran A beserta tingkat keyakinan; layanan tanpa sumber dicatat sebagai tidak ditambahkan | — |

## Tahap 1 — Inti deteksi (rilis α)

| | ID | Task | Requirement | Selesai bila | Butuh |
| --- | --- | --- | --- | --- | --- |
| [x] | T-101 | Inisialisasi workspace Rust: crate `omnirail-core` (pustaka murni, tanpa I/O) dan `omnirail` (binary CLI, nanti juga server), CI (fmt, clippy, test, `cargo audit`, `cargo deny`) | DIST-08 (sebagian) | `cargo test` hijau di CI; `omnirail-core` tidak bergantung pada axum maupun tokio, memakai `#![forbid(unsafe_code)]`, dan CI membangunnya untuk `wasm32-unknown-unknown` | T-006 |
| [ ] | T-301 | Normalisasi teks (NFKC, casefold, hapus karakter lebar-nol) dengan peta posisi ke teks asli | POL-02 | Rentang temuan pada teks normal bisa dipetakan kembali ke teks asli; test Unicode lulus | T-101 |
| [ ] | T-302 | Validator: Luhn + prefix kartu, struktur NIK, KK, dan NIP, nomor HP, NPWP, paspor, BPJS, tanggal | PII-01, bagian 7.10 | Test unit memakai semua baris dev yang relevan; asumsi yang belum terverifikasi (K1 s.d. K5) ditandai di kode agar mudah diganti | T-301 (T-321 s.d. T-325 bila sudah selesai) |
| [ ] | T-303 | Detektor entitas, kata konteks wajib, dan aturan prioritas tumpang tindih | PII-01, PII-07 | D050 terdeteksi sebagai `nik`, D051 sebagai `credit_card`; `kk`, `passport_id`, `bpjs`, `birth_date`, dan `bank_account` tanpa konteks tidak terdeteksi | T-302 |
| [ ] | T-319 | Kata konteks lintas pesan: jendela konteks memakai ≤ 15 kata terakhir pesan sebelumnya bila nilai ada di 10 kata pertama pesan | PII-10 | Kriteria terima PII-10 di PRD 7.4 lulus; baris multi-pesan dev dengan `cakupan_mvp = ya` lulus | T-303 |
| [ ] | T-304 | Tokenisasi dan pemulihan: token konsisten dengan kunci nilai yang dinormalisasi per jenis, lompati token yang sudah ada di input, tabel hanya di memori | PII-02 s.d. PII-06 | Kriteria terima PII di PRD 7.4 lulus, termasuk dua penulisan nomor HP yang sama mendapat satu token | T-303 |
| [ ] | T-305 | Detektor credentials dan pengecualian placeholder | CRED-01 s.d. CRED-03 | Semua baris `kredensial` dev dengan `cakupan_mvp = ya` lulus | T-301 |
| [ ] | T-306 | Kebijakan: `max_input_chars`, `deny_patterns`, dan `blocked_keywords` per kata utuh | POL-01, POL-02 | Baris `injeksi` dev dengan `cakupan_mvp = ya` lulus; `politikus` tidak tertangkap oleh kata kunci `politik` | T-301 |
| [ ] | T-309 | Pack `id-general` dibundel; pemuat pack mewajibkan tes; urutan prioritas konfigurasi; regex tanpa backtracking | CFG-03 s.d. CFG-05, POL-06 | Pack tanpa `tests/` ditolak; override di `omnirail.yaml` menang; pola dengan look-around atau backreference ditolak dengan pesan yang menyebut polanya | T-306 |
| [ ] | T-310 | `omnirail test --pack` | EVAL-03 | Gagal bila ada satu baris `should_detect` terlewat atau satu baris `should_ignore` tertangkap | T-309 |
| [ ] | T-313 | `omnirail eval`: metrik per entitas dengan interval Wilson 95%, hasil JSON bernomor versi, dan ringkasan Markdown | EVAL-02, EVAL-09 | Menghitung metrik sesuai aturan `eval/README.md`, termasuk memecah baris multi-pesan menjadi `messages`; angka sama dengan `eval/tools/statistik.py`; recall juga dilaporkan per kelompok identifier langsung dan kuasi; baris di luar cakupan dilaporkan terpisah | T-303, T-305, T-306, T-319 |
| [ ] | T-314 | Baseline dan ambang CI | EVAL-04, EVAL-09 | Baseline dev tercatat; CI gagal bila uji McNemar per baris menunjukkan recall memburuk atau false positive bertambah secara bermakna (p < 0,05), atau angka titik melewati ambang; target PRD bagian 9 direvisi tertulis | T-313, T-310 |
| [ ] | T-316 | Fungsi `inspect` di `omnirail-core`: keputusan, temuan berupa posisi (tanpa nilai), teks bertoken, versi dan hash kebijakan | PG-01 (fungsi), EVAL-06 | Fungsi murni tanpa I/O, dipakai CLI dan demo WASM; test membuktikan keluaran tidak memuat nilai entitas | T-304, T-305, T-306, T-309 |
| [ ] | T-317 | CLI `omnirail inspect "<teks>"` dan `--file` | EVAL-06 | Keluaran sama dengan endpoint T-316 untuk input yang sama; kode keluar bukan nol bila diblokir | T-316 |
| [ ] | T-320 | `omnirail scan <path>...` beserta contoh hook pre-commit dan langkah CI | EVAL-07, EVAL-08 | Kriteria terima `omnirail scan` di PRD 7.11 lulus; kode keluar 1 bila ada temuan; contoh pre-commit dan CI teruji di repo contoh | T-316 |
| [ ] | T-337 | Uji perilaku (uji fungsional berbasis templat): tes fungsi minimum per entitas dan tes invarian (pemisah, huruf, bingkai, gaya ketik), dibangkitkan dari templat | EVAL-10 | Dijalankan di CI; setiap entitas P0 punya tes fungsi minimum dan minimal tiga jenis tes invarian | T-303 |
| [ ] | T-338 | *Property-based testing* (`proptest`) untuk invarian tokenisasi dan normalisasi | EVAL-11 | Invarian di PRD EVAL-11 diuji dengan input acak di CI; setiap kasus gagal yang ditemukan disimpan sebagai test regresi | T-301, T-304 |
| [ ] | T-339 | Uji silang implementasi Rust lawan prototipe Python (T-011) pada dataset dev | EVAL-12 | Nol perbedaan temuan, atau setiap perbedaan tercatat sebagai keputusan | T-011, T-303 |
| [ ] | T-342 | Dokumen model ancaman: STRIDE dan LINDDUN untuk alur proxy, audit log, laporan paparan, dan demo WASM; pemetaan ke OWASP Top 10 for LLM Applications edisi terbaru | Bagian 10 | `docs/THREAT_MODEL.md` berisi aliran data, ancaman per elemen, mitigasi, dan risiko yang diterima; bagian 10 PRD diperbarui bila ada celah baru | — |

## Tahap 2 — Rilis α

| | ID | Task | Requirement | Selesai bila | Butuh |
| --- | --- | --- | --- | --- | --- |
| [ ] | T-507 | Halaman tab Coba mode periksa saja: input, pilihan pack dan mode, sorotan entitas berlabel, tabel temuan tersamarkan, teks bertoken, keputusan, waktu, versi dan hash kebijakan | PG-03, PG-06, PG-07 | Tidak ada teks di `localStorage`/`sessionStorage`; berfungsi tanpa internet; HTML, CSS, dan JS ≤ 200 KB (di luar berkas WASM). Halaman yang sama nanti disajikan binary (T-506) | T-316 |
| [ ] | T-510 | Demo WASM: bangun `omnirail-core` ke WebAssembly, sajikan halaman T-507 sebagai situs statis (GitHub Pages) lewat workflow | DIST-06 | Hasil identik dengan `omnirail inspect` untuk teks contoh; `Content-Security-Policy: connect-src 'none'`; uji E2E membuktikan tidak ada request jaringan setelah halaman dimuat | T-507 |
| [ ] | T-514 | Rilis yang bisa diverifikasi: tanda tangan Sigstore atau GitHub artifact attestations, provenance SLSA, SBOM, dan OpenSSF Scorecard | DIST-08 | Binary rilis α punya tanda tangan dan SBOM yang bisa diverifikasi dengan perintah di README; Scorecard tampil di README | T-101 |
| [ ] | T-508 | Aksesibilitas dan uji E2E tab Coba (di demo WASM) | PG-03, kriteria 7.13 | Bisa dipakai penuh dengan keyboard; kontras WCAG 2.1 AA; satu uji E2E (Playwright) untuk alur tempel teks → periksa → lihat temuan | T-510 |
| [ ] | T-512 | Rilis α: binary CLI (Linux x86_64 dan arm64, macOS arm64), tag dan catatan rilis, README bagian "Coba sekarang" (demo, `inspect`, `scan`) dengan batas klaim | DIST-01 (CLI), DIST-08, bagian 10 | Artefak bertanda tangan terlampir di GitHub Release bertag; demo bisa dibuka publik; batas klaim tertulis di README dan halaman demo | T-314, T-317, T-320, T-510, T-514 |
| [ ] | T-513 | Wawancara pertama (≥ 3) memakai demo WASM dan `scan` | G5 | Ringkasan tertulis; provider dan SDK yang dipakai calon pengguna tercatat dan dipakai memilih provider cloud UP-01; Q3 dan Q9 mulai terjawab; waktu sampai temuan pertama di demo terukur (target bagian 9) | T-512 |

## Tahap 3 — Kerangka proxy (rilis β)

| | ID | Task | Requirement | Selesai bila | Butuh |
| --- | --- | --- | --- | --- | --- |
| [ ] | T-102 | Skema dan pemuat `omnirail.yaml`: validasi, substitusi `${ENV}`, default aman | CFG-01, CFG-02, CFG-06 | Konfigurasi salah menghentikan start dengan pesan berisi kunci yang salah; variabel kosong ditolak | T-101 |
| [ ] | T-103 | Server axum: `POST /v1/chat/completions` (non-streaming), `/healthz`, `/readyz`, batas body, field yang didukung | API-01, API-04, API-07, POL-01 | Request valid diteruskan ke handler; body > `max_body_bytes` mendapat 413 | T-101 |
| [ ] | T-104 | Autentikasi kunci OmniRail secara *constant-time* | CFG-07 | Kunci salah mendapat 401; kunci provider tidak pernah muncul di log, error, atau `/readyz` | T-103 |
| [ ] | T-105 | Kontrak error format OpenAI dan header `x-omnirail-request-id` | Bagian 8 | Semua kode error di PRD bagian 8 punya test | T-103 |
| [ ] | T-106 | Tolak fitur yang belum didukung: `tools`/`functions`, konten non-teks, `n` > 1 | API-02 | Ketiganya mendapat 400 `omnirail_unsupported_feature` tanpa memanggil upstream | T-105 |
| [ ] | T-107 | Format internal dan adapter Ollama; resolusi rute dari `routes` | UP-01, UP-02 | SDK OpenAI Python dan Node mendapat jawaban dari Ollama lewat proxy | T-103 |
| [ ] | T-108 | Pseudo-streaming: `stream: true` dipanggil ke provider tanpa streaming, jawaban final dikirim sebagai SSE | API-08 | SDK OpenAI Python dan Node dengan `stream=True` menerima jawaban lengkap; mock membuktikan provider dipanggil tanpa streaming; potongan SSE berisi nilai yang sudah dipulihkan; header `x-omnirail-stream: buffered` | T-107 |
| [ ] | T-201 | Mock server upstream untuk provider cloud yang dipilih (dan nanti provider lain) | — | Test adapter berjalan tanpa jaringan dan tanpa biaya token | T-107 |
| [ ] | T-202 | Adapter provider cloud pertama: Anthropic Messages API, kecuali T-513 menunjukkan provider lain | UP-01, UP-05, UP-06 | Pemetaan system, `max_tokens` default, `finish_reason`, dan `usage` lulus di mock; uji integrasi nyata lulus | T-201, T-513 |
| [ ] | T-206 | `allowed_providers`, timeout upstream, dan penyaringan body error provider | UP-03, UP-04, UP-07, POL-03 | Provider terlarang gagal saat start dan mendapat 403 saat request; timeout mendapat 504; body error provider tidak muncul di respons maupun log | T-202 |

## Tahap 4 — Alur proxy lengkap (rilis β)

| | ID | Task | Requirement | Selesai bila | Butuh |
| --- | --- | --- | --- | --- | --- |
| [ ] | T-307 | Rangkai alur request dan response sesuai urutan PRD 7.1, termasuk pemeriksaan semua peran pesan dan riwayat | Bagian 7.1, API-03 | Test integrasi membuktikan request yang diblokir tidak pernah ditokenisasi dan tidak memanggil upstream | T-304, T-305, T-306, T-206 |
| [ ] | T-308 | Mode `enforce` dan `shadow`, serta `fail_mode` per rute | POL-04, POL-05 | Tabel semantik shadow di PRD 7.6 lulus baris per baris | T-307 |
| [ ] | T-311 | Audit log JSON per request, beserta `policy_version`, `policy_hash`, dan `stream` | AUD-01 s.d. AUD-03 | Field sesuai PRD 7.7; hash berubah bila kebijakan berubah dan tetap bila hanya kunci rahasia yang berubah; tidak ada nilai PII di log | T-307 |
| [ ] | T-332 | `omnirail report`: laporan paparan data dari audit log, termasuk atribut `kategori_pdp` di pack | REP-01, REP-02 | Kriteria terima PRD 7.15 lulus; kategori PDP ditandai draf sampai Q6 terjawab | T-311 |
| [ ] | T-334 | Endpoint `POST /omnirail/v1/inspect` dan `GET /omnirail/v1/packs` | PG-01, PG-02 | Respons sama dengan fungsi T-316; mock upstream membuktikan provider tidak dipanggil; `grep` nilai uji pada body respons kosong | T-307, T-316 |
| [ ] | T-318 | `omnirail validate --config`, contoh `CODEOWNERS` dan workflow CI untuk repo pengguna, dan berkas contoh `omnirail.example.yaml` dari PRD 7.14 | CFG-10, bagian 7.14 | Konfigurasi atau tes pack yang gagal menghasilkan kode keluar bukan nol; kunci tak dikenal ditolak; contoh 7.14 lolos validasi | T-309, T-310 |

## Tahap 5 — Rilis β (rilis publik pertama)

| | ID | Task | Requirement | Selesai bila | Butuh |
| --- | --- | --- | --- | --- | --- |
| [ ] | T-501 | Benchmark latensi dengan mock upstream (1 rb, 5 rb, dan 20 rb karakter), beban open-loop pada laju tetap | EVAL-05 | p50 dan p99 overhead tercatat tanpa *coordinated omission* (latensi dihitung dari jadwal kirim, HdrHistogram) dan dibandingkan dengan target; perangkat keras, laju, dan durasi dicantumkan | T-307 |
| [ ] | T-502 | Build rilis: Linux x86_64 dan arm64, macOS arm64, image container minimal | DIST-01, DIST-02, DIST-08 | Artefak dan image bertanda tangan, dengan SBOM, terlampir di GitHub Release bertag | T-308, T-512 |
| [ ] | T-503 | README rilis: quickstart ≤ 5 langkah, batas klaim, dan hasil benchmark | DIST-03, bagian 10 | 3 orang baru berhasil mengirim request pertama dalam ≤ 10 menit | T-501, T-502 |
| [ ] | T-504 | Jalankan holdout sebelum rilis, dan catat setiap run | EVAL-01, EVAL-13 | Hasil holdout tercatat di `eval/results/holdout.md` (tanggal, commit, versi pack, hasil dengan interval Wilson); penurunan dibanding dev dijelaskan | T-314 |
| [ ] | T-505 | Wawancara lanjutan sampai total 5 sampai 10 calon pengguna, termasuk mencoba mode shadow dan laporan paparan | G5 | Ringkasan tertulis menentukan prioritas setelah rilis β, dan Q3, Q8, Q9 terjawab; waktu sampai laporan paparan pertama dan tugas "coba pack lalu jelaskan satu temuan" terukur (target bagian 9) | T-332, T-513 |
| [x] | T-509 | `SECURITY.md`, `CONTRIBUTING.md`, dan `CODEOWNERS` untuk repo OmniRail | DIST-05 | Ada jalur pelaporan kerentanan privat; folder `policy-packs/` wajib ditinjau pemilik | — |

---

## Setelah rilis β (P1, urutan ditentukan umpan balik)

| | ID | Task | Requirement | Selesai bila | Butuh |
| --- | --- | --- | --- | --- | --- |
| [ ] | T-203 | Cek ulang format Gemini API ke dokumentasi resmi | Q7 | Catatan perbedaan (bila ada) dengan blueprint tertulis | — |
| [ ] | T-204 | Adapter Gemini API | UP-08, UP-05, UP-06 | Sama seperti T-202, termasuk `assistant` → `model` dan `systemInstruction` | T-201, T-203 |
| [ ] | T-205 | Adapter OpenAI (passthrough), dan Anthropic bila belum dipilih di T-202 | UP-08, UP-05, UP-06 | Sama seperti T-202 | T-201 |
| [ ] | T-207 | Eksperimen format token: tingkat bertahan `<JENIS_n>`, variasinya, dan nilai pengganti sintetis di tiap provider | Q14, PII-04 | Hasil per provider tercatat dan diterbitkan; keputusan format token ditulis di catatan keputusan | T-202 |
| [ ] | T-312 | Metrik OpenTelemetry (OTLP) | AUD-04 | Metrik di PRD AUD-04 terlihat di collector lokal | T-307 |
| [ ] | T-315 | Entitas P1 `vehicle_plate` dan `ip_address`, mati secara default | PII-01b | Baris dev kedua entitas lulus saat diaktifkan; tidak memengaruhi metrik MVP saat mati | T-303 |
| [ ] | T-330 | Angka terucap: normalisasi kata bilangan satu digit sebelum validator, mati secara default | PII-11 | Baris dev angka terucap lulus saat `spoken_digits: true`; negatif angka terucap tidak tertangkap; tidak memengaruhi metrik MVP saat mati | T-303 |
| [ ] | T-331 | Detektor credentials ekosistem lokal tambahan | CRED-05 | Hanya layanan yang terverifikasi di T-326; baris dataset `kredensial` untuk tiap layanan ditambahkan dan lulus | T-305, T-326 |
| [ ] | T-333 | Rute berdasarkan sensitivitas (`on_sensitive`, `pii_action`, `local: true`) | ROUTE-01 s.d. ROUTE-03 | Kriteria terima PRD 7.16 lulus | T-307, T-311 |
| [ ] | T-335 | Aksi `mask` dan `block` per entitas, termasuk semantik shadow untuk `block` | PII-12 | `mask` menampilkan 4 digit terakhir kartu dan rekening; `block` menghasilkan 400 `omnirail_policy_violation` di enforce dan `would_block` di shadow | T-304, T-308 |
| [ ] | T-336 | Pemulihan toleran untuk variasi token, opt-in per rute | PII-13 | Variasi di PRD PII-13 dipulihkan hanya untuk token yang diterbitkan di request yang sama; dihitung terpisah di audit log | T-207, T-304 |
| [ ] | T-340 | Audit log tahan ubah: `prev_hash`, *checkpoint* bertanda tangan, dan `omnirail audit verify` | AUD-06 | Baris yang dihapus, disisipkan, atau diubah terdeteksi; test memakai log hasil set uji | T-311 |
| [ ] | T-341 | *Skeleton* confusables UTS #39 untuk deny-list dan kata kunci | POL-07 | Kata kunci yang ditulis dengan huruf Kiril yang mirip Latin tertangkap; tidak menambah false positive pada baris negatif dev | T-306 |
| [ ] | T-343 | Fuzzing (`cargo-fuzz`) untuk normalisasi Unicode dan parser request | EVAL-11 | Target fuzzing berjalan di CI terjadwal; tidak ada panic atau pelanggaran invarian | T-301, T-103 |
| [ ] | T-401 | Schema per rute di konfigurasi | JSON-01 | Rute tanpa schema tidak divalidasi | T-307 |
| [ ] | T-402 | Perbaikan sintaks lokal | JSON-02 | Pagar markdown, koma ekstra, kurung yang tidak tertutup, dan kutip tunggal diperbaiki; test per kasus | T-401 |
| [ ] | T-403 | Urutan perbaiki → parse → pulihkan → validasi; `fail_mode.egress` | JSON-03, JSON-04 | Kriteria terima PRD 7.8 lulus | T-402, T-304 |
| [ ] | T-404 | Set uji JSON rusak dan metriknya di `omnirail eval` | Bagian 9 | Persentase JSON valid setelah perbaikan tercatat | T-403, T-313 |
| [ ] | T-506 | Tampilan uji disajikan binary: konfigurasi `playground` (enabled, admin_keys, allowed_routes, datasets), kunci admin terpisah, berkas halaman T-507 tertanam dengan CSP | PG-04, PG-05 | Default 404; bukan loopback tanpa `admin_keys` gagal start; kunci aplikasi mendapat 403 `omnirail_admin_required` | T-334, T-507 |
| [ ] | T-511 | Benchmark terbuka: terbitkan split `dev` dengan kartu dataset, lisensi, dan skor alat lain | DIST-07, Q15 | Dataset publik bisa diunduh; holdout tidak ikut; skor Tahap 0 dan OmniRail tercantum | T-004, T-007, T-314 |
| [ ] | T-601 | Kirim ke provider dari tab Coba: tampilan berdampingan teks bertoken, jawaban provider, dan jawaban setelah dipulihkan; dibatasi `allowed_routes` | PG-08 | Rute di luar daftar ditolak; nilai asli tidak pernah dikirim ke provider | T-506 |
| [ ] | T-602 | Bandingkan `enforce` dan `shadow` dalam satu tampilan | PG-09 | Perbedaan keputusan per aturan terlihat untuk teks yang sama | T-507 |
| [ ] | T-603 | Override entitas sementara | PG-10 | Override tidak tersimpan, ditandai jelas, dan menghasilkan hash kebijakan sementara | T-507 |
| [ ] | T-604 | Tab Evaluasi: metrik per entitas, selisih dengan baseline, kasus gagal yang bisa disaring, unduh JSON/Markdown | PG-11 | Hasil sama dengan `omnirail eval` untuk dataset dan pack yang sama | T-313, T-506 |
| [ ] | T-605 | Kunci holdout di tab Evaluasi | PG-12 | Membuka holdout butuh konfirmasi dan tercatat di audit log | T-604 |
| [ ] | T-606 | Backlog P1 lain dari PRD: `GET /v1/models` (API-05), ekspor laporan untuk auditor (REP-03), reload konfigurasi via SIGHUP (CFG-08), deteksi secret entropi tinggi (CRED-04), contoh pemasangan di depan LiteLLM (DIST-04), `response_format` dari klien dan retry JSON (JSON-05, JSON-06), entitas kustom (PII-08) | API-05, REP-03, CFG-08, CRED-04, DIST-04, JSON-05, JSON-06, PII-08 | Dipecah menjadi task sendiri saat diprioritaskan | — |

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
| 11 Nov 2026 | Pemeriksa dataset (T-009) dijalankan di CI: 3.370 baris, 0 error. Lima peringatan adalah nomor telepon kantor `(021) …` yang sengaja ditandai `cakupan_mvp = tidak`. Pemeriksa hanya memvalidasi bentuk label, bukan menyetel aturan, sehingga boleh membaca holdout. T-509 selesai: `SECURITY.md` (pelaporan privat lewat GitHub), `CONTRIBUTING.md`, `.github/CODEOWNERS` (termasuk `policy-packs/` dan `eval/`) |
| 11 Nov 2026 | PRD v1.6: MVP dipecah menjadi rilis α (periksa: inti deteksi, `inspect`, `eval`, `scan`, demo WASM) dan rilis β (proxy). Validasi JSON, OpenTelemetry, adapter kedua dan ketiga, serta tampilan uji yang disajikan binary turun ke P1. Baru: pseudo-streaming (T-108), konteks lintas pesan (T-319), `scan` (T-320), laporan paparan (T-332), rute sensitivitas (T-333, P1), angka terucap (T-330, P1), credentials lokal (T-326, T-331), eksperimen format token (T-207), benchmark terbuka (T-511). Provider cloud pertama dipilih dari wawancara rilis α (T-513). Dataset v0.6 (T-010): 2.506 baris dev dan 1.072 holdout |
| 11 Nov 2026 | **Kriteria keputusan Tahap 0 (T-003).** Angka mutu dihitung di split dev untuk entitas `nik`, `kk`, `credit_card`, `bpjs`, dan `bank_account` (bentrok 16 digit dan konteks wajib), membandingkan prototipe referensi (T-011) dengan Presidio + regex sederhana (T-004). **(A) Mutu:** prototipe unggul ≥ 10 poin precision rata-rata, **atau** false positive pada baris negatif ≤ setengah Presidio, dengan recall tidak turun lebih dari 2 poin. **(B) Celah proxy (T-005):** LiteLLM + Presidio punya ≥ 2 dari empat celah ini: pemulihan token gagal di jalur Anthropic; tidak ada blokir kunci Midtrans, Xendit, atau token bot Telegram tanpa kode kustom; tidak ada audit log dengan hash kebijakan; tidak ada mode shadow yang setara. **Lanjut** bila A dan B terpenuhi. **Pivot** bila A terpenuhi tetapi B tidak: inti deteksi (Tahap 1 dan 2) dikirim sebagai recognizer Presidio atau plugin LiteLLM, dan proxy (Tahap 3 dan 4) dibatalkan. **Berhenti** bila selisih precision < 5 poin dan false positive tidak membaik berarti; dataset tetap diterbitkan sebagai benchmark (DIST-07). **Zona abu-abu** (selisih 5 sampai 10 poin): kerjakan rilis α, yang dipakai di jalur lanjut maupun pivot, lalu putuskan proxy setelah wawancara T-513 |
| 11 Nov 2026 | PII-03 diperjelas: kunci token memakai nilai yang dinormalisasi per jenis. Ditambah PII-12 (`mask`, `block`, P1) dan PII-13 (pemulihan toleran, P1), serta task T-011, T-335, T-336. Pembangkit baris v0.6 disimpan di `eval/tools/bangkitkan_v06.py` dan dicek di CI; baris v0.1 s.d. v0.5 masih tanpa pembangkit (T-008 tetap terbuka) |
| 11 Nov 2026 | **Tambahan kriteria T-003 (PRD v1.7, EVAL-09).** Semua angka Tahap 0 dilaporkan dengan interval Wilson 95%. "Unggul" berarti selisihnya juga bermakna secara statistik: recall dan false positive dibandingkan per baris dengan uji McNemar eksak (p < 0,05), pada gabungan lima entitas yang disebut di kriteria. Alasannya, interval per entitas dengan ukuran dataset sekarang masih sekitar ±5 poin (Landasan metode bagian 1) |
| 11 Nov 2026 | Landasan metode ditulis di `docs/LANDASAN_METODE.md`, dengan rujukan yang dicek lewat pencarian web. Target false positive ≤ 0,02 dinilai pada gabungan baris negatif. Ditambah task T-012 dan T-013 (selesai), T-337 s.d. T-343, dan T-514 |
| 11 Nov 2026 | Rujukan di `docs/LANDASAN_METODE.md` dibatasi pada terbitan lima tahun terakhir (akhir 2021 s.d. 2026), atas permintaan pemilik. Metode klasik (Wilson, McNemar, kappa Cohen, Luhn) tetap dipakai, dengan rujukan karya terbaru yang menerapkannya. Pengecualian: RFC 8785 (2020) tetap dipakai untuk `policy_hash` karena belum ada spesifikasi pengganti |
| 11 Nov 2026 | **T-004 dan T-011 selesai** (`eval/results/README.md`). Pada gabungan lima entitas T-003 di dev, prototipe OmniRail: recall 1,000, precision 1,000, false positive 0,000; Presidio + regex sederhana: recall 0,846, precision 0,738, false positive 0,286. McNemar: 80 butir recall hanya benar di prototipe, 0 sebaliknya (p < 10⁻²³). **Kriteria (A) terpenuhi di dev**, dengan catatan: angka prototipe optimistis karena dataset dan prototipe berasal dari spesifikasi dan penyusun yang sama, dan baseline Presidio sengaja tanpa validator. Kriteria (B) menunggu T-005, jadi T-006 belum diputuskan. Temuan tambahan: recognizer kartu bawaan Presidio tidak mengenali Mastercard seri 2, dan 29 dari 33 email yang dilewatkan Presidio berdomain `.test` (artefak dataset) |
| 11 Nov 2026 | Dari T-011: dua aturan baru di PRD v1.7.2 (seri jarak konteks dimenangkan kata konteks sebelum nilai; kata konteks tidak wajib untuk `phone_id`), serta pencocokan akhiran `-nya`/`-ku`/`-mu` |
| 11 Nov 2026 | **T-005 selesai** (`eval/results/t005-litellm.md`, LiteLLM 1.109.0). Kriteria (B): celah 2, 3, dan 4 ada; celah 1 tidak (pemulihan di jalur Anthropic berjalan dengan `presidio_filter_scope: input`). Temuan tambahan: dengan konfigurasi default, pemulihan dibatalkan oleh penyamaran keluaran; nilai yang sama mendapat token berbeda (PII-03); token yang ditulis pengguna ikut dipulihkan (PII-04); credentials lokal lolos ke provider; `hide-secrets` hanya di paket enterprise. Overhead p50 sekitar 23 ms (LiteLLM sendiri 14 ms). **Kriteria (A) dan (B) terpenuhi, sehingga menurut T-003 hasilnya mengarah ke "lanjut".** T-006 menunggu keputusan pemilik produk |
| 11 Nov 2026 | **Keputusan Tahap 0 (T-006): lanjut.** Kriteria (A) dan (B) T-003 terpenuhi (`eval/results/README.md`). Titik periksa kedua di T-513, setelah rilis α: beralih ke **pivot** (Tahap 3 dan 4 diganti plugin untuk LiteLLM atau Presidio) bila sebagian besar calon pengguna sudah memakai gateway lain dan tidak mau menambah proxy, **dan** yang mereka minta hanya deteksi, bukan blokir credentials, mode shadow, atau audit. Beralih ke **berhenti** bila holdout atau tinjauan label (T-007) menunjukkan keunggulan deteksi jauh lebih kecil dari angka dev, **dan** wawancara tidak menemukan kebutuhan blokir credentials |
| 11 Nov 2026 | T-101 selesai: workspace Rust (`omnirail-core` tanpa I/O dan `#![forbid(unsafe_code)]`, `omnirail` sebagai CLI), toolchain dipin ke 1.97.0, edisi 2024, CI menjalankan fmt, clippy, test, build `wasm32-unknown-unknown`, pengecekan bahwa `omnirail-core` tidak bergantung pada axum atau tokio, `cargo deny`, dan `cargo audit` |
| 11 Nov 2026 | **T-007: perangkat dan pra-tinjauan siap, menunggu penilai manusia.** Sampel 120 baris dev dan formulir buta ada di `eval/tinjauan/`, dengan penghitung kesepakatan dan kappa di `eval/tools/tinjau_label.py`. Pra-tinjauan oleh asisten AI memberi κ = 0,989; satu-satunya perbedaan (D1234) adalah soal konvensi, bukan label keliru. Konvensi itu kini dipertegas di panduan penilai. Pra-tinjauan ini **tidak** memenuhi T-007, karena penilainya memakai spesifikasi yang sama dengan penyusun dataset |
| 11 Nov 2026 | **T-008 ditutup tanpa dikerjakan penuh.** Pembangkit asli v0.1 s.d. v0.5 tidak tersedia. Membangkitkan ulang dataset akan mengubah isinya dan membatalkan hasil T-004 dan T-005. Sebagai gantinya, baris v0.6 sudah punya pembangkit yang dicek di test, dan setiap tambahan baris ke depan wajib disertai pembangkitnya (`eval/README.md`, bagian "Menambah baris") |
| 11 Nov 2026 | **Tahap 0 selesai, kecuali T-007** yang hanya bisa diselesaikan oleh orang kedua. T-007 tidak menghalangi Tahap 1, tetapi wajib selesai sebelum baseline dan ambang CI ditetapkan (T-314) dan sebelum benchmark diterbitkan (T-511) |
