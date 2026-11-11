# Tinjauan label oleh orang kedua (T-007)

`t007-formulir.csv` berisi 120 baris sampel dari split **dev**: 4 positif dan 4 negatif per entitas P0, 3 dan 3 per entitas P1, 10 baris kredensial, dan 10 baris injeksi. Label dataset sengaja tidak ditampilkan agar penilaian independen. Sampel dibuat ulang dengan `python3 eval/tools/tinjau_label.py sampel`.

## Cara mengisi

1. Salin `t007-formulir.csv` menjadi `t007-formulir-NAMA.csv`.
2. Isi tiga kolom untuk setiap baris, hanya dengan membaca `teks`:

| Kolom | Isi |
| --- | --- |
| `label_penilai` | Jenis entitas yang **benar-benar ada** di teks, dipisah `+` (misalnya `nik+phone_id`), meskipun MVP tidak akan mendeteksinya. Untuk credentials: `api_key`, `jwt`, `private_key`, `connection_string`, atau `password_assignment`. Untuk upaya prompt injection: `deny`. Bila tidak ada apa pun: `-` |
| `cakupan_penilai` | `ya` bila MVP seharusnya menangani baris ini sesuai PRD 7.10; `tidak` bila entitasnya ada tetapi sengaja di luar MVP (misalnya tanpa kata konteks wajib, entitas P1, angka terucap, atau injeksi yang diparafrasekan) |
| `komentar` | Opsional: nilai yang menurut Anda keliru, atau alasan keraguan |

Jenis entitas: `email`, `phone_id`, `credit_card`, `nik`, `npwp`, `bank_account`, `nip`, `kk`, `passport_id`, `bpjs`, `birth_date`, `vehicle_plate`, `ip_address`. Nama orang dan alamat **tidak** dilabeli, kecuali menjadi inti baris itu. Aturan lengkap ada di [`eval/README.md`](../README.md) dan PRD bagian 7.10.

3. Hitung hasilnya:

```bash
python3 eval/tools/tinjau_label.py nilai eval/tinjauan/t007-formulir-NAMA.csv
```

Hasil tersimpan di `eval/results/t007-NAMA.{json,md}`: kesepakatan, kappa Cohen, dan daftar baris yang berbeda.

## Selesai bila

- κ ≥ 0,8 dan tingkat kesalahan sampel ≤ 5% setelah adjudikasi. Adjudikasi berarti pemilik dataset dan penilai membahas setiap baris yang berbeda, lalu menetapkan label yang benar.
- Label yang terbukti keliru diperbaiki di dataset, dengan catatan di `docs/TASKS.md`.
- Bila kesalahan > 5% atau κ < 0,8, entitas yang bermasalah ditinjau ulang seluruhnya.

## Pra-tinjauan

`t007-formulir-pra-ai.csv` adalah penilaian buta oleh asisten AI, **bukan pengganti** penilai manusia. Penilainya memakai spesifikasi PRD yang sama dengan penyusun dataset, sehingga tidak independen. Hasilnya (`eval/results/t007-pra-ai.md`): kappa 0,989, dengan satu ketidaksepakatan (D1234) karena perbedaan konvensi, bukan label keliru. Konvensi itu kini dipertegas di kolom `label_penilai` di atas.
