# OmniRail Engine — PRD MVP v1.3

| | |
| --- | --- |
| **Status** | Draf, menunggu tinjauan pemilik produk |
| **Tanggal** | 9 November 2026 |
| **Pemilik** | devaldi caliesta |
| **Sumber** | [Blueprint v1.1](OmniRail_Engine_Blueprint_v1.1.md) |
| **Lingkup** | MVP sampai rilis publik pertama (Tahap 0 s.d. 5) |

PRD ini menjadi acuan **apa yang dibangun dan kapan dianggap selesai** untuk MVP. Blueprint v1.1 tetap menjadi acuan latar belakang, pemetaan regulasi (bagian 6 dan 7), dan arah setelah MVP (bagian 13). Bila keduanya berbeda, PRD ini yang berlaku. Daftar perbedaannya ada di bagian 1.

---

## 1. Perubahan dari blueprint v1.1

Blueprint sudah kuat dari sisi posisi produk, batas klaim, dan konteks regulasi. Bagian yang diperbaiki di bawah ini adalah celah yang akan muncul saat implementasi atau yang bisa melemahkan klaim produk.

| # | Perubahan | Alasan |
| --- | --- | --- |
| 1 | **Tahap 0 (validasi) ditambahkan sebagai gerbang keputusan** sebelum menulis kode proxy | Blueprint menyebut perbandingan dengan LiteLLM + Presidio, tetapi tidak menaruhnya di roadmap. Tanpa gerbang ini, risiko membangun ulang yang sudah ada tidak pernah diuji |
| 2 | **Tokenisasi reversibel tidak lagi diklaim sebagai pembeda** | LiteLLM dengan guardrail Presidio sudah punya opsi `output_parse_pii` yang memulihkan token di jawaban (terkonfirmasi di dokumentasi LiteLLM; ada laporan bug pemulihan di jalur Anthropic, lihat Lampiran A). Pembeda yang dipegang: entitas Indonesia dengan validator struktur, eval terbuka berbahasa Indonesia, policy pack bertes, dan audit log dengan hash kebijakan |
| 3 | **Urutan alur request diubah:** credentials dan kebijakan dicek pada teks asli, **sebelum** penyamaran PII | Di diagram blueprint, PII disamarkan dulu lalu kebijakan dicek pada teks bertoken. Request yang pasti diblokir tidak perlu ditokenisasi, dan deteksi credentials harus melihat teks utuh |
| 4 | **Urutan alur response diubah:** perbaikan sintaks → parse → pemulihan token di dalam nilai string → validasi schema | Di blueprint, validasi JSON jalan sebelum pemulihan. Akibatnya schema dengan `format: email` atau `pattern` akan gagal pada `<EMAIL_1>`, dan pemulihan berbasis teks bisa merusak JSON bila nilai asli mengandung tanda kutip |
| 5 | **Semantik `mode: shadow` didefinisikan** (bagian 7.6) | Blueprint hanya menulis "catat tanpa memblokir". Tanpa definisi, mode shadow bisa diartikan meneruskan data mentah, termasuk credentials, ke provider |
| 6 | **Konflik pola 16 digit diselesaikan** dengan validator struktur NIK, Luhn + prefix untuk kartu, dan aturan prioritas | NIK, nomor kartu, NPWP format baru, dan nomor pesanan sama-sama bisa 16 digit. Regex `\b\d{16}\b` saja akan menghasilkan false positive tinggi, padahal ini risiko produk nomor dua di blueprint |
| 7 | **`bank_account` wajib punya kata konteks** | Nomor rekening tidak punya format atau checksum nasional. Tanpa kata konteks, setiap angka 10 sampai 16 digit akan tertangkap |
| 8 | **Kontrak error kompatibel OpenAI** dan **fitur yang belum didukung ditolak secara eksplisit** (`stream`, tool call, gambar) | Blueprint tidak mengatur apa yang terjadi saat klien mengirim `stream: true` atau gambar. Meneruskannya diam-diam berarti data tidak diperiksa |
| 9 | **Default aman untuk jaringan:** `listen` ke `127.0.0.1`, batas ukuran body, perbandingan kunci *constant-time*, dan tampilan uji mati secara default | Contoh blueprint memakai `0.0.0.0:8080`, sehingga proxy yang memegang kunci provider langsung terbuka ke jaringan |
| 10 | **Normalisasi Unicode** sebelum deny-list dan kata kunci dicocokkan | Deny-list mudah dilewati dengan huruf mirip atau karakter lebar-nol. Normalisasi menutup jalan pintas yang paling murah |
| 11 | **"Rute" didefinisikan sebagai alias model**, dengan schema JSON dan `fail_mode` per rute | Blueprint memakai satu `schema_file` global, padahal tiap fitur aplikasi biasanya punya bentuk output berbeda |
| 12 | **`policy_hash` dan isi audit log ditetapkan** (bagian 7.7) | Blueprint mewajibkan versi dan hash kebijakan di tiap request, tetapi tidak mendefinisikan cara menghitung hash atau field yang dicatat |
| 13 | **Target awal ditulis sebagai hipotesis** yang direvisi setelah baseline | Blueprint menolak menulis target. Tanpa angka, kriteria selesai tiap tahap tidak bisa diperiksa. Angka di bagian 9 sengaja ditandai sementara |
| 14 | **Dataset uji `uji_pii_id.csv` dijadikan deliverable P0** | Dataset ini dirujuk di blueprint, tetapi belum ada di repo |
| 15 | **Entitas ditambah:** `nip`, `kk`, `passport_id`, `bpjs`, `birth_date` (P0), `vehicle_plate`, `ip_address` (P1), serta kunci Midtrans, Xendit, dan token bot Telegram | Blueprint hanya memuat enam entitas berformat tetap. Dokumen identitas Indonesia lain (NIP, KK, paspor, BPJS) sama murahnya untuk dideteksi dan memperkuat pembeda "konteks Indonesia". Kunci payment gateway lokal relevan untuk fintech, dan credentials adalah kekhawatiran utama di wawancara pertama |

---

## 2. Ringkasan

OmniRail adalah proxy open-source di depan LLM. Ia menyamarkan data pribadi dan memblokir credentials sebelum request keluar, menegakkan kebijakan sederhana, lalu memvalidasi dan memulihkan jawaban. Semuanya dalam satu binary Rust tanpa GPU. Aplikasi cukup mengganti `base_url` ke OmniRail.

MVP membuktikan satu hal: **request bisa melewati proxy, datanya tersamarkan, dan jawaban dari provider kembali utuh dan valid, dengan overhead yang terukur.**

## 3. Masalah

Tim di Indonesia yang memakai LLM API (Claude, Gemini, ChatGPT) mengirim prompt yang sering berisi data pelanggan: NIK, nomor HP, email, nomor kartu, nomor rekening, dan kadang credentials yang tertempel di potongan kode atau log. Data itu keluar ke provider di luar negeri tanpa penyaringan.

- **Siapa yang terdampak:** engineer yang membangun fitur LLM, dan penanggung jawab keamanan atau pelindungan data di organisasi yang sama.
- **Dampak bila dibiarkan:** kebocoran credentials yang bisa langsung disalahgunakan, data pribadi spesifik (termasuk data keuangan) terkirim ke luar negeri tanpa kontrol teknis, dan tidak ada jejak yang bisa ditunjukkan ke auditor. UU 27/2022 dan peraturan pelaksananya menaikkan taruhan ini, meskipun OmniRail tidak mengklaim kepatuhan.
- **Kenapa solusi yang ada belum cukup (hipotesis, diuji di Tahap 0):** alat umum seperti Presidio dirancang untuk entitas berbahasa Inggris. Entitas Indonesia butuh recognizer kustom tanpa validator struktur dan tanpa set uji berbahasa Indonesia, sehingga false positive dan recall-nya tidak terukur.
- **Bukti saat ini:** baru satu wawancara, dengan pembangun sendiri dalam konteks fintech. Kekhawatiran utamanya adalah credentials. Ini hipotesis, belum validasi.

