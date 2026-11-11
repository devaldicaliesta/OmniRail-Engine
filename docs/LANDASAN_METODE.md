# OmniRail Engine — Landasan metode dan rujukan

Dokumen ini memetakan setiap bagian OmniRail ke metode yang sudah dipublikasikan atau distandarkan. Tujuannya agar setiap klaim ("deteksi lebih baik", "log bisa diaudit", "rilis bisa dipercaya") punya dasar yang bisa diperiksa orang lain, bukan sekadar pernyataan pembangun.

**Batas rujukan:** hanya terbitan **lima tahun terakhir**, yaitu sejak akhir 2021 sampai 2026. Metode klasik (misalnya interval Wilson atau algoritma Luhn) tetap dipakai, tetapi rujukannya adalah karya terbaru yang menerapkan atau menganjurkan metode itu. Satu pengecualian dijelaskan di bagian [Spesifikasi yang tetap berlaku](#spesifikasi-yang-tetap-berlaku).

Status di setiap tabel:

- **Diadopsi**: sudah ada di repo.
- **Requirement**: sudah masuk PRD dan punya task.
- **Kandidat**: dipertimbangkan, belum diputuskan.

Bila dokumen ini berbeda dengan PRD, PRD yang berlaku; dokumen ini menjelaskan **alasannya**.

---

## 1. Evaluasi yang bisa dipercaya

Angka evaluasi adalah inti klaim OmniRail. Bagian ini memastikan angka itu jujur tentang ketidakpastiannya.

| Metode | Dipakai untuk | Status |
| --- | --- | --- |
| Interval kepercayaan per metrik dan analisis daya [1] | Setiap recall, precision, dan false positive rate dilaporkan dengan interval 95% (rumus skor Wilson, cocok untuk proporsi dekat 0 atau 1), dan jumlah baris uji direncanakan agar selisih yang dicari bisa terdeteksi | Diadopsi (`eval/tools/statistik.py`), requirement EVAL-09 |
| Perbandingan berpasangan per butir uji [1], [2] | Dua sistem pada baris yang sama dibandingkan per baris (uji McNemar eksak), bukan dengan membandingkan angka ringkasan. Dipakai untuk OmniRail lawan Presidio di Tahap 0 dan versi baru lawan baseline di CI | Diadopsi (`statistik.py`), requirement EVAL-09 |
| Manajemen mutu anotasi [3] | Tinjauan label oleh orang kedua (T-007): kesepakatan dihitung dengan kappa Cohen (target κ ≥ 0,8), tingkat kesalahan dihitung dari sampel yang dinilai ulang, dan perbedaan diselesaikan lewat adjudikasi | Diadopsi (`statistik.py`), requirement T-007 |
| Perlindungan set uji dari kontaminasi [4] | Holdout tidak dibuka saat menyetel aturan, tidak diterbitkan, dan setiap run dicatat. Set uji yang sudah "terlihat" tidak lagi memberi angka yang jujur | Requirement EVAL-13 |
| *Datasheets for Datasets* [5] | Dokumentasi asal-usul, batas, dan cara pakai dataset | Diadopsi (`eval/DATASHEET.md`) |
| Uji fungsional berbasis templat [6] | Tes fungsi minimum per entitas dan tes kontras (kalimat mirip yang tidak boleh terdeteksi), dibangkitkan dari templat dan divalidasi. Tes invarian: pemisah, huruf, bingkai, dan gaya ketik tidak boleh mengubah temuan | Requirement EVAL-10 |
| Text Anonymization Benchmark (TAB) [7] | Membedakan identifier langsung (NIK, nomor kartu) dan identifier kuasi (tanggal lahir, plat) saat melaporkan recall | Requirement (catatan di EVAL-09) |
| *Property-based testing* dan uji silang (*differential testing*) [8] | Invarian tokenisasi: `pulihkan(samarkan(x)) = x`, teks bertoken tidak memuat nilai entitas, normalisasi idempoten. Uji silang: implementasi Rust harus memberi temuan yang sama dengan prototipe Python (T-011) | Requirement EVAL-11, EVAL-12 |
| Fuzzing [9] | Mencari panic dan pelanggaran invarian pada normalisasi Unicode dan parser request | Requirement EVAL-11 (P1) |
| Dokumentasi model dan komponen [10] | "Kartu pack": setiap policy pack menyertakan metrik, dataset uji, dan batasnya. Studi atas 32 ribu model card menunjukkan bagian batasan dan evaluasi paling sering dikosongkan, jadi keduanya dibuat wajib | Kandidat (bersama CFG-09) |

### Temuan dari menerapkan interval kepercayaan ke dataset sekarang

`python3 eval/tools/statistik.py` menghasilkan setengah lebar interval 95% berikut:

| n | p = 0,80 | p = 0,90 | p = 0,95 | p = 0,98 |
| --- | --- | --- | --- | --- |
| 50 | ±10,9 | ±8,5 | ±6,2 | ±5,1 |
| 100 | ±7,8 | ±6,0 | ±4,5 | ±3,2 |
| 150 | ±6,4 | ±4,8 | ±3,7 | ±2,5 |
| 300 | ±4,5 | ±3,4 | ±2,5 | ±1,7 |
| 1000 | ±2,5 | ±1,9 | ±1,4 | ±0,9 |

Akibatnya:

1. **Target false positive ≤ 2% per entitas belum bisa dibuktikan.** Dengan ± 110 baris negatif per entitas dan nol false positive, batas atas intervalnya masih 3,4%. Butuh ≥ 190 baris negatif per entitas, atau penilaian pada gabungan entitas (± 1.300 baris, batas atas 0,3%). PRD bagian 9 kini menilai target ini pada gabungan.
2. **Recall per entitas punya ketelitian sekitar ±5 poin.** Selisih 3 poin antara dua versi belum tentu nyata. Karena itu, CI memakai uji berpasangan per baris (apakah baris yang berubah hasilnya lebih banyak memburuk daripada membaik), bukan selisih angka mentah [1].
3. **Kriteria Tahap 0 ("unggul ≥ 10 poin") masuk akal pada gabungan lima entitas** (± 600 kemunculan, interval sekitar ±2,5 poin), tetapi tidak per entitas.

## 2. Deteksi

| Metode | Dipakai untuk | Status |
| --- | --- | --- |
| Pola + validator + kata konteks, seperti arsitektur recognizer Presidio [11] | Kerangka deteksi entitas. Bedanya: OmniRail mewajibkan kata konteks untuk entitas berisiko tinggi, dan validatornya memeriksa struktur dokumen Indonesia | Requirement PII-01, PII-07 |
| Algoritma Luhn | Validasi nomor kartu, digabung dengan prefix jaringan | Diadopsi (validator di pemeriksa dataset), requirement PII-01 |
| Regex tanpa backtracking [12] | ReDoS masih ditemukan di layanan produksi besar [13]. Crate Rust `regex` berbasis automata hingga menjamin waktu pencocokan `O(m × n)`, sehingga pola di policy pack tidak bisa dipakai untuk ReDoS. Fitur look-around dan backreference ditolak | Requirement POL-06 |
| Pencocokan banyak kata sekaligus (crate `aho-corasick`) [12] | Mencocokkan banyak kata kunci dan kata konteks dalam satu lintasan teks | Kandidat (detail implementasi) |
| Normalisasi Unicode NFKC (UAX #15) [14] | Menutup penghindaran deny-list dengan huruf lebar penuh | Requirement POL-02 |
| *Skeleton* confusables (UTS #39) [14] | Menutup penghindaran dengan huruf mirip lintas aksara (misalnya huruf Kiril yang tampak seperti huruf Latin), yang tidak ditangani NFKC | Requirement POL-07 (P1) |
| Perbandingan alat deteksi secret [15] | Dasar pendekatan prefix khusus per layanan: studi ini menemukan bahwa sebagian besar false positive alat deteksi secret berasal dari regex generik dan perhitungan entropi yang tidak efektif. Deteksi entropi (CRED-04) karenanya tetap P1 dan wajib diukur dulu | Requirement CRED-01 |
| SecretBench [16] | Set uji eksternal untuk mengukur false positive detektor credentials (akses diminta ke penyusunnya) | Kandidat (pelengkap T-305) |
| GLiNER [17] dan sumber data NLP Indonesia NusaCrowd [18] | Jalur NER lokal untuk nama, alamat, dan instansi (PII-09, P2). Perhatikan lisensi: sebagian model PII turunan GLiNER berlisensi non-komersial | Kandidat |

## 3. Penyamaran dan pemulihan

| Metode | Dipakai untuk | Status |
| --- | --- | --- |
| Kerangka de-identifikasi ISO/IEC 27559:2022 dan NIST SP 800-188 [19] | Istilah yang tepat: tokenisasi OmniRail adalah **pseudonimisasi reversibel**. Teks bertoken tetap data pribadi bagi pihak yang memegang tabel token, jadi dokumen publik tidak boleh menyebutnya "anonimisasi" | Requirement (bagian 10, kata yang dipakai di materi publik) |
| Hide and Seek (HaS) [20] | Pembanding desain: HaS memakai model lokal untuk menyamarkan dan memulihkan; OmniRail memakai tabel token deterministik. Dipakai sebagai prior art di eksperimen format token | Kandidat (Q14, T-207) |
| *Format-preserving encryption* FF1 [21] | Opsi nilai pengganti yang tampak realistis dan konsisten tanpa menyimpan tabel, untuk dibandingkan di eksperimen Q14. Draf revisi NIST 2025 menghapus FF3, jadi hanya FF1 yang dipertimbangkan | Kandidat |
| Penghapusan memori eksplisit (crate `zeroize`) | Tabel token dihapus dari memori begitu request selesai, bukan hanya dibebaskan | Requirement PII-05 |

## 4. Audit log dan kebijakan

| Metode | Dipakai untuk | Status |
| --- | --- | --- |
| Serialisasi JSON kanonik (RFC 8785, lihat [pengecualian](#spesifikasi-yang-tetap-berlaku)) | Kebijakan efektif diserialisasi secara kanonik sebelum dihitung `policy_hash`, sehingga hash yang sama bisa dihitung ulang oleh pihak lain dengan pustaka apa pun | Requirement AUD-02 |
| Log transparansi berbasis pohon Merkle: Certificate Transparency 2.0 [22] dan log transparansi Sigstore [23] | Setiap baris audit log memuat hash baris sebelumnya, dengan *checkpoint* bertanda tangan berkala. Penghapusan atau pengubahan baris bisa dideteksi oleh `omnirail audit verify` | Requirement AUD-06 (P1) |
| Perbandingan *constant-time* (crate `subtle`) | Perbandingan kunci OmniRail tanpa kebocoran lewat waktu | Requirement CFG-07 |

## 5. Rantai pasok dan rilis

Proxy yang memegang kunci provider dan melihat data pribadi harus bisa dibuktikan berasal dari kode yang dipublikasikan.

| Metode | Dipakai untuk | Status |
| --- | --- | --- |
| Sigstore [23] atau GitHub artifact attestations, dengan provenance SLSA | Setiap binary dan image rilis ditandatangani tanpa kunci jangka panjang dan bisa diverifikasi asal build-nya | Requirement DIST-08 |
| SBOM (SPDX atau CycloneDX) | Daftar dependensi setiap rilis | Requirement DIST-08 |
| `cargo audit` (RustSec) dan `cargo deny` | CI gagal bila ada dependensi dengan advisori keamanan atau lisensi yang tidak diizinkan | Requirement DIST-08 |
| `#![forbid(unsafe_code)]` di `omnirail-core` | Menutup kelas bug memori di bagian yang memproses data pribadi | Requirement DIST-08 |
| OpenSSF Scorecard | Penilaian praktik keamanan repo yang bisa dilihat publik | Requirement DIST-08 |
| Penandatanganan policy pack dengan mekanisme yang sama | Pack dari pihak lain bisa diverifikasi sebelum dimuat | Kandidat (CFG-09, P2) |

## 6. Benchmark latensi

| Metode | Dipakai untuk | Status |
| --- | --- | --- |
| Beban *open-loop* dan menghindari *coordinated omission* [24] | Beban dikirim pada laju tetap, dan latensi dihitung dari jadwal kirim, bukan dari saat request benar-benar terkirim. Benchmark *closed-loop* bisa meremehkan p99 berkali-kali lipat | Requirement EVAL-05 |
| HdrHistogram (dipakai `wrk2`) [24] | Menyimpan distribusi latensi dengan presisi tetap sampai persentil tinggi | Requirement EVAL-05 |

## 7. Model ancaman dan kerangka risiko

| Kerangka | Dipakai untuk | Status |
| --- | --- | --- |
| STRIDE dan LINDDUN, termasuk perluasan LINDDUN untuk sistem GenAI [25] | Model ancaman keamanan (STRIDE) dan privasi (LINDDUN: *linkability*, *identifiability*, dan seterusnya). LINDDUN relevan karena audit log dan laporan paparan sendiri bisa menjadi sumber *linkability*. Perluasan GenAI-nya menambah contoh ancaman khusus sistem LLM | Requirement (T-342) |
| OWASP Top 10 for LLM Applications, edisi 2025 [26] | Kosakata risiko yang dikenal pembeli dan auditor. Edisi yang lebih baru mungkin sudah terbit; cek sebelum dipakai di materi publik | Requirement (T-342) |
| NIST AI RMF 1.0 dan profil Generative AI (NIST AI 600-1) [27] | Bahasa untuk laporan "bukti pendukung": risiko privasi data dan keamanan informasi. Kerangka sukarela, bukan sertifikasi | Kandidat (REP-03) |

Pemetaan awal ke OWASP Top 10 for LLM Applications 2025:

| Risiko | Cakupan OmniRail | Catatan |
| --- | --- | --- |
| LLM01 Prompt Injection | Sebagian kecil | Hanya deny-list. Tidak boleh diklaim sebagai proteksi injection |
| LLM02 Sensitive Information Disclosure | Inti produk | Untuk arah aplikasi → provider. Kebocoran dari jawaban model hanya tercakup lewat pemulihan token, bukan pemindaian jawaban |
| LLM03 Supply Chain | Untuk OmniRail sendiri | DIST-08 |
| LLM05 Improper Output Handling | Sebagian (P1) | Validasi JSON (JSON-01 s.d. 04) |
| LLM10 Unbounded Consumption | Sebagian | Batas body dan panjang input (POL-01); rate limit ditunda |

---

## Rujukan

Semua terbit akhir 2021 sampai 2026. Dokumentasi perangkat lunak dan standar yang terus diperbarui dikutip pada versi terbarunya.

1. E. Miller. "Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations." [arXiv:2411.00640](https://arxiv.org/abs/2411.00640), 2024.
2. D. Ulmer, C. Hardmeier, J. Frellsen. "deep-significance: Easy and Meaningful Statistical Significance Testing in the Age of Neural Networks." [arXiv:2204.06815](https://arxiv.org/abs/2204.06815), 2022.
3. J.-C. Klie, R. Eckart de Castilho, I. Gurevych. "Analyzing Dataset Annotation Quality Management in the Wild." *Computational Linguistics* 50(3), 2024. [ACL Anthology](https://aclanthology.org/2024.cl-3.1).
4. O. Sainz dkk. "NLP Evaluation in trouble: On the Need to Measure LLM Data Contamination for each Benchmark." Findings of EMNLP 2023. [ACL Anthology](https://aclanthology.org/2023.findings-emnlp.722).
5. T. Gebru dkk. "Datasheets for Datasets." *Communications of the ACM* 64(12), Desember 2021.
6. P. Röttger, H. Seelawi, D. Nozza, Z. Talat, B. Vidgen. "Multilingual HateCheck: Functional Tests for Multilingual Hate Speech Detection Models." WOAH 2022. [ACL Anthology](https://aclanthology.org/2022.woah-1.15).
7. I. Pilán, P. Lison, L. Øvrelid, A. Papadopoulou, D. Sánchez, M. Batet. "The Text Anonymization Benchmark (TAB): A Dedicated Corpus and Evaluation Framework for Text Anonymization." *Computational Linguistics* 48(4), 2022. [ACL Anthology](https://aclanthology.org/2022.cl-4.19), [kode evaluasi](https://github.com/NorskRegnesentral/text-anonymization-benchmark).
8. H. Goldstein, J. W. Cutler, D. Dickstein, B. C. Pierce, A. Head. "Property-Based Testing in Practice." ICSE 2024. [Halaman ICSE](https://conf.researchr.org/details/icse-2024/icse-2024-research-track/90/Property-Based-Testing-in-Practice). Implementasi Rust: `proptest`.
9. X. Zhu, S. Wen, S. Camtepe, Y. Xiang. "Fuzzing: A Survey for Roadmap." *ACM Computing Surveys*, 2022. DOI 10.1145/3512345. Implementasi Rust: `cargo-fuzz` (libFuzzer).
10. W. Liang dkk. "Systematic analysis of 32,111 AI model cards characterizes documentation practice in AI." *Nature Machine Intelligence*, 2024. Pracetak: [arXiv:2402.05160](https://arxiv.org/abs/2402.05160).
11. Microsoft Presidio, dokumentasi [analyzer](https://microsoft.github.io/presidio/analyzer) dan [peningkatan skor dengan kata konteks](https://microsoft.github.io/presidio/tutorial/06_context) (diakses November 2026).
12. Dokumentasi crate Rust [`regex`](https://docs.rs/crate/regex/1.12.3/source/README.md) (versi 1.12) dan `aho-corasick`.
13. E. Barlas, X. Du, J. C. Davis. "Exploiting Input Sanitization for Regex Denial of Service." ICSE 2022. [arXiv:2303.01996](https://arxiv.org/abs/2303.01996).
14. Unicode Technical Standard #39, *Unicode Security Mechanisms*, versi 17.0 (2025), [unicode.org/reports/tr39](https://unicode.org/reports/tr39/); dan UAX #15, *Unicode Normalization Forms*, versi terbaru.
15. S. K. Basak, J. Cox, B. Reaves, L. Williams. "A Comparative Study of Software Secrets Reporting by Secret Detection Tools." ESEM 2023. [arXiv:2307.00714](https://arxiv.org/abs/2307.00714).
16. S. K. Basak, L. Neil, B. Reaves, L. Williams. "SecretBench: A Dataset of Software Secrets." MSR 2023. [arXiv:2303.06729](https://arxiv.org/abs/2303.06729).
17. U. Zaratiana dkk. "GLiNER: Generalist Model for Named Entity Recognition using Bidirectional Transformer." NAACL 2024. Varian PII: "GLiNER2-PII: A Multilingual Model for Personally Identifiable Information Extraction," [arXiv:2605.09973](https://arxiv.org/abs/2605.09973), 2026.
18. S. Cahyawijaya dkk. "NusaCrowd: Open Source Initiative for Indonesian NLP Resources." Findings of ACL 2023. [ACL Anthology](https://aclanthology.org/2023.findings-acl.868).
19. ISO/IEC 27559:2022, *Privacy enhancing data de-identification framework*; NIST SP 800-188, *De-Identifying Government Datasets: Techniques and Governance* (2023).
20. Y. Chen, T. Li, H. Liu, Y. Yu. "Hide and Seek (HaS): A Lightweight Framework for Prompt Privacy Protection." [arXiv:2309.03057](https://arxiv.org/abs/2309.03057), 2023.
21. NIST SP 800-38G Revision 1, Second Public Draft, *Recommendation for Block Cipher Modes of Operation: Methods for Format-Preserving Encryption*, Februari 2025. [csrc.nist.gov](https://csrc.nist.gov/pubs/sp/800/38/g/r1/2pd).
22. B. Laurie, E. Messeri, R. Stradling. RFC 9162, *Certificate Transparency Version 2.0*, Desember 2021.
23. Z. Newman, J. S. Meyers, S. Torres-Arias. "Sigstore: Software Signing for Everybody." ACM CCS 2022. [Pengumuman Sigstore](https://blog.sigstore.dev/sigstore-software-signing-for-everybody-has-been-published-in-the-proceedings-of-the-acm-bb7e7d679a73/).
24. M. Brooker. Tulisan teknis tentang beban *open-loop* dan *closed-loop*, Mei 2023. [brooker.co.za](https://brooker.co.za/blog/2023/05/10/open-closed.html). Alat: [wrk2](https://github.com/giltene/wrk2) dan HdrHistogram. Bukan paper peer-review; belum ditemukan paper 2021–2026 yang setara.
25. Q. Liao, J. Bellemans, L. Sion dkk. "A LINDDUN-based Privacy Threat Modeling Framework for GenAI." [arXiv:2603.06051](https://arxiv.org/abs/2603.06051), 2026. Metodologi: [linddun.org](https://linddun.org).
26. OWASP Top 10 for LLM Applications 2025. [genai.owasp.org](https://genai.owasp.org/llm-top-10/).
27. NIST AI 100-1, *AI Risk Management Framework 1.0* (2023); NIST AI 600-1, *Generative Artificial Intelligence Profile* (2024). [doi.org/10.6028/NIST.AI.600-1](https://doi.org/10.6028/NIST.AI.600-1).

### Spesifikasi yang tetap berlaku

- **RFC 8785, *JSON Canonicalization Scheme* (Juni 2020).** Sedikit di luar batas lima tahun, tetapi belum ada versi pengganti dan masih menjadi satu-satunya spesifikasi IETF untuk JSON kanonik. Dipakai sebagai spesifikasi teknis untuk `policy_hash` (AUD-02), bukan sebagai rujukan ilmiah. Bila batas lima tahun harus diterapkan ketat, alternatifnya adalah mendefinisikan serialisasi kanonik sendiri di PRD, dengan konsekuensi pihak lain harus mengikuti definisi OmniRail.
- Algoritma Luhn, uji McNemar, kappa Cohen, dan rumus interval Wilson adalah metode baku yang tercantum di buku teks. Dokumen ini tidak mengutip makalah aslinya; rujukan [1] s.d. [3] menjelaskan pemakaiannya dalam evaluasi modern.

Catatan verifikasi: rujukan di atas dicek lewat pencarian web pada 11 November 2026. Beberapa hanya terverifikasi sampai abstrak atau halaman konferensi, belum dari teks lengkap; detail angka di paper perlu dibaca langsung sebelum dikutip di materi publik.
