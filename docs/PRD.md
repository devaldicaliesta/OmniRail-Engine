# OmniRail Engine — PRD MVP v1.7.1

| | |
| --- | --- |
| **Status** | Draf, menunggu tinjauan pemilik produk |
| **Tanggal** | 11 November 2026 (v1.7.1) |
| **Pemilik** | devaldi caliesta |
| **Sumber** | [Blueprint v1.1](OmniRail_Engine_Blueprint_v1.1.md) |
| **Lingkup** | MVP sampai rilis publik pertama, dalam dua rilis: α (periksa, tanpa proxy) dan β (proxy). Tahap 0 s.d. 5 |

PRD ini menjadi acuan **apa yang dibangun dan kapan dianggap selesai** untuk MVP. Dasar metode dan rujukan paper atau standar untuk setiap bagian ada di [Landasan metode](LANDASAN_METODE.md). Blueprint v1.1 tetap menjadi acuan latar belakang, pemetaan regulasi (bagian 6 dan 7), dan arah setelah MVP (bagian 13). Bila keduanya berbeda, PRD ini yang berlaku. Daftar perbedaannya ada di bagian 1.

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
| 16 | **Tampilan uji (playground) dirinci menjadi requirement** (bagian 7.13): endpoint `inspect` dan CLI `omnirail inspect` (P0, Tahap 3), tab Coba mode periksa saja (P0, Tahap 5), kirim ke provider dan tab Evaluasi (P1) | Blueprint bagian 11 sudah menggambarkan tampilan uji, tetapi PRD v1.0 hanya punya satu baris P1. Padahal "cara mencoba tanpa risiko" adalah syarat pemakaian dari wawancara pertama, dan penanggung jawab kepatuhan tidak menulis kode |
| 17 | **MVP dipecah menjadi dua rilis** (bagian 11). **Rilis α (periksa):** `omnirail-core`, CLI `inspect`, `eval`, dan `scan`, serta demo web WASM, tanpa proxy. **Rilis β (proxy):** rilis publik pertama | Hipotesis inti adalah mutu deteksi data pribadi Indonesia. Hipotesis itu bisa diuji dan dipakai orang dalam hitungan minggu, tanpa menunggu proxy, tiga adapter, dan validasi JSON selesai. Wawancara pun bisa memakai alat nyata |
| 18 | **Scope rilis β dikecilkan:** validasi JSON (JSON-01 s.d. 04) dan metrik OpenTelemetry (AUD-04) turun ke P1; rilis β hanya wajib adapter Ollama dan **satu** provider cloud (UP-01, UP-08); tampilan uji yang disajikan binary (PG-04, PG-05) turun ke P1 | Provider utama sudah punya structured output bawaan, jadi perbaikan JSON bukan pembeda. Satu pembangun tidak bisa merawat tiga adapter sebelum ada pengguna. Demo WASM menggantikan server tampilan uji untuk kebutuhan mencoba |
| 19 | **Pseudo-streaming** (API-08): `stream: true` dilayani dengan memanggil provider tanpa streaming, lalu mengirim jawaban yang sudah diperiksa sebagai SSE | Sebagian besar aplikasi chat memakai `stream: true`. Bila ditolak, G2 (cukup ganti `base_url`) gagal untuk mereka. Jawaban di-buffer penuh, jadi tidak ada teks yang lolos sebelum diperiksa |
| 20 | **Kata konteks lintas pesan** (PII-10, P0) | Di chat CS, kata konteks sering ada di pertanyaan asisten ("Boleh minta nomor rekeningnya?"), sedangkan pengguna hanya mengirim angkanya. Dengan aturan jarak ≤ 5 kata di pesan yang sama, `bank_account`, `passport_id`, `bpjs`, dan `birth_date` **lolos tanpa disamarkan**. Ini celah kebocoran, bukan sekadar salah jenis |
| 21 | **Angka terucap** (PII-11, P1): `nol delapan satu dua …` di transkrip panggilan dan voice-to-text | Ringkasan panggilan CS adalah kasus LLM yang umum, dan alat umum tidak membaca bilangan berbahasa Indonesia. Dataset v0.6 sudah memuat barisnya |
| 22 | **Laporan paparan data** `omnirail report` (bagian 7.15, P0) | Mode shadow perlu menghasilkan sesuatu yang bisa dibaca penanggung jawab kepatuhan: data apa terkirim ke provider mana, dari aplikasi mana. Ini nilai yang terlihat sejak minggu pertama tanpa satu request pun diblokir |
| 23 | **Rute berdasarkan sensitivitas** (bagian 7.16, P1) | Bukan sekadar menyamarkan, tetapi mengarahkan request berisi data pribadi spesifik ke model lokal. Ini menjawab kekhawatiran transfer data ke luar negeri dan berbeda dari fallback antar-provider (non-goal) |
| 24 | **`omnirail scan`** untuk berkas, repo, dan CI (EVAL-07, EVAL-08), **benchmark terbuka** (DIST-07), **credentials ekosistem lokal tambahan** (CRED-05), dan **eksperimen format token** (Q14) | Jalur adopsi developer tanpa mengubah arsitektur aplikasi, dan bukti terukur yang memperkuat posisi "konteks Indonesia" |
| 25 | **Kunci token dinormalisasi** (PII-03), aksi `mask` dan `block` per entitas (PII-12, P1), dan **pemulihan toleran** (PII-13, P1). Kriteria keputusan Tahap 0 ditetapkan (Q2) | Nomor yang sama dengan penulisan berbeda harus dikenali model sebagai orang yang sama. `mask` berguna untuk jawaban yang dibaca operator, `block` untuk kebutuhan PCI DSS. Model sering menulis ulang token, dan ini langsung menurunkan pemulihan token (G3) |
| 26 | **Metode dari paper dan standar** ([Landasan metode](LANDASAN_METODE.md)): interval Wilson dan uji McNemar untuk semua metrik (EVAL-09), uji fungsional berbasis templat (EVAL-10), *property-based testing* dan fuzzing (EVAL-11), uji silang Rust lawan prototipe Python (EVAL-12), catatan run holdout (EVAL-13), regex tanpa backtracking (POL-06), *skeleton* UTS #39 (POL-07, P1), JCS RFC 8785 untuk `policy_hash` (AUD-02), audit log berantai hash (AUD-06, P1), rilis bertanda tangan dengan SBOM dan provenance (DIST-08), dan benchmark tanpa *coordinated omission* (EVAL-05) | Klaim produk ini adalah angka deteksi dan jejak audit. Keduanya hanya dipercaya bila metodenya bisa diperiksa orang lain. Dengan ± 110 baris negatif per entitas, target false positive ≤ 2% per entitas bahkan belum bisa dibuktikan secara statistik (bagian 9) |

---

## 2. Ringkasan

OmniRail adalah proxy open-source di depan LLM. Ia menyamarkan data pribadi dan memblokir credentials sebelum request keluar, menegakkan kebijakan sederhana, lalu memvalidasi dan memulihkan jawaban. Semuanya dalam satu binary Rust tanpa GPU. Aplikasi cukup mengganti `base_url` ke OmniRail.

MVP dikirim dalam dua rilis (bagian 11). **Rilis α** membuktikan mutu deteksi: `omnirail inspect`, `eval`, `scan`, dan demo web yang berjalan sepenuhnya di browser. **Rilis β** menambahkan proxy dan menjadi rilis publik pertama.

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
| G5 | Hipotesis diferensiasi teruji sebelum fitur lanjutan dibangun | Bisnis | Gerbang Tahap 0 diputuskan tertulis; ≥ 3 wawancara tercatat di rilis α dan 5 sampai 10 sampai rilis β |

## 5. Non-goals

| Non-goal | Alasan |
| --- | --- |
| Menjadi gateway pengganti (fallback, load balancing, tracking biaya) | LiteLLM dan gateway lain sudah melakukannya. OmniRail dipasang di depan atau di samping gateway. Rute berdasarkan sensitivitas (7.16) bukan fallback: tujuannya ditentukan kebijakan data, bukan ketersediaan provider |
| Streaming sejati (token per token), tool call, gambar, dan format klien asli Anthropic atau Gemini | Streaming sejati bisa memecah token PII dan butuh desain buffer sendiri. Di MVP, `stream: true` dilayani sebagai pseudo-streaming (API-08): jawaban diperiksa penuh lebih dulu. Tool call dan gambar **ditolak eksplisit**, bukan diteruskan tanpa diperiksa |
| Deteksi PII bebas-bentuk (nama, alamat) | Butuh NER. Ditunda ke setelah MVP lewat ONNX lokal |
| Deteksi prompt injection yang andal | Deny-list hanya penyaring murah. Classifier menyusul. Klaim publik tidak boleh menyebut proteksi injection |
| Dasbor, admin API, rate limiting, Redis | Log terstruktur dan laporan `omnirail report` (7.15) cukup untuk MVP. Metrik OpenTelemetry menyusul (P1) |
| Klaim kepatuhan hukum | OmniRail adalah kontrol teknis pendukung. Persetujuan subjek data, DPIA, DPO, kontrak provider, notifikasi insiden, dan keabsahan transfer tetap urusan organisasi |

## 6. Persona dan user stories

Persona diurutkan menurut prioritas. Pembangun sendiri adalah pengguna pertama untuk persona P1 dan P2.

**P1. Engineer aplikasi (integrator)**