## 4. Tujuan

| # | Tujuan | Jenis | Cara mengetahui berhasil |
| --- | --- | --- | --- |
| G1 | Data pribadi Indonesia berformat tetap dan credentials tidak sampai ke provider | Pengguna | Recall dan tingkat blokir pada set uji memenuhi target bagian 9 |
| G2 | Integrasi tanpa mengubah kode aplikasi selain `base_url` dan kunci | Pengguna | SDK OpenAI resmi (Python dan Node) berjalan tanpa modifikasi; waktu dari unduh sampai request pertama ≤ 10 menit |
| G3 | Guard tidak merusak jawaban | Pengguna | Pemulihan token ≥ 99%; false positive pada baris negatif ≤ 2% |
| G4 | Overhead kecil dan dipublikasikan | Bisnis | Benchmark p50 dan p99 terbit di README untuk setiap rilis |
| G5 | Hipotesis diferensiasi teruji sebelum fitur lanjutan dibangun | Bisnis | Gerbang Tahap 0 diputuskan tertulis; 5 sampai 10 wawancara calon pengguna tercatat di Tahap 5 |

## 5. Non-goals

| Non-goal | Alasan |
| --- | --- |
| Menjadi gateway pengganti (fallback, load balancing, tracking biaya) | LiteLLM dan gateway lain sudah melakukannya. OmniRail dipasang di depan atau di samping gateway |
| Streaming, tool call, gambar, dan format klien asli Anthropic atau Gemini | Streaming bisa memecah token PII dan butuh desain buffer sendiri. Di MVP fitur ini **ditolak eksplisit**, bukan diteruskan tanpa diperiksa |
| Deteksi PII bebas-bentuk (nama, alamat) | Butuh NER. Ditunda ke setelah MVP lewat ONNX lokal |
| Deteksi prompt injection yang andal | Deny-list hanya penyaring murah. Classifier menyusul. Klaim publik tidak boleh menyebut proteksi injection |
| Dasbor, admin API, rate limiting, Redis | Log terstruktur dan OpenTelemetry cukup untuk MVP |
| Klaim kepatuhan hukum | OmniRail adalah kontrol teknis pendukung. Persetujuan subjek data, DPIA, DPO, kontrak provider, notifikasi insiden, dan keabsahan transfer tetap urusan organisasi |

## 6. Persona dan user stories

Persona diurutkan menurut prioritas. Pembangun sendiri adalah pengguna pertama untuk persona P1 dan P2.

**P1. Engineer aplikasi (integrator)**

1. Sebagai engineer aplikasi, saya ingin cukup mengganti `base_url` dan kunci di SDK OpenAI agar aplikasi saya terlindungi tanpa menulis ulang kode.
2. Sebagai engineer aplikasi, saya ingin jawaban model berisi nilai asli (email, nomor HP) dan bukan token, agar pengguna akhir tidak melihat `<EMAIL_1>`.
3. Sebagai engineer aplikasi, saya ingin pesan error yang jelas dan berformat OpenAI saat request diblokir, agar aplikasi bisa menampilkan pesan yang tepat tanpa logika khusus.
4. Sebagai engineer aplikasi, saya ingin output JSON yang rusak diperbaiki otomatis dan dicek terhadap schema, agar parser di aplikasi tidak gagal.
5. *(Kasus tepi)* Sebagai engineer aplikasi, saya ingin request dengan `stream: true` atau gambar ditolak dengan pesan yang jelas, agar saya tahu fitur itu belum dilindungi dan tidak mengira datanya sudah diperiksa.

**P2. Penanggung jawab keamanan atau pelindungan data**

6. Sebagai penanggung jawab kepatuhan, saya ingin memasang policy pack dalam mode shadow lebih dulu, agar saya bisa melihat apa yang akan diblokir sebelum penegakan memengaruhi pengguna.
7. Sebagai penanggung jawab kepatuhan, saya ingin membatasi provider yang boleh dipakai (misalnya hanya Ollama lokal), agar data tidak keluar ke provider yang belum disetujui.
8. Sebagai penanggung jawab kepatuhan, saya ingin perubahan kebijakan hanya lewat git dengan persetujuan peran tertentu, agar tidak ada yang mengubah guard diam-diam.
9. Sebagai penanggung jawab kepatuhan, saya ingin credentials tidak pernah diteruskan mentah, bahkan dalam mode shadow, agar masa uji tidak menjadi celah kebocoran.

**P3. Operator atau SRE**

10. Sebagai operator, saya ingin satu binary dengan satu file konfigurasi yang divalidasi saat start, agar kesalahan konfigurasi ketahuan sebelum menerima trafik.
11. Sebagai operator, saya ingin menentukan perilaku saat guard gagal (`fail_mode`) per rute, agar fitur kritis tetap jalan dan fitur sensitif tetap tertutup.
12. Sebagai operator, saya ingin metrik dan health check standar, agar OmniRail bisa dipantau dengan alat yang sudah ada.

**P4. Auditor internal**

13. Sebagai auditor, saya ingin melihat untuk setiap request: kebijakan yang berlaku (versi dan hash), keputusan, provider, dan jenis entitas yang terdeteksi tanpa nilai mentahnya, agar saya bisa menelusuri kejadian tanpa melihat data pribadi.

**P5. Kontributor policy pack**

14. Sebagai kontributor pack, saya ingin menulis entitas dan aturan beserta contoh yang wajib terdeteksi dan wajib diabaikan, lalu menjalankan `omnirail test`, agar kualitas pack terbukti sebelum dibagikan.

## 7. Requirements

Prioritas: **P0** wajib untuk rilis awal, **P1** segera setelah rilis bila waktu tidak cukup, **P2** tidak dibangun sekarang tetapi desain tidak boleh menghalanginya.

### 7.1 Alur pemrosesan

Urutan ini mengikat. Setiap langkah yang menolak request menghentikan alur dan tidak memanggil provider.

**Request**

1. Autentikasi kunci OmniRail.
2. Batas ukuran body (byte) dan parse JSON.
3. Tolak fitur yang belum didukung: `stream: true`, `tools`/`functions`, konten non-teks.
4. Resolusi rute: alias model → provider + model, lalu cek `allowed_providers`.
5. Normalisasi teks untuk pencocokan (NFKC, casefold, hapus karakter lebar-nol). Teks yang dikirim ke provider tetap teks asli.
6. Batas panjang input (`max_input_chars`, dijumlah dari semua pesan).
7. Deteksi credentials.
8. Kebijakan: `deny_patterns` dan `blocked_keywords`.
9. Deteksi dan penyamaran PII (tokenize atau redact).
10. Ubah format ke adapter provider, lalu panggil upstream dengan timeout.

**Response**

1. Ubah format dari adapter ke format OpenAI.
2. Bila rute punya schema JSON: perbaiki sintaks, parse, pulihkan token di dalam nilai string, lalu validasi schema.
3. Bila tanpa schema: pulihkan token pada teks.
4. Tulis audit log, lalu kirim jawaban ke aplikasi.

### 7.2 API klien

| ID | Prioritas | Requirement |
| --- | --- | --- |
| API-01 | P0 | `POST /v1/chat/completions` kompatibel format OpenAI untuk teks, non-streaming |
| API-02 | P0 | Fitur yang belum didukung ditolak dengan error eksplisit (bagian 8), bukan diteruskan |
| API-03 | P0 | Semua peran pesan (`system`, `user`, `assistant`) diperiksa, termasuk riwayat percakapan |
| API-04 | P0 | `GET /healthz` (proses hidup) dan `GET /readyz` (konfigurasi termuat, upstream terkonfigurasi) |
| API-05 | P1 | `GET /v1/models` mengembalikan daftar alias rute |
| API-06 | P2 | Streaming dengan buffer token, format klien asli Anthropic dan Gemini |

