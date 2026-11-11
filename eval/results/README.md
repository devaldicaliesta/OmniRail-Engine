# Hasil evaluasi

Hasil `eval/tools/evaluasi.py` pada split **dev** (dataset v0.6). Holdout belum pernah dijalankan (PRD EVAL-13).

| Berkas | Isi |
| --- | --- |
| `dev-prototipe.{json,md}` | Prototipe referensi OmniRail (T-011): regex + validator + kata konteks sesuai PRD 7.10 |
| `dev-presidio.{json,md}` | Baseline Presidio (T-004): recognizer bawaan + regex Indonesia sederhana tanpa validator |
| `banding-prototipe-presidio.md` | Uji McNemar eksak per butir antara keduanya |

Berkas JSON memuat metrik dengan interval Wilson 95%, hasil per butir (untuk uji berpasangan), dan daftar kasus gagal. Nilai entitas tidak disimpan di JSON; hanya ID baris dan jenisnya.

## Ringkasan Tahap 0, bagian mutu deteksi (11 November 2026)

Gabungan lima entitas kriteria T-003 (`nik`, `kk`, `credit_card`, `bpjs`, `bank_account`):

| Ukuran | Prototipe OmniRail | Presidio + regex sederhana | Uji McNemar |
| --- | --- | --- | --- |
| Recall | 1,000 (0,993–1,000) | 0,846 (0,812–0,874) | 80 butir hanya benar di prototipe, 0 sebaliknya; p < 10⁻²³ |
| Precision | 1,000 (0,993–1,000) | 0,738 (0,701–0,771) | — |
| False positive (baris negatif) | 0,000 (0,000–0,009) | 0,286 (0,244–0,332) | Semua baris negatif: 171 lawan 1; p < 10⁻⁴⁹ |

Untuk semua entitas P0: recall 0,999 lawan 0,864, precision 0,995 lawan 0,813, false positive 0,005 lawan 0,173.

**Terhadap kriteria (A) T-003, angka dev memenuhi syarat "unggul":** precision +26 poin, false positive jauh di bawah setengahnya, recall tidak turun, dan selisihnya bermakna menurut McNemar. Kriteria (B), yaitu celah LiteLLM sebagai proxy, menunggu T-005. **Keputusan T-006 belum bisa diambil.**

### Asal selisih, dari daftar kasus gagal Presidio

| Penyebab | Contoh | Butir |
| --- | --- | --- |
| Tanpa validator struktur, angka 16 digit apa pun ditandai NIK | nomor pesanan, kode voucher | 110 salah tandai `nik` |
| Skor Luhn bawaan Presidio mengalahkan kata konteks | "NIK saya 5171…" dilabeli kartu (kasus D050 di PRD) | sebagian dari 46 salah tandai `credit_card` |
| Recognizer kartu bawaan tidak mengenali Mastercard seri 2 | `2221-7821-3003-1109` | 14 kartu terlewat |
| Tanpa konteks lintas pesan | "Boleh minta nomor rekeningnya?" → "7511563447" | 66 butir terlewat di baris multi-pesan |
| Kata konteks berimbuhan atau berupa singkatan tidak cocok persis | "rekeningnya", "a/n", "no_kk" | sebagian `bank_account` dan `kk` terlewat |
| "Hari lahir Pancasila, 1 Juni 2025" | tidak ada pengecualian frasa | 22 salah tandai `birth_date` |

### Catatan yang membatasi kesimpulan

1. **Angka prototipe optimistis.** Dataset dan prototipe disusun oleh orang yang sama dari spesifikasi yang sama (PRD 7.10), dan prototipe disetel di dev. Angka 0,99+ bukan perkiraan mutu di trafik nyata. Perkiraan yang lebih jujur datang dari holdout (sekali sebelum rilis, EVAL-13), tinjauan label orang kedua (T-007), dan wawancara.
2. **Baseline Presidio sengaja sederhana.** Pengguna Presidio yang mahir bisa menambah validator (`validate_result`), kata konteks, dan aturan prioritas sendiri. Selisih di atas mengukur **nilai dari validator dan aturan Indonesia yang sudah jadi**, bukan batas kemampuan Presidio. Ini justru relevan untuk jalur **pivot** (paket recognizer untuk Presidio).
3. **Artefak dataset pada email.** 29 dari 33 email yang dilewatkan Presidio memakai domain `.test`, yang ditolak validator TLD Presidio. Tanpa domain `.test`, recall email Presidio 0,956 (0,892–0,983) dan prototipe 1,000 (0,959–1,000). Domain `.test` tetap dipakai karena aman untuk data rekaan, tetapi metrik email perlu dibaca dengan catatan ini.
4. **Kasus yang tetap gagal di prototipe** sesuai dokumentasi dataset: "Nomor pesanan 0857…" (negatif sulit `phone_id`, 5 baris) dan email yang menempel dengan kata "mailto" hasil voice-to-text (D1298).

### Dua aturan baru dari prototipe (sudah dicatat di PRD v1.7.2)

- **Seri jarak konteks (PII-07):** bila dua kata konteks sama dekatnya, yang **sebelum** nilai menang ("No. KK 7250…, NIK kepala keluarga 5245…").
- **Kata konteks `phone_id`** (`hp`, `telp`, `wa`, dan seterusnya) tidak wajib, tetapi dipakai untuk menentukan jenis. Tanpa ini, "telp 0811… a.n. Pak Joko" dilabeli rekening.

## Mengulang hasil

```bash
python3 eval/tools/evaluasi.py jalan prototipe
```

```bash
python3 -m venv .venv-presidio
```

```bash
.venv-presidio/bin/pip install presidio-analyzer==2.2.366
```

```bash
.venv-presidio/bin/python eval/tools/evaluasi.py jalan presidio
```

```bash
python3 eval/tools/evaluasi.py banding prototipe presidio
```

Baseline Presidio tidak mengunduh model spaCy maupun daftar domain dari internet. Waktu, commit, dan konfigurasi tercatat di bagian `meta` setiap berkas JSON.