1. Sebagai engineer aplikasi, saya ingin cukup mengganti `base_url` dan kunci di SDK OpenAI agar aplikasi saya terlindungi tanpa menulis ulang kode.
2. Sebagai engineer aplikasi, saya ingin jawaban model berisi nilai asli (email, nomor HP) dan bukan token, agar pengguna akhir tidak melihat `<EMAIL_1>`.
3. Sebagai engineer aplikasi, saya ingin pesan error yang jelas dan berformat OpenAI saat request diblokir, agar aplikasi bisa menampilkan pesan yang tepat tanpa logika khusus.
4. Sebagai engineer aplikasi, saya ingin output JSON yang rusak diperbaiki otomatis dan dicek terhadap schema, agar parser di aplikasi tidak gagal.
5. *(Kasus tepi)* Sebagai engineer aplikasi, saya ingin request dengan `stream: true` tetap berjalan (jawaban dikirim setelah diperiksa penuh), sedangkan tool call atau gambar ditolak dengan pesan yang jelas, agar saya tahu bagian mana yang belum dilindungi dan tidak mengira datanya sudah diperiksa.

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

**P2b. Penanggung jawab kepatuhan di tampilan uji**

15. Sebagai penanggung jawab kepatuhan, saya ingin menempelkan contoh teks di halaman web lalu melihat bagian yang terdeteksi, jenisnya, dan aturan yang memicunya, agar saya bisa menilai sebuah pack tanpa menulis kode dan tanpa mengirim data ke provider.
16. Sebagai penanggung jawab kepatuhan, saya ingin membandingkan hasil `enforce` dan `shadow` untuk teks yang sama, agar saya tahu dampak penegakan sebelum mengaktifkannya.
17. Sebagai engineer aplikasi, saya ingin melihat teks bertoken yang akan dikirim ke provider dan jawaban setelah token dipulihkan, agar saya bisa memastikan jawaban tidak rusak sebelum memasang OmniRail di produksi.
18. Sebagai kontributor pack, saya ingin menjalankan evaluasi dan melihat kasus gagal (terlewat dan salah tandai) beserta selisih dengan baseline, agar saya tahu apakah perubahan aturan memperbaiki atau merusak.

**P5. Kontributor policy pack**

14. Sebagai kontributor pack, saya ingin menulis entitas dan aturan beserta contoh yang wajib terdeteksi dan wajib diabaikan, lalu menjalankan `omnirail test`, agar kualitas pack terbukti sebelum dibagikan.

**Tambahan v1.6**

19. Sebagai penanggung jawab kepatuhan, saya ingin laporan berkala tentang jenis data pribadi yang terkirim ke tiap provider, dari aplikasi dan rute mana, dikelompokkan menurut kategori data pribadi umum dan spesifik, agar saya bisa menilai besar risikonya sebelum memutuskan penegakan.
20. *(P1)* Sebagai penanggung jawab kepatuhan, saya ingin request yang memuat data pribadi spesifik diarahkan ke model lokal, agar data itu tidak keluar dari infrastruktur sendiri.
21. Sebagai engineer aplikasi, saya ingin memindai fixture tes, log, dan dataset di repo dengan aturan yang sama sebelum commit, agar data pribadi dan credentials tidak ikut ter-commit.
22. *(P1)* Sebagai engineer layanan pelanggan, saya ingin nomor yang diucapkan di transkrip panggilan ("nol delapan satu dua …") ikut tersamarkan, agar ringkasan panggilan tidak membocorkan nomor pelanggan.
23. Sebagai engineer aplikasi, saya ingin nomor yang dikirim pengguna sebagai jawaban atas pertanyaan asisten ("Boleh minta nomor rekeningnya?") tetap terdeteksi, agar data di percakapan CS tidak lolos hanya karena kata konteksnya ada di pesan sebelumnya.

## 7. Requirements

Prioritas: **P0** wajib untuk rilis awal, **P1** segera setelah rilis bila waktu tidak cukup, **P2** tidak dibangun sekarang tetapi desain tidak boleh menghalanginya.

Sejak v1.6, P0 dibagi menurut rilis. Daftar requirement per rilis ada di bagian 11: yang tercantum di **rilis α** wajib untuk rilis α, dan P0 lainnya wajib untuk rilis β (rilis publik pertama).

### 7.1 Alur pemrosesan

Urutan ini mengikat. Setiap langkah yang menolak request menghentikan alur dan tidak memanggil provider.

**Request**

1. Autentikasi kunci OmniRail.
2. Batas ukuran body (byte) dan parse JSON.
3. Tolak fitur yang belum didukung: `tools`/`functions`, konten non-teks, dan `n` > 1. Bila `stream: true`, catat untuk pseudo-streaming (API-08); request tetap diproses tanpa streaming ke provider.
4. Resolusi rute: alias model → provider + model, lalu cek `allowed_providers`.
5. Normalisasi teks untuk pencocokan (NFKC, casefold, hapus karakter lebar-nol). Teks yang dikirim ke provider tetap teks asli.
6. Batas panjang input (`max_input_chars`, dijumlah dari semua pesan).
7. Deteksi credentials.
8. Kebijakan: `deny_patterns` dan `blocked_keywords`.
9. Deteksi dan penyamaran PII (tokenize atau redact), termasuk kata konteks lintas pesan (PII-10).
9a. *(P1)* Rute sensitivitas: bila temuan memenuhi `on_sensitive` milik rute, tujuan diganti ke rute itu, lalu `allowed_providers` dicek ulang (7.16).
10. Ubah format ke adapter provider, lalu panggil upstream dengan timeout.

**Response**

1. Ubah format dari adapter ke format OpenAI.
2. Bila rute punya schema JSON: perbaiki sintaks, parse, pulihkan token di dalam nilai string, lalu validasi schema.
3. Bila tanpa schema: pulihkan token pada teks.
4. Tulis audit log, lalu kirim jawaban ke aplikasi. Bila `stream: true`, jawaban yang sudah final dikirim sebagai SSE (API-08).

### 7.2 API klien

| ID | Prioritas | Requirement |
| --- | --- | --- |
| API-01 | P0 | `POST /v1/chat/completions` kompatibel format OpenAI untuk teks, non-streaming |
| API-02 | P0 | Fitur yang belum didukung (`tools`/`functions`, konten non-teks, `n` > 1) ditolak dengan error eksplisit (bagian 8), bukan diteruskan |
| API-03 | P0 | Semua peran pesan (`system`, `user`, `assistant`) diperiksa, termasuk riwayat percakapan |
| API-04 | P0 | `GET /healthz` (proses hidup) dan `GET /readyz` (konfigurasi termuat, upstream terkonfigurasi) |
| API-05 | P1 | `GET /v1/models` mengembalikan daftar alias rute |
| API-06 | P2 | Streaming dengan buffer token, format klien asli Anthropic dan Gemini |
| API-07 | P0 | Field request yang didukung: `model`, `messages` (`role` dan `content` berupa string atau bagian `type: text`), `temperature`, `top_p`, `max_tokens` dan `max_completion_tokens`, `stop`, `n` (hanya 1), `response_format`, `seed`, dan `user`. Field lain dibuang dan dicatat (seperti UP-06). Field respons: `id`, `object`, `created`, `model` (alias rute), `choices[].message`, `choices[].finish_reason`, dan `usage` |
| API-08 | P0 | **Pseudo-streaming.** Request dengan `stream: true` diteruskan ke provider **tanpa** streaming. Setelah seluruh alur response selesai (pemulihan token, dan validasi bila ada), jawaban dikirim sebagai SSE format OpenAI (`chat.completion.chunk`), dipecah menjadi beberapa potongan dari teks final, lalu diakhiri `data: [DONE]`. `stream_options.include_usage` dihormati. Respons memuat header `x-omnirail-stream: buffered`. Error sebelum jawaban dikirim tetap memakai respons JSON biasa (bagian 8) |

Kriteria terima:

- [ ] SDK OpenAI resmi Python dan Node mendapat jawaban lewat OmniRail hanya dengan mengganti `base_url` dan kunci.
- [ ] SDK OpenAI Python dan Node dengan `stream=True` menerima jawaban lengkap lewat OmniRail; mock upstream membuktikan provider dipanggil tanpa streaming, dan token di potongan SSE sudah dipulihkan.
- [ ] Request dengan `tools` mendapat HTTP 400 kode `omnirail_unsupported_feature` dan provider tidak dipanggil.
- [ ] Request dengan bagian `image_url` mendapat HTTP 400 kode yang sama, dan provider tidak dipanggil.
- [ ] Email di pesan `assistant` dari giliran sebelumnya ikut ditokenisasi.
- [ ] Respons menyertakan header `x-omnirail-request-id`, yang sama dengan `request_id` di audit log.

### 7.3 Upstream dan rute

**Rute** adalah satu entri di `routes` (menggantikan `model_map` di blueprint). Nama alias dipakai aplikasi sebagai `model`. Rute bisa menimpa `fail_mode` dan schema JSON.

