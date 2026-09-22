"""Version 0.6.0: STOP, Freigaben und Simulation ohne wiederholte Kalibrierung."""
import copy
from datetime import timedelta
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from steuerzentrale import Steuerzentrale
from verbindung import Verbindung
from test_pc import status, SpeicherPort


def gespeicherter_status():
    n=status()
    n.update(version="0.4.0",device_id="testgeraet",position_storage=True,storage_ok=True)
    for a in n["axes"]: a.update(calibration_id=7,position=600)
    return n


def verbinden(c,n=None):
    c.link=Verbindung(SpeicherPort()); c.link.bereit=c.link.hallo=True
    c.rtc_sync=True; c.empfangen(n or gespeicherter_status())


class PersistenzTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.pfad=Path(self.tmp.name)/"betrieb.json"
        self.c=Steuerzentrale(speicherpfad=self.pfad); verbinden(self.c)
        self.c.bestaetige_ausrichtung(True); self.c.bestaetige_grenzen(True)

    def tearDown(self): self.tmp.cleanup()

    def neu(self,n=None):
        c=Steuerzentrale(speicherpfad=self.pfad)
        c.laden(Path(self.tmp.name)/"einstellungen.json")
        verbinden(c,n)
        return c

    def test_freigaben_nach_neuem_fenster(self):
        c=self.neu()
        self.assertTrue(c.grenzen_bestaetigt)
        self.assertTrue(c.ausrichtung_bestaetigt)
        self.assertEqual(c.freigabe(),[])

    def test_anderes_geraet_braucht_eigene_bestaetigung(self):
        n=gespeicherter_status(); n["device_id"]="anderesgeraet"
        self.assertFalse(self.neu(n).grenzen_bestaetigt)

    def test_neue_kalibrierung_invalidiert_alte_sichtpruefung(self):
        n=gespeicherter_status(); n["axes"][0]["calibration_id"]+=1
        self.assertFalse(self.neu(n).grenzen_bestaetigt)

    def test_geaenderte_ausrichtung_braucht_bestaetigung(self):
        p=Path(self.tmp.name)/"einstellungen.json"
        self.c.speichern(p,{**self.c.werte,"az_null":100})
        self.assertFalse(self.neu().ausrichtung_bestaetigt)

    def test_stop_erhaelt_status_und_grenzen(self):
        self.c.status["axes"][0]["state"]=1
        self.c.stopp(); nummer=self.c.pending
        self.c.empfangen(dict(type="ack",id=nummer,ok=True))
        self.c.empfangen(gespeicherter_status())
        self.assertTrue(self.c.grenzen_bestaetigt)
        self.assertTrue(self.c.status["axes"][0]["referenced"])
        self.assertEqual(self.c.status["axes"][0]["position"],600)
        self.assertFalse(self.c.beschaeftigt)

    def test_keine_erneute_kalibrierung_oder_grenztests(self):
        self.c.endschaltertest(); self.c.grenztest(0); self.c.grenztest(1)
        self.assertEqual(self.c.link.port.gesendet,[])

    def test_fehlende_kalibrierung_startet_pruefung(self):
        self.c.status["axes"][1].update(calibrated=False,span=0,referenced=False,limits_ok=False)
        self.c.endschaltertest()
        self.assertIn(b" SWTEST",self.c.link.port.gesendet[-1])

    def test_referenzfahrt_nur_wenn_position_fehlt(self):
        self.c.referenzfahrt(0)
        self.assertEqual(self.c.link.port.gesendet,[])
        self.c.status["axes"][0]["referenced"]=False
        self.c.referenzfahrt(0)
        self.assertIn(b" HOME AZ",self.c.link.port.gesendet[-1])
        self.assertTrue(self.c.status["axes"][0]["limits_ok"])

    def test_simulation_stop_und_fortsetzen_ohne_startfahrt(self):
        self.c.starten("Simulation")
        self.c.ablauf="Sonnenlauf"; self.c.simzeit+=timedelta(hours=2)
        zeit=self.c.simzeit
        self.c.stopp(); self.c.empfangen(dict(type="ack",id=self.c.pending,ok=True)); self.c.empfangen(gespeicherter_status())
        self.c.starten("Simulation")
        self.assertEqual(self.c.simzeit,zeit)
        self.assertEqual(self.c.ablauf,"Sonnenlauf")

    def test_simulation_nach_pc_neustart_fortsetzen(self):
        self.c.starten("Simulation"); self.c.ablauf="Rueckfahrt"; self.c.simzeit=self.c.simende
        self.c.stopp()
        c=self.neu(); c.starten("Simulation")
        self.assertEqual(c.ablauf,"Rueckfahrt")
        self.assertEqual(c.simzeit,self.c.simende)

    def test_bewusster_neuer_sonnentag(self):
        self.c.starten("Simulation"); self.c.ablauf="Sonnenlauf"; self.c.simzeit+=timedelta(hours=2)
        self.c.stopp()
        c=self.neu(); c.starten("Simulation",neu=True)
        self.assertEqual(c.ablauf,"Startposition anfahren")
        self.assertEqual(c.simzeit,c.simstart)

    def test_speicherfehler_verhindert_auto(self):
        self.c.status["storage_ok"]=False
        with self.assertRaisesRegex(ValueError,"Positionsspeicher"):
            self.c.starten("Normalbetrieb")

    def test_defekte_pc_datei_keine_erfundene_freigabe(self):
        self.pfad.write_text("{kaputt",encoding="utf-8")
        c=self.neu()
        self.assertFalse(c.grenzen_bestaetigt)
        self.assertFalse(c.ausrichtung_bestaetigt)


if __name__=="__main__": unittest.main()