Kriteria terima:

- [ ] SDK OpenAI resmi Python dan Node mendapat jawaban lewat OmniRail hanya dengan mengganti `base_url` dan kunci.
- [ ] Request dengan `stream: true` mendapat HTTP 400 kode `omnirail_unsupported_feature` dan provider tidak dipanggil.
- [ ] Request dengan bagian `image_url` mendapat HTTP 400 kode yang sama, dan provider tidak dipanggil.
- [ ] Email di pesan `assistant` dari giliran sebelumnya ikut ditokenisasi.
- [ ] Respons menyertakan header `x-omnirail-request-id`, yang sama dengan `request_id` di audit log.

### 7.3 Upstream dan rute

**Rute** adalah satu entri di `model_map`. Nama alias dipakai aplikasi sebagai `model`. Rute bisa menimpa `fail_mode` dan schema JSON.

| ID | Prioritas | Requirement |
| --- | --- | --- |
| UP-01 | P0 | Satu format internal dan adapter Ollama (Tahap 1), Anthropic Messages API, Gemini API, dan OpenAI passthrough (Tahap 2) |
| UP-02 | P0 | Model yang tidak ada di `model_map` ditolak dengan 404 `model_not_found`, kecuali ada rute `default` |
| UP-03 | P0 | Provider di luar `allowed_providers` ditolak saat konfigurasi divalidasi (start gagal) dan saat request (403) |
| UP-04 | P0 | Timeout upstream bisa diatur (default 60 detik). Tidak ada retry atau fallback antar-provider |
| UP-05 | P0 | Pemetaan adapter: pesan `system` ke `system` (Anthropic) atau `systemInstruction` (Gemini); `assistant` ke `model` (Gemini); `max_tokens` diisi default rute bila klien tidak mengirim (Anthropic mewajibkannya); `finish_reason` dan `usage` dipetakan ke format OpenAI |
| UP-06 | P0 | Parameter yang tidak didukung provider tujuan dibuang dan dicatat di log, tidak didiamkan |
| UP-07 | P0 | Body error dari provider tidak diteruskan mentah ke aplikasi atau log, karena bisa memuat ulang isi prompt |

Kriteria terima:

- [ ] Uji integrasi lulus untuk tiap provider dengan kasus: satu giliran, multi-giliran, pesan system, dan `max_tokens` kosong.
- [ ] Uji dengan mock server tanpa biaya token menutup pemetaan `finish_reason` dan `usage` semua adapter.
- [ ] Adapter Gemini ditulis setelah format API dicek ulang ke dokumentasi resmi (Pertanyaan terbuka Q7).

### 7.4 Deteksi PII dan tokenisasi

| ID | Prioritas | Requirement |
| --- | --- | --- |
| PII-01 | P0 | Entitas `email`, `phone_id`, `credit_card`, `nik`, `npwp`, `bank_account`, `nip`, `kk`, `passport_id`, `bpjs`, `birth_date` dengan pola, validator, dan kata konteks sesuai bagian 7.10 |
| PII-01b | P1 | Entitas `vehicle_plate` dan `ip_address` (bagian 7.10), mati secara default di pack `id-general` |
| PII-02 | P0 | Aksi per entitas: `tokenize` (dipulihkan di jawaban) atau `redact` (diganti `[NIK]` dan tidak dipulihkan) |
| PII-03 | P0 | Nilai yang sama dalam satu request selalu mendapat token yang sama; nilai berbeda mendapat token berbeda |
| PII-04 | P0 | Format token `<JENIS_n>`. Bila input sudah memuat teks berbentuk token (misalnya pengguna menulis `<EMAIL_1>`), penomoran melompati nomor itu, dan hanya token yang diterbitkan OmniRail yang dipulihkan |
| PII-05 | P0 | Tabel token hanya hidup di memori selama satu request dan tidak pernah ditulis ke log, disk, atau metrik |
| PII-06 | P0 | Pemulihan hanya untuk kecocokan persis. Token tak dikenal dibiarkan apa adanya. Token yang diterbitkan tetapi tidak kembali dihitung sebagai metrik, bukan error |
| PII-07 | P0 | Bila satu rentang teks lolos validator lebih dari satu entitas, kata konteks yang paling dekat menentukan jenisnya (misalnya `NIK` atau `kartu`). Tanpa kata konteks, dipakai urutan prioritas: credentials > `credit_card` (Luhn valid) > `nip` > `nik` (struktur valid) > `npwp` > `bpjs` > `bank_account` > `phone_id` > `passport_id` > `birth_date` > `email` > `ip_address` > `vehicle_plate`. Entitas yang mewajibkan kata konteks (`kk`, `passport_id`, `bpjs`, `birth_date`, `bank_account`) tidak pernah menang tanpa konteks; nilai 16 digit tanpa kata `KK` diperlakukan sebagai `nik`. Rentang yang tumpang tindih diselesaikan dengan memilih yang terpanjang |
| PII-08 | P1 | Entitas kustom di `omnirail.yaml` (customisasi tingkat 2) dengan validator bawaan yang bisa dipilih |
| PII-09 | P2 | NER lokal (ONNX) untuk nama, alamat, dan nama instansi |

Kriteria terima:

- [ ] Untuk input "email saya a@b.co dan a@b.co", provider menerima dua kemunculan `<EMAIL_1>`, dan aplikasi menerima dua kemunculan `a@b.co`.
- [ ] Input yang sudah memuat `<EMAIL_1>` tidak dipulihkan menjadi email orang lain.
- [ ] Nomor 16 digit yang lolos Luhn dan memiliki prefix kartu, tanpa kata konteks NIK, dikenali sebagai `credit_card`, bukan `nik`. Nilai yang sama setelah kata `NIK` dikenali sebagai `nik` (dataset D050 dan D051).
- [ ] Nomor pesanan 16 digit dengan tanggal tidak valid di posisi 7 sampai 12 tidak dikenali sebagai `nik`.
- [ ] Nilai 16 digit setelah kata `No. KK` dikenali sebagai `kk`; nilai yang sama tanpa kata konteks dikenali sebagai `nik`.
- [ ] "Mohon maaf lahir dan batin, 10-04-2026" tidak dikenali sebagai `birth_date`; "lahir 12/04/1974" dikenali.
- [ ] `grep` nilai uji di semua log setelah menjalankan set uji tidak menemukan satu pun nilai.

### 7.5 Credentials

| ID | Prioritas | Requirement |
| --- | --- | --- |
| CRED-01 | P0 | Detektor: `api_key` (prefix dikenal seperti `sk-`, `sk-ant-`, `AIza`, `AKIA`, `ghp_`, `github_pat_`, `glpat-`, `xox?-`, Midtrans `Mid-server-` dan `SB-Mid-server-`, Xendit `xnd_production_` dan `xnd_development_` dengan sufiks berpanjang variabel yang bisa memuat `+`, `/`, dan `=`, serta token bot Telegram `\d{8,10}:[A-Za-z0-9_-]{35}`; kunci publik `xnd_public_` dan client key Midtrans tidak diblokir), `jwt` (tiga segmen base64url dengan header JSON berisi `alg`), `private_key` (blok `-----BEGIN ... PRIVATE KEY-----`), `connection_string` (skema basis data atau broker dengan password tidak kosong), `password_assignment` (`password`, `pwd`, `kata sandi` diikuti `:` atau `=`) |
| CRED-02 | P0 | Aksi `block` (default) atau `redact`. Credentials **tidak pernah** ditokenisasi dan tidak pernah dipulihkan |
| CRED-03 | P0 | Placeholder umum (`***`, `<password>`, `${VAR}`, `xxx`) tidak dianggap credentials |
| CRED-04 | P1 | Deteksi entropi tinggi setelah kata kunci (`token=`, `secret=`) untuk secret tanpa prefix |

