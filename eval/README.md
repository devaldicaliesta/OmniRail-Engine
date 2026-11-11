# Dataset uji `uji_pii_id.csv`

Set uji berlabel untuk Tahap 0 (perbandingan dengan LiteLLM + Presidio) dan untuk `omnirail eval` (PRD EVAL-01, EVAL-02).

> **Status: v0.6.** Dibanding v0.5, ditambah baris percakapan multi-pesan untuk kata konteks lintas pesan (PRD PII-10) dan baris angka terucap (PRD PII-11). Format NIP (termasuk NI PPPK), paspor, BPJS, dan kode plat sudah disesuaikan dengan hasil verifikasi di PRD Lampiran A. Setiap entitas (P0 dan P1) punya ≥ 50 baris positif dan ≥ 50 baris negatif (PRD Q1), dan holdout sekitar 30% dari total. Isinya belum ditinjau orang kedua, jadi label bisa saja keliru. Laporkan atau perbaiki bila menemukan label yang salah.

## Isi

| Berkas | Baris | Kegunaan |
| --- | --- | --- |
| `dev/uji_pii_id.csv` | 2.506 | Boleh dilihat dan dipakai saat menyetel aturan |
| `holdout/uji_pii_id.csv` | 1.072 | **Jangan dibuka saat menyetel aturan.** Hanya dijalankan sebelum rilis, agar aturan tidak sekadar disetel supaya lulus uji |

### Jumlah per entitas (dev + holdout)

| Entitas | Prioritas | Positif | Negatif | Kasus di luar cakupan |
| --- | --- | --- | --- | --- |
| `email` | P0 | 168 | 111 | — |
| `phone_id` | P0 | 157 | 120 | 36 (5 telepon kantor, 31 angka terucap) |
| `credit_card` | P0 | 139 | 109 | — |
| `nik` | P0 | 161 | 117 | 17 (5 NIK berpemisah, 12 angka terucap) |
| `npwp` | P0 | 130 | 108 | — |
| `bank_account` | P0 | 162 | 129 | 17 (5 tanpa kata konteks, 12 angka terucap) |
| `nip` | P0 | 118 | 104 | — |
| `kk` | P0 | 134 | 106 | 7 (angka terucap) |
| `passport_id` | P0 | 140 | 112 | 6 (tanpa kata konteks) |
| `bpjs` | P0 | 135 | 109 | 6 (tanpa kata konteks) |
| `birth_date` | P0 | 142 | 112 | — |
| `vehicle_plate` | P1 | 114 | 104 | seluruh baris positif bertanda `cakupan_mvp = tidak` |
| `ip_address` | P1 | 114 | 104 | seluruh baris positif bertanda `cakupan_mvp = tidak` |

Hitungan positif menghitung kemunculan entitas, sehingga baris campuran terhitung di beberapa entitas sekaligus. Baris positif entitas P1 bertanda `cakupan_mvp = tidak` karena detektornya mati secara default. Baris negatifnya tetap `ya`, karena tidak boleh memicu detektor MVP mana pun. Di luar itu ada 203 baris credentials (termasuk Midtrans, Xendit, dan token bot Telegram), 96 baris injeksi, serta 40 kemunculan nama dan alamat yang butuh NER.

### Variasi

- **Percakapan multi-pesan (v0.6):** pertanyaan asisten berisi kata konteks ("Boleh minta nomor rekeningnya?"), lalu jawaban pengguna yang hanya berisi nilai. Baris positif (`cakupan_mvp = ya`) menguji PRD PII-10. Baris negatif menguji pertanyaan yang meminta hal lain (nomor pesanan, tanggal pengiriman, kode voucher) dan kata konteks yang terlalu jauh dari akhir pesan sebelumnya. Holdout memakai pertanyaan berbahasa Inggris dan formulir data diri.
- **Angka terucap (v0.6):** nilai yang ditulis sebagai kata bilangan, seperti di transkrip panggilan atau hasil voice-to-text: `nol delapan satu dua …`, `kosong` untuk nol, dan campuran (`0812 tiga empat …`). Baris positif bertanda `cakupan_mvp = tidak` karena PII-11 adalah P1, dan nilai digitnya ditulis di `catatan`. Baris negatif (bilangan terucap yang bukan PII: jumlah barang, harga, jam, RT/RW, ukuran sepatu) bertanda `ya`.

