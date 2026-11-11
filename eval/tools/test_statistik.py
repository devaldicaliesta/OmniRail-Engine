"""Test unit untuk `statistik.py`. Jalankan: python3 -m unittest discover -s eval/tools"""

import unittest

import statistik as s


class TestWilson(unittest.TestCase):
    def test_nilai_rujukan(self):
        # Nilai rujukan interval skor Wilson 95% untuk 90/100.
        lo, hi = s.wilson(90, 100)
        self.assertAlmostEqual(lo, 0.8256, places=4)
        self.assertAlmostEqual(hi, 0.9448, places=4)

    def test_batas_nol_dan_penuh(self):
        lo, hi = s.wilson(0, 110)
        self.assertEqual(lo, 0.0)
        self.assertAlmostEqual(hi, 0.0337, places=4)
        lo, hi = s.wilson(50, 50)
        self.assertEqual(hi, 1.0)
        self.assertLess(lo, 1.0)

    def test_input_salah(self):
        with self.assertRaises(ValueError):
            s.wilson(1, 0)
        with self.assertRaises(ValueError):
            s.wilson(5, 4)


class TestMcNemar(unittest.TestCase):
    def test_nilai_rujukan(self):
        # 2 * P(X <= 3), X ~ Binomial(15, 0,5) = 2 * 576 / 32768
        self.assertAlmostEqual(s.mcnemar_eksak(12, 3), 0.03515625)
        self.assertAlmostEqual(s.mcnemar_eksak(3, 12), 0.03515625)

    def test_tanpa_perbedaan(self):
        self.assertEqual(s.mcnemar_eksak(0, 0), 1.0)
        self.assertEqual(s.mcnemar_eksak(5, 5), 1.0)


class TestKappa(unittest.TestCase):
    def test_nilai_rujukan(self):
        # teramati 5/6, harapan 0,5 -> kappa 2/3
        self.assertAlmostEqual(s.cohen_kappa("aabbab", "aabbbb"), 2 / 3)

    def test_sepakat_penuh(self):
        self.assertEqual(s.cohen_kappa(["x", "y", "x"], ["x", "y", "x"]), 1.0)

    def test_input_salah(self):
        with self.assertRaises(ValueError):
            s.cohen_kappa(["a"], ["a", "b"])


if __name__ == "__main__":
    unittest.main()