Kriteria terima:

- [ ] Prompt yang memuat `postgres://app:s3cret@db:5432/x` diblokir dengan HTTP 400 `omnirail_policy_violation`, dan provider tidak dipanggil.
- [ ] Pesan error menyebut jenis (`connection_string`), tidak menyebut nilainya.
- [ ] `DATABASE_URL=${DATABASE_URL}` tidak diblokir.

### 7.6 Kebijakan, mode, dan fail mode

| ID | Prioritas | Requirement |
| --- | --- | --- |
| POL-01 | P0 | `max_input_chars` (total semua pesan) dan `server.max_body_bytes` (default 1 MiB) |
| POL-02 | P0 | `deny_patterns` (regex, tidak peka huruf besar) dan `blocked_keywords` (cocok per kata utuh), keduanya pada teks yang dinormalisasi |
| POL-03 | P0 | `allowed_providers` |
| POL-04 | P0 | `mode: enforce \| shadow`, global dan bisa ditimpa per rute |
| POL-05 | P0 | `fail_mode.ingress` dan `fail_mode.egress` (`open \| closed`), global dan bisa ditimpa per rute |

**Semantik mode shadow**

| Kontrol | `enforce` | `shadow` |
| --- | --- | --- |
| Blokir kebijakan (deny, kata kunci, panjang input) | Tolak request | Teruskan, catat `would_block` |
| Credentials | Tolak request (`block`) | **Diredaksi**, diteruskan, catat `would_block` |
| Penyamaran PII | Diterapkan | Diterapkan bila `shadow.apply_transforms: true` (default); bila `false`, hanya dicatat |
| `allowed_providers` | Tolak request | **Tetap ditolak** (bukan kontrol yang diuji, melainkan batas keras) |
| Validasi schema JSON | Mengikuti `fail_mode.egress` | Selalu diteruskan, catat hasilnya |

Alasan default ini: masa uji tidak boleh lebih bocor daripada penegakan untuk hal yang tidak bisa ditarik kembali (credentials, provider terlarang). Penyamaran PII bisa dipulihkan, sehingga dampaknya ke jawaban kecil.

**Fail mode** berlaku saat guard sendiri gagal (panic, regex timeout, konfigurasi rusak saat reload), bukan saat guard berhasil memblokir. `ingress: closed` berarti request ditolak dengan 503. `egress: open` berarti jawaban diteruskan apa adanya, dan kegagalan dicatat.

Kriteria terima:

- [ ] Dalam shadow, prompt berisi kata yang diblokir sampai ke provider, dan audit log mencatat `decision: would_block` beserta ID aturannya.
- [ ] Dalam shadow, provider menerima `[CREDENTIAL]`, bukan nilai credentials asli.
- [ ] `ｐｏｌｉｔｉｋ` (huruf lebar penuh) dan `pol​itik` (lebar-nol) tertangkap oleh kata kunci `politik`, sedangkan `politikus` tidak tertangkap.

### 7.7 Audit log dan observabilitas

| ID | Prioritas | Requirement |
| --- | --- | --- |
| AUD-01 | P0 | Satu baris JSON per request ke stdout (atau file), dengan field di bawah |
| AUD-02 | P0 | `policy_hash` = SHA-256 dari kebijakan efektif (default + pack + override `omnirail.yaml`) yang diserialisasi sebagai JSON kanonik (kunci terurut), **tanpa** nilai rahasia. `policy_version` = versi `omnirail.yaml` + nama dan versi setiap pack |
| AUD-03 | P0 | `store_raw_prompts: false` secara default. Bila `true`, start mencetak peringatan dan field ini ikut tercatat di audit log |
| AUD-04 | P0 | Metrik OpenTelemetry (OTLP): jumlah request per keputusan, temuan per jenis entitas, latensi proxy dan upstream (histogram), hasil JSON, dan statistik pemulihan token |
| AUD-05 | P1 | Ekspor ringkasan audit untuk auditor (cikal bakal "laporan bukti pendukung") |

Field audit log:

| Field | Isi |
| --- | --- |
| `ts`, `request_id` | Waktu dan ID request |
| `api_key_id` | Nama atau ID kunci OmniRail, **bukan** kuncinya |
| `route`, `provider`, `model` | Rute dan tujuan |
| `mode`, `decision` | `allow`, `block`, `would_block`, `error` |
| `rules` | ID aturan yang terpicu |
| `entities` | Jumlah per jenis entitas, misalnya `{"nik": 1, "email": 2}`, **tanpa nilai** |
| `credentials` | Jumlah per jenis credentials |
| `input_chars`, `latency_ms.proxy`, `latency_ms.upstream` | Ukuran dan waktu |
| `json` | `n/a`, `valid`, `repaired`, `invalid` |
| `tokens` | Jumlah token diterbitkan, dipulihkan, dan hilang |
| `policy_version`, `policy_hash`, `omnirail_version` | Untuk penelusuran |

### 7.8 Validasi output JSON

| ID | Prioritas | Requirement |
| --- | --- | --- |
| JSON-01 | P0 | Schema per rute (`routes.<alias>.json_schema_file`). Rute tanpa schema tidak divalidasi |
| JSON-02 | P0 | Perbaikan sintaks lokal: buang pagar kode markdown, koma ekstra, kurung yang tidak tertutup di akhir, dan kutip tunggal |
| JSON-03 | P0 | Urutan: perbaiki → parse → pulihkan token di nilai string → validasi schema → serialisasi ulang |
| JSON-04 | P0 | Pelanggaran schema mengikuti `fail_mode.egress`: `open` meneruskan dengan header `x-omnirail-json: invalid`, `closed` mengembalikan 502 `omnirail_output_invalid` |
| JSON-05 | P1 | Menghormati `response_format.json_schema` dari klien bila rute tidak punya schema |
| JSON-06 | P1 | Satu kali retry ke provider dengan pesan perbaikan, opsional per rute |

Kriteria terima:

- [ ] Schema dengan `"format": "email"` lulus saat model mengembalikan `<EMAIL_1>` yang kemudian dipulihkan menjadi email valid.
- [ ] Nilai asli yang mengandung `"` tetap menghasilkan JSON valid setelah dipulihkan.

### 7.9 Konfigurasi dan policy pack

| ID | Prioritas | Requirement |
| --- | --- | --- |
| CFG-01 | P0 | Satu file `omnirail.yaml`, divalidasi saat start. Kesalahan menghentikan start dan menyebut baris serta kunci yang salah |
| CFG-02 | P0 | Substitusi `${ENV}` hanya untuk nilai rahasia. Variabel yang kosong menghentikan start |
| CFG-03 | P0 | Prioritas: `omnirail.yaml` > pack > default |
| CFG-04 | P0 | Pack `id-general` dibundel di binary |
| CFG-05 | P0 | Pack wajib punya `pack.yaml` (nama, versi, `min_omnirail_version`), `tests/should_detect.txt`, dan `tests/should_ignore.txt`. Pack tanpa tes ditolak saat dimuat |
| CFG-06 | P0 | Default aman: `server.listen: 127.0.0.1:8080`, `store_raw_prompts: false`, `fail_mode.ingress: closed`, tampilan uji mati |
| CFG-07 | P0 | Kunci OmniRail dibandingkan secara *constant-time*. Kunci provider tidak pernah muncul di log, error, atau `/readyz` |
| CFG-08 | P1 | Reload konfigurasi tanpa restart (SIGHUP). Konfigurasi baru yang tidak valid ditolak, dan konfigurasi lama tetap dipakai |
| CFG-09 | P2 | Pack yang ditandatangani dan marketplace pack; kustomisasi tingkat 4 (WASM atau webhook) |

