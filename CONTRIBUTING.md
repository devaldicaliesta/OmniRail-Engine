# Berkontribusi ke OmniRail Engine

Terima kasih sudah tertarik. Proyek ini masih di **tahap desain dan validasi** (lihat [README](README.md)), jadi kontribusi paling berguna saat ini adalah tinjauan dokumen, perbaikan label dataset uji, dan informasi format resmi entitas Indonesia.

Laporan kerentanan **tidak** lewat issue publik. Ikuti [SECURITY.md](SECURITY.md).

## Acuan

- [PRD MVP](docs/PRD.md) adalah acuan scope dan requirement. Bila berbeda dengan blueprint, PRD yang berlaku.
- [TASKS.md](docs/TASKS.md) berisi task per tahap. Satu task berarti satu pull request dengan kriteria selesai yang bisa diperiksa.
- Fitur di luar PRD bagian 7 tidak diterima ke MVP kecuali ada yang dikeluarkan (PRD bagian 12, risiko scope creep). Usulkan lewat issue lebih dulu.

## Aturan data

- **Hanya data rekaan.** Jangan pernah memasukkan NIK, nomor kartu, nomor HP, email, atau credentials asli ke repo, issue, maupun pull request, termasuk di pesan commit dan tangkapan layar.
- Pakai domain `example.*` atau `.test` untuk email, dan nomor yang dibangkitkan agar lolos validator (Luhn, struktur NIK) bila memang perlu realistis.
- Data nyata hanya boleh masuk setelah dianonimkan dan disetujui penanggung jawab data.

## Dataset uji

Aturan lengkap ada di [eval/README.md](eval/README.md). Ringkasnya:

1. Tambahkan baris di `eval/dev/`. Jangan menyentuh `eval/holdout/` kecuali sedang menyusun holdout baru sebelum rilis, dan jangan pernah memindahkan baris holdout ke dev.
2. Isi kolom `catatan` dengan apa yang diuji. Baris `negatif` diawali entitas yang dijebak, misalnya `[nik]`.
3. Bila jumlah per entitas berubah, perbarui tabel di `eval/README.md`.
4. Jalankan pemeriksa sebelum membuka pull request:

   ```bash
   python3 eval/tools/cek_dataset.py --ringkasan
   ```

   Pemeriksa memvalidasi format, label, validator struktur, kebocoran dev ke holdout, dan kecocokan tabel README. CI menjalankan pemeriksaan yang sama.

Menemukan label yang keliru? Buka issue dengan template **Label dataset keliru**, atau langsung kirim pull request perbaikannya.

## Pull request

- Satu pull request untuk satu task di `docs/TASKS.md`. Sebut ID task-nya (misalnya `T-302`) dan kode requirement PRD yang terkait.
- Centang task di `TASKS.md` bila kriteria selesainya terpenuhi. Keputusan baru dicatat di bagian "Catatan keputusan".
- Bila mengubah perilaku yang dijelaskan PRD, perbarui PRD (termasuk riwayat dokumen di bagian 14) dalam pull request yang sama.
- Perubahan di `policy-packs/` dan `eval/` wajib ditinjau pemilik kode ([CODEOWNERS](.github/CODEOWNERS)). Setiap policy pack wajib punya tes (PRD CFG-03 s.d. CFG-05).
- CI harus hijau.

### Pesan commit

Ikuti gaya yang sudah dipakai: awalan area, titik dua, lalu ringkasan dalam bahasa Indonesia dengan kalimat perintah atau deskriptif singkat.

```
docs: rinci tampilan uji di PRD dan task
eval: tambah baris negatif NIP dengan tanggal tidak valid
ci: jalankan pemeriksa dataset di setiap pull request
```

Awalan yang dipakai: `docs`, `eval`, `ci`, `chore`, dan nanti `core`, `proxy`, `pack` saat kode Rust mulai ditulis.

## Gaya penulisan dokumen

- Bahasa Indonesia baku yang lugas. Istilah teknis yang lazim (proxy, token, recall) boleh tetap dalam bahasa Inggris.
- Klaim publik memakai "mengurangi risiko", bukan "melindungi sepenuhnya". OmniRail tidak mengklaim kepatuhan hukum apa pun (PRD bagian 10).
- Sertakan sumber dan tingkat keyakinan untuk informasi format resmi, seperti di PRD Lampiran A.

## Lisensi

Dengan mengirim kontribusi, Anda setuju kontribusi itu dilisensikan di bawah [Apache License 2.0](LICENSE), sesuai pasal 5 lisensi tersebut.
