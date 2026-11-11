# OmniRail Engine

[![CI](https://github.com/devaldicaliesta/OmniRail-Engine/actions/workflows/ci.yml/badge.svg)](https://github.com/devaldicaliesta/OmniRail-Engine/actions/workflows/ci.yml)

Proxy open-source yang berdiri di depan LLM. OmniRail menyamarkan data pribadi, menegakkan kebijakan, dan memvalidasi output, dalam satu binary tanpa GPU.

> **Status: Tahap 0 selesai, keputusan lanjut.** Kerangka workspace Rust sudah ada, tetapi belum ada fungsi produk. Repo ini berisi [PRD MVP v1.7.3](docs/PRD.md), dataset uji, dan blueprint v1.1, yang belum divalidasi: perbandingan dengan LiteLLM dan Presidio belum dilakukan, policy pack belum ditinjau staf kepatuhan, dan beberapa pasal UU PDP belum dicek ke naskah resmi.

## Apa itu OmniRail

OmniRail **bukan** pengganti gateway LLM. Ia lapisan guard yang bisa berdiri sendiri atau dipasang di depan gateway lain. Aplikasi cukup mengganti `base_url` ke OmniRail.

```
Aplikasi ──► OmniRail ──► Provider LLM (Anthropic, Gemini, OpenAI, Ollama)
             │ request:  samarkan PII, blokir credentials, cek kebijakan
             │ response: validasi JSON, kembalikan token PII ke nilai asli
```

- **Deterministik dulu.** Deteksi berbasis regex dan validator (Luhn, format NIK), dengan footprint kecil dan overhead latensi yang diukur lalu dipublikasikan.
- **Konteks Indonesia.** NIK, nomor KK, NIP, NPWP, paspor, BPJS, nomor rekening, nomor +62, dan tanggal lahir, dengan validator struktur (misalnya kode provinsi dan tanggal lahir pada NIK). Ditambah deteksi kunci payment gateway lokal (Midtrans, Xendit).
- **Tokenisasi reversibel.** Contohnya `<EMAIL_1>`, yang hanya hidup di memori selama satu request.
- **Mode shadow.** Kebijakan dicatat tanpa memblokir, supaya bisa diuji sebelum diberlakukan.
- **Policy pack.** Bundel aturan per sektor (`id-general`, `id-fintech`, `id-ecommerce`, `id-instansi`), dan setiap pack wajib punya tes.
- **Laporan paparan data.** `omnirail report` merangkum audit log: jenis data pribadi apa yang terkirim ke provider mana, dari aplikasi mana, tanpa memuat nilainya.
- **Paham percakapan.** Kata konteks dicari juga di pesan sebelumnya ("Boleh minta nomor rekeningnya?" → "1234567890"), dan angka yang diucapkan di transkrip panggilan ("nol delapan satu dua …") menyusul (P1).
- **Pakai di luar proxy.** `omnirail scan` memeriksa log, fixture tes, dan dataset di repo atau CI, dan demo web memeriksa teks langsung di browser tanpa server.

## Scope MVP

MVP dikirim dalam dua rilis (PRD bagian 11).

| Area | Rilis α (periksa) | Rilis β (proxy, rilis publik pertama) |
| --- | --- | --- |
| Deteksi | Regex + validator struktur, kata konteks lintas pesan, tokenisasi reversibel, credentials, deny-list | Sama, dijalankan di jalur proxy |
| Antarmuka | CLI `omnirail inspect`, `eval`, `scan`; demo web WASM yang berjalan di browser | `POST /v1/chat/completions` (format OpenAI), teks saja, `stream: true` sebagai pseudo-streaming |
| Upstream | — | Ollama dan satu provider cloud (Anthropic, kecuali wawancara menunjukkan lain) |
| Kebijakan | Pack `id-general` bertes | Mode `enforce` dan `shadow`, `allowed_providers`, `fail_mode` per rute |
| Operasional | Hook pre-commit dan langkah CI untuk `scan` | Config YAML, API key proxy, audit log dengan versi dan hash kebijakan, `omnirail report` |

Yang ditunda setelah rilis β: validasi JSON, provider cloud lain, rute berdasarkan sensitivitas (request berisi data pribadi spesifik diarahkan ke model lokal), angka terucap, OpenTelemetry, tampilan uji dari binary, streaming sejati, tool call, gambar, NER untuk nama dan alamat, classifier injection, fallback antar-provider, dan dasbor.

## Contoh konfigurasi (rencana)

```yaml
version: "1.1"
mode: shadow               # enforce | shadow
policy_pack: id-general

upstream:
  providers:
    anthropic: { api_key: "${ANTHROPIC_API_KEY}" }
    ollama:    { base_url: "http://localhost:11434" }

ingress:
  pii:
    action: tokenize       # tokenize | redact
    entities: [email, phone_id, credit_card, nik, kk, nip, npwp, passport_id, bpjs, bank_account, birth_date]
  credentials:
    action: block
  policy:
    allowed_providers: [anthropic, ollama]

fail_mode:
  ingress: closed
  egress: open

logging:
  store_raw_prompts: false
```

Contoh lengkap ada di bagian 4 blueprint.

## Batas klaim

- OmniRail mengurangi risiko tertentu, tetapi **tidak menjamin keamanan**. PII dengan format tak lazim dan secret tanpa pola bisa lolos.
- PII bebas-bentuk seperti nama dan alamat belum terdeteksi.
- Prompt injection hanya ditangani lewat deny-list, yang mudah dilewati.
- Lampiran dan gambar tidak diperiksa, dan tokenisasi berlaku per request, tidak lintas sesi.
- OmniRail **tidak mengklaim kepatuhan hukum apa pun**, termasuk UU 27/2022 tentang Pelindungan Data Pribadi dan panduan OJK. Kepatuhan tetap tanggung jawab pengguna.

## Tech stack

Rust (tokio, axum, reqwest), konfigurasi YAML, log terstruktur, dan OpenTelemetry. State hanya di memori per request, tanpa dependensi eksternal untuk MVP.

## Roadmap

0. **Validasi.** Bandingkan dengan LiteLLM + Presidio pada set uji berbahasa Indonesia, lalu putuskan lanjut, pivot, atau berhenti. *Selesai: lanjut.* Disusul **validasi lanjutan (Tahap 0.5)**: set uji dari penulis lain, pembanding Presidio yang adil, tinjauan label, dan tiga wawancara singkat sebelum Tahap 1 dikerjakan penuh.
1. **Inti deteksi (α).** `omnirail-core`, entitas Indonesia, credentials, pack bertes, `inspect`, `eval`, `scan`, dan baseline recall/precision.
2. **Rilis α.** Demo web WASM, binary CLI, dan wawancara pertama memakai demo.
3. **Kerangka proxy (β).** Endpoint format OpenAI dengan pseudo-streaming, adapter Ollama dan satu provider cloud.
4. **Alur proxy lengkap (β).** Mode shadow, audit log, dan laporan paparan data.
5. **Rilis β.** README dengan batas klaim, benchmark latensi, holdout, dan wawancara lanjutan.

## Dokumen

- [PRD MVP](docs/PRD.md): acuan scope, requirements, kriteria terima, dan tahapan MVP. Bila berbeda dengan blueprint, PRD yang berlaku.
- [Rincian task](docs/TASKS.md): task per tahap dengan kriteria selesai.
- [Hasil evaluasi Tahap 0](eval/results/README.md): prototipe referensi OmniRail dibandingkan dengan Presidio pada split dev, beserta batas kesimpulannya. Bisa diulang di Google Colab: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/devaldicaliesta/OmniRail-Engine/blob/main/notebooks/OmniRail_Tahap0_Colab.ipynb)
- [Landasan metode](docs/LANDASAN_METODE.md): paper dan standar yang mendasari evaluasi, deteksi, audit log, dan rilis, beserta status penerapannya.
- [Dataset uji](eval/README.md): set uji PII dan credentials berbahasa Indonesia (draf, v0.6), diperiksa otomatis di CI oleh `eval/tools/cek_dataset.py`, dengan [datasheet](eval/DATASHEET.md) yang menjelaskan asal-usul dan batasnya.
- [Panduan kontribusi](CONTRIBUTING.md) dan [kebijakan keamanan](SECURITY.md) (laporkan kerentanan secara privat, bukan lewat issue).

Blueprint v1.1 (latar belakang, pemetaan regulasi, dan arah setelah MVP) tersedia dalam tiga format:

- [Markdown](docs/OmniRail_Engine_Blueprint_v1.1.md)
- [PDF](docs/OmniRail_Engine_Blueprint_v1.1.pdf)
- [DOCX](docs/OmniRail_Engine_Blueprint_v1.1.docx)

## Lisensi

Copyright 2026 devaldi caliesta

Dilisensikan di bawah [Apache License 2.0](LICENSE).
