# Dataset uji `uji_pii_id.csv`

Set uji berlabel untuk Tahap 0 (perbandingan dengan LiteLLM + Presidio) dan untuk `omnirail eval` (PRD EVAL-01, EVAL-02).

> **Status: draf v0.1.** Jumlah baris per entitas masih di bawah usulan minimum (≥ 50 positif dan ≥ 50 negatif per entitas, PRD Q1). Baseline dari draf ini hanya indikatif.

## Isi

| Berkas | Baris | Kegunaan |
| --- | --- | --- |
| `dev/uji_pii_id.csv` | 106 | Boleh dilihat dan dipakai saat menyetel aturan |
| `holdout/uji_pii_id.csv` | 47 | **Jangan dibuka saat menyetel aturan.** Hanya dijalankan sebelum rilis, agar aturan tidak sekadar disetel supaya lulus uji |

Semua data adalah **data rekaan**: NIK, nomor kartu, nomor HP, email (domain `example.*` dan `.test`), dan credentials dibuat secara acak. NIK dan nomor kartu dibangkitkan agar lolos validator struktur dan Luhn, sehingga bentuknya realistis. Data nyata hanya boleh masuk setelah dianonimkan dan disetujui penanggung jawab data.

## Format kolom

| Kolom | Isi |
| --- | --- |
| `id` | `D001…` untuk dev, `H001…` untuk holdout |
| `kategori` | `positif`, `negatif`, `kredensial`, atau `injeksi` |
| `teks` | Isi pesan pengguna. Bisa multi-baris (dikutip sesuai CSV) |
| `diharapkan` | Lihat aturan di bawah |
| `cakupan_mvp` | `ya` bila MVP seharusnya menangani baris ini; `tidak` bila baris ini sengaja mendokumentasikan batas MVP |
| `catatan` | Alasan baris ini ada atau apa yang diuji |

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