- **Bingkai teks (v0.5):** sekitar sepertiga baris dibungkus bentuk yang lazim sampai ke proxy LLM: instruksi tugas ("Ringkas percakapan berikut:", "Terjemahkan ke bahasa Inggris:", "Ekstrak informasi penting… dalam format JSON"), transkrip chat CS dengan atau tanpa jam, badan email formal, tabel Markdown, dan kalimat panjang dengan konteks tambahan. Holdout memakai bingkai yang tidak ada di dev: YAML, payload JSON, pesan terusan WhatsApp, dan catatan internal. Bingkai sengaja tidak memuat data pribadi.
- **Gaya ketik (v0.5):** singkatan chat (`tlg`, `yg`, `udh`, `gak`, `sy`, `mhn`) dan gaya voice-to-text (huruf kecil tanpa tanda baca). Kata konteks ikut berubah huruf, sedangkan nilai entitas tetap utuh. Gaya voice-to-text hanya ada di dev.
- **Credentials dalam prompt teknis (v0.5):** "Tolong review kode berikut:" dengan blok kode, "Kenapa error ini muncul?", dan pada holdout isi `.env` serta log deploy.
- **Gaya kalimat:** chat CS formal dan informal (singkatan, slang, emoji), log aplikasi, JSON, CSV, `key=value`, header email, SQL, perintah shell, potongan kode, dan kalimat campuran bahasa Inggris.
- **Format nilai:** 36 prefix operator seluler dengan 8 gaya penulisan (`08…`, `+62`, `62`, pemisah spasi, titik, atau tanda hubung); kartu Visa, Mastercard (seri 5 dan 2), Amex, dan JCB dengan atau tanpa pemisah; NIK laki-laki dan perempuan dari semua provinsi; NPWP 15 digit bertitik, 15 digit polos, dan 16 digit; rekening 10 sampai 16 digit dari 16 nama bank.
- **Negatif yang menjebak:** `git@github.com:…`, `logo@2x.png`, IMEI yang lolos Luhn, barcode EAN-13, nomor seri faktur pajak, kode wilayah Kemendagri, saldo bertitik di dekat kata "rekening", pesan bisnis wajar yang memuat frasa deny-list, "mohon maaf lahir dan batin" diikuti tanggal, "KKN", SKU berbentuk nomor paspor, "Kamar D 12 VIP" yang cocok pola plat, serta nomor versi empat bagian dan subnet mask yang mirip IPv4.
- **Konsistensi antar-entitas:** di baris campuran, tanggal lahir yang ditulis sama dengan tanggal lahir di NIP, dan nomor KK yang juga lolos struktur NIK ditandai di `catatan`.
- **Template dev dan holdout terpisah.** Kalimat holdout memakai template yang tidak pernah muncul di dev, sehingga holdout menguji generalisasi, bukan hafalan pola kalimat.

Baris berlabel `negatif sulit` di kolom `catatan` adalah kasus yang kemungkinan besar gagal di MVP. Baris ini tetap dihitung, karena tujuannya memperlihatkan false positive yang nyata.

Semua data adalah **data rekaan**: NIK, nomor kartu, nomor HP, email (domain `example.*` dan `.test`), dan credentials dibuat secara acak. NIK dan nomor kartu dibangkitkan agar lolos validator struktur dan Luhn, sehingga bentuknya realistis. Data nyata hanya boleh masuk setelah dianonimkan dan disetujui penanggung jawab data.

## Format kolom

| Kolom | Isi |
| --- | --- |
| `id` | `D001…` untuk dev, `H001…` untuk holdout |
| `kategori` | `positif`, `negatif`, `kredensial`, atau `injeksi` |
| `teks` | Isi pesan pengguna. Bisa multi-baris (dikutip sesuai CSV). Bila diawali penanda peran, teks berisi beberapa pesan (lihat di bawah) |
| `diharapkan` | Lihat aturan di bawah |
| `cakupan_mvp` | `ya` bila MVP seharusnya menangani baris ini; `tidak` bila baris ini sengaja mendokumentasikan batas MVP |
| `catatan` | Alasan baris ini ada atau apa yang diuji. Untuk baris `negatif`, diawali entitas yang dijebak, misalnya `[nik]` |

**Percakapan multi-pesan.** Teks yang diawali `<<assistant>> `, `<<user>> `, atau `<<system>> ` di awal baris dipecah menjadi beberapa pesan oleh `omnirail eval`, dengan peran sesuai penandanya. Setiap penanda membuka pesan baru sampai penanda berikutnya. Teks seperti ini minimal memuat dua pesan, dan nilai di `diharapkan` tetap ditulis persis seperti di teks.

Aturan kolom `diharapkan`:

- **`positif` dan `negatif`:** daftar `jenis:nilai` dipisah ` | `, persis seperti tertulis di `teks`. `-` berarti tidak ada entitas. Nilai yang sama bisa muncul dua kali bila memang muncul dua kali di teks.
- **`kredensial`:** satu jenis detektor (`api_key`, `jwt`, `private_key`, `connection_string`, `password_assignment`), atau `-` bila tidak boleh diblokir. Dinilai per baris (diblokir atau tidak, beserta jenisnya), bukan per rentang teks.
- **`injeksi`:** `deny` bila deny-list pack `id-general` harus menangkapnya, atau `-` bila tidak boleh tertangkap.

