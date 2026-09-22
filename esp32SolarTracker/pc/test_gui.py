"""Version 0.1.0: GUI-Pruefung ohne serielle Hardware oder Motorbewegung."""
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from bedienfeld import Bedienfeld
from test_pc import status, SpeicherPort
from verbindung import Verbindung


class FensterTests(unittest.TestCase):
    def setUp(self):
        self.app = Bedienfeld()
        self.app.withdraw()

    def tearDown(self):
        self.app.beenden()

    def freigeben(self):
        self.app.link = Verbindung(SpeicherPort())
        self.app.link.bereit = True
        self.app.empfangen(status())
        self.app.ausrichtung.set(True)
        self.app.grenzen_gesehen.set(True)

    def test_simulation_und_grafik(self):
        app = self.app
        self.freigeben()
        with patch.object(app, "sim_startzeit", return_value=datetime(2026,6,21,12,tzinfo=timezone.utc)):
            app.starten("Simulation")
        self.assertEqual(app.modus, "Simulation")
        start = app.simzeit
        app.tickzeit -= 1
        app.tick()
        self.assertGreater(app.simzeit, start)
        self.assertEqual(len(app.kurve), 145)
        self.assertGreater(len(app.canvas.find_all()), 200)
        self.assertIsNotNone(app.link)

    def test_echte_fahrt_ohne_verbindung_gesperrt(self):
        with patch("bedienfeld.messagebox.showerror") as fehler:
            self.app.starten("Normalbetrieb")
            fehler.assert_called_once()
        self.assertEqual(self.app.modus, "Pause")

    def test_einstellungswechsel_stoppt(self):
        self.freigeben()
        self.app.starten("Simulation")
        self.app.ausrichtung.set(True)
        self.app.werte["az_null"].set("15")
        self.assertEqual(self.app.modus, "Pause")
        self.assertFalse(self.app.ausrichtung.get())

    def test_entlastung_nicht_vom_pc_abbrechen(self):
        port = SpeicherPort()
        self.app.link = Verbindung(port)
        self.app.modus = "Normalbetrieb"
        self.app.empfangen(dict(type="event", message="Endschalter: Entlastung"))
        self.assertEqual(self.app.modus, "Pause")
        self.assertEqual(port.gesendet, [])

    def test_status_und_bestaetigung(self):
        self.app.link = Verbindung(SpeicherPort())
        self.app.link.bereit = True
        self.app.auftrag = 7
        self.app.empfangen(dict(type="ack", id=7, ok=True))
        self.app.empfangen(status())
        self.assertIsNone(self.app.auftrag)
        self.assertIn("10.0", self.app.achslabels[0].get())

    def test_simulation_ohne_pruefungen_gesperrt(self):
        self.freigeben()
        for feld in ("calibrated", "referenced", "limits_ok"):
            for i in range(2):
                with self.subTest(feld=feld, achse=i):
                    self.app.achsen[i][feld] = False
                    with patch("bedienfeld.messagebox.showerror") as fehler:
                        self.app.starten("Simulation")
                        fehler.assert_called_once()
                    self.assertEqual(self.app.modus, "Pause")
                    self.app.achsen[i][feld] = True
        for anzahl in range(4):
            self.app.pruefstatus["switch_test"] = anzahl
            self.assertIsNotNone(self.app.freigabe_fehler())
        self.app.pruefstatus["switch_test"] = 4
        self.app.grenzen_gesehen.set(False)
        self.assertIsNotNone(self.app.freigabe_fehler())
        self.assertFalse(any(b" AUTO " in cmd for cmd in self.app.link.port.gesendet))

    def test_rtc_erhaelt_nur_echte_zeit(self):
        with patch("bedienfeld.time.time", return_value=1800000000):
            self.freigeben()
            self.app.empfangen(status())
        zeiten = [cmd for cmd in self.app.link.port.gesendet if b" TIME " in cmd]
        self.assertEqual(len(zeiten), 1)
        self.assertIn(b"TIME 1800000000", zeiten[0])

    def test_simulation_sendet_auto(self):
        self.freigeben()
        self.app.modus = "Simulation"
        self.app.nachfuehren(45,45,dict(az_null=0,el_null=0))
        self.assertIn(b"AUTO AZ 45", self.app.link.port.gesendet[-1])

    def test_beide_achsen_werden_bedient(self):
        self.freigeben()
        self.app.nachfuehren(45,45,dict(az_null=0,el_null=0))
        self.app.auftrag = None
        self.app.nachfuehren(46,45,dict(az_null=0,el_null=0))
        self.assertIn(b"AUTO EL 45",self.app.link.port.gesendet[-1])

    def test_automatischer_endtest_ein_knopf(self):
        self.freigeben()
        self.app.schalterpruefung()
        self.assertIn(b" SWTEST", self.app.link.port.gesendet[-1])
        self.assertIsNotNone(self.app.auftrag)
        self.assertFalse(self.app.grenzen_gesehen.get())
        vorher = len(self.app.link.port.gesendet)
        with patch("bedienfeld.messagebox.showerror"):
            self.app.schalterpruefung()
        self.assertEqual(len(self.app.link.port.gesendet),vorher)

    def test_automatischer_endtest_status(self):
        self.freigeben()
        self.app.auftrag = 9
        self.app.bestaetigt = True
        n = status()
        n["switch_test"] = 2
        n["switch_testing"] = True
        n["axes"][1]["state"] = 2
        self.app.empfangen(n)
        self.assertIn("Elevation",self.app.freigabe_fehler())
        self.assertEqual(self.app.auftrag,9)
        self.app.empfangen(status())
        self.assertIsNone(self.app.auftrag)

    def test_fehler_zeigt_achse_und_kontakte(self):
        self.freigeben()
        self.app.empfangen(dict(type="fault", axis="az", phase=3, direction=1,
                                steps=10, position=10, min=True, max=False,
                                message="Gegenkontakt unerwartet geschlossen"))
        text = self.app.meldung.get()
        self.assertIn("Azimut",text)
        self.assertIn("Entlaste MIN",text)
        self.assertIn("MIN=True",text)
        self.assertIn("Schritte 10",text)
        self.assertEqual(self.app.modus,"Pause")

    def test_pc_startzeit(self):
        zeit = self.app.sim_startzeit()
        self.assertLess(abs(zeit.timestamp()-datetime.now().timestamp()),2)

    def test_fahrt_haelt_simulationsuhr_an(self):
        self.freigeben()
        self.app.modus = "Simulation"
        start = self.app.simzeit
        self.app.auftrag = 100
        self.app.tickzeit -= 1
        self.app.tick()
        self.assertEqual(start,self.app.simzeit)


if __name__ == "__main__":
    unittest.main()
