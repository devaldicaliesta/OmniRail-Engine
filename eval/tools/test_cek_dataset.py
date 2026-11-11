"""Test unit untuk `cek_dataset.py`. Jalankan: python3 -m unittest discover eval/tools"""

import unittest

import cek_dataset as c


class TestValidator(unittest.TestCase):
    def lolos(self, fungsi, *nilai):
        for v in nilai:
            with self.subTest(v=v):
                self.assertIsNone(fungsi(v))

    def gagal(self, fungsi, *nilai):
        for v in nilai:
            with self.subTest(v=v):
                self.assertIsNotNone(fungsi(v))

    def test_luhn_dan_prefix_kartu(self):
        # D050/D051: nilai yang lolos struktur NIK sekaligus Luhn Mastercard.
        self.lolos(c.cek_credit_card, "5171041203944539", "4207492652071376",
                   "373525425663999", "2221-7821-3003-1109", "5464 3489 2897 6704")
        self.gagal(c.cek_credit_card, "5171041203944538", "1234567890123452", "4207-4926-52O7-1376")

    def test_nik(self):
        self.lolos(c.cek_nik, "5171041203944539", "3374054901950002", "3273011503900001")
        self.gagal(
            c.cek_nik,
            "3273013203900001",  # tanggal 32
            "3273011513900001",  # bulan 13
            "3273011503900000",  # nomor urut 0000
            "2073011503900001",  # kode provinsi 20
            "327301150390001",   # 15 digit
        )

    def test_kk_tidak_menerima_tanggal_perempuan(self):
        self.lolos(c.cek_kk, "3330060605122124")
        self.gagal(c.cek_kk, "3330064605122124")

    def test_nip_pns_dan_pppk(self):
        self.lolos(c.cek_nip, "19580818 198404 1 001", "199002192019211001")
        self.gagal(
            c.cek_nip,
            "19580818 197004 1 001",  # diangkat sebelum umur 18
            "19580818 198413 1 001",  # bulan TMT 13
            "19580818 198404 3 001",  # jenis kelamin 3
            "19580818 198404 1 000",  # nomor urut 000
        )

    def test_phone_id(self):
        self.lolos(c.cek_phone_id, "0812-3456-7801", "+62 813 2222 4455", "6285712345678")
        self.gagal(c.cek_phone_id, "(021) 5550 1234", "0212345678", "0812345")

    def test_birth_date(self):
        self.lolos(c.cek_birth_date, "12/04/1974", "1974-04-12", "17 November 1992", "18 Mei 1956", "3 Agt 1990")
        self.gagal(c.cek_birth_date, "31/02/1990", "12/04/1899", "12 Foo 1990")

    def test_ip_address(self):
        self.lolos(c.cek_ip_address, "203.0.113.193", "2001:db8:9572::47cf")
        self.gagal(c.cek_ip_address, "10.1.2.3", "192.168.0.1", "127.0.0.1", "224.0.0.1", "01.2.3.4")

    def test_lainnya(self):
        self.lolos(c.cek_passport_id, "B2492233", "EB 5619567")
        self.gagal(c.cek_passport_id, "b2492233", "ABC123456")
        self.lolos(c.cek_bpjs, "3045157118236", "66420080184", "3093119106167541")
        self.gagal(c.cek_bpjs, "123456789012")
        self.lolos(c.cek_npwp, "01.234.567.8-901.000", "012345678901000", "0012345678901000")
        self.gagal(c.cek_npwp, "01234567890")
        self.lolos(c.cek_vehicle_plate, "B 1234 ABC", "DC 942 N")
        self.gagal(c.cek_vehicle_plate, "Kamar D 12", "B 1234")
        self.lolos(c.cek_email, "a.wijaya+promo@example.net")
        self.gagal(c.cek_email, "git@github", "logo@2x.p")


class TestBaris(unittest.TestCase):
    def periksa(self, **r):
        baris = {"id": "D999", "kategori": "positif", "teks": "", "diharapkan": "-",
                 "cakupan_mvp": "ya", "catatan": ""}
        baris.update(r)
        lap, hit = c.Laporan(), c.Hitungan()
        c.periksa_baris("dev", 2, baris, lap, hit)
        return lap, hit

    def test_baris_valid(self):
        lap, hit = self.periksa(teks="email saya a@b.co dan a@b.co",
                                diharapkan="email:a@b.co | email:a@b.co")
        self.assertEqual(lap.error, [])
        self.assertEqual(hit.positif["email"], 2)

    def test_nilai_harus_muncul_sebanyak_yang_ditulis(self):
        lap, _ = self.periksa(teks="email saya a@b.co", diharapkan="email:a@b.co | email:a@b.co")
        self.assertTrue(any("muncul 1x" in e for e in lap.error))

    def test_negatif_wajib_menandai_entitas(self):
        lap, _ = self.periksa(kategori="negatif", teks="Nomor pesanan 123")
        self.assertTrue(any("diawali entitas" in e for e in lap.error))
        lap, hit = self.periksa(kategori="negatif", teks="Nomor pesanan 123", catatan="[nik] pesanan")
        self.assertEqual(lap.error, [])
        self.assertEqual(hit.negatif["nik"], 1)

    def test_ner_dan_p1_harus_di_luar_cakupan(self):
        lap, _ = self.periksa(teks="Nama saya Siti", diharapkan="nama:Siti")
        self.assertTrue(any("NER" in e for e in lap.error))
        lap, _ = self.periksa(teks="plat B 1234 ABC", diharapkan="vehicle_plate:B 1234 ABC")
        self.assertTrue(any("P1" in e for e in lap.error))

    def test_validator_gagal_error_atau_peringatan(self):
        lap, _ = self.periksa(teks="NIK 3273013203900001", diharapkan="nik:3273013203900001")
        self.assertEqual(len(lap.error), 1)
        lap, _ = self.periksa(teks="NIK 3273013203900001", diharapkan="nik:3273013203900001",
                              cakupan_mvp="tidak")
        self.assertEqual((len(lap.error), len(lap.peringatan)), (0, 1))

    def test_kredensial_dan_injeksi(self):
        lap, _ = self.periksa(kategori="kredensial", teks="x", diharapkan="api_key")
        self.assertEqual(lap.error, [])
        lap, _ = self.periksa(kategori="kredensial", teks="x", diharapkan="token")
        self.assertEqual(len(lap.error), 1)
        lap, _ = self.periksa(kategori="injeksi", teks="x", diharapkan="blok")
        self.assertEqual(len(lap.error), 1)


class TestDatasetRepo(unittest.TestCase):
    def test_dataset_di_repo_lolos(self):
        self.assertEqual(c.main([]), 0)


if __name__ == "__main__":
    unittest.main()