| ID | Prioritas | Requirement |
| --- | --- | --- |
| UP-01 | P0 | Satu format internal, adapter Ollama (untuk uji lokal), dan adapter **satu** provider cloud untuk rilis β: Anthropic Messages API, kecuali calon pengguna dari wawancara rilis α memakai provider lain (diputuskan di T-513) |
| UP-02 | P0 | Model yang tidak ada di `routes` ditolak dengan 404 `model_not_found`, kecuali ada rute `default` |
| UP-03 | P0 | Provider di luar `allowed_providers` ditolak saat konfigurasi divalidasi (start gagal) dan saat request (403) |
| UP-04 | P0 | Timeout upstream bisa diatur (default 60 detik). Tidak ada retry atau fallback antar-provider |
| UP-05 | P0 | Pemetaan adapter: pesan `system` ke `system` (Anthropic) atau `systemInstruction` (Gemini); `assistant` ke `model` (Gemini); `max_tokens` diisi default rute bila klien tidak mengirim (Anthropic mewajibkannya); `finish_reason` dan `usage` dipetakan ke format OpenAI |
| UP-06 | P0 | Parameter yang tidak didukung provider tujuan dibuang dan dicatat di log, tidak didiamkan |
| UP-07 | P0 | Body error dari provider tidak diteruskan mentah ke aplikasi atau log, karena bisa memuat ulang isi prompt |
| UP-08 | P1 | Adapter provider cloud lainnya (Anthropic Messages API, Gemini API, OpenAI passthrough) setelah rilis β, berurutan sesuai permintaan pengguna |

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
| PII-03 | P0 | Nilai yang sama dalam satu request selalu mendapat token yang sama; nilai berbeda mendapat token berbeda. "Sama" dinilai **setelah normalisasi per jenis**: hapus spasi, titik, dan tanda hubung; `+62` dan `62` di depan `phone_id` menjadi `0`; `email` dibandingkan dalam huruf kecil. Pemulihan memakai bentuk yang pertama kali muncul di request |
| PII-04 | P0 | Format token `<JENIS_n>`. Bila input sudah memuat teks berbentuk token (misalnya pengguna menulis `<EMAIL_1>`), penomoran melompati nomor itu, dan hanya token yang diterbitkan OmniRail yang dipulihkan |
| PII-05 | P0 | Tabel token hanya hidup di memori selama satu request dan tidak pernah ditulis ke log, disk, atau metrik. Isinya dihapus eksplisit dari memori (misalnya dengan crate `zeroize`) begitu request selesai |
| PII-06 | P0 | Pemulihan hanya untuk kecocokan persis. Token tak dikenal dibiarkan apa adanya. Token yang diterbitkan tetapi tidak kembali dihitung sebagai metrik, bukan error |
| PII-07 | P0 | Bila satu rentang teks lolos validator lebih dari satu entitas, kata konteks yang paling dekat menentukan jenisnya (misalnya `NIK` atau `kartu`). Tanpa kata konteks, dipakai urutan prioritas: credentials > `credit_card` (Luhn valid) > `nip` > `nik` (struktur valid) > `npwp` > `bpjs` > `bank_account` > `phone_id` > `passport_id` > `birth_date` > `email` > `ip_address` > `vehicle_plate`. Entitas yang mewajibkan kata konteks (`kk`, `passport_id`, `bpjs`, `birth_date`, `bank_account`) tidak pernah menang tanpa konteks; nilai 16 digit tanpa kata `KK` diperlakukan sebagai `nik`. Rentang yang tumpang tindih diselesaikan dengan memilih yang terpanjang |
| PII-08 | P1 | Entitas kustom di `omnirail.yaml` (customisasi tingkat 2) dengan validator bawaan yang bisa dipilih |
| PII-09 | P2 | NER lokal (ONNX) untuk nama, alamat, dan nama instansi |
| PII-10 | P0 | **Kata konteks lintas pesan.** Untuk entitas yang mewajibkan atau memakai kata konteks, bila nilai muncul dalam 10 kata pertama sebuah pesan, maka ≤ 15 kata terakhir pesan sebelumnya di `messages` (peran apa pun) ikut dihitung sebagai jendela konteks. Aturan PII-07 (kata konteks terdekat menentukan jenis) berlaku di jendela gabungan ini. Dataset: baris multi-pesan (`<<assistant>>`, `<<user>>`) di `eval/README.md` |
| PII-11 | P1 | **Angka terucap.** Urutan kata bilangan satu digit (`nol`/`kosong`, `satu` s.d. `sembilan`, serta `plus` untuk `+`), boleh bercampur digit, dinormalisasi menjadi digit sebelum validator dijalankan. Berlaku untuk `phone_id`, `nik`, `kk`, `bank_account`, `npwp`, dan `bpjs`, dengan kata konteks yang sama. Bilangan gabungan (`dua belas`, `delapan puluh`) tidak ditafsirkan. Temuan mencakup seluruh rentang kata asli, sehingga token menggantikan semua kata itu. Mati secara default (`ingress.pii.spoken_digits`) |
| PII-12 | P1 | Aksi per entitas tambahan: `mask` (sebagian nilai tetap terlihat, misalnya 4 digit terakhir kartu dan rekening, `3273••••••••0001` untuk NIK; tidak dipulihkan) dan `block` (request ditolak 400 `omnirail_policy_violation`, misalnya nomor kartu lengkap untuk organisasi yang terikat PCI DSS). Dalam mode shadow, `block` diperlakukan seperti credentials: nilai diredaksi, request diteruskan, dan dicatat `would_block` |
| PII-13 | P1 | **Pemulihan toleran**, opt-in per rute (`restore_variants`): variasi token yang lazim ditulis ulang model (`EMAIL_1`, `[EMAIL_1]`, `<email_1>`, `< EMAIL_1 >`) dipulihkan hanya bila token itu diterbitkan di request yang sama. Pemulihan variasi dihitung terpisah di audit log dan metrik. Default mati sampai eksperimen Q14 (T-207) memberi angka |

Kriteria terima:

- [ ] Untuk input "email saya a@b.co dan a@b.co", provider menerima dua kemunculan `<EMAIL_1>`, dan aplikasi menerima dua kemunculan `a@b.co`.
- [ ] Input yang sudah memuat `<EMAIL_1>` tidak dipulihkan menjadi email orang lain.
- [ ] `0812-3456-7801` dan `+62 812 3456 7801` dalam satu request mendapat token `<PHONE_ID_1>` yang sama.
- [ ] Nomor 16 digit yang lolos Luhn dan memiliki prefix kartu, tanpa kata konteks NIK, dikenali sebagai `credit_card`, bukan `nik`. Nilai yang sama setelah kata `NIK` dikenali sebagai `nik` (dataset D050 dan D051).
- [ ] Nomor pesanan 16 digit dengan tanggal tidak valid di posisi 7 sampai 12 tidak dikenali sebagai `nik`.
- [ ] Nilai 16 digit setelah kata `No. KK` dikenali sebagai `kk`; nilai yang sama tanpa kata konteks dikenali sebagai `nik`.
- [ ] "Mohon maaf lahir dan batin, 10-04-2026" tidak dikenali sebagai `birth_date`; "lahir 12/04/1974" dikenali.
- [ ] Pesan asisten "Boleh minta nomor rekeningnya untuk refund?" diikuti pesan pengguna "1234567890" menghasilkan `bank_account` di pesan pengguna; bila pesan asisten meminta nomor pesanan, tidak ada temuan.
- [ ] Kata `rekening` yang berjarak lebih dari 15 kata dari akhir pesan sebelumnya tidak menjadi kata konteks.
- [ ] `grep` nilai uji di semua log setelah menjalankan set uji tidak menemukan satu pun nilai.

### 7.5 Credentials

| ID | Prioritas | Requirement |
| --- | --- | --- |
| CRED-01 | P0 | Detektor: `api_key` (prefix dikenal seperti `sk-`, `sk-ant-`, `AIza`, `AKIA`, `ghp_`, `github_pat_`, `glpat-`, `xox?-`, Midtrans `Mid-server-` dan `SB-Mid-server-`, Xendit `xnd_production_` dan `xnd_development_` dengan sufiks berpanjang variabel yang bisa memuat `+`, `/`, dan `=`, serta token bot Telegram `\d{8,10}:[A-Za-z0-9_-]{35}`; kunci publik `xnd_public_` dan client key Midtrans tidak diblokir), `jwt` (tiga segmen base64url dengan header JSON berisi `alg`), `private_key` (blok `-----BEGIN ... PRIVATE KEY-----`), `connection_string` (skema basis data atau broker dengan password tidak kosong), `password_assignment` (`password`, `pwd`, `kata sandi` diikuti `:` atau `=`) |
| CRED-02 | P0 | Aksi `block` (default) atau `redact`. Credentials **tidak pernah** ditokenisasi dan tidak pernah dipulihkan |
| CRED-03 | P0 | Placeholder umum (`***`, `<password>`, `${VAR}`, `xxx`) tidak dianggap credentials |
| CRED-04 | P1 | Deteksi entropi tinggi setelah kata kunci (`token=`, `secret=`) untuk secret tanpa prefix |
| CRED-05 | P1 | Detektor credentials ekosistem lokal tambahan, misalnya token gateway WhatsApp (Fonnte, Wablas), payment gateway lain (DOKU, iPaymu, OY!, Flip), dan API logistik (RajaOngkir, Biteship). Hanya ditambahkan setelah format diverifikasi ke dokumentasi resmi masing-masing layanan dan dicatat di Lampiran A (T-326) |

Kriteria terima:

- [ ] Prompt yang memuat `postgres://app:s3cret@db:5432/x` diblokir dengan HTTP 400 `omnirail_policy_violation`, dan provider tidak dipanggil.
- [ ] Pesan error menyebut jenis (`connection_string`), tidak menyebut nilainya.
- [ ] `DATABASE_URL=${DATABASE_URL}` tidak diblokir.

### 7.6 Kebijakan, mode, dan fail mode