## Cara menghitung metrik

Asal-usul, batas, dan cara pakai dataset ini dijelaskan di [DATASHEET.md](DATASHEET.md). Setiap metrik dilaporkan dengan interval Wilson 95%, dan perbandingan dua sistem memakai uji McNemar eksak per baris (PRD EVAL-09, `eval/tools/statistik.py`). Dengan ukuran dataset sekarang, interval per entitas masih sekitar ±5 poin, jadi target false positive dinilai pada gabungan entitas.

- **Baris yang dihitung:** hanya baris dengan `cakupan_mvp = ya` yang masuk recall, precision, dan ambang CI. Baris `tidak` dilaporkan terpisah sebagai "di luar cakupan" agar celah MVP tetap terlihat.
- **Kecocokan PII:** temuan dihitung benar bila jenisnya sama dan nilainya sama setelah normalisasi (hapus spasi, titik, dan tanda hubung). Temuan dengan jenis berbeda dihitung sebagai satu false negative dan satu false positive.
- **False positive rate:** dihitung dari baris `negatif` yang menghasilkan temuan apa pun.
- **Tingkat blokir credentials:** baris `kredensial` dengan jenis selain `-` yang diblokir, dibagi semua baris tersebut. Baris `-` yang diblokir dihitung sebagai false positive credentials.
- **Entitas di luar MVP:** jenis `nama` dan `alamat` hanya muncul di baris `cakupan_mvp = tidak`.

## Kasus yang sengaja dimasukkan

- **Bentrok 16 digit:** NIK yang juga lolos Luhn Mastercard, dengan kata konteks yang menentukan jenisnya (D050, D051). Juga nomor pesanan, invoice, dan kode booking 16 digit yang gagal di validator struktur NIK.
- **Uji e-commerce:** nomor resi dan nomor pesanan yang tidak boleh dikenali sebagai nomor HP, rekening, atau kartu. Salah satunya (D025) sengaja identik dengan bentuk nomor HP, sebagai negatif sulit.
- **Tokenisasi:** nilai sama yang muncul dua kali, serta input yang sudah memuat teks berbentuk token `<EMAIL_1>` (PRD PII-03, PII-04).
- **Placeholder credentials:** `${VAR}`, `********`, `<password>`, dan `xxx` yang tidak boleh diblokir (PRD CRED-03).
- **Penghindaran deny-list:** huruf lebar penuh, karakter lebar-nol, dan spasi ganda (PRD POL-02).

## Memeriksa dataset

```bash
python3 eval/tools/cek_dataset.py --ringkasan
```

Pemeriksa (Python 3.9+, tanpa dependensi) memastikan header dan `id` benar, kolom `diharapkan` sesuai aturan per kategori, setiap nilai benar-benar muncul di `teks`, nilai berlabel lolos validator struktur PRD 7.10 (Luhn dan prefix kartu, struktur NIK, KK, dan NIP, panjang nomor, tanggal valid), baris `negatif` menandai entitas yang dijebak, teks dev tidak muncul di holdout, target jumlah terpenuhi, dan tabel jumlah di atas sama dengan isi berkas. Kegagalan validator di baris `cakupan_mvp = tidak` hanya menjadi peringatan. CI menjalankan pemeriksaan ini di setiap pull request, dan `python3 -m unittest discover -s eval/tools` menjalankan test unitnya.

Pemeriksa hanya memvalidasi bentuk label, tidak menyetel aturan deteksi, sehingga aturan "jangan buka holdout" tidak dilanggar.

Baris yang ditambahkan di v0.6 (D2362–D2506, H1010–H1072) dibangkitkan oleh `eval/tools/bangkitkan_v06.py`. Test unit memastikan baris itu identik dengan hasil pembangkit. Baris v0.1 s.d. v0.5 belum punya pembangkit di repo (T-008).

## Menambah baris

1. Tambahkan baris di `dev`, kecuali Anda sedang menyusun holdout baru sebelum rilis.
2. Pakai data rekaan. Untuk NIK dan nomor kartu, pastikan lolos validator (PRD bagian 7.10), kecuali baris itu memang contoh negatif.
3. Isi `catatan` dengan apa yang diuji.
4. Perbarui tabel jumlah di atas bila berubah, lalu jalankan `python3 eval/tools/cek_dataset.py`.
5. Jangan memindahkan baris dari holdout ke dev setelah holdout pernah dijalankan.
