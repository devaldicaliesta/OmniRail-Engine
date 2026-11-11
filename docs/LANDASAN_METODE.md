# OmniRail Engine — Landasan metode dan rujukan

Dokumen ini memetakan setiap bagian OmniRail ke metode yang sudah dipublikasikan atau distandarkan. Tujuannya agar setiap klaim ("deteksi lebih baik", "log bisa diaudit", "rilis bisa dipercaya") punya dasar yang bisa diperiksa orang lain, bukan sekadar pernyataan pembangun.

Status di setiap tabel:

- **Diadopsi**: sudah ada di repo.
- **Requirement**: sudah masuk PRD dan punya task.
- **Kandidat**: dipertimbangkan, belum diputuskan.

Rujukan lengkap ada di bagian akhir. Bila rujukan berbeda dengan PRD, PRD yang berlaku; dokumen ini menjelaskan **alasannya**.

---

## 1. Evaluasi yang bisa dipercaya

Angka evaluasi adalah inti klaim OmniRail. Bagian ini memastikan angka itu jujur tentang ketidakpastiannya.

| Metode | Dipakai untuk | Status |
| --- | --- | --- |
| Interval skor Wilson [1] | Setiap recall, precision, dan false positive rate dilaporkan dengan interval kepercayaan 95% | Diadopsi (`eval/tools/statistik.py`), requirement EVAL-09 |
| Uji McNemar eksak [2] | Membandingkan dua sistem pada baris uji yang sama (OmniRail lawan Presidio di Tahap 0, versi baru lawan baseline di CI) | Diadopsi (`statistik.py`), requirement EVAL-09 |
| Kappa Cohen [3] | Kesepakatan dua penilai pada tinjauan label (T-007), target κ ≥ 0,8 | Diadopsi (`statistik.py`) |
| *Reusable holdout* [4] | Holdout yang dipakai berulang secara adaptif menghasilkan angka yang terlalu optimistis. Setiap run holdout dicatat, dan jumlahnya dibatasi | Requirement EVAL-13 |
| *Datasheets for Datasets* [5] | Dokumentasi asal-usul, batas, dan cara pakai dataset | Diadopsi (`eval/DATASHEET.md`) |
| CheckList [6] | Uji perilaku: tes fungsi minimum per entitas, dan tes invarian (pemisah, huruf, bingkai, dan gaya ketik tidak boleh mengubah temuan) | Requirement EVAL-10 |
| Text Anonymization Benchmark (TAB) [7] | Membedakan identifier langsung (NIK, nomor kartu) dan identifier kuasi (tanggal lahir, plat) saat melaporkan recall | Requirement (catatan di EVAL-09) |
| Uji silang / *differential testing* [8] | Prototipe Python (T-011) menjadi acuan; implementasi Rust harus memberi temuan yang sama pada dataset dev | Requirement EVAL-12 |
| *Property-based testing* [9] dan fuzzing | Invarian tokenisasi: `pulihkan(samarkan(x)) = x`, teks bertoken tidak memuat nilai entitas, normalisasi idempoten; fuzzing pada normalisasi Unicode dan parser | Requirement EVAL-11 |
| *Model Cards* [10] | "Kartu pack": setiap policy pack menyertakan metrik, dataset uji, dan batasnya | Kandidat (bersama CFG-09) |

### Temuan dari menerapkan interval Wilson ke dataset sekarang

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
2. **Recall per entitas punya ketelitian sekitar ±5 poin.** Selisih 3 poin antara dua versi belum tentu nyata. Karena itu, CI memakai McNemar (apakah baris yang berubah hasilnya lebih banyak memburuk daripada membaik), bukan selisih angka mentah.
3. **Kriteria Tahap 0 ("unggul ≥ 10 poin") masuk akal pada gabungan lima entitas** (± 600 kemunculan, interval sekitar ±2,5 poin), tetapi tidak per entitas.

## 2. Deteksi

