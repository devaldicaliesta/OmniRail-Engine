# Datasheet: `uji_pii_id` v0.6

Disusun mengikuti kerangka *Datasheets for Datasets* (Gebru dkk., Communications of the ACM, 2021). Aturan format dan cara menghitung metrik ada di [README](README.md); dokumen ini menjelaskan asal-usul, batas, dan cara memakai dataset dengan benar.

## Motivasi

- **Tujuan.** Mengukur deteksi data pribadi berformat tetap dan credentials dalam teks berbahasa Indonesia yang dikirim ke LLM: gerbang keputusan Tahap 0 (perbandingan dengan Presidio dan LiteLLM), `omnirail eval`, dan ambang CI (PRD EVAL-01 s.d. EVAL-04).
- **Celah yang diisi.** Set uji PII yang beredar umumnya berbahasa Inggris atau berfokus pada teks medis dan hukum. Belum ada set uji terbuka untuk NIK, KK, NIP, NPWP, BPJS, dan credentials payment gateway lokal dengan negatif yang menjebak.
- **Penyusun dan pendanaan.** Disusun oleh pemilik proyek OmniRail Engine, tanpa pendanaan eksternal.

## Komposisi

- **Isi.** 3.578 baris teks pendek: 2.506 dev dan 1.072 holdout (30%). Kategori: `positif`, `negatif`, `kredensial`, `injeksi`. Hitungan per entitas ada di README.
- **Satuan.** Satu baris adalah satu pesan, atau satu percakapan multi-pesan bila diawali penanda `<<assistant>>`/`<<user>>`/`<<system>>`.
- **Label.** Kolom `diharapkan` (jenis dan nilai persis), `cakupan_mvp`, dan `catatan`. Label positif dan negatif dinilai per kemunculan nilai; kredensial dan injeksi dinilai per baris.
- **Data pribadi.** **Tidak ada data asli.** Semua nilai rekaan. Email memakai domain `example.*` dan `.test`. Namun, NIK, nomor kartu, dan nomor HP dibangkitkan agar lolos validator struktur, Luhn, dan prefix operator, sehingga **sebuah nilai bisa kebetulan sama dengan nomor milik orang sungguhan**. Nomor kartu tidak disertai tanggal kedaluwarsa atau CVV. Jangan memakai nilai di dataset ini untuk menghubungi, memverifikasi, atau bertransaksi.
- **Ketidakseimbangan yang disengaja.** Baris negatif sengaja dipenuhi kasus menjebak (nomor resi, IMEI lolos Luhn, nomor faktur pajak, "mohon maaf lahir dan batin"). Angka false positive dari dataset ini lebih pesimistis daripada trafik nyata.
- **Batas cakupan.** Nama dan alamat (butuh NER), telepon kantor, angka terucap, dan entitas P1 hanya muncul di baris `cakupan_mvp = tidak`.

## Proses pengumpulan

- **Cara dibuat.** v0.1 dan v0.2 ditulis tangan (D001–D106, H001–H047), lalu diperbanyak dengan templat kalimat dan pembangkit nilai. Templat dev dan holdout dipisah agar holdout menguji generalisasi, bukan hafalan pola kalimat.
- **Format entitas.** Mengikuti PRD bagian 7.10. Sumber dan tingkat keyakinannya tercatat di PRD Lampiran A, termasuk lima keterbatasan (K1 s.d. K5) yang belum terverifikasi ke sumber primer.
- **Pembangkit.** Baris v0.6 dibangkitkan ulang secara deterministik oleh `eval/tools/bangkitkan_v06.py`. Pembangkit v0.1 s.d. v0.5 belum ada di repo (T-008).

## Pelabelan

- **Penilai.** Satu orang (penyusun). Belum ada tinjauan penilai kedua; ini adalah keterbatasan terbesar dataset (T-007).
- **Rencana tinjauan.** Sampel ± 120 baris dev dinilai ulang oleh orang kedua. Kesepakatan dihitung dengan kappa Cohen (`eval/tools/statistik.py`); target κ ≥ 0,8. Bila tingkat kesalahan sampel > 5%, entitas yang bermasalah ditinjau ulang seluruhnya.
- **Pemeriksaan otomatis.** `eval/tools/cek_dataset.py` memastikan setiap nilai muncul di teks, lolos validator struktur, dan tidak bocor dari dev ke holdout. Pemeriksa ini memvalidasi bentuk label, bukan kebenaran maknanya.

## Pemakaian

- **Dianjurkan.** Membandingkan detektor PII berbahasa Indonesia; regresi CI; melaporkan metrik per entitas **dengan interval kepercayaan** (PRD EVAL-09).
- **Tidak dianjurkan.**
  - Mengklaim tingkat deteksi di trafik produksi. Distribusi dataset ini berbeda dari trafik nyata.
  - Melatih model lalu menguji pada split yang sama.
  - Menyetel aturan sambil melihat holdout. Setiap run holdout dicatat (PRD EVAL-13), karena pemakaian holdout berulang yang adaptif membuat angkanya terlalu optimistis (Dwork dkk., *Science*, 2015).
- **Ketelitian angka.** Dengan ± 110 sampai 160 kemunculan per entitas, interval Wilson 95% untuk recall 0,90 masih sekitar ±5 poin. Dengan ± 110 baris negatif per entitas dan **nol** false positive, batas atasnya masih sekitar 3,4%. Jadi target false positive ≤ 2% (PRD bagian 9) hanya bisa dibuktikan pada gabungan entitas, atau bila suatu entitas punya ≥ 190 baris negatif. Jalankan `python3 eval/tools/statistik.py` untuk tabel lengkapnya.

## Distribusi

- **Lokasi.** Repo OmniRail Engine, di bawah lisensi Apache 2.0 bersama kode.
- **Rencana publikasi.** Split `dev` akan diterbitkan terpisah sebagai benchmark (PRD DIST-07). Lisensi dataset publik masih terbuka (Q15). Holdout tidak diterbitkan.

## Pemeliharaan

- **Versi.** Setiap versi dicatat di README dan di catatan keputusan `docs/TASKS.md`. Riwayat: v0.1 (153 baris), v0.2 (1.008), v0.3 (1.825), v0.4 (format disesuaikan dengan PRD Lampiran A), v0.5 (3.370), v0.6 (3.578).
- **Melaporkan kesalahan.** Gunakan template issue **Label dataset keliru**. Jangan menempelkan data pribadi asli.
- **Aturan perubahan.** Baris holdout tidak boleh dipindah ke dev setelah holdout pernah dijalankan. Perubahan di `eval/` wajib ditinjau pemilik kode (`.github/CODEOWNERS`).
