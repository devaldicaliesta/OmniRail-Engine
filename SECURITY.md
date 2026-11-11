# Kebijakan keamanan

OmniRail Engine adalah lapisan guard yang menyamarkan data pribadi dan memblokir credentials sebelum prompt sampai ke provider LLM. Celah keamanan di proyek ini bisa berarti data pribadi bocor, jadi laporan Anda sangat kami hargai.

## Versi yang didukung

| Versi | Didukung |
| --- | --- |
| Belum ada rilis | — |

Proyek masih di tahap desain (lihat [README](README.md)). Setelah rilis pertama, perbaikan keamanan hanya diberikan untuk rilis minor terbaru. Tabel ini akan diperbarui saat rilis bertag pertama terbit.

## Melaporkan kerentanan

**Jangan laporkan kerentanan lewat issue, diskusi, atau pull request publik.**

Laporkan secara privat lewat GitHub: buka tab **Security** di repo ini, lalu pilih **Report a vulnerability** ([private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)). Laporan hanya terlihat oleh pemelihara.

Sertakan:

- versi atau commit yang diuji, beserta konfigurasi (`omnirail.yaml`) dengan semua kunci rahasia dihapus;
- langkah reproduksi dan dampaknya (misalnya nilai PII yang lolos ke provider);
- contoh input yang memakai **data rekaan**. Jangan pernah mengirim data pribadi atau credentials asli, termasuk dalam laporan privat.

### Yang bisa Anda harapkan

| Tahap | Target waktu |
| --- | --- |
| Konfirmasi laporan diterima | 3 hari kerja |
| Penilaian awal (diterima atau tidak, tingkat keparahan) | 10 hari kerja |
| Perbaikan dan advisori publik | Bergantung keparahan; kami kabari perkembangannya |

Kami akan mencantumkan nama pelapor di advisori, kecuali Anda meminta tetap anonim.

## Apa yang termasuk kerentanan

Termasuk:

- nilai entitas yang **masuk cakupan MVP** (lihat PRD bagian 7.10) lolos ke provider dalam bentuk yang seharusnya terdeteksi;
- token PII dipulihkan menjadi nilai milik request lain, atau tabel token bertahan melewati satu request;
- nilai PII, credentials, atau kunci provider muncul di log, metrik, pesan error, `/readyz`, atau tampilan uji;
- melewati autentikasi kunci OmniRail atau kunci admin tampilan uji;
- request yang diblokir tetap diteruskan ke provider;
- body error provider diteruskan ke klien.

Tidak termasuk (sudah tercatat sebagai batas klaim di [README](README.md#batas-klaim) dan PRD bagian 10):

- PII bebas-bentuk (nama, alamat) atau PII berformat tak lazim yang tidak terdeteksi;
- prompt injection yang lolos deny-list;
- secret tanpa prefix yang dikenal;
- isi lampiran, gambar, streaming, atau tool call (ditolak, bukan diperiksa).

Temuan false negative atau false positive biasa pada deteksi PII lebih tepat dilaporkan sebagai issue publik dengan contoh **data rekaan**, supaya bisa ditambahkan ke dataset uji.
