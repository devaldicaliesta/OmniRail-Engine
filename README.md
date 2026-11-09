# OmniRail Engine

Proxy open-source yang berdiri di depan LLM. OmniRail menyamarkan data pribadi, menegakkan kebijakan, dan memvalidasi output, dalam satu binary tanpa GPU.

> **Status: tahap desain.** Belum ada kode. Repo ini berisi [PRD MVP](docs/PRD.md) dan blueprint v1.1, yang belum divalidasi: perbandingan dengan LiteLLM dan Presidio belum dilakukan, policy pack belum ditinjau staf kepatuhan, dan beberapa pasal UU PDP belum dicek ke naskah resmi.

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

## Scope MVP

| Area | Masuk MVP |
| --- | --- |
| API klien | `POST /v1/chat/completions` (format OpenAI), non-streaming, teks saja |
| Upstream | Anthropic Messages API, Gemini API, OpenAI (passthrough), dan Ollama untuk uji lokal |
| PII | Regex + validasi, tokenisasi reversibel per request; credentials diblokir, tidak ditokenisasi |
| Kebijakan | Deny-list pola, batas panjang input, blokir kata kunci, `allowed_providers` |
| Output | Validasi JSON schema + perbaikan sintaks |
| Operasional | Config YAML, API key proxy, log terstruktur, OpenTelemetry, `fail_mode` per rute, audit log berisi versi dan hash kebijakan |
| Distribusi | Satu binary, `omnirail eval`, benchmark latensi, tampilan uji satu halaman |

Yang ditunda: streaming, tool call, gambar, NER untuk nama dan alamat, classifier injection, fallback antar-provider, dan dasbor.

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

0. **Validasi.** Bandingkan dengan LiteLLM + Presidio pada set uji berbahasa Indonesia, lalu putuskan lanjut, pivot, atau berhenti.
1. **Kerangka proxy.** Endpoint non-streaming, upstream Ollama, config YAML.
2. **Jalur provider.** Adapter Anthropic, lalu Gemini, lalu OpenAI.
3. **PII tokenisasi.** Entitas Indonesia, deteksi credentials, `omnirail eval`, dan baseline recall/precision.
4. **Validasi JSON.** Schema check dan perbaikan sintaks.
5. **Rilis awal.** README dengan batas klaim, benchmark latensi, tampilan uji, dan wawancara calon pengguna.

## Dokumen

- [PRD MVP](docs/PRD.md): acuan scope, requirements, kriteria terima, dan tahapan MVP. Bila berbeda dengan blueprint, PRD yang berlaku.
- [Rincian task](docs/TASKS.md): task per tahap dengan kriteria selesai.
- [Dataset uji](eval/README.md): set uji PII dan credentials berbahasa Indonesia (draf).

Blueprint v1.1 (latar belakang, pemetaan regulasi, dan arah setelah MVP) tersedia dalam tiga format:

- [Markdown](docs/OmniRail_Engine_Blueprint_v1.1.md)
- [PDF](docs/OmniRail_Engine_Blueprint_v1.1.pdf)
- [DOCX](docs/OmniRail_Engine_Blueprint_v1.1.docx)

## Lisensi

Copyright 2026 devaldi caliesta

Dilisensikan di bawah [Apache License 2.0](LICENSE).