| ID | Prioritas | Requirement |
| --- | --- | --- |
| POL-01 | P0 | `max_input_chars` (total semua pesan) dan `server.max_body_bytes` (default 1 MiB) |
| POL-02 | P0 | `deny_patterns` (regex, tidak peka huruf besar) dan `blocked_keywords` (cocok per kata utuh), keduanya pada teks yang dinormalisasi (NFKC, UAX #15) |
| POL-03 | P0 | `allowed_providers` |
| POL-04 | P0 | `mode: enforce \| shadow`, global dan bisa ditimpa per rute |
| POL-05 | P0 | `fail_mode.ingress` dan `fail_mode.egress` (`open \| closed`), global dan bisa ditimpa per rute |
| POL-06 | P0 | Semua regex (pola entitas, `deny_patterns`, entitas kustom) dikompilasi dengan mesin tanpa backtracking yang menjamin waktu pencocokan linear terhadap panjang teks (crate Rust `regex`). Pola yang memakai look-around atau backreference ditolak saat pack dimuat, dengan pesan yang menyebut polanya. Ukuran regex hasil kompilasi dibatasi |
| POL-07 | P1 | Pencocokan deny-list dan kata kunci juga memakai *skeleton* confusables UTS #39, sehingga huruf mirip lintas aksara (misalnya huruf Kiril yang tampak seperti Latin) tidak bisa dipakai untuk menghindar |

**Semantik mode shadow**

| Kontrol | `enforce` | `shadow` |
| --- | --- | --- |
| Blokir kebijakan (deny, kata kunci, panjang input) | Tolak request | Teruskan, catat `would_block` |
| Credentials | Tolak request (`block`) | **Diredaksi**, diteruskan, catat `would_block` |
| PII beraksi `block` (P1, PII-12) | Tolak request | Diredaksi, diteruskan, catat `would_block` |
| Penyamaran PII | Diterapkan | Diterapkan bila `shadow.apply_transforms: true` (default); bila `false`, hanya dicatat |
| `allowed_providers` | Tolak request | **Tetap ditolak** (bukan kontrol yang diuji, melainkan batas keras) |
| Validasi schema JSON | Mengikuti `fail_mode.egress` | Selalu diteruskan, catat hasilnya |
| Rute sensitivitas (P1, 7.16) | Diarahkan ke rute tujuan | Tidak diarahkan, catat `would_route` |

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
| AUD-02 | P0 | `policy_hash` = SHA-256 dari kebijakan efektif (default + pack + override `omnirail.yaml`) yang diserialisasi dengan JSON Canonicalization Scheme (RFC 8785), **tanpa** nilai rahasia, sehingga pihak lain bisa menghitung ulang hash yang sama. `policy_version` = versi `omnirail.yaml` + nama dan versi setiap pack |
| AUD-03 | P0 | `store_raw_prompts: false` secara default. Bila `true`, start mencetak peringatan dan field ini ikut tercatat di audit log |
| AUD-04 | P1 | Metrik OpenTelemetry (OTLP): jumlah request per keputusan, temuan per jenis entitas, latensi proxy dan upstream (histogram), hasil JSON, dan statistik pemulihan token. Turun dari P0 di v1.6; selama MVP, audit log dan `omnirail report` (7.15) menjadi sumber angka |
| AUD-05 | P1 | Ekspor ringkasan audit untuk auditor (cikal bakal "laporan bukti pendukung") |
| AUD-06 | P1 | **Audit log tahan ubah.** Setiap baris memuat `prev_hash` (SHA-256 baris sebelumnya), dan secara berkala ditulis *checkpoint* bertanda tangan berisi hash terakhir dan jumlah baris. `omnirail audit verify <file>` mendeteksi baris yang dihapus, disisipkan, atau diubah. Dasar: log berantai hash dan struktur *tamper-evident* (Landasan metode bagian 4) |

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
| `stream` | `true` bila jawaban dikirim sebagai pseudo-streaming (API-08) |
| `routed_from`, `route_reason` | *(P1)* Rute asal dan alasan pengalihan (jenis atau kategori data, tanpa nilai) bila rute sensitivitas aktif (7.16) |
| `tokens` | Jumlah token diterbitkan, dipulihkan, dan hilang |
| `policy_version`, `policy_hash`, `omnirail_version` | Untuk penelusuran |

### 7.8 Validasi output JSON

Sejak v1.6 seluruh bagian ini **P1** (setelah rilis β). Provider utama sudah punya structured output bawaan, dan validasi JSON tidak menguji hipotesis inti produk. Urutan alur response di 7.1 tetap menyisakan tempat untuk langkah ini, sehingga desainnya tidak berubah.

| ID | Prioritas | Requirement |
| --- | --- | --- |
| JSON-01 | P1 | Schema per rute (`routes.<alias>.json_schema_file`). Rute tanpa schema tidak divalidasi |
| JSON-02 | P1 | Perbaikan sintaks lokal: buang pagar kode markdown, koma ekstra, kurung yang tidak tertutup di akhir, dan kutip tunggal |
| JSON-03 | P1 | Urutan: perbaiki → parse → pulihkan token di nilai string → validasi schema → serialisasi ulang |
| JSON-04 | P1 | Pelanggaran schema mengikuti `fail_mode.egress`: `open` meneruskan dengan header `x-omnirail-json: invalid`, `closed` mengembalikan 502 `omnirail_output_invalid` |
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
| CFG-10 | P0 | `omnirail validate --config <file>` untuk CI di repo pengguna: memvalidasi konfigurasi, menjalankan tes semua pack yang dimuat, lalu mencetak `policy_version` dan `policy_hash`. Kode keluar bukan nol bila gagal. Disertai contoh `CODEOWNERS` dan workflow CI di dokumentasi, sehingga perubahan kebijakan hanya lewat pull request yang disetujui peran yang ditetapkan |

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
| EVAL-05 | P0 | Benchmark latensi: mock upstream dengan waktu tetap, input 1 rb, 5 rb, dan 20 rb karakter, mengukur selisih p50 dan p99 dengan dan tanpa proxy. Beban dikirim pada laju tetap (open-loop), latensi dihitung dari jadwal kirim untuk menghindari *coordinated omission*, dan distribusi disimpan dengan HdrHistogram. Hasil mencantumkan perangkat keras, laju, dan durasi |
| EVAL-06 | P0 | CLI `omnirail inspect "<teks>"` (atau `--file`) menampilkan keputusan, temuan, dan teks bertoken tanpa memanggil provider. Memakai fungsi yang sama dengan endpoint PG-01 |
| EVAL-07 | P0 | `omnirail scan <path>...` memindai berkas teks (log, CSV, JSON, Markdown, kode) dengan pack yang sama dengan jalur proxy. Keluaran per temuan: `path:baris:kolom`, jenis, dan nilai yang **disamarkan** (`3273••••••••0001`); format `text` dan `json` (SARIF P1). Kode keluar 1 bila ada temuan. Berkas biner dan berkas di atas batas ukuran dilewati. Pengecualian lewat `.omnirailignore` dan komentar `omnirail:ignore` di baris yang sama |
| EVAL-08 | P0 | Contoh pemasangan `omnirail scan` sebagai hook pre-commit dan sebagai langkah CI, di dokumentasi rilis α |
| EVAL-09 | P0 | **Ketidakpastian dilaporkan.** Setiap recall, precision, dan false positive rate dari `omnirail eval` disertai interval kepercayaan Wilson 95% dan jumlah sampelnya. Perbandingan dua sistem atau dua versi pada baris yang sama memakai uji McNemar eksak per baris. Recall juga dilaporkan per kelompok identifier langsung (`nik`, `kk`, `credit_card`, dan seterusnya) dan kuasi (`birth_date`, `vehicle_plate`, `ip_address`), mengikuti TAB. Implementasi rujukan: `eval/tools/statistik.py` |
| EVAL-10 | P0 | **Uji perilaku** berupa uji fungsional berbasis templat (seperti Multilingual HateCheck), dibangkitkan dari templat dan dijalankan di CI: tes fungsi minimum per entitas, dan tes invarian (mengubah pemisah, huruf besar-kecil, bingkai teks, atau gaya ketik tidak boleh mengubah temuan, kecuali perubahan itu memang membuat nilai tidak valid) |
| EVAL-11 | P0 | ***Property-based testing*** untuk invarian inti: `pulihkan(samarkan(x)) = x` untuk teks tanpa token buatan pengguna, teks bertoken tidak memuat nilai entitas yang terdeteksi, normalisasi idempoten, dan peta posisi normalisasi selalu menunjuk ke rentang teks asli yang sah. Fuzzing (P1) untuk normalisasi Unicode dan parser request |
| EVAL-12 | P0 | **Uji silang**: temuan implementasi Rust sama dengan prototipe referensi Python (T-011) pada seluruh dataset dev. Setiap perbedaan diselesaikan dengan memperbaiki salah satunya, atau dicatat sebagai keputusan |
| EVAL-13 | P0 | **Catatan run holdout.** Setiap kali holdout dijalankan, tanggal, commit, versi pack, dan hasilnya dicatat di `eval/results/holdout.md`. Holdout dijalankan sekali per rilis. Bila aturan disetel ulang setelah melihat hasil holdout, holdout itu dianggap terpakai dan holdout baru disusun sebelum rilis berikutnya |

Kriteria terima `omnirail scan`:

- [ ] Menjalankan `omnirail scan eval/dev/` menemukan nilai positif dataset dan tidak pernah mencetak nilai mentah, kecuali dengan `--show-values`.
- [ ] Baris yang diberi komentar `omnirail:ignore` dan path di `.omnirailignore` tidak dilaporkan.
- [ ] Untuk teks yang sama, temuan `scan` identik dengan `inspect`.

### 7.12 Distribusi

| ID | Prioritas | Requirement |
| --- | --- | --- |
| DIST-01 | P0 | Binary rilis untuk Linux x86_64 dan arm64, dan macOS arm64. Windows menyusul (Q9) |
| DIST-02 | P0 | Image container minimal (distroless atau scratch) |
| DIST-03 | P0 | README dengan quickstart ≤ 5 langkah, batas klaim (bagian 10), dan hasil benchmark terbaru |
| DIST-04 | P1 | Contoh pemasangan di depan LiteLLM |
| DIST-05 | P0 | `SECURITY.md` (cara melaporkan kerentanan secara privat, versi yang didukung), `CONTRIBUTING.md`, dan `CODEOWNERS` untuk repo OmniRail sendiri, termasuk folder `policy-packs/` |
| DIST-06 | P0 | **Demo web WASM.** `omnirail-core` dikompilasi ke WebAssembly dan disajikan sebagai halaman statis (misalnya GitHub Pages) berisi tab Coba mode periksa saja (PG-03, PG-06, PG-07 berlaku). Halaman tidak mengirim permintaan jaringan apa pun setelah dimuat (`Content-Security-Policy: connect-src 'none'`), sehingga teks tidak pernah meninggalkan browser. Hasil identik dengan `omnirail inspect` versi yang sama |
| DIST-07 | P1 | **Benchmark terbuka.** Split `dev` diterbitkan sebagai dataset publik berbahasa Indonesia, dengan kartu dataset, lisensi (Q15), dan tabel skor alat lain dari Tahap 0. Holdout tidak diterbitkan |
| DIST-08 | P0 | **Rilis yang bisa diverifikasi.** Setiap binary dan image rilis ditandatangani (Sigstore atau GitHub artifact attestations) dengan provenance build (SLSA) dan disertai SBOM (SPDX atau CycloneDX). CI menjalankan `cargo audit` dan `cargo deny` (advisori keamanan dan lisensi dependensi). `omnirail-core` memakai `#![forbid(unsafe_code)]`. Repo memasang OpenSSF Scorecard. README menjelaskan cara memverifikasi tanda tangan |

### 7.13 Tampilan uji (playground)

Satu halaman web untuk mencoba kebijakan tanpa menulis kode. Halaman ini memakai fungsi inti yang sama dengan jalur proxy, sehingga hasilnya identik dengan perilaku produksi untuk konfigurasi yang sama. Tampilan uji **bukan** dasbor pemantauan dan **tidak bisa** mengubah konfigurasi.

Sejak v1.6, tab Coba mode periksa saja dikirim lebih dulu sebagai demo WASM (DIST-06) di rilis α, sehingga teks diperiksa di browser tanpa server. Penyajian halaman yang sama dari binary (PG-04, PG-05) turun ke P1, dan dibutuhkan saat pengguna ingin mencoba pack atau konfigurasi milik mereka sendiri, atau saat fitur P1 seperti kirim ke provider dibangun.

| ID | Prioritas | Requirement |
| --- | --- | --- |
| PG-01 | P0 | `POST /omnirail/v1/inspect` menerima `text` atau `messages`, serta `pack` dan `mode` opsional. Endpoint menjalankan alur request 7.1 langkah 5 s.d. 9 **tanpa** memanggil provider, lalu mengembalikan keputusan, daftar temuan, teks bertoken, waktu proses, `policy_version`, dan `policy_hash`. Temuan dikembalikan sebagai **posisi** (`start`, `end`), bukan nilai, karena klien sudah memegang teksnya |
| PG-02 | P0 | `GET /omnirail/v1/packs` mengembalikan pack yang termuat (nama, versi, jumlah entitas dan aturan) |
| PG-03 | P0 | **Tab Coba** mode periksa saja: kotak teks, pilihan pack dan mode, hasil berwarna per entitas, tabel temuan, teks bertoken, keputusan, waktu proses, versi dan hash kebijakan. Rilis α: di demo WASM (DIST-06), memanggil fungsi `inspect` langsung. Setelah rilis β: juga di `/playground` yang disajikan binary, memakai PG-01 |
| PG-04 | P1 | Berkas halaman (HTML, CSS, JS) ditanam di binary, tanpa CDN atau skrip pihak ketiga, dan tetap berfungsi tanpa internet. Header `Content-Security-Policy: default-src 'self'`. Ukuran total ≤ 200 KB |
| PG-05 | P1 | Tampilan uji **mati secara default** (`playground.enabled: false`). Saat aktif, hanya melayani dari loopback, kecuali `playground.admin_keys` diisi. Kunci admin terpisah dari kunci aplikasi, dan kunci aplikasi ditolak dengan 403 `omnirail_admin_required` |
| PG-06 | P0 | Teks input tidak disimpan di server, log, atau `localStorage` browser. Audit log hanya mencatat `source: playground`, keputusan, dan jumlah temuan per entitas |
| PG-07 | P0 | Nilai di tabel temuan disamarkan secara default (misalnya `3273••••••••0001`); tombol "Tampilkan" hanya membuka nilai di browser, tanpa permintaan ke server |
| PG-08 | P1 | Tombol **Kirim ke provider** di tab Coba, lewat `POST /omnirail/v1/playground/send`: alur penuh dengan kunci provider di proxy. Menampilkan berdampingan teks bertoken yang dikirim, jawaban provider (bertoken), dan jawaban setelah dipulihkan. Rute dibatasi oleh `playground.allowed_routes` |
| PG-09 | P1 | Bandingkan `enforce` dan `shadow` untuk teks yang sama dalam satu tampilan |
| PG-10 | P1 | Matikan atau nyalakan entitas untuk satu kali percobaan. Override ini tidak disimpan, ditandai "tidak berlaku untuk trafik", dan menghasilkan hash kebijakan sementara yang berbeda |
| PG-11 | P1 | **Tab Evaluasi** lewat `POST /omnirail/v1/eval`: pilih dataset dari daftar yang diizinkan (`playground.datasets`) dan pack, jalankan, lalu tampilkan metrik per entitas, selisih dengan baseline (naik atau turun), dan daftar kasus gagal yang bisa disaring (terlewat atau salah tandai). Hasil bisa diunduh sebagai JSON dan Markdown, dengan format sama seperti `omnirail eval` |
| PG-12 | P1 | Dataset `holdout` terkunci di tab Evaluasi; membukanya butuh konfirmasi eksplisit dan tercatat di audit log |
| PG-13 | P2 | Contoh teks siap pakai dari `should_detect` dan `should_ignore` pack yang termuat |

**Wireframe tab Coba**

```text
┌ OmniRail · Tampilan uji ─────────────────────── kebijakan v1.1 · a3f9c2 · LOKAL ┐
│ [ Coba ]  [ Evaluasi ]                                                          │
├────────────────────────────────────┬────────────────────────────────────────────┤
│ Pack  [ id-general ▾ ]             │ Keputusan:  ● DIBLOKIR  (credentials)       │
│ Mode  (•) enforce  ( ) shadow      │ Waktu proses: 0,8 ms                        │
│                                    │                                             │
│ ┌────────────────────────────────┐ │ Teks asli                                   │
│ │ Halo, NIK saya 3273...0001,    │ │ Halo, NIK saya [nik ███████] , HP           │
│ │ HP 0812-3456-7801. Password    │ │ [phone_id ███████]. Password=[credential]   │
│ │ DB=Rahasia#2026                │ │                                             │
│ └────────────────────────────────┘ │ Dikirim ke provider                         │
│ 0 / 20.000 karakter                │ (tidak dikirim: request diblokir)           │
│                                    │                                             │
│ [ Periksa ]  [ Kirim ke provider ] │ Temuan                                      │
│              (P1, perlu rute)      │ Entitas   Nilai          Validator  Aksi    │
│                                    │ nik       3273••••0001   struktur   tokenize│
│ Override sementara (P1)            │ phone_id  0812••••7801   panjang    tokenize│
│ [x] nik [x] phone_id [x] email ... │ password  ••••••••       pola       block   │
│                                    │ [ Tampilkan nilai ]                         │
└────────────────────────────────────┴────────────────────────────────────────────┘
```

**Wireframe tab Evaluasi (P1)**

```text
Dataset [ dev ▾ ]  Pack [ id-general ▾ ]  [ Jalankan ]    Baseline: run 2026-11-20 (v0.5)
Entitas       Recall        Precision     False positive
nik           0,97 (+0,02)  0,93 (−0,01)  0,01 (=)
bank_account  0,84 (+0,05)  0,88 (+0,03)  0,03 (−0,01)
...
Kasus gagal: [ Semua ▾ ] [ Terlewat ] [ Salah tandai ]
D025  phone_id  salah tandai  "Nomor pesanan 0857…"  catatan: negatif sulit
[ Unduh JSON ]  [ Unduh Markdown ]
```

Kriteria terima:

- [ ] Dengan konfigurasi default, `GET /playground` mengembalikan 404.
- [ ] Dengan `playground.enabled: true` dan `listen` bukan loopback tanpa `admin_keys`, start gagal dengan pesan yang jelas.
- [ ] Untuk teks dan konfigurasi yang sama, keputusan dan temuan di tab Coba identik dengan audit log dari jalur proxy.
- [ ] Respons PG-01 tidak memuat nilai entitas mentah (diuji dengan `grep` nilai uji pada body respons).
- [ ] Mode periksa saja tidak pernah memanggil upstream (diuji dengan mock yang gagal bila dipanggil).
- [ ] Setelah halaman ditutup, tidak ada teks input di `localStorage`, `sessionStorage`, maupun log server.
- [ ] Halaman bisa dipakai penuh dengan keyboard. Sorotan entitas tidak hanya dibedakan dengan warna, tetapi juga label jenis. Kontras teks memenuhi WCAG 2.1 AA.
- [ ] Halaman berfungsi tanpa koneksi internet.
- [ ] Demo WASM tidak mengirim permintaan jaringan setelah halaman dimuat (uji E2E memblokir dan mencatat semua request setelah `load`).

### 7.14 Referensi konfigurasi

Seluruh kunci `omnirail.yaml` untuk MVP di satu tempat. Nilai yang ditulis adalah default. Kunci bertanda `# P1` belum dibaca di MVP.

```yaml
version: "1.4"
mode: enforce                    # enforce | shadow (7.6)
policy_pack: id-general
shadow:
  apply_transforms: true         # penyamaran PII tetap jalan dalam shadow (7.6)

server:
  listen: "127.0.0.1:8080"       # CFG-06
  api_keys: ["${OMNIRAIL_KEY}"]  # kunci aplikasi
  max_body_bytes: 1048576        # POL-01

upstream:
  timeout_seconds: 60            # UP-04
  providers:
    anthropic: { api_key: "${ANTHROPIC_API_KEY}" }
    gemini:    { api_key: "${GEMINI_API_KEY}" }
    openai:    { api_key: "${OPENAI_API_KEY}" }
    ollama:    { base_url: "http://localhost:11434" }

routes:                          # rute = alias model (7.3)
  default:
    provider: anthropic
    model: "claude-sonnet-5-5"
    max_tokens: 1024             # dipakai bila klien tidak mengirim (UP-05)
    json_schema_file: null       # JSON-01 (P1)
    on_sensitive: null           # P1, 7.16
    restore_variants: false      # P1, PII-13
    mode: null                   # null = ikut global
    fail_mode: null              # null = ikut global

ingress:
  pii:
    action: tokenize             # tokenize | redact | mask (P1) | block (P1), bisa per entitas
    restore_on_egress: true
    cross_message_context: true  # PII-10
    spoken_digits: false         # P1, PII-11
    entities: [email, phone_id, credit_card, nik, kk, nip, npwp, passport_id, bpjs, bank_account, birth_date]
    # vehicle_plate dan ip_address (P1) mati secara default
  credentials:
    action: block                # block | redact
    detectors: [api_key, jwt, private_key, connection_string, password_assignment]
  policy:
    max_input_chars: 20000
    allowed_providers: [anthropic, gemini, openai, ollama]
    deny_patterns: []            # diisi pack
    blocked_keywords: []

fail_mode:
  ingress: closed
  egress: open

audit:
  log_policy_version: true
  sink: stdout                   # stdout | file (Q8)
  file_path: null

logging:
  store_raw_prompts: false

telemetry:                       # P1
  otlp_endpoint: null            # AUD-04; null = metrik mati

playground:                      # 7.13
  enabled: false
  admin_keys: []                 # wajib bila listen bukan loopback
  allowed_routes: []             # P1, PG-08
  datasets: []                   # P1, PG-11
```

Kriteria terima:

- [ ] Kunci yang tidak dikenal menghentikan start dengan pesan berisi nama kunci, sehingga salah ketik tidak diam-diam diabaikan.
- [ ] Contoh di atas dimuat tanpa error oleh `omnirail validate` dan dipakai sebagai berkas contoh di repo.

### 7.15 Laporan paparan data

`omnirail report` merangkum audit log (7.7) menjadi laporan yang bisa dibaca penanggung jawab kepatuhan. Laporan hanya memakai isi audit log, yang memang tidak memuat nilai PII, sehingga laporan pun tidak bisa memuat nilai.

| ID | Prioritas | Requirement |
| --- | --- | --- |
| REP-01 | P0 | `omnirail report --audit <file>... [--since 7d] [--format md\|json]` menghasilkan: jumlah request per keputusan (`allow`, `block`, `would_block`, `error`); temuan per jenis entitas, per provider, per rute, dan per `api_key_id`; credentials per jenis; aturan `would_block` terbanyak (mode shadow); serta tren harian. Setiap laporan memuat `policy_version` dan `policy_hash` yang berlaku di rentang waktunya |
| REP-02 | P0 | Setiap entitas di pack punya atribut `kategori_pdp` (`umum` atau `spesifik`). Laporan mengelompokkan temuan menurut kategori ini. Pemetaan di bawah adalah **draf**: laporan menandainya "belum ditinjau" sampai Q6 terjawab, dan setiap laporan memuat kalimat batas klaim (bagian 10) |
| REP-03 | P1 | Ekspor laporan untuk auditor (menggantikan AUD-05), dengan ringkasan per bulan dan lampiran hasil `omnirail eval` versi yang berlaku |

Draf pemetaan `kategori_pdp`. Dasarnya UU 27/2022 Pasal 4, yang memasukkan data keuangan pribadi dan data kesehatan ke data pribadi spesifik. Pemetaan ini wajib ditinjau penanggung jawab kepatuhan (Q6) sebelum dipakai di materi publik.

| Entitas | Draf kategori | Catatan |
| --- | --- | --- |
| `credit_card`, `bank_account` | spesifik | Data keuangan pribadi |
| `npwp` | spesifik (perlu ditinjau) | Terkait data keuangan; NPWP orang pribadi sama dengan NIK |
| `bpjs` | spesifik (perlu ditinjau) | Nomor kepesertaan, bukan data kesehatan itu sendiri |
| `nik`, `kk`, `nip`, `passport_id`, `email`, `phone_id`, `birth_date` | umum | Data yang dapat mengidentifikasi, terutama bila dikombinasikan |
| `vehicle_plate`, `ip_address` | umum (perlu ditinjau) | Status sebagai data pribadi bergantung konteks (Q12) |

Contoh ringkasan (Markdown):

```text
Laporan paparan data · 4–10 Nov 2026 · kebijakan v1.1 · a3f9c2 · mode shadow
Request: 18.240 (allow 17.912 · would_block 328)
Data pribadi spesifik ke provider luar: 353 temuan (bank_account 312, credit_card 41)
Credentials: 4 (api_key: xnd_production_ 3, connection_string 1) — semua diredaksi
Terbanyak per rute: ringkas-chat-cs (nik 1.022, phone_id 884, bank_account 301)
Kategori PDP: draf, belum ditinjau penanggung jawab kepatuhan.
OmniRail mengurangi risiko, tidak menjamin kepatuhan.
```

Kriteria terima:

- [ ] Laporan dari audit log hasil menjalankan set uji tidak memuat satu pun nilai uji (`grep`).
- [ ] Angka di laporan sama dengan hitungan manual dari audit log yang sama.
- [ ] Waktu dari memasang mode shadow sampai laporan pertama ≤ 30 menit, diukur pada 3 orang (bagian 9).

### 7.16 Rute berdasarkan sensitivitas (P1)

Request yang memuat data tertentu bisa diarahkan ke rute lain, misalnya model lokal lewat Ollama. Ini keputusan kebijakan yang tercatat di audit log, **bukan** fallback karena provider gagal.

| ID | Prioritas | Requirement |
| --- | --- | --- |
| ROUTE-01 | P1 | `routes.<alias>.on_sensitive: { when: <daftar entitas atau kategori_pdp>, route: <alias> }`. Dievaluasi setelah deteksi PII (7.1 langkah 9a). Rute tujuan tetap dicek `allowed_providers`. Pengalihan berantai tidak diizinkan (divalidasi saat start) |
| ROUTE-02 | P1 | `pii_action: keep` (default: penyamaran tetap berlaku) atau `passthrough` (nilai asli dikirim). `passthrough` hanya diizinkan bila provider tujuan bertanda `local: true` (misalnya Ollama atau endpoint di jaringan sendiri), dan ini dicek saat start. Credentials tetap diblokir dalam keadaan apa pun |
| ROUTE-03 | P1 | Audit log mencatat `routed_from` dan `route_reason`; dalam mode shadow, request tidak dialihkan dan dicatat sebagai `would_route` |

Contoh:

```yaml
upstream:
  providers:
    anthropic: { api_key: "${ANTHROPIC_API_KEY}" }
    ollama:    { base_url: "http://10.0.0.5:11434", local: true }
routes:
  ringkas-chat-cs:
    provider: anthropic
    model: "claude-sonnet-5-5"
    on_sensitive:
      when: [kategori_pdp: spesifik]
      route: ringkas-lokal
  ringkas-lokal:
    provider: ollama
    model: "qwen3:8b"
    pii_action: passthrough
```

Kriteria terima:

- [ ] Request berisi `bank_account` ke `ringkas-chat-cs` diteruskan ke Ollama (mock), dan provider cloud tidak dipanggil.
- [ ] `pii_action: passthrough` ke provider tanpa `local: true` menghentikan start dengan pesan yang jelas.
- [ ] Dalam shadow, request tetap ke provider awal dan audit log mencatat `would_route`.

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
| 400 | `omnirail_unsupported_feature` | Tool call, konten non-teks, `n` > 1 (`stream: true` tidak ditolak, lihat API-08) |
| 401 | `invalid_api_key` | Kunci OmniRail salah atau tidak ada |
| 403 | `omnirail_admin_required` | Endpoint tampilan uji dipanggil dengan kunci aplikasi, atau dari luar loopback tanpa kunci admin |
| 403 | `omnirail_provider_not_allowed` | Rute menunjuk provider di luar `allowed_providers` |
| 404 | `model_not_found` | Alias tidak ada dan tidak ada rute `default` |
| 413 | `omnirail_input_too_large` | Melewati `max_body_bytes` atau `max_input_chars` |
| 502 | `omnirail_upstream_error` | Provider mengembalikan error (body provider tidak diteruskan) |
| 502 | `omnirail_output_invalid` | Schema gagal dan `fail_mode.egress: closed` |
| 503 | `omnirail_guard_unavailable` | Guard gagal dan `fail_mode.ingress: closed` |
| 504 | `omnirail_upstream_timeout` | Melewati timeout upstream |

Pesan error menyebut jenis temuan, tidak pernah nilainya.

## 9. Metrik keberhasilan

Angka di bawah adalah **target awal (hipotesis)**. Angka ini memberi kriteria lulus yang bisa diperiksa per tahap, lalu direvisi tertulis setelah baseline Tahap 1 dan benchmark Tahap 5. Revisi dicatat di bagian 14.

**Cara membaca target (EVAL-09).** Setiap angka dilaporkan dengan interval Wilson 95%. Target dianggap tercapai bila angka titiknya memenuhi target **dan** batas bawah interval (untuk recall dan precision) atau batas atasnya (untuk false positive) tidak meleset lebih dari 5 poin dari target. Target false positive ≤ 0,02 dinilai pada **gabungan** baris negatif, karena dengan ± 110 baris negatif per entitas, nol false positive pun hanya memberi batas atas 3,4%. Angka per entitas tetap dilaporkan beserta intervalnya. Lihat [Landasan metode](LANDASAN_METODE.md) bagian 1.

**Indikator awal (diukur per rilis, dari `omnirail eval` dan benchmark)**

| Metrik | Target awal | Sumber |
| --- | --- | --- |
| Tingkat blokir credentials | ≥ 0,95 | Baris kredensial, `dev` dan `holdout` |
| Recall `email`, `credit_card`, `nik` | ≥ 0,95 | Baris positif |
| Recall `phone_id`, `npwp` | ≥ 0,90 | Baris positif |
| Recall `nip`, `kk` | ≥ 0,95 | Baris positif |
| Recall `passport_id`, `bpjs`, `birth_date` (dengan kata konteks) | ≥ 0,90 | Baris positif |
| Recall `bank_account` (dengan kata konteks) | ≥ 0,80 | Baris positif |
| Recall entitas berkonteks wajib pada baris multi-pesan (PII-10) | ≥ 0,90 | Baris positif lintas pesan |
| Recall angka terucap (PII-11, P1) | Dilaporkan terpisah, tanpa target sampai PII-11 dibangun | Baris `cakupan_mvp = tidak` bercatatan angka terucap |
| Precision per entitas | ≥ 0,90 | Baris positif dan negatif |
| False positive pada baris negatif | ≤ 0,02 | Baris negatif (termasuk nomor resi dan nomor pesanan) |
| Pemulihan token (token yang dikembalikan model secara persis) | ≥ 0,99 | Baris positif lewat mock dan provider nyata |
| Overhead latensi, input 5 rb karakter | p50 ≤ 5 ms, p99 ≤ 15 ms | Benchmark EVAL-05 |
| Output JSON valid setelah perbaikan tanpa retry (P1) | ≥ 0,95 dari output yang rusak sintaks | Set uji JSON |
| Waktu dari unduh sampai request pertama berhasil | ≤ 10 menit | Diukur pada 3 orang yang belum pernah memakai |
| Waktu dari memasang mode shadow sampai laporan paparan pertama (REP-01) | ≤ 30 menit | Diukur pada 3 orang yang belum pernah memakai |
| Waktu dari membuka demo WASM sampai melihat temuan pertama | ≤ 1 menit | Sesi wawancara rilis α |
| Tugas "coba pack lalu jelaskan satu temuan" di tampilan uji tanpa bantuan | ≥ 3 dari 5 peserta wawancara, ≤ 5 menit | Sesi wawancara rilis α dan β |

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
| Data tak diperiksa lewat streaming, gambar, atau tool call | Ya | Streaming di-buffer penuh lalu dikirim sebagai pseudo-streaming (API-08); gambar dan tool call ditolak eksplisit (API-02) |
| Nomor di transkrip suara (angka terucap) | Tidak | PII-11 (P1); celahnya terlihat di dataset sebagai baris di luar cakupan |
| Data pribadi ter-commit ke repo (fixture, log, dataset) | Sebagian | `omnirail scan` di pre-commit dan CI (EVAL-07, EVAL-08) |
| Penghindaran deny-list dengan Unicode | Sebagian | Normalisasi NFKC dan lebar-nol; parafrase tetap lolos |
| Kebocoran lewat log atau error provider | Ya | Nilai PII tidak pernah ditulis; body error provider tidak diteruskan |
| Proxy terbuka ke jaringan | Ya | Default `127.0.0.1`, kunci OmniRail wajib |
| Tampilan uji menjadi celah (data input bocor, kunci provider dipakai pihak lain) | Ya | Mati secara default, loopback atau kunci admin terpisah, input tidak disimpan, nilai disamarkan, kirim ke provider dibatasi rute (PG-05 s.d. PG-08) |
| Kebocoran kunci provider | Sebagian | Kunci hanya di proxy; rotasi dan rate limit per kunci ditunda |
| Proxy gagal atau lambat | Ya | `fail_mode` per rute, health check, timeout |

**Wajib tertulis di README:** lampiran dan gambar ditolak (tidak diperiksa), tokenisasi berlaku per request, OmniRail tidak mengklaim kepatuhan hukum apa pun (termasuk UU PDP dan panduan OJK), dan kalimat publik memakai "mengurangi risiko", bukan "melindungi sepenuhnya".

**Istilah.** Tokenisasi OmniRail adalah **pseudonimisasi reversibel** (ISO/IEC 27559:2022, NIST SP 800-188), bukan anonimisasi: teks bertoken tetap bisa dikaitkan kembali selama tabel token ada. Materi publik tidak boleh menyebut data yang dikirim ke provider sebagai "anonim".

Pemetaan ancaman ke OWASP Top 10 for LLM Applications dan model ancaman privasi LINDDUN ada di [Landasan metode](LANDASAN_METODE.md) bagian 7, dan dirinci di T-342.

Pemetaan ke regulasi (UU 27/2022, panduan OJK) tetap di blueprint bagian 6 dan 7. Pemetaan itu perlu dicocokkan dengan naskah resmi oleh penanggung jawab kepatuhan sebelum dipakai di materi publik (Q6).

## 11. Tahapan dan kriteria selesai

Belum ada tanggal. Kecepatan kerja ditetapkan setelah Tahap 1. Satu-satunya tanggal eksternal yang relevan: menurut Hukumonline, PP 33/2026 berlaku 16 Januari 2027. Tanggal ini konteks pasar, bukan komitmen rilis.

| Tahap | Isi | Selesai bila |
| --- | --- | --- |
| **0. Validasi** (maks. 2 minggu) | Susun `uji_pii_id.csv` (dev + holdout). Jalankan terhadap LiteLLM + Presidio dengan recognizer Indonesia sederhana. Konfirmasi fitur pemulihan token LiteLLM | Catatan keputusan tertulis: **lanjut** (celah recall/precision atau ergonomi cukup besar), **pivot** ke plugin untuk LiteLLM atau Presidio (blueprint lapis 3), atau **berhenti** |
| **1. Inti deteksi** (rilis α) | `omnirail-core` tanpa I/O dan bisa dikompilasi ke WASM: normalisasi, validator, PII-01 s.d. 07, PII-10, CRED-01 s.d. 03, POL-01 dan POL-02, CFG-03 s.d. 05, pack `id-general`, EVAL-01 s.d. 04, EVAL-06 (`inspect`), EVAL-07 dan EVAL-08 (`scan`), EVAL-09 s.d. 12, POL-06, PII-05 | Baseline per entitas tercatat; ambang CI ditetapkan; target bagian 9 direvisi tertulis |
| **2. Rilis α** | DIST-06 (demo WASM, dengan PG-03, PG-06, PG-07), binary CLI (bagian dari DIST-01) dengan DIST-08, README "coba sekarang", wawancara pertama memakai demo | Rilis α bertag; demo publik bisa dibuka; ≥ 3 wawancara tercatat |
| **3. Kerangka proxy** (rilis β) | API-01, API-02, API-04, API-07, API-08, UP-01 (Ollama + satu provider cloud), UP-02 s.d. UP-07, CFG-01/02/06/07, kontrak error | SDK OpenAI (dengan dan tanpa `stream=True`) mendapat jawaban lewat proxy dari Ollama dan provider cloud yang dipilih; konfigurasi salah menghentikan start dengan pesan yang jelas |
| **4. Alur proxy lengkap** (rilis β) | API-03, POL-03 s.d. 05, AUD-01 s.d. 03, REP-01, REP-02, PG-01, PG-02, CFG-10 | Test integrasi membuktikan request yang diblokir tidak pernah memanggil upstream; laporan paparan bisa dibuat dari audit log |
| **5. Rilis β** (rilis publik pertama) | DIST-01 s.d. 03, DIST-05, DIST-08, EVAL-05, EVAL-13, README dengan batas klaim, holdout, wawancara lanjutan | Rilis bertag; benchmark terbit; ringkasan wawancara tertulis menentukan prioritas berikutnya |

Setelah rilis β, urutan ditentukan umpan balik. Kandidatnya: audit log tahan ubah (AUD-06), *skeleton* UTS #39 (POL-07), validasi JSON (JSON-01 s.d. 06), adapter provider lain (UP-08), rute sensitivitas (7.16), angka terucap (PII-11), credentials lokal tambahan (CRED-05), metrik OpenTelemetry (AUD-04), benchmark terbuka (DIST-07), tampilan uji dari binary dan fiturnya (PG-04, PG-05, PG-08 s.d. PG-12), entitas kustom (PII-08), streaming sejati, NER, laporan untuk auditor (REP-03), dan marketplace pack (blueprint bagian 13).

## 12. Risiko

| Risiko | Dampak | Mitigasi |
| --- | --- | --- |
| LiteLLM + Presidio sudah cukup untuk kebutuhan yang sama | Produk tidak punya alasan dipakai | Gerbang Tahap 0, dengan opsi pivot ke plugin |
| False positive merusak jawaban | Pengguna mematikan guard | Validator struktur, konteks wajib untuk `bank_account`, mode shadow, entitas bisa dimatikan satu per satu |
| Model mengubah atau menerjemahkan token (`<EMAIL_1>` jadi `EMAIL_1`) | Nilai asli tidak kembali | Metrik token hilang; instruksi sistem opsional yang meminta model mempertahankan token (P1); format token diuji ke tiap provider di Tahap 3 dan lewat eksperimen Q14 |
| Scope creep dari daftar fitur blueprint | MVP tidak pernah rilis | Tabel prioritas di bagian 7; fitur baru masuk hanya bila ada yang dikeluarkan |
| Satu pembangun, Rust memperlambat iterasi awal | Tahap molor | Tahap kecil dengan kriteria selesai yang bisa diperiksa; P1 boleh dilepas tanpa menggeser rilis |
| Klaim publik terbaca sebagai klaim kepatuhan | Risiko reputasi dan hukum | Batas klaim wajib di README; kata "bukti pendukung", bukan "patuh" |
| Laporan paparan (7.15) terbaca sebagai penilaian kepatuhan | Keputusan salah berdasarkan kategori yang belum ditinjau | Kategori PDP ditandai draf sampai Q6 terjawab; kalimat batas klaim di setiap laporan |
| Rilis α kurang menarik karena belum ada proxy | Sedikit yang mencoba | `scan` dan demo WASM punya nilai sendiri; rilis α juga dipakai sebagai alat wawancara, bukan peluncuran besar |

## 13. Pertanyaan terbuka

| # | Pertanyaan | Penjawab | Menghalangi |
| --- | --- | --- | --- |
| Q1 | ~~Siapa yang menyusun dataset dan berapa baris minimum~~ **Terjawab:** dataset v0.6 (3.578 baris) punya ≥ 100 positif dan ≥ 100 negatif per entitas. Yang tersisa: tinjauan label oleh orang kedua (T-007) | Pembangun | Baseline Tahap 1 |
| Q2 | ~~Apa kriteria angka untuk keputusan "lanjut" di Tahap 0?~~ **Terjawab** 11 Nov 2026: kriteria di catatan keputusan [TASKS.md](TASKS.md) (T-003) | Pembangun | Tahap 0 |
| Q3 | Apakah default `shadow.apply_transforms: true` diterima calon pengguna, atau mereka ingin shadow murni mengamati? | Calon pengguna (wawancara) | Tidak |
| Q4 | ~~Aturan NPWP 16 digit~~ **Terjawab sebagian** (Lampiran A): NIK untuk orang pribadi, `0` + 15 digit untuk badan. Yang tersisa: adakah checksum resmi NPWP? | Pembangun, dicek ke sumber DJP | Tidak |
| Q5 | Daftar prefix kartu GPN (tidak ditemukan sumber publik), dan konfirmasi kode provinsi 93 s.d. 96 dari Kepmendagri 100.1.1-6117/2022 | Pembangun | Tahap 1 |
| Q6 | Teks resmi UU 27/2022 Pasal 4, 36 s.d. 39, dan 56, serta PP 33/2026, sebelum dipakai di materi publik, pack `id-fintech`, atau pemetaan `kategori_pdp` di laporan paparan (REP-02) | Penanggung jawab kepatuhan | Pack `id-fintech` dan label "belum ditinjau" di REP-02, bukan MVP |
| Q7 | Format Gemini API dicek ke dokumentasi resmi ai.google.dev | Pembangun | Adapter Gemini (UP-08, setelah rilis β) |
| Q8 | Retensi dan tujuan audit log: cukup stdout + file berotasi, atau perlu sink lain sejak awal? | Calon pengguna fintech | Tidak |
| Q9 | Apakah Windows perlu didukung sejak rilis awal? | Wawancara | Tidak |
| Q10 | ~~Struktur NIP~~ **Terjawab** untuk PNS (Perka BKN 22/2007). NI PPPK baru dari sumber sekunder; konfirmasi ke dokumen BKN | Pembangun | Tidak |
| Q11 | Format resmi nomor paspor dari Ditjen Imigrasi (sekarang memakai definisi Microsoft Purview), dampak sistem paspor tunggal 2027, dan panjang resmi nomor BPJS Ketenagakerjaan (11 atau 16 digit) | Pembangun | Precision `passport_id` dan `bpjs` di Tahap 1 |
| Q12 | Daftar kode plat dicek langsung ke teks Perpol 7/2021 (sekarang dari sumber sekunder), dan apakah plat termasuk data pribadi untuk pengguna sasaran | Pembangun, calon pengguna | `vehicle_plate` (P1) |
| Q13 | Apakah nama bank (BCA, BRI, dan seterusnya) dijadikan kata konteks `bank_account`? | Pembangun | Tidak |
| Q14 | Format token mana yang paling sering bertahan utuh di jawaban tiap provider: `<JENIS_n>`, variasinya, atau nilai pengganti sintetis yang tampak realistis? Hasilnya diterbitkan | Pembangun (eksperimen T-207) | Tidak; memengaruhi target pemulihan token |
| Q15 | Lisensi dataset publik (DIST-07), misalnya CC BY 4.0, dan apakah tetap memakai nama `uji_pii_id` | Pembangun | DIST-07 |

## 14. Riwayat dokumen

| Versi | Tanggal | Perubahan |
| --- | --- | --- |
| 1.0 | 9 November 2026 | Draf pertama dari blueprint v1.1, dengan perbaikan di bagian 1 |
| 1.1 | 9 November 2026 | PII-07: kata konteks menentukan jenis bila dua validator lolos. EVAL-01: lokasi dataset. Rincian task di [TASKS.md](TASKS.md) |
| 1.2 | 9 November 2026 | Entitas baru (perubahan 15), urutan prioritas PII-07 diperluas, detektor credentials Midtrans/Xendit/Telegram, Q10 s.d. Q13 |
| 1.3 | 9 November 2026 | Keterbatasan verifikasi K1 s.d. K5 dicatat di Lampiran A. Format diverifikasi ke sumber publik (Lampiran A): NI PPPK, paspor 1–2 huruf + 6–7 digit, BPJS TK 16 digit, kode plat Perpol 7/2021, NPWP 16 digit, prefix Xendit/Midtrans/Telegram, `output_parse_pii` LiteLLM |
| 1.4 | 9 November 2026 | Tampilan uji dirinci (bagian 7.13, PG-01 s.d. PG-13), EVAL-06 menjadi CLI `omnirail inspect` (P0), user stories 15 s.d. 18, kode error `omnirail_admin_required`, metrik dan ancaman terkait |
| 1.5 | 9 November 2026 | Crosscheck kesiapan: API-07 (field yang didukung), CFG-10 (`omnirail validate` dan kontrol perubahan kebijakan), DIST-05 (`SECURITY.md`), referensi konfigurasi 7.14, Q1 terjawab |
| 1.6 | 11 November 2026 | MVP dipecah menjadi rilis α (periksa) dan β (proxy); JSON-01 s.d. 04, AUD-04, PG-04, PG-05 turun ke P1; UP-01 cukup satu provider cloud (UP-08 untuk sisanya); baru: API-08 (pseudo-streaming), PII-10 (konteks lintas pesan), PII-11 (angka terucap, P1), CRED-05 (P1), EVAL-07 dan EVAL-08 (`scan`), DIST-06 (demo WASM), DIST-07 (P1), laporan paparan 7.15 (REP-01 s.d. 03), rute sensitivitas 7.16 (P1), PII-03 diperjelas (normalisasi kunci token), PII-12 dan PII-13 (P1), Q2 terjawab, Q14, Q15; dataset v0.6 |
| 1.7 | 11 November 2026 | Landasan metode dan rujukan ([LANDASAN_METODE.md](LANDASAN_METODE.md)). Baru: EVAL-09 s.d. 13 (interval Wilson dan McNemar, uji perilaku, *property-based testing*, uji silang, catatan holdout), POL-06 (regex tanpa backtracking), POL-07 (P1, UTS #39), AUD-06 (P1, audit log tahan ubah), DIST-08 (rilis bertanda tangan, SBOM, audit dependensi). Diperjelas: PII-05 (`zeroize`), AUD-02 (RFC 8785), EVAL-05 (*coordinated omission*), cara membaca target di bagian 9, istilah pseudonimisasi di bagian 10 |
| 1.7.1 | 11 November 2026 | Rujukan di [Landasan metode](LANDASAN_METODE.md) dibatasi pada terbitan lima tahun terakhir (akhir 2021 s.d. 2026); ISO/IEC 20889 diganti ISO/IEC 27559:2022; RFC 8785 dipertahankan sebagai spesifikasi teknis tanpa pengganti |

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
