"""Version 0.6.1: Gesamttest-Freigabe, Abbruch und GUI ohne Motoren."""
import copy
import tempfile
import unittest
from pathlib import Path
from PySide6.QtWidgets import QApplication
from steuerzentrale import Steuerzentrale
from bedienfeld_qt import Bedienpanel
from verbindung import status_pruefen
from test_persistenz import gespeicherter_status, verbinden


def auto_status(ok=False,aktiv=False):
    n=gespeicherter_status()
    n.update(version="0.4.1",auto_supported=True,auto_testing=aktiv,auto_ok=ok,
             auto_message="Alle Tests OK" if ok else "Test offen",lcd_present=True)
    return n

class AutoTests(unittest.TestCase):
    def setUp(self):
        self.c=Steuerzentrale(); verbinden(self.c,auto_status())
        self.c.bestaetige_ausrichtung(True)

    def test_start_auch_mit_gespeicherten_endlagen(self):
        self.c.auto_kalibrierung()
        self.assertIn(b"AUTOCAL",self.c.link.port.gesendet[-1])
        self.assertTrue(self.c.beschaeftigt)
        self.assertTrue(self.c.freigabe())

    def test_ack_und_ruhezustand_waehrend_rtc_reichen_nicht(self):
        self.c.auto_kalibrierung(); nummer=self.c.pending
        self.c.empfangen(dict(type="ack",id=nummer,ok=True))
        self.c.empfangen(auto_status(aktiv=True))
        self.assertEqual(self.c.pending,nummer)
        self.assertTrue(self.c.freigabe())
        with self.assertRaises(ValueError): self.c.auto_kalibrierung()

    def test_erfolg_nach_abschluss(self):
        self.c.auto_kalibrierung()
        self.c.empfangen(dict(type="ack",id=self.c.pending,ok=True))
        self.c.empfangen(auto_status(ok=True))
        self.assertFalse(self.c.beschaeftigt)
        self.assertTrue(self.c.grenzen_bestaetigt)
        self.assertEqual(self.c.freigabe(),[])

    def test_abbruch_gibt_nicht_frei(self):
        self.c.auto_kalibrierung(); self.c.stopp()
        self.c.empfangen(dict(type="ack",id=self.c.pending,ok=True))
        self.c.empfangen(auto_status())
        self.assertFalse(self.c.beschaeftigt)
        self.assertTrue(self.c.freigabe())
        self.assertTrue(self.c.status["axes"][0]["calibrated"])

    def test_fehler_stoppt(self):
        self.c.auto_kalibrierung()
        self.c.empfangen(dict(type="fault",message="RTC ungueltig"))
        self.assertIn(b"STOP",self.c.link.port.gesendet[-1])
        self.assertTrue(self.c.freigabe())

    def test_fehlendes_lcd_oder_rtc_sperrt(self):
        for feld in ("lcd_present","rtc_present","rtc_valid","storage_ok"):
            n=auto_status(ok=True); n[feld]=False
            self.c.empfangen(n)
            self.assertTrue(self.c.freigabe(),feld)

    def test_keine_erfundene_ausrichtung(self):
        self.c.bestaetige_ausrichtung(False)
        with self.assertRaisesRegex(ValueError,"Ausrichtung"): self.c.auto_kalibrierung()
        self.assertEqual(self.c.link.port.gesendet,[])

    def test_alte_firmware_erhaelt_keinen_neuen_befehl(self):
        self.c.status=gespeicherter_status()
        with self.assertRaisesRegex(ValueError,"0.4.1"): self.c.auto_kalibrierung()

    def test_status_bool_streng_pruefen(self):
        n=auto_status(); n["auto_ok"]="false"
        with self.assertRaises(ValueError): status_pruefen(n)

class AutoGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app=QApplication.instance() or QApplication([])

    def test_knopf_und_farbe_nur_bei_vollstaendigem_erfolg(self):
        with tempfile.TemporaryDirectory() as ordner:
            w=Bedienpanel(datenordner=Path(ordner)); w.timer.stop()
            try:
                verbinden(w.core,auto_status()); w.core.bestaetige_ausrichtung(True)
                w.update_all_status()
                self.assertEqual(w.auto_cal_btn.text(),"Auto Kalibrierung")
                self.assertIn("#101010",w.btn_sim.styleSheet())
                self.assertFalse(w.operation_btn.isEnabled())
                w.auto_cal_btn.click()
                self.assertIn(b"AUTOCAL",w.core.link.port.gesendet[-1])
                w.core.empfangen(dict(type="ack",id=w.core.pending,ok=True))
                w.core.empfangen(auto_status(ok=True)); w.update_all_status()
                for b in (w.btn_oper,w.btn_sim,w.sim_start,w.operation_btn):
                    self.assertIn("#208447",b.styleSheet())
                self.assertTrue(w.operation_btn.isEnabled())
                w.core.status["rtc_valid"]=False; w.update_all_status()
                self.assertIn("#101010",w.operation_btn.styleSheet())
            finally: w.close()

if __name__=="__main__": unittest.main()
