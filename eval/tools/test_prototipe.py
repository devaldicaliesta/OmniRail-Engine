import unittest

import evaluasi as e
import prototipe_detektor as p


def jenis_nilai(teks, lalu=None):
    return [(t.jenis, t.nilai) for t in p.deteksi_pesan(teks, lalu)]


class TestKriteriaPRD(unittest.TestCase):
    def test_konteks_menentukan_nik_atau_kartu(self):
        self.assertEqual(jenis_nilai("NIK saya 5171041203944539"), [("nik", "5171041203944539")])
        self.assertEqual(jenis_nilai("Pembayaran dengan kartu 5171041203944539 berhasil"),
                         [("credit_card", "5171041203944539")])

    def test_kk_butuh_konteks(self):
        self.assertEqual(jenis_nilai("No. KK 3330060605122124"), [("kk", "3330060605122124")])
        self.assertEqual(jenis_nilai("3330060605122124"), [("nik", "3330060605122124")])

    def test_konteks_sebelum_nilai_menang_bila_seimbang(self):
        self.assertEqual(
            jenis_nilai("No. KK 7250270205242406, NIK kepala keluarga 5245280311400260"),
            [("kk", "7250270205242406"), ("nik", "5245280311400260")])

    def test_tanggal_lahir(self):
        self.assertEqual(jenis_nilai("Mohon maaf lahir dan batin, 10-04-2026"), [])
        self.assertEqual(jenis_nilai("lahir 12/04/1974"), [("birth_date", "12/04/1974")])

    def test_nomor_pesanan_dengan_tanggal_tidak_valid_bukan_nik(self):
        self.assertEqual(jenis_nilai("Nomor pesanan 2311093234567890 siap dikirim"), [])

    def test_konteks_lintas_pesan(self):
        self.assertEqual(jenis_nilai("1234567890", "Boleh minta nomor rekeningnya untuk refund?"),
                         [("bank_account", "1234567890")])
        self.assertEqual(jenis_nilai("1234567890", "Boleh minta nomor pesanannya?"), [])

    def test_email_dan_jebakannya(self):
        self.assertEqual(jenis_nilai("Kontak: a.wijaya+promo@example.net."),
                         [("email", "a.wijaya+promo@example.net")])
        self.assertEqual(jenis_nilai("git clone git@github.com:contoh/web.git"), [])
        self.assertEqual(jenis_nilai("pakai logo@2x.png"), [])


class TestEvaluasi(unittest.TestCase):
    def test_pecah_multi_pesan(self):
        self.assertEqual(e.pesan_dari_teks("<<assistant>> Nomor rekening?\n<<user>> 123"),
                         [("assistant", "Nomor rekening?"), ("user", "123")])
        self.assertEqual(e.pesan_dari_teks("biasa"), [("user", "biasa")])

    def test_regresi_prototipe_di_dev(self):
        hasil = e.evaluasi(e.muat_detektor("prototipe")[0])
        semua = hasil["gabungan"]["semua_p0"]
        self.assertGreaterEqual(semua["recall"]["nilai"], 0.99)
        self.assertGreaterEqual(semua["precision"]["nilai"], 0.99)
        self.assertLessEqual(semua["false_positive"]["nilai"], 0.01)


if __name__ == "__main__":
    unittest.main()