### 7.10 Spesifikasi entitas `id-general`

| Entitas | Pola | Validator | Kata konteks | Risiko false positive |
| --- | --- | --- | --- | --- |
| `email` | Bagian lokal + `@` + domain dengan TLD ≥ 2 huruf | Panjang total ≤ 254 | Tidak wajib | Rendah |
| `phone_id` | `+62`, `62`, atau `0` diikuti `8`, lalu 7 sampai 11 digit, boleh dipisah spasi, titik, atau tanda hubung | Setelah dinormalisasi menjadi `08…`, panjangnya 10 sampai 13 digit | Tidak wajib | Sedang (bentrok dengan angka panjang lain) |
| `credit_card` | 13 sampai 19 digit, boleh dipisah spasi atau tanda hubung | Luhn **dan** prefix jaringan dikenal (Visa, Mastercard, Amex, JCB; prefix GPN dicek di Q5) | Menaikkan keyakinan | Rendah bila validator lengkap |
| `nik` | 16 digit | Struktur: 2 digit kode provinsi valid (termasuk 93 s.d. 96 untuk provinsi Papua hasil pemekaran, Q5), 4 digit kode kab/kota dan kecamatan, 6 digit tanggal lahir `DDMMYY` (tanggal 01 sampai 31, atau 41 sampai 71 untuk perempuan; bulan 01 sampai 12), lalu 4 digit nomor urut bukan `0000` | `nik`, `ktp`, `no. induk` menaikkan keyakinan | Sedang (bentrok dengan nomor kartu dan NPWP 16 digit) |
| `npwp` | 15 digit berformat `99.999.999.9-999.999`, atau 15 dan 16 digit tanpa format | 15 digit tanpa format dan 16 digit wajib punya kata konteks. Sejak 1 Juli 2024 (PMK 136/2023), NPWP orang pribadi penduduk = NIK, sedangkan badan dan bukan penduduk memakai `0` + 15 digit lama | `npwp`, `nomor pokok wajib pajak` | Sedang. NPWP 15 digit masih muncul di dokumen lama |
| `bank_account` | 8 sampai 16 digit, boleh dipisah | **Wajib** kata konteks dalam jarak ≤ 5 kata | `rekening`, `rek`, `no rek`, `norek`, `a/n`, `account` | Tinggi tanpa konteks, karenanya konteks diwajibkan |
| `nip` | 18 digit, boleh dipisah spasi (`19580818 198404 1 001`), termasuk NI PPPK | Tanggal lahir `YYYYMMDD` valid (1940 s.d. 2008); tahun pengangkatan ≥ tahun lahir + 18; digit ke-13 s.d. ke-14 berupa bulan TMT `01` s.d. `12` (PNS) **atau** frekuensi pengangkatan `21` s.d. `29` (PPPK); digit ke-15 `1` atau `2`; nomor urut bukan `000` | `nip`, `pns`, `asn`, `pegawai` menaikkan keyakinan | Rendah |
| `kk` | 16 digit | Struktur wilayah seperti NIK, 6 digit tanggal terbit `DDMMYY` (tanggal 01 s.d. 31), nomor urut bukan `0000` | **Wajib**: `kk`, `kartu keluarga`, `no. kk` | Rendah dengan konteks; tanpa konteks diperlakukan sebagai `nik` |
| `passport_id` | 1 s.d. 2 huruf + 6 s.d. 7 digit, boleh dengan spasi setelah huruf (`A1234567`, `AB123456`) | Tanpa checksum. Pola mengikuti definisi Microsoft Purview; belum dari Ditjen Imigrasi (Q11) | **Wajib**: `paspor`, `passport` | Tinggi tanpa konteks (kode produk, nomor tiket) |
| `bpjs` | 13 digit (Kesehatan/KIS); 11 atau 16 digit (Ketenagakerjaan; sumber berbeda soal panjangnya) | Panjang. Nomor 16 digit yang juga lolos struktur NIK ditentukan oleh kata konteks | **Wajib**: `bpjs`, `kis`, `jkn`, `kpj` | Tinggi tanpa konteks |
| `birth_date` | `DD-MM-YYYY`, `DD/MM/YYYY`, `DD.MM.YYYY`, `YYYY-MM-DD`, `DD Bulan YYYY` (nama bulan Indonesia lengkap atau 3 huruf) | Tanggal valid, tahun 1900 s.d. tahun berjalan. Nilai hanya tanggalnya, tanpa kota pada TTL | **Wajib** dalam jarak ≤ 5 kata: `lahir`, `tgl lahir`, `tanggal lahir`, `ttl`, `dob`, `birth`, `kelahiran`; frasa `lahir dan batin` dan `hari lahir` dikecualikan | Sedang |
| `vehicle_plate` (P1) | Kode wilayah dikenal + 1 s.d. 4 digit + **wajib** 1 s.d. 3 huruf kapital, spasi opsional (`B 1234 ABC`) | Kode wilayah mengikuti Perpol 7/2021 ditambah kode Papua baru (`PG`, `PS`, `PT`, `PY`); `DS` tidak berlaku lagi (Q12) | `plat`, `nopol`, `nomor polisi`, `kendaraan`, `mobil`, `motor` menaikkan keyakinan | Sedang (`Kamar D 12 VIP`, `Ruang B 201 AC`); plat huruf kecil belum dicakup |
| `ip_address` (P1) | IPv4 dan IPv6 | Oktet 0 s.d. 255 tanpa nol di depan, tidak diapit `.angka` (menghindari OID); IP privat, loopback, link-local, dan ≥ 224 dikecualikan | Tidak wajib | Sedang (nomor versi empat bagian seperti `4.5.4.3`) |

### 7.11 Evaluasi dan CLI

| ID | Prioritas | Requirement |
| --- | --- | --- |
| EVAL-01 | P0 | `eval/dev/uji_pii_id.csv` dan `eval/holdout/uji_pii_id.csv` di repo (format di `eval/README.md`), dengan kolom `id`, `kategori`, `teks`, `diharapkan`, `cakupan_mvp`, `catatan`, dibagi `dev` dan `holdout`, dan seluruhnya data rekaan |
| EVAL-02 | P0 | `omnirail eval` menghasilkan recall, precision, dan false positive per entitas; tingkat blokir credentials; deteksi deny-list; dan pemulihan token. Hasilnya disimpan sebagai JSON bernomor versi (kode, pack, dataset, waktu) plus ringkasan Markdown |
| EVAL-03 | P0 | `omnirail test --pack <dir>` gagal bila satu baris `should_detect` tidak terdeteksi, atau satu baris `should_ignore` terdeteksi |
| EVAL-04 | P0 | CI menjalankan `omnirail test` untuk semua pack dan `omnirail eval` pada `dev`. CI gagal bila recall turun atau false positive naik melewati ambang yang ditetapkan dari baseline |
| EVAL-05 | P0 | Benchmark latensi: mock upstream dengan waktu tetap, input 1 rb, 5 rb, dan 20 rb karakter, mengukur selisih p50 dan p99 dengan dan tanpa proxy |
| EVAL-06 | P1 | Tampilan uji satu halaman (tab Coba dan tab Evaluasi), hanya dari localhost atau dengan kunci admin |

### 7.12 Distribusi

| ID | Prioritas | Requirement |
| --- | --- | --- |
| DIST-01 | P0 | Binary rilis untuk Linux x86_64 dan arm64, dan macOS arm64. Windows menyusul (Q9) |
| DIST-02 | P0 | Image container minimal (distroless atau scratch) |
| DIST-03 | P0 | README dengan quickstart ≤ 5 langkah, batas klaim (bagian 10), dan hasil benchmark terbaru |
| DIST-04 | P1 | Contoh pemasangan di depan LiteLLM |

