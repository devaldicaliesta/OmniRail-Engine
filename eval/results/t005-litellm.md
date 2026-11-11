# T-005: LiteLLM + guardrail Presidio sebagai proxy

Diuji 11 November 2026 dengan LiteLLM 1.109.0, presidio-analyzer dan presidio-anonymizer 2.2.366. Data mentah ada di `t005-litellm.json`; cara mengulang ada di bagian akhir.

## Susunan uji

- LiteLLM proxy sungguhan (`litellm --config`), satu worker, guardrail `presidio` dengan `mode: pre_call`, `output_parse_pii: true`, `presidio_language: id`.
- Layanan Presidio lokal dengan recognizer yang sama seperti baseline T-004, ambang skor 0,4.
- Server tiruan (mock) OpenAI Chat Completions dan Anthropic Messages, dengan jeda tetap 50 ms. Server ini mengembalikan pesan pengguna apa adanya, sehingga terlihat apakah token dipulihkan. Streaming dikirim per 7 karakter, jadi token sengaja terpotong di tengah antar-potongan.
- Tanpa jaringan keluar dan tanpa kunci API sungguhan. Semua credentials adalah data rekaan.

## Hasil fungsi

Input: `Email saya budi@example.com dan budi@example.com, NIK 3273011503900001`.

| Skenario | Konfigurasi default | Dengan `presidio_filter_scope: input` |
| --- | --- | --- |
| OpenAI, non-streaming | Tidak dipulihkan | Dipulihkan |
| Anthropic lewat `/v1/chat/completions` | Tidak dipulihkan | Dipulihkan |
| Anthropic native `/v1/messages` | Tidak dipulihkan | Dipulihkan |
| OpenAI, `stream: true` | Tidak dipulihkan | Dipulihkan (jawaban di-buffer) |
| Nilai asli sampai ke provider | Tidak | Tidak |

Yang diterima provider di semua skenario: `Email saya <EMAIL_ADDRESS_1> dan <EMAIL_ADDRESS_2>, NIK <ID_NIK_3>`.

**Konfigurasi default membatalkan pemulihan.** Nilai default `presidio_filter_scope` adalah `both`. Akibatnya, jawaban yang sudah dipulihkan oleh `output_parse_pii` langsung disamarkan lagi oleh callback keluaran, sehingga aplikasi menerima `<EMAIL_ADDRESS>`. Hal ini tidak terlihat dari nama opsinya, dan baru ketahuan dari log debug dan kode `guardrail_initializers.py`.

**Bug jalur Anthropic ([BerriAI/litellm#22821](https://github.com/BerriAI/litellm/issues/22821)) tidak muncul di versi ini.** Pemulihan berjalan di `/v1/messages` maupun lewat `/v1/chat/completions`, termasuk streaming. Ada PR perbaikan yang menyebut issue itu ([BerriAI/litellm#22882](https://github.com/BerriAI/litellm/pull/22882), [BerriAI/litellm#24291](https://github.com/BerriAI/litellm/pull/24291)). Uji ini memakai mock, bukan API Anthropic sungguhan.

## Celah yang ditemukan

| Celah | Bukti | Relevan untuk OmniRail |
| --- | --- | --- |
| Nilai yang sama mendapat token berbeda | `budi@example.com` dua kali menjadi `<EMAIL_ADDRESS_1>` dan `<EMAIL_ADDRESS_2>`; model melihat dua orang | PII-03 |
| Token yang ditulis pengguna bertabrakan dengan token terbitan | Input `Balas ke <EMAIL_ADDRESS_1> saja, jangan ke budi@example.com` sampai di provider sebagai dua `<EMAIL_ADDRESS_1>`, dan keduanya dipulihkan menjadi `budi@example.com` | PII-04 |
| Credentials tidak diblokir | Kunci Midtrans, Xendit, token bot Telegram, connection string Postgres, dan kunci AWS (contoh dokumentasi) sampai ke provider tanpa diubah | CRED-01 |
| Deteksi secret hanya di paket enterprise | Guardrail `hide-secrets` ada di `litellm_enterprise` (lisensi komersial), hanya meredaksi menjadi `[REDACTED]` tanpa memblokir, dan daftar pluginnya tidak memuat Midtrans maupun Xendit (dibaca dari kode, tidak dijalankan) | CRED-01, CRED-02 |
| Audit log tanpa hash kebijakan | Log guardrail per request mencatat nama guardrail, status, dan jumlah entitas yang disamarkan. Versi kebijakan ada di mesin kebijakan berbasis database, tetapi tidak ada hash kebijakan efektif per request | AUD-02 |
| Tanpa mode shadow untuk Presidio | Mode `logging_only` hanya menyamarkan isi log. Tidak ada pencatatan "seharusnya diblokir" untuk guardrail Presidio; mode `monitor` hanya ada di beberapa guardrail lain | POL-04 |

## Overhead latensi

Beban open-loop 10 request per detik selama 20 detik (200 request), input 946 karakter, jeda mock 50 ms. Latensi dihitung dari jadwal kirim.

| Jalur | p50 | p99 | Overhead p50 |
| --- | --- | --- | --- |
| Langsung ke mock | 54,9 ms | 59,6 ms | — |
| LiteLLM tanpa guardrail | 69,3 ms | 85,1 ms | 14,4 ms |
| LiteLLM + Presidio | 78,1 ms | 86,6 ms | 23,2 ms |

Guardrail Presidio menambah sekitar 9 ms di atas LiteLLM, karena ada dua panggilan HTTP (`/analyze` dan `/anonymize`) per pesan. Target overhead OmniRail di PRD adalah p50 ≤ 5 ms untuk input 5 ribu karakter.

Catatan ukuran: layanan Presidio berjalan di proses Python yang sama dengan pembangkit beban, dan LiteLLM memakai satu worker. Dengan 200 sampel, p99 hanya ditentukan oleh dua sampel terburuk, jadi angka p99 kasar. Angka ini bukan benchmark resmi; yang bisa dipegang adalah urutan besarnya (puluhan milidetik).

## Terhadap kriteria (B) T-003

| Celah di kriteria | Hasil |
| --- | --- |
| 1. Pemulihan token gagal di jalur Anthropic | **Tidak**, di LiteLLM 1.109.0 dengan `presidio_filter_scope: input`. Dengan konfigurasi default, pemulihan gagal di **semua** jalur |
| 2. Tidak ada blokir kunci Midtrans, Xendit, atau token bot Telegram tanpa kode kustom | **Ya** |
| 3. Tidak ada audit log dengan hash kebijakan | **Ya**, dengan catatan: ada log guardrail per request dan versi kebijakan berbasis database |
| 4. Tidak ada mode shadow yang setara | **Ya** untuk guardrail Presidio |

Tiga dari empat celah terpenuhi, jadi **kriteria (B) terpenuhi secara tertulis**. Celah 3 dan 4 bisa ditutup tim yang bersedia menulis callback sendiri di LiteLLM. Yang paling kuat adalah celah 2, ditambah dua celah tokenisasi (PII-03, PII-04) yang tidak ada di daftar kriteria.

## Mengulang

```bash
python3 -m venv .venv-litellm
```

```bash
.venv-litellm/bin/pip install 'litellm[proxy]==1.109.0' presidio-analyzer==2.2.366 presidio-anonymizer==2.2.366 flask
```

```bash
.venv-litellm/bin/python eval/tools/uji_litellm.py
```
