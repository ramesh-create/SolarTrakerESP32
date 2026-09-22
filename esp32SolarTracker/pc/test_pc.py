"""Version 0.1.0: prueft Sonnenstand, Grenzen und Verbindungsfehler ohne Motoren."""
from datetime import datetime, timezone, timedelta
import json
import unittest
from sonne import sonnenstand, motorziel
from verbindung import Verbindung, status_pruefen


def status():
    achse = dict(position=114, span=2048, margin=114, calibrated=True, limits_ok=True,
                 referenced=True, state=0, min=False, max=False)
    return dict(type="status", protocol=3, version="0.3.0", switch_test=4, switch_testing=False,
                rtc_present=True, rtc_valid=True, rtc_epoch=1789473600, axes=[achse.copy(), achse.copy()])


class SpeicherPort:
    def __init__(self):
        self.daten = bytearray()
        self.gesendet = []
        self.geschlossen = False

    @property
    def in_waiting(self):
        return len(self.daten)

    def read(self, anzahl):
        daten = self.daten[:anzahl]
        del self.daten[:anzahl]
        return daten

    def write(self, daten):
        self.gesendet.append(daten)
        return len(daten)

    def close(self):
        self.geschlossen = True

    def antwort(self, nachricht):
        self.daten.extend(json.dumps(nachricht).encode() + b"\n")


class SonnenTests(unittest.TestCase):
    def test_mittag_sommer_frankfurt(self):
        az, el = sonnenstand(datetime(2026,6,21,12,tzinfo=timezone.utc), 50.187,8.739)
        self.assertTrue(190 < az < 205)
        self.assertTrue(61 < el < 64)

    def test_nacht(self):
        _, el = sonnenstand(datetime(2026,12,21,0,tzinfo=timezone.utc), 50.187,8.739)
        self.assertLess(el, -50)

    def test_zeitzone(self):
        zeit = datetime(2026,6,21,12,tzinfo=timezone.utc)
        a = sonnenstand(zeit,50,9)
        b = sonnenstand(zeit.astimezone(timezone(timedelta(hours=2))),50,9)
        for x,y in zip(a,b):
            self.assertAlmostEqual(x,y,delta=0.03)

    def test_ungueltige_werte(self):
        for breite in (91,float("nan")):
            with self.assertRaises(ValueError):
                sonnenstand(datetime.now(timezone.utc),breite,0)
        with self.assertRaises(ValueError):
            sonnenstand(datetime.now(),0,0)

    def test_grenzen_und_norddurchgang(self):
        achse = status()["axes"][0]
        self.assertEqual(motorziel(10,350,achse,True),20)
        for ziel in (0,10,175,180,360):
            with self.assertRaises(ValueError):
                motorziel(ziel,0,achse)
        self.assertEqual(motorziel(90,0,achse),90)
        achse["referenced"] = False
        with self.assertRaises(ValueError):
            motorziel(90,0,achse)


class ProtokollTests(unittest.TestCase):
    def setUp(self):
        self.zeit = 0.0
        self.port = SpeicherPort()
        self.link = Verbindung(self.port,lambda: self.zeit)

    def test_handshake_und_fragmentierung(self):
        nummer = self.link.senden("HELLO", 3)
        self.port.daten.extend(b"ESP-ROM Boot\n{\"type\":\"ack\",")
        self.link.lesen()
        self.assertFalse(self.link.bereit)
        self.port.daten.extend(f'"id":{nummer},"ok":true}}\n'.encode())
        self.port.antwort(status())
        self.link.lesen()
        self.assertTrue(self.link.bereit)
        self.assertNotIn(nummer,self.link.offen)

    def test_status_allein_reicht_nicht(self):
        self.port.antwort(status())
        self.link.lesen()
        self.assertFalse(self.link.bereit)

    def test_falsche_firmware(self):
        daten = status()
        daten["protocol"] = 99
        self.port.antwort(daten)
        with self.assertRaises(ValueError):
            self.link.lesen()

    def test_fehlende_bestaetigung_trotz_status(self):
        self.link.senden("MOVE","AZ",30)
        self.zeit = 3
        self.port.antwort(status())
        with self.assertRaises(ConnectionError):
            self.link.lesen()

    def test_verbindungsabbruch(self):
        self.zeit = 3
        with self.assertRaises(ConnectionError):
            self.link.lesen()

    def test_schliessen_stoppt(self):
        self.link.schliessen()
        self.assertIn(b"STOP",self.port.gesendet[-1])
        self.assertTrue(self.port.geschlossen)

    def test_beschaedigte_grenzen(self):
        daten = status()
        daten["axes"][0]["margin"] = 0
        with self.assertRaises(ValueError):
            status_pruefen(daten)


if __name__ == "__main__":
    unittest.main()