## 8. Kontrak error

Semua error memakai bentuk OpenAI agar SDK menanganinya tanpa kode tambahan:

```json
{
  "error": {
    "message": "Request diblokir: terdeteksi credentials (connection_string).",
    "type": "omnirail_error",
    "code": "omnirail_policy_violation",
    "param": null,
    "request_id": "req_01J..."
  }
}
```

| HTTP | `code` | Kapan |
| --- | --- | --- |
| 400 | `omnirail_policy_violation` | Credentials, deny-list, atau kata kunci (mode enforce) |
| 400 | `omnirail_unsupported_feature` | `stream`, tool call, konten non-teks |
| 401 | `invalid_api_key` | Kunci OmniRail salah atau tidak ada |
| 403 | `omnirail_provider_not_allowed` | Rute menunjuk provider di luar `allowed_providers` |
| 404 | `model_not_found` | Alias tidak ada dan tidak ada rute `default` |
| 413 | `omnirail_input_too_large` | Melewati `max_body_bytes` atau `max_input_chars` |
| 502 | `omnirail_upstream_error` | Provider mengembalikan error (body provider tidak diteruskan) |
| 502 | `omnirail_output_invalid` | Schema gagal dan `fail_mode.egress: closed` |
| 503 | `omnirail_guard_unavailable` | Guard gagal dan `fail_mode.ingress: closed` |
| 504 | `omnirail_upstream_timeout` | Melewati timeout upstream |

Pesan error menyebut jenis temuan, tidak pernah nilainya.

## 9. Metrik keberhasilan

Angka di bawah adalah **target awal (hipotesis)**. Angka ini memberi kriteria lulus yang bisa diperiksa per tahap, lalu direvisi tertulis setelah baseline Tahap 3 dan benchmark Tahap 5. Revisi dicatat di bagian 14.

**Indikator awal (diukur per rilis, dari `omnirail eval` dan benchmark)**

| Metrik | Target awal | Sumber |
| --- | --- | --- |
| Tingkat blokir credentials | ≥ 0,95 | Baris kredensial, `dev` dan `holdout` |
| Recall `email`, `credit_card`, `nik` | ≥ 0,95 | Baris positif |
| Recall `phone_id`, `npwp` | ≥ 0,90 | Baris positif |
| Recall `nip`, `kk` | ≥ 0,95 | Baris positif |
| Recall `passport_id`, `bpjs`, `birth_date` (dengan kata konteks) | ≥ 0,90 | Baris positif |
| Recall `bank_account` (dengan kata konteks) | ≥ 0,80 | Baris positif |
| Precision per entitas | ≥ 0,90 | Baris positif dan negatif |
| False positive pada baris negatif | ≤ 0,02 | Baris negatif (termasuk nomor resi dan nomor pesanan) |
| Pemulihan token (token yang dikembalikan model secara persis) | ≥ 0,99 | Baris positif lewat mock dan provider nyata |
| Overhead latensi, input 5 rb karakter | p50 ≤ 5 ms, p99 ≤ 15 ms | Benchmark EVAL-05 |
| Output JSON valid setelah perbaikan tanpa retry | ≥ 0,95 dari output yang rusak sintaks | Set uji JSON |
| Waktu dari unduh sampai request pertama berhasil | ≤ 10 menit | Diukur pada 3 orang yang belum pernah memakai |

**Indikator lanjutan (1 sampai 3 bulan setelah rilis)**

| Metrik | Target awal |
| --- | --- |
| Wawancara calon pengguna tercatat | 5 sampai 10, dengan ringkasan tertulis |
| Tim eksternal yang menjalankan mode shadow ≥ 2 minggu | ≥ 3 |
| Precision lapangan dari sampel shadow yang ditinjau | ≥ 0,90 |
| Tim yang beralih dari shadow ke enforce | ≥ 1 |

## 10. Keamanan dan batas klaim

Ringkasan threat model blueprint bagian 9, dengan tambahan dari PRD ini:

| Ancaman | Dicakup MVP | Catatan |
| --- | --- | --- |
| PII berformat tetap dan credentials terkirim ke provider | Sebagian | Format tak lazim dan secret tanpa prefix bisa lolos |
| PII bebas-bentuk (nama, alamat) | Tidak | Butuh NER |
| Prompt injection langsung | Tidak | Deny-list hanya penyaring murah |
| Data tak diperiksa lewat streaming, gambar, atau tool call | Ya | Ditolak eksplisit (API-02) |
| Penghindaran deny-list dengan Unicode | Sebagian | Normalisasi NFKC dan lebar-nol; parafrase tetap lolos |
| Kebocoran lewat log atau error provider | Ya | Nilai PII tidak pernah ditulis; body error provider tidak diteruskan |
| Proxy terbuka ke jaringan | Ya | Default `127.0.0.1`, kunci OmniRail wajib |
| Kebocoran kunci provider | Sebagian | Kunci hanya di proxy; rotasi dan rate limit per kunci ditunda |
| Proxy gagal atau lambat | Ya | `fail_mode` per rute, health check, timeout |

**Wajib tertulis di README:** lampiran dan gambar ditolak (tidak diperiksa), tokenisasi berlaku per request, OmniRail tidak mengklaim kepatuhan hukum apa pun (termasuk UU PDP dan panduan OJK), dan kalimat publik memakai "mengurangi risiko", bukan "melindungi sepenuhnya".

Pemetaan ke regulasi (UU 27/2022, panduan OJK) tetap di blueprint bagian 6 dan 7. Pemetaan itu perlu dicocokkan dengan naskah resmi oleh penanggung jawab kepatuhan sebelum dipakai di materi publik (Q6).

## 11. Tahapan dan kriteria selesai

Belum ada tanggal. Kecepatan kerja ditetapkan setelah Tahap 1. Satu-satunya tanggal eksternal yang relevan: menurut Hukumonline, PP 33/2026 berlaku 16 Januari 2027. Tanggal ini konteks pasar, bukan komitmen rilis.

| Tahap | Isi | Selesai bila |
| --- | --- | --- |
| **0. Validasi** (maks. 2 minggu) | Susun `uji_pii_id.csv` (dev + holdout). Jalankan terhadap LiteLLM + Presidio dengan recognizer Indonesia sederhana. Konfirmasi fitur pemulihan token LiteLLM | Catatan keputusan tertulis: **lanjut** (celah recall/precision atau ergonomi cukup besar), **pivot** ke plugin untuk LiteLLM atau Presidio (blueprint lapis 3), atau **berhenti** |
| **1. Kerangka proxy** | API-01, API-04, UP-01 (Ollama), CFG-01/02/06/07, kontrak error | SDK OpenAI mendapat jawaban lewat proxy; konfigurasi salah menghentikan start dengan pesan yang jelas |
| **2. Jalur provider** | Adapter Anthropic, lalu Gemini, lalu OpenAI; UP-02 s.d. UP-07 | Uji integrasi lulus terhadap tiap provider; uji mock menutup pemetaan |
| **3. PII dan credentials** | PII-01 s.d. 07, CRED-01 s.d. 03, POL-01 s.d. 05, AUD-01 s.d. 04, EVAL-01 s.d. 04, pack `id-general` | Baseline per entitas tercatat; ambang CI ditetapkan; target bagian 9 direvisi tertulis |
| **4. Validasi JSON** | JSON-01 s.d. 04 | Pelanggaran schema dan perbaikan terhitung di metrik dan audit log |
| **5. Rilis awal** | DIST-01 s.d. 03, EVAL-05, README dengan batas klaim, wawancara | Rilis bertag; benchmark terbit; ringkasan wawancara tertulis menentukan prioritas berikutnya |

