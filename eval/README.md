# Dataset uji `uji_pii_id.csv`

Set uji berlabel untuk Tahap 0 (perbandingan dengan LiteLLM + Presidio) dan untuk `omnirail eval` (PRD EVAL-01, EVAL-02).

> **Status: v0.3.** Setiap entitas (P0 dan P1) sudah punya ≥ 50 baris positif dan ≥ 50 baris negatif (PRD Q1), dan holdout sekitar 30% dari total. Isinya belum ditinjau orang kedua, jadi label bisa saja keliru. Laporkan atau perbaiki bila menemukan label yang salah.

## Isi

| Berkas | Baris | Kegunaan |
| --- | --- | --- |
| `dev/uji_pii_id.csv` | 1.276 | Boleh dilihat dan dipakai saat menyetel aturan |
| `holdout/uji_pii_id.csv` | 549 | **Jangan dibuka saat menyetel aturan.** Hanya dijalankan sebelum rilis, agar aturan tidak sekadar disetel supaya lulus uji |

### Jumlah per entitas (dev + holdout)

| Entitas | Prioritas | Positif | Negatif | Kasus di luar cakupan |
| --- | --- | --- | --- | --- |
| `email` | P0 | 106 | 61 | — |
| `phone_id` | P0 | 94 | 62 | 5 (telepon kantor) |
| `credit_card` | P0 | 81 | 59 | — |
| `nik` | P0 | 99 | 64 | 5 (NIK berpemisah) |
| `npwp` | P0 | 68 | 58 | — |
| `bank_account` | P0 | 78 | 61 | 5 (tanpa kata konteks) |
| `nip` | P0 | 63 | 54 | — |
| `kk` | P0 | 64 | 54 | — |
| `passport_id` | P0 | 59 | 54 | 6 (tanpa kata konteks) |
| `bpjs` | P0 | 57 | 54 | 6 (tanpa kata konteks) |
| `birth_date` | P0 | 62 | 54 | — |
| `vehicle_plate` | P1 | 54 | 54 | seluruh baris positif bertanda `cakupan_mvp = tidak` |
| `ip_address` | P1 | 54 | 54 | seluruh baris positif bertanda `cakupan_mvp = tidak` |

Hitungan positif menghitung kemunculan entitas, sehingga baris campuran terhitung di beberapa entitas sekaligus. Baris positif entitas P1 bertanda `cakupan_mvp = tidak` karena detektornya mati secara default. Baris negatifnya tetap `ya`, karena tidak boleh memicu detektor MVP mana pun. Di luar itu ada 140 baris credentials (termasuk Midtrans, Xendit, dan token bot Telegram), 44 baris injeksi, serta 40 kemunculan nama dan alamat yang butuh NER.

### Variasi

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
| `teks` | Isi pesan pengguna. Bisa multi-baris (dikutip sesuai CSV) |
| `diharapkan` | Lihat aturan di bawah |
| `cakupan_mvp` | `ya` bila MVP seharusnya menangani baris ini; `tidak` bila baris ini sengaja mendokumentasikan batas MVP |
| `catatan` | Alasan baris ini ada atau apa yang diuji. Untuk baris `negatif`, diawali entitas yang dijebak, misalnya `[nik]` |

Aturan kolom `diharapkan`:

- **`positif` dan `negatif`:** daftar `jenis:nilai` dipisah ` | `, persis seperti tertulis di `teks`. `-` berarti tidak ada entitas. Nilai yang sama bisa muncul dua kali bila memang muncul dua kali di teks.
- **`kredensial`:** satu jenis detektor (`api_key`, `jwt`, `private_key`, `connection_string`, `password_assignment`), atau `-` bila tidak boleh diblokir. Dinilai per baris (diblokir atau tidak, beserta jenisnya), bukan per rentang teks.
- **`injeksi`:** `deny` bila deny-list pack `id-general` harus menangkapnya, atau `-` bila tidak boleh tertangkap.

## Cara menghitung metrik

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

## Menambah baris

1. Tambahkan baris di `dev`, kecuali Anda sedang menyusun holdout baru sebelum rilis.
2. Pakai data rekaan. Untuk NIK dan nomor kartu, pastikan lolos validator (PRD bagian 7.10), kecuali baris itu memang contoh negatif.
3. Isi `catatan` dengan apa yang diuji.
4. Jangan memindahkan baris dari holdout ke dev setelah holdout pernah dijalankan.