| Metode | Dipakai untuk | Status |
| --- | --- | --- |
| Pola + validator + kata konteks, seperti arsitektur recognizer Presidio [11] | Kerangka deteksi entitas. Bedanya: OmniRail mewajibkan kata konteks untuk entitas berisiko tinggi, dan validatornya memeriksa struktur dokumen Indonesia | Requirement PII-01, PII-07 |
| Algoritma Luhn (ISO/IEC 7812-1) | Validasi nomor kartu, digabung dengan prefix jaringan | Diadopsi (validator di pemeriksa dataset), requirement PII-01 |
| Regex tanpa backtracking (crate Rust `regex`, berbasis automata hingga) [12] | Waktu pencocokan terbatas (`O(m × n)`), sehingga pola di policy pack tidak bisa dipakai untuk ReDoS. Fitur look-around dan backreference ditolak | Requirement POL-06 |
| Aho–Corasick [13] | Pencocokan banyak kata kunci dan kata konteks sekaligus dalam satu lintasan teks | Kandidat (detail implementasi) |
| Normalisasi Unicode NFKC (UAX #15) | Menutup penghindaran deny-list dengan huruf lebar penuh | Requirement POL-02 |
| *Skeleton* confusables (UTS #39) [14] | Menutup penghindaran dengan huruf mirip lintas aksara (misalnya huruf Kiril yang tampak seperti huruf Latin), yang tidak ditangani NFKC | Requirement POL-07 (P1) |
| Studi kebocoran secret di GitHub [15] | Dasar pendekatan prefix untuk credentials berformat khas, dan bukti bahwa secret yang sudah dihapus tetap tersimpan di riwayat git (alasan `omnirail scan` di pre-commit) | Requirement CRED-01, EVAL-07 |
| SecretBench [16] | Set uji eksternal untuk mengukur false positive detektor credentials (akses diminta ke penyusunnya) | Kandidat (pelengkap T-305) |
| GLiNER [17] dan data NER Indonesia IndoNLU (NERGrit, NERP) [18] | Jalur NER lokal untuk nama, alamat, dan instansi (PII-09, P2). Perhatikan lisensi: sebagian model PII turunan GLiNER berlisensi non-komersial | Kandidat |

## 3. Penyamaran dan pemulihan

| Metode | Dipakai untuk | Status |
| --- | --- | --- |
| Terminologi de-identifikasi ISO/IEC 20889:2018 dan NIST SP 800-188 [19] | Istilah yang tepat: tokenisasi OmniRail adalah **pseudonimisasi reversibel**. Teks bertoken tetap data pribadi bagi pihak yang memegang tabel token, jadi dokumen publik tidak boleh menyebutnya "anonimisasi" | Requirement (bagian 10, kata yang dipakai di materi publik) |
| Hide and Seek (HaS) [20] | Pembanding desain: HaS memakai model lokal untuk menyamarkan dan memulihkan; OmniRail memakai tabel token deterministik. Dipakai sebagai prior art di eksperimen format token | Kandidat (Q14, T-207) |
| *Format-preserving encryption* FF1 (NIST SP 800-38G) [21] | Opsi nilai pengganti yang tampak realistis dan konsisten tanpa menyimpan tabel, untuk dibandingkan di eksperimen Q14 | Kandidat |
| Penghapusan memori eksplisit (crate `zeroize`) | Tabel token dihapus dari memori begitu request selesai, bukan hanya dibebaskan | Requirement PII-05 |

## 4. Audit log dan kebijakan

| Metode | Dipakai untuk | Status |
| --- | --- | --- |
| JSON Canonicalization Scheme, RFC 8785 [22] | Serialisasi kanonik kebijakan efektif sebelum dihitung `policy_hash`, sehingga hash yang sama bisa dihitung ulang oleh pihak lain dengan pustaka apa pun | Requirement AUD-02 |
| Log berantai hash [23] dan struktur *tamper-evident* berbasis pohon [24], seperti Certificate Transparency (RFC 9162) | Setiap baris audit log memuat hash baris sebelumnya, dengan *checkpoint* bertanda tangan berkala. Penghapusan atau pengubahan baris bisa dideteksi oleh `omnirail audit verify` | Requirement AUD-06 (P1) |
| Perbandingan *constant-time* (crate `subtle`) | Perbandingan kunci OmniRail tanpa kebocoran lewat waktu | Requirement CFG-07 |

## 5. Rantai pasok dan rilis

Proxy yang memegang kunci provider dan melihat data pribadi harus bisa dibuktikan berasal dari kode yang dipublikasikan.

| Metode | Dipakai untuk | Status |
| --- | --- | --- |
| Sigstore [25] atau GitHub artifact attestations, dengan provenance SLSA | Setiap binary dan image rilis ditandatangani tanpa kunci jangka panjang dan bisa diverifikasi asal build-nya | Requirement DIST-08 |
| SBOM (SPDX atau CycloneDX) | Daftar dependensi setiap rilis | Requirement DIST-08 |
| `cargo audit` (RustSec) dan `cargo deny` | CI gagal bila ada dependensi dengan advisori keamanan atau lisensi yang tidak diizinkan | Requirement DIST-08 |
| `#![forbid(unsafe_code)]` di `omnirail-core` | Menutup kelas bug memori di bagian yang memproses data pribadi | Requirement DIST-08 |
| OpenSSF Scorecard | Penilaian praktik keamanan repo yang bisa dilihat publik | Requirement DIST-08 |
| Penandatanganan policy pack dengan mekanisme yang sama | Pack dari pihak lain bisa diverifikasi sebelum dimuat | Kandidat (CFG-09, P2) |

## 6. Benchmark latensi

| Metode | Dipakai untuk | Status |
| --- | --- | --- |
| Menghindari *coordinated omission* [26] | Beban dikirim pada laju tetap (open-loop, seperti wrk2), dan latensi dihitung dari jadwal kirim, bukan dari saat request benar-benar terkirim. Tanpa ini, p99 terlihat jauh lebih baik dari kenyataannya | Requirement EVAL-05 |
| HdrHistogram | Menyimpan distribusi latensi dengan presisi tetap sampai persentil tinggi | Requirement EVAL-05 |

## 7. Model ancaman dan kerangka risiko

| Kerangka | Dipakai untuk | Status |
| --- | --- | --- |
| STRIDE dan LINDDUN [27] | Model ancaman keamanan (STRIDE) dan privasi (LINDDUN: *linkability*, *identifiability*, dan seterusnya). LINDDUN relevan karena audit log dan laporan paparan sendiri bisa menjadi sumber *linkability* | Requirement (T-342) |
| OWASP Top 10 for LLM Applications, edisi 2025 [28] | Kosakata risiko yang dikenal pembeli dan auditor. Edisi yang lebih baru mungkin sudah terbit; cek sebelum dipakai di materi publik | Requirement (T-342) |
| NIST AI RMF dan profil Generative AI (NIST AI 600-1) [29] | Bahasa untuk laporan "bukti pendukung": risiko privasi data dan keamanan informasi. Kerangka sukarela, bukan sertifikasi | Kandidat (REP-03) |

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

1. E. B. Wilson. "Probable Inference, the Law of Succession, and Statistical Inference." *Journal of the American Statistical Association* 22(158), 1927.
2. Q. McNemar. "Note on the sampling error of the difference between correlated proportions or percentages." *Psychometrika* 12(2), 1947.
3. J. Cohen. "A Coefficient of Agreement for Nominal Scales." *Educational and Psychological Measurement* 20(1), 1960.
4. C. Dwork, V. Feldman, M. Hardt, T. Pitassi, O. Reingold, A. Roth. "The reusable holdout: Preserving validity in adaptive data analysis." *Science* 349(6248), 2015. [Ringkasan Google Research](https://research.google/blog/the-reusable-holdout-preserving-validity-in-adaptive-data-analysis/), [arXiv:1506.02629](https://arxiv.org/abs/1506.02629).
5. T. Gebru dkk. "Datasheets for Datasets." *Communications of the ACM* 64(12), 2021.
6. M. T. Ribeiro, T. Wu, C. Guestrin, S. Singh. "Beyond Accuracy: Behavioral Testing of NLP Models with CheckList." ACL 2020. [ACL Anthology](https://aclanthology.org/2020.acl-main.442).
7. I. Pilán, P. Lison, L. Øvrelid, A. Papadopoulou, D. Sánchez, M. Batet. "The Text Anonymization Benchmark (TAB): A Dedicated Corpus and Evaluation Framework for Text Anonymization." *Computational Linguistics* 48(4), 2022. [ACL Anthology](https://aclanthology.org/2022.cl-4.19), [kode evaluasi](https://github.com/NorskRegnesentral/text-anonymization-benchmark).
8. W. M. McKeeman. "Differential Testing for Software." *Digital Technical Journal* 10(1), 1998.
9. K. Claessen, J. Hughes. "QuickCheck: A Lightweight Tool for Random Testing of Haskell Programs." ICFP 2000. Implementasi Rust: `proptest`; fuzzing: `cargo-fuzz` (libFuzzer).
10. M. Mitchell dkk. "Model Cards for Model Reporting." FAT* 2019.
11. Microsoft Presidio: [analyzer](https://microsoft.github.io/presidio/analyzer) dan [peningkatan skor dengan kata konteks](https://microsoft.github.io/presidio/tutorial/06_context).
12. Crate Rust `regex`: [README dan jaminan kompleksitas](https://docs.rs/crate/regex/1.12.3/source/README.md). Dasar teori: K. Thompson, "Regular Expression Search Algorithm," *CACM* 11(6), 1968.
13. A. V. Aho, M. J. Corasick. "Efficient String Matching: An Aid to Bibliographic Search." *CACM* 18(6), 1975.
14. Unicode Technical Standard #39, *Unicode Security Mechanisms*. [unicode.org/reports/tr39](https://unicode.org/reports/tr39/). Normalisasi: UAX #15.
15. M. Meli, M. R. McNiece, B. Reaves. "How Bad Can It Git? Characterizing Secret Leakage in Public GitHub Repositories." NDSS 2019. [NDSS](https://www.ndss-symposium.org/ndss-paper/how-bad-can-it-git-characterizing-secret-leakage-in-public-github-repositories/).
16. S. K. Basak, L. Neil, B. Reaves, L. Williams. "SecretBench: A Dataset of Software Secrets." MSR 2023 Data and Tool Showcase. [arXiv:2303.06729](https://arxiv.org/abs/2303.06729).
17. U. Zaratiana dkk. "GLiNER: Generalist Model for Named Entity Recognition using Bidirectional Transformer." NAACL 2024. Varian PII: [GLiNER2-PII, arXiv:2605.09973](https://arxiv.org/abs/2605.09973).
18. B. Wilie dkk. "IndoNLU: Benchmark and Resources for Evaluating Indonesian Natural Language Understanding." [arXiv:2009.05387](https://arxiv.org/abs/2009.05387), [dataset](https://huggingface.co/datasets/indonlp/indonlu).
19. ISO/IEC 20889:2018, *Privacy enhancing data de-identification terminology and classification of techniques*; NIST SP 800-188, *De-Identifying Government Datasets* (2023).
20. Y. Chen, T. Li, H. Liu, Y. Yu. "Hide and Seek (HaS): A Lightweight Framework for Prompt Privacy Protection." [arXiv:2309.03057](https://arxiv.org/abs/2309.03057), 2023.
21. NIST SP 800-38G, *Recommendation for Block Cipher Modes of Operation: Methods for Format-Preserving Encryption* (FF1).
22. A. Rundgren, B. Jordan, S. Erdtman. RFC 8785, *JSON Canonicalization Scheme (JCS)*, 2020. [rfc-editor.org](https://www.rfc-editor.org/rfc/rfc8785).
23. B. Schneier, J. Kelsey. "Secure Audit Logs to Support Computer Forensics." *ACM TISSEC* 2(2), 1999.
24. S. A. Crosby, D. S. Wallach. "Efficient Data Structures for Tamper-Evident Logging." USENIX Security 2009. [USENIX](https://www.usenix.org/conference/usenixsecurity09/technical-sessions/presentation/efficient-data-structures-tamper-evident). Lihat juga RFC 9162 (Certificate Transparency 2.0).
25. Z. Newman, J. S. Meyers, S. Torres-Arias. "Sigstore: Software Signing for Everybody." ACM CCS 2022. [Pengumuman Sigstore](https://blog.sigstore.dev/sigstore-software-signing-for-everybody-has-been-published-in-the-proceedings-of-the-acm-bb7e7d679a73/).
26. G. Tene, tentang *coordinated omission*; alat `wrk2` dan HdrHistogram. [wrk2](https://github.com/giltene/wrk2).
27. LINDDUN privacy threat modeling, KU Leuven. [linddun.org](https://linddun.org). STRIDE: Microsoft Threat Modeling.
28. OWASP Top 10 for LLM Applications 2025. [genai.owasp.org](https://genai.owasp.org/llm-top-10/).
29. NIST AI 100-1, *AI Risk Management Framework 1.0* (2023); NIST AI 600-1, *Generative Artificial Intelligence Profile* (2024). [doi.org/10.6028/NIST.AI.600-1](https://doi.org/10.6028/NIST.AI.600-1).

Catatan verifikasi: rujukan di atas dicek lewat pencarian web pada 11 November 2026. Beberapa hanya terverifikasi sampai abstrak atau halaman konferensi, belum dari teks lengkap; detail angka di paper perlu dibaca langsung sebelum dikutip di materi publik.