Setelah Tahap 5, urutan ditentukan umpan balik. Kandidatnya: tampilan uji (EVAL-06), entitas kustom (PII-08), streaming, NER, laporan bukti pendukung, dan marketplace pack (blueprint bagian 13).

## 12. Risiko

| Risiko | Dampak | Mitigasi |
| --- | --- | --- |
| LiteLLM + Presidio sudah cukup untuk kebutuhan yang sama | Produk tidak punya alasan dipakai | Gerbang Tahap 0, dengan opsi pivot ke plugin |
| False positive merusak jawaban | Pengguna mematikan guard | Validator struktur, konteks wajib untuk `bank_account`, mode shadow, entitas bisa dimatikan satu per satu |
| Model mengubah atau menerjemahkan token (`<EMAIL_1>` jadi `EMAIL_1`) | Nilai asli tidak kembali | Metrik token hilang; instruksi sistem opsional yang meminta model mempertahankan token (P1); format token diuji ke tiap provider di Tahap 2 |
| Scope creep dari daftar fitur blueprint | MVP tidak pernah rilis | Tabel prioritas di bagian 7; fitur baru masuk hanya bila ada yang dikeluarkan |
| Satu pembangun, Rust memperlambat iterasi awal | Tahap molor | Tahap kecil dengan kriteria selesai yang bisa diperiksa; P1 boleh dilepas tanpa menggeser rilis |
| Klaim publik terbaca sebagai klaim kepatuhan | Risiko reputasi dan hukum | Batas klaim wajib di README; kata "bukti pendukung", bukan "patuh" |

## 13. Pertanyaan terbuka

| # | Pertanyaan | Penjawab | Menghalangi |
| --- | --- | --- | --- |
| Q1 | Siapa yang menyusun `uji_pii_id.csv`, dan berapa baris minimum per entitas untuk baseline yang bermakna (usulan: ≥ 50 positif dan ≥ 50 negatif per entitas)? | Pembangun | Tahap 0 |
| Q2 | Apa kriteria angka untuk keputusan "lanjut" di Tahap 0 (misalnya selisih recall ≥ 10 poin atau false positive setengahnya)? | Pembangun | Tahap 0 |
| Q3 | Apakah default `shadow.apply_transforms: true` diterima calon pengguna, atau mereka ingin shadow murni mengamati? | Calon pengguna (wawancara) | Tidak |
| Q4 | ~~Aturan NPWP 16 digit~~ **Terjawab sebagian** (Lampiran A): NIK untuk orang pribadi, `0` + 15 digit untuk badan. Yang tersisa: adakah checksum resmi NPWP? | Pembangun, dicek ke sumber DJP | Tidak |
| Q5 | Daftar prefix kartu GPN (tidak ditemukan sumber publik), dan konfirmasi kode provinsi 93 s.d. 96 dari Kepmendagri 100.1.1-6117/2022 | Pembangun | Tahap 3 |
| Q6 | Teks resmi UU 27/2022 Pasal 36 s.d. 39 dan 56, serta PP 33/2026, sebelum dipakai di materi publik atau pack `id-fintech` | Penanggung jawab kepatuhan | Pack `id-fintech`, bukan MVP |
| Q7 | Format Gemini API dicek ke dokumentasi resmi ai.google.dev | Pembangun | Adapter Gemini (Tahap 2) |
| Q8 | Retensi dan tujuan audit log: cukup stdout + file berotasi, atau perlu sink lain sejak awal? | Calon pengguna fintech | Tidak |
| Q9 | Apakah Windows perlu didukung sejak rilis awal? | Wawancara | Tidak |
| Q10 | ~~Struktur NIP~~ **Terjawab** untuk PNS (Perka BKN 22/2007). NI PPPK baru dari sumber sekunder; konfirmasi ke dokumen BKN | Pembangun | Tidak |
| Q11 | Format resmi nomor paspor dari Ditjen Imigrasi (sekarang memakai definisi Microsoft Purview), dampak sistem paspor tunggal 2027, dan panjang resmi nomor BPJS Ketenagakerjaan (11 atau 16 digit) | Pembangun | Precision `passport_id` dan `bpjs` di Tahap 3 |
| Q12 | Daftar kode plat dicek langsung ke teks Perpol 7/2021 (sekarang dari sumber sekunder), dan apakah plat termasuk data pribadi untuk pengguna sasaran | Pembangun, calon pengguna | `vehicle_plate` (P1) |
| Q13 | Apakah nama bank (BCA, BRI, dan seterusnya) dijadikan kata konteks `bank_account`? | Pembangun | Tidak |

## 14. Riwayat dokumen

| Versi | Tanggal | Perubahan |
| --- | --- | --- |
| 1.0 | 9 November 2026 | Draf pertama dari blueprint v1.1, dengan perbaikan di bagian 1 |
| 1.1 | 9 November 2026 | PII-07: kata konteks menentukan jenis bila dua validator lolos. EVAL-01: lokasi dataset. Rincian task di [TASKS.md](TASKS.md) |
| 1.2 | 9 November 2026 | Entitas baru (perubahan 15), urutan prioritas PII-07 diperluas, detektor credentials Midtrans/Xendit/Telegram, Q10 s.d. Q13 |
| 1.3 | 9 November 2026 | Keterbatasan verifikasi K1 s.d. K5 dicatat di Lampiran A. Format diverifikasi ke sumber publik (Lampiran A): NI PPPK, paspor 1–2 huruf + 6–7 digit, BPJS TK 16 digit, kode plat Perpol 7/2021, NPWP 16 digit, prefix Xendit/Midtrans/Telegram, `output_parse_pii` LiteLLM |

## Lampiran A. Hasil verifikasi format (9 November 2026)

Dicek lewat pencarian web. Sebagian halaman sumber tidak bisa dibuka langsung dari lingkungan kerja, jadi beberapa poin berasal dari ringkasan hasil pencarian. Tingkat keyakinan ditulis apa adanya.

