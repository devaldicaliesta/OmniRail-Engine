import csv
import tempfile
import unittest
from pathlib import Path

import tinjau_label as t


class TestLabelBaris(unittest.TestCase):
    def test_bentuk_label(self):
        self.assertEqual(t.label_baris({"kategori": "positif", "diharapkan": "phone_id:0812 | nik:3273 | nik:3274"}),
                         "nik+phone_id")
        self.assertEqual(t.label_baris({"kategori": "negatif", "diharapkan": "-"}), "-")
        self.assertEqual(t.label_baris({"kategori": "kredensial", "diharapkan": "jwt"}), "jwt")
        self.assertEqual(t.label_baris({"kategori": "injeksi", "diharapkan": "deny"}), "deny")


class TestNilai(unittest.TestCase):
    def test_label_dataset_sendiri_sepakat_penuh(self):
        dev = t.baca_dev()
        with tempfile.TemporaryDirectory(dir=t.AKAR / "eval") as d:
            path = Path(d) / "t007-formulir-uji.csv"
            with path.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=t.KOLOM_FORMULIR, lineterminator="\n")
                w.writeheader()
                for rid in ("D025", "D082", "D587", "D691"):
                    r = dev[rid]
                    w.writerow({"id": rid, "teks": r["teks"], "label_penilai": t.label_baris(r),
                                "cakupan_penilai": r["cakupan_mvp"], "komentar": ""})
            h = t.nilai(path)
        self.assertEqual(h["kesepakatan"], 1.0)
        self.assertEqual(h["beda_label"], [])
        self.assertEqual(h["beda_cakupan"], [])


if __name__ == "__main__":
    unittest.main()