| Hal | Temuan | Keyakinan | Sumber |
| --- | --- | --- | --- |
| NIP PNS | 18 digit: tanggal lahir `YYYYMMDD`, TMT CPNS `YYYYMM`, jenis kelamin (1 pria, 2 wanita), nomor urut 3 digit. Contoh resmi `19580818 198404 1 001` | Tinggi (peraturan) | [Perka BKN 22/2007](https://peraturan.bpk.go.id/Download/250999/Perka%20BKN%20Nomor%2022%20Tahun%202007.pdf), [Perka BKN 43/2007](https://pasal.id/peraturan/perban/perka-bkn-no-43-tahun-2007) |
| NI PPPK | 18 digit; digit ke-13 s.d. ke-14 adalah frekuensi pengangkatan yang dimulai dari `21`, bukan bulan. Contoh `199002192019211001` | Sedang (sumber sekunder) | [kumparan](https://kumparan.com/info-cpns/nip-pppk-apakah-sama-dengan-pns-ini-penjelasannya-1xSqrwxpPsT), [JadiASN](https://jadiasn.id/apa-perbedaan-nip-pns-dan-pppk/) |
| Paspor | 7 s.d. 9 karakter: 1 s.d. 2 huruf diikuti 6 s.d. 7 digit, tanpa checksum | Sedang (definisi vendor, bukan Imigrasi) | [Microsoft Purview](https://learn.microsoft.com/en-us/purview/sit-defn-indonesia-passport-number) |
| BPJS Kesehatan | 13 digit | Tinggi | [Kompas TV](https://www.kompas.tv/info-publik/559588/cara-cek-nomor-bpjs-kesehatan-secara-online-lewat-hp), [OCBC](https://www.ocbc.id/id/article/2022/01/03/bpjs-adalah) |
| BPJS Ketenagakerjaan | KPJ 11 digit menurut sumber lama; 16 digit menurut CNN Indonesia (2025). Bukan NIK | Rendah (sumber bertentangan) | [CNN Indonesia 2025](https://www.cnnindonesia.com/edukasi/20250121153434-561-1189775/bagaimana-jika-lupa-nomor-bpjs-ketenagakerjaan-ini-cara-mengatasinya), [Bisnis 2023](https://finansial.bisnis.com/read/20230208/215/1626091/begini-cara-cek-nomor-kpj-bpjs-ketenagakerjaan-dengan-gampang) |
| NPWP 16 digit | Orang pribadi penduduk memakai NIK; badan, instansi, dan bukan penduduk memakai `0` + 15 digit lama; berlaku penuh 1 Juli 2024 (PMK 136/2023) | Tinggi | [DJP SP-40/2023](https://www.pajak.go.id/sites/default/files/2023-12/SP-40%202023%20Pemerintah%20Atur%20Kembali%20Saat%20Implementasi%20Penuh%20NIK-NPWP.pdf), [DJP](https://pajak.go.id/id/artikel/hikmah-di-balik-perpanjangan-implementasi-npwp-16-digit) |
| Kode plat | Diatur Perpol 7/2021. `DC` (Sulawesi Barat) dan `DW` (Bone, Soppeng, Wajo, Sinjai) ada; `DS` diganti `PA`/`PB`; provinsi Papua baru memakai `PG`, `PS`, `PT`, `PY` | Sedang (sumber sekunder) | [Itera](https://blog.itera.ac.id/kode-pelat-nomor-kendaraan-indonesia-lengkap-dari-a-sampai-z-dan-asal-daerahnya/), [Wikipedia](https://ipfs.aleph.im/ipfs/QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco/wiki/Indonesian_car_number_plates.html), [detikOto](https://oto.detik.com/berita/d-7086258/plat-d-daerah-mana-cek-daftar-kode-plat-nomor-seluruh-indonesia) |
| Kode provinsi Papua baru | Empat provinsi baru (38 provinsi). Kode 93 s.d. 96 belum ditemukan di tabel resmi | Rendah | [NU Online](https://nu.or.id/nasional/indonesia-resmi-miliki-38-provinsi-ini-yang-terbaru-K2V5I), [Kepmendagri 100.1.1-6117/2022](https://id.wikisource.org/wiki/Halaman:Kepmendagri_Nomor_100.1.1-6117_Tahun_2022.pdf/3754) |
| Midtrans | Server key sandbox berawalan `SB-Mid-server-`, production `Mid-server-`; dipakai sebagai username Basic Auth | Tinggi untuk sandbox, sedang untuk production | [Midtrans docs](https://docs.midtrans.com/docs/api-authorization-headers), [Access Keys](https://docs.midtrans.com/docs/access-keys), [GitGuardian](https://docs.gitguardian.com/secrets-detection/secrets-detection-engine/detectors/specifics/midtrans_apikey) |
| Xendit | Secret key `xnd_production_` (live) dan `xnd_development_` (test); kunci publik `xnd_public_`; panjang dan karakter sufiks tidak tetap | Tinggi | [Xendit Help Center](https://help.xendit.co/hc/en-us/articles/16516398053273-What-is-API-Key-and-How-Do-I-Create-Them) |
| Token bot Telegram | ID bot (angka), titik dua, 35 karakter `[A-Za-z0-9_-]` | Sedang (bukan dokumentasi Telegram) | [gitleaks](https://www.github.com/gitleaks/gitleaks/pull/1404), [RedHunt Labs](https://docs.redhuntlabs.com/docs/exposure-risks/credentials/telegram_bot_token) |
| LiteLLM `output_parse_pii` | Ada; hanya memulihkan token setelah model menjawab. Ada laporan bug: pemulihan tidak jalan di jalur Anthropic native | Tinggi (dokumentasi resmi) | [LiteLLM docs](https://docs.litellm.ai/docs/proxy/guardrails/pii_masking_v2), [Issue #22821](https://github.com/BerriAI/litellm/issues/22821) |
| Prefix kartu GPN | Tidak ditemukan sumber publik | — | [Bank Indonesia](https://www.bi.go.id/id/fungsi-utama/sistem-pembayaran/ritel/instrumen/default.aspx) |

### Keterbatasan verifikasi dan tindak lanjut

Lima hal berikut belum bisa dipastikan. Validator memakai asumsi sementara di kolom "Asumsi sekarang" sampai sumber resmi didapat. Setiap butir punya task di [TASKS.md](TASKS.md) (T-321 s.d. T-325).

| # | Keterbatasan | Asumsi sekarang | Risiko bila asumsi salah | Tindak lanjut | Task |
| --- | --- | --- | --- | --- | --- |
| K1 | **Prefix kartu GPN tidak ditemukan di sumber publik** | Kartu hanya dikenali bila prefix-nya Visa, Mastercard, Amex, atau JCB | Kartu debit GPN 16 digit tidak terdeteksi sebagai `credit_card` (false negative). Bila juga lolos struktur NIK, kartu itu bisa salah dilabeli `nik`, tetapi tetap tersamarkan | Minta daftar BIN GPN ke ASPI, Bank Indonesia, atau bank calon pengguna. Sementara itu, pertimbangkan Luhn + kata konteks `kartu`/`debit`/`GPN` sebagai jalur deteksi kedua | T-321 |
| K2 | **Kode provinsi Papua baru (93 s.d. 96) belum terkonfirmasi** dari tabel Kemendagri | Kode 93, 94, 95, 96 diterima di validator NIK dan KK | Bila kodenya berbeda, NIK dari provinsi itu tidak terdeteksi, dan angka berawalan 93 s.d. 96 bisa salah ditandai sebagai NIK | Cocokkan dengan lampiran Kepmendagri 100.1.1-6117/2022 atau peraturan kode wilayah yang lebih baru; perbarui daftar dan dataset | T-322 |
| K3 | **Panjang resmi nomor BPJS Ketenagakerjaan bertentangan** (11 digit menurut sumber lama, 16 digit menurut CNN Indonesia 2025) | Keduanya diterima, selama ada kata konteks `bpjs`, `kpj`, `jkn`, atau `kis` | Bila hanya satu yang berlaku, precision `bpjs` sedikit turun. Dampaknya kecil, karena kata konteks tetap wajib | Cek kartu digital JMO atau dokumen resmi BPJS Ketenagakerjaan; minta contoh format (bukan data asli) dari calon pengguna fintech atau HR | T-323 |
| K4 | **Format paspor bersandar pada definisi Microsoft Purview**, bukan Ditjen Imigrasi. Rencana sistem paspor tunggal 2027 belum diketahui dampaknya ke format nomor | 1 s.d. 2 huruf + 6 s.d. 7 digit, kata konteks wajib | Format baru 2027 bisa tidak terdeteksi | Cari peraturan Imigrasi tentang nomor paspor dan pengumuman paspor tunggal 2027; pantau sebelum rilis | T-324 |
| K5 | **Beberapa halaman sumber tidak bisa dibuka langsung**, karena jaringan lingkungan kerja membatasi domainnya (detik.com, learn.microsoft.com, cnnindonesia.com, dan lain-lain). Temuan NI PPPK, kode plat, dan token Telegram hanya bersandar pada ringkasan hasil pencarian | Temuan dipakai dengan tingkat keyakinan seperti di tabel Lampiran A | Detail kecil bisa keliru, misalnya rentang frekuensi PPPK `21` s.d. `29`, daftar kode plat, atau panjang ID bot Telegram | Buka ulang sumber dari jaringan tanpa batasan, utamakan sumber primer (dokumen BKN, teks Perpol 7/2021, dokumentasi Telegram Bot API), lalu perbarui tabel ini | T-325 |
