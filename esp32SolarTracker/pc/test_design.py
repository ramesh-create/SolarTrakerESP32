"""Version 0.5.1: Design-1-Anbindung und Freigaben ohne echte Motorbewegung."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from PySide6.QtWidgets import QApplication, QPushButton
from verbindung import Verbindung
from test_pc import SpeicherPort, status
from steuerzentrale import Steuerzentrale, grenztest_fehler, STANDARD
from bedienfeld_qt import Bedienpanel


def vorbereiten(c):
    c.link=Verbindung(SpeicherPort())
    c.link.bereit=c.link.hallo=True
    c.empfangen(status())
    c.grenzen_bestaetigt=c.ausrichtung_bestaetigt=True


class SteuerungsTests(unittest.TestCase):
    def setUp(self):
        self.log=[]
        self.c=Steuerzentrale(self.log.append)
        vorbereiten(self.c)

    def test_grenztest_nach_erfolg_zugelassen(self):
        self.c.status["axes"][0]["limits_ok"]=False
        self.assertEqual(grenztest_fehler(self.c.status,0),[])
        self.c.grenztest(0)
        self.assertIn(b" LIMIT AZ",self.c.link.port.gesendet[-1])

    def test_fehlende_referenz_praezise(self):
        self.c.status["axes"][1]["limits_ok"]=False
        self.c.status["axes"][1]["referenced"]=False
        with self.assertRaisesRegex(ValueError,"Elevation.*Referenz fehlt"):
            self.c.grenztest(1)
        self.assertTrue(self.c.status["axes"][1]["calibrated"])

    def test_aktiver_kontakt_praezise(self):
        self.c.status["axes"][0]["limits_ok"]=False
        self.c.status["axes"][0]["max"]=True
        with self.assertRaisesRegex(ValueError,"Azimut MAX.*GEDRUECKT"):
            self.c.grenztest(0)

    def test_zehn_grad_manuell(self):
        self.c.manuell(0,10)
        self.assertIn(b" MOVE AZ 20.01953",self.c.link.port.gesendet[-1])

    def test_unreferenziert_nur_begrenzter_test(self):
        self.c.status["axes"][0]["referenced"]=False
        with self.assertRaises(ValueError): self.c.manuell(0,10)
        self.c.manuell(0,5,test=True)
        self.assertIn(b" JOG AZ 5",self.c.link.port.gesendet[-1])

    def test_keine_doppelte_fahrt(self):
        for a in self.c.status["axes"]: a.update(calibrated=False,referenced=False,span=0,limits_ok=False)
        self.c.endschaltertest()
        with self.assertRaises(ValueError): self.c.endschaltertest()
        self.assertEqual(sum(b" SWTEST" in x for x in self.c.link.port.gesendet),1)

    def test_ack_ist_nicht_fahrtende(self):
        for a in self.c.status["axes"]: a.update(calibrated=False,referenced=False,span=0,limits_ok=False)
        self.c.endschaltertest(); nummer=self.c.pending
        self.c.empfangen(dict(type="ack",id=nummer,ok=True))
        n=status(); n["switch_testing"]=True; n["switch_test"]=2
        n["axes"][1]["state"]=2
        self.c.empfangen(n)
        self.assertEqual(self.c.pending,nummer)
        self.c.empfangen(status())
        self.assertIsNone(self.c.pending)

    def test_stopp_verhindert_anschlussbefehl_mit_altem_status(self):
        self.c.status["axes"][0]["limits_ok"]=False
        self.c.stopp()
        with self.assertRaises(ValueError): self.c.grenztest(0)

    def test_ablehnung_erhaelt_status_diagnose(self):
        self.c.status["axes"][0]["limits_ok"]=False
        self.c.grenztest(0); nummer=self.c.pending
        self.c.empfangen(dict(type="ack",id=nummer,ok=False,message="Kontakt aktiv"))
        self.assertIsNone(self.c.pending)
        self.assertIn("Endlagen=gespeichert","\n".join(self.log))
        self.assertIn(b" STATUS",self.c.link.port.gesendet[-1])

    def test_simulation_bleibt_gesperrt(self):
        self.c.status["axes"][1]["limits_ok"]=False
        with self.assertRaisesRegex(ValueError,"Grenztest Elevation"):
            self.c.starten("Simulation")
        self.assertEqual(self.c.modus,"Pause")

    def test_simulationszeit_wartet(self):
        self.c.starten("Simulation",60)
        self.c.senden("AUTO","AZ",60,bewegung=True)  # Auftrag noch nicht abgeschlossen
        self.c.modus="Simulation"
        start=self.c.simzeit
        self.c.letzter_tick-=1
        self.c.poll()
        self.assertEqual(start,self.c.simzeit)

    def test_speichern_und_laden(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"werte.json"
            self.c.speichern(p,{**STANDARD,"breite":49.2})
            c=Steuerzentrale(); c.laden(p)
            self.assertEqual(c.werte["breite"],49.2)

    def test_referenz_ok_verhindert_erneutes_ref(self):
        vorher=len(self.c.link.port.gesendet)
        with self.assertRaisesRegex(ValueError,"Referenz bereits OK"):
            self.c.referenz(0)
        self.assertEqual(len(self.c.link.port.gesendet),vorher)
        self.assertTrue(self.c.status["axes"][0]["limits_ok"])

    def test_verlorene_referenz_wiederherstellbar(self):
        self.c.status["axes"][0]["referenced"]=False
        self.c.referenz(0)
        self.assertIn(b" REF AZ",self.c.link.port.gesendet[-1])

    def test_lcd_ohne_firmwarefunktion_keine_uebertragung(self):
        with self.assertRaisesRegex(ValueError,"Firmware 0.3.2"):
            self.c.lcd_senden("SolarTracker","LCD Test OK")
        self.assertFalse(any(b" LCD " in b for b in self.c.link.port.gesendet))

    def test_lcd_hex_und_bestaetigung(self):
        self.c.status["lcd_supported"]=True
        self.c.lcd_senden("SolarTracker","LCD Test OK")
        cmd=self.c.link.port.gesendet[-1].decode().split()
        self.assertEqual(cmd[1],"LCD")
        self.assertEqual(bytes.fromhex(cmd[2]),b"SolarTracker    ")
        self.assertEqual(bytes.fromhex(cmd[3]),b"LCD Test OK     ")
        self.assertNotIn("Bitte sichtbare",self.c.lcd_meldung)
        self.c.empfangen(dict(type="ack",id=self.c.pending,ok=True))
        self.assertIn("Bitte sichtbare",self.c.lcd_meldung)

    def test_lcd_beim_fahren_gesperrt(self):
        self.c.status["lcd_supported"]=True
        self.c.status["axes"][0]["state"]=1
        with self.assertRaises(ValueError): self.c.lcd_senden("a","b")

    def test_lcd_ungueltige_zeichen_keine_befehlsinjektion(self):
        self.c.status["lcd_supported"]=True
        for text in ("a\nSWTEST", "x"*17, "\u2600"):
            with self.assertRaises(ValueError): self.c.lcd_senden(text,"")
        self.assertFalse(any(b" LCD " in b for b in self.c.link.port.gesendet))

    def test_lcd_ablehnung_keine_erfolgsmeldung(self):
        self.c.status["lcd_supported"]=True
        self.c.lcd_senden("a","b")
        self.c.empfangen(dict(type="ack",id=self.c.pending,ok=False,message="LCD 0x27 nicht erreichbar"))
        self.assertIn("nicht erreichbar",self.c.lcd_meldung)
        self.assertNotIn("Text zum LCD gesendet",self.c.lcd_meldung)

    def test_grenztestabschluss_wird_gemeldet(self):
        self.c.status["axes"][0]["limits_ok"]=False
        self.c.empfangen(status())
        self.assertTrue(any("Grenztest Azimut erfolgreich" in z for z in self.log))

    def test_kalibrierabschluss_wird_gemeldet(self):
        self.c.status["switch_testing"]=True
        self.c.empfangen(status())
        self.assertTrue(any("Endschaltertest abgeschlossen" in z for z in self.log))

    def test_trennen_loescht_unbestaetigte_position(self):
        self.c.trennen()
        self.assertIsNone(self.c.status)
        self.assertFalse(self.c.bereit)


class DesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.win=Bedienpanel(datenordner=Path(self.tmp.name))
        self.win.timer.stop()

    def tearDown(self):
        self.win.close()
        self.tmp.cleanup()

    def test_vorlagenlayout_ohne_demowerte(self):
        self.assertEqual(self.win.pages.count(),4)
        self.assertEqual(self.win.test_stack.count(),7)
        self.assertIsNone(self.win.az_gauge.value)
        self.assertIsNone(self.win.core.link)

    def test_unbekannte_position_bleibt_unbekannt(self):
        vorbereiten(self.win.core)
        self.win.core.status["axes"][0]["referenced"]=False
        self.win.update_all_status()
        self.assertIsNone(self.win.az_gauge.value)
        self.assertIn("Referenz=fehlt",self.win.pruef_details.text())

    def test_echte_position_statt_demowert(self):
        vorbereiten(self.win.core)
        self.win.core.status["axes"][0]["position"]=1024
        self.win.update_all_status()
        self.assertAlmostEqual(self.win.az_gauge.value,self.win.core.werte["az_null"]+(1024-114)*360/4096)

    def test_alle_seiten_rendern(self):
        self.win.show()
        for i in range(4):
            self.win.pages.setCurrentIndex(i)
            for j in range(7) if i==3 else (0,):
                self.win.test_stack.setCurrentIndex(j)
                self.app.processEvents()
                self.assertFalse(self.win.grab().isNull())

    def test_referenz_und_grenztest_tasten(self):
        vorbereiten(self.win.core)
        self.win.update_all_status()
        self.assertFalse(self.win.ref_buttons[0].isEnabled())
        self.assertIn("bestanden",self.win.grenz_buttons[0].text())
        self.win.core.status["axes"][0]["referenced"]=False
        self.win.core.status["axes"][0]["limits_ok"]=False
        self.win.update_all_status()
        self.assertTrue(self.win.ref_buttons[0].isEnabled())
        self.assertFalse(self.win.grenz_buttons[0].isEnabled())

    def test_anzeige_startposition_osten(self):
        vorbereiten(self.win.core)
        self.win.core.werte.update(az_null=90,el_neigung=90)
        self.win.update_all_status()
        self.assertEqual(self.win.az_gauge.value,90)
        self.assertEqual(self.win.el_gauge.value,90)

    def test_grafik_nur_sonnenstunden(self):
        from datetime import datetime, timezone, timedelta
        tag=datetime(2026,9,16,12,tzinfo=timezone(timedelta(hours=2)))
        self.win.chart.berechnen(tag,self.win.core.werte)
        self.assertGreater(self.win.chart.beginn,0)
        self.assertLess(self.win.chart.ende,24)
        self.assertEqual(len(self.win.chart.punkte),145)
        self.assertTrue(all(self.win.chart.beginn <= p[0] <= self.win.chart.ende for p in self.win.chart.punkte))

    def test_lcd_taste_sendet_hardwarebefehl(self):
        vorbereiten(self.win.core)
        self.win.core.status["lcd_supported"]=True
        self.win.update_all_status()
        self.win.lcd_send_btn.click()
        self.assertIn(b" LCD ",self.win.core.link.port.gesendet[-1])

    def test_beide_motortests_senden_richtige_achse(self):
        vorbereiten(self.win.core)
        for i,name in enumerate(("AZ","EL")):
            self.win.core.pending=None
            self.win.core.status["axes"][i]["position"]=800
            self.win.update_all_status()
            minus,plus,_=self.win.motor_controls[i]
            plus.click()
            self.assertIn(f" JOG {name} 5.00000".encode(),self.win.core.link.port.gesendet[-1])
            self.win.core.pending=None
            self.win.update_all_status()
            minus.click()
            self.assertIn(f" JOG {name} -5.00000".encode(),self.win.core.link.port.gesendet[-1])

    def test_motortest_min_nur_wegfahren(self):
        vorbereiten(self.win.core)
        self.win.update_all_status()
        minus,plus,hinweis=self.win.motor_controls[0]
        self.assertFalse(minus.isEnabled())
        self.assertTrue(plus.isEnabled())
        self.assertIn("Fahrgrenze",minus.toolTip())

    def test_komponententest_navigation_zur_originalauswahl(self):
        self.win.show(); self.win.btn_test.click(); self.app.processEvents()
        selector=self.win.test_stack.widget(0)
        erwartet=["Azimut-Motor","Elevations-Motor","Endschalter","RTC DS3231","LCD 16x2","Bedientasten"]
        buttons=selector.findChildren(QPushButton)
        self.assertEqual([b.text() for b in buttons],erwartet)
        for index,btn in enumerate(buttons,1):
            btn.click(); self.app.processEvents()
            self.assertEqual(self.win.test_stack.currentIndex(),index)
            self.assertTrue(self.win.test_zurueck.isVisible())
            self.win.test_zurueck.click()
            self.assertEqual(self.win.test_stack.currentIndex(),0)
        self.win.test_stack.setCurrentIndex(5)
        self.win.btn_sim.click(); self.win.btn_test.click()
        self.assertEqual(self.win.test_stack.currentIndex(),0)

    def test_zurueck_bleibt_beim_scrollen_erreichbar(self):
        self.win.resize(1150,720); self.win.show(); self.win.btn_test.click()
        self.win.test_stack.setCurrentIndex(3); self.app.processEvents()
        scroll=self.win.test_stack.currentWidget()
        scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
        self.app.processEvents()
        self.assertTrue(self.win.test_zurueck.isVisible())
        self.win.test_zurueck.click(); self.app.processEvents()
        auswahl=self.win.test_stack.currentWidget()
        self.assertEqual(auswahl.verticalScrollBar().value(),0)
        self.assertEqual(auswahl.horizontalScrollBar().maximum(),0)
        self.assertEqual(auswahl.verticalScrollBar().maximum(),0)

    def test_bedientasten_fahren_beide_achsen(self):
        vorbereiten(self.win.core)
        for a in self.win.core.status["axes"]: a["position"]=800
        for taste,cmd in (("LINKS",b" JOG AZ -5.00000"),("RECHTS",b" JOG AZ 5.00000"),("OBEN",b" JOG EL 5.00000"),("UNTEN",b" JOG EL -5.00000")):
            self.win.core.pending=None; self.win.update_all_status()
            self.win.test_tasten[taste].click()
            self.assertIn(cmd,self.win.core.link.port.gesendet[-1])
            self.assertIn("angefordert",self.win.button_test_value.text())

    def test_bedientasten_stop_auch_bei_laufender_fahrt(self):
        vorbereiten(self.win.core)
        self.win.core.status["axes"][0]["state"]=1
        self.win.update_all_status()
        self.assertFalse(self.win.test_tasten["RECHTS"].isEnabled())
        self.win.test_tasten["ENTER"].click()
        self.assertIn(b" STOP",self.win.core.link.port.gesendet[-1])
        self.win.stop_btn.click()
        self.assertIn(b" STOP",self.win.core.link.port.gesendet[-1])

    def test_bedientasten_offline_und_grenzen(self):
        self.assertFalse(self.win.test_tasten["OBEN"].isEnabled())
        vorbereiten(self.win.core); self.win.update_all_status()
        self.assertFalse(self.win.test_tasten["LINKS"].isEnabled())
        self.assertTrue(self.win.test_tasten["RECHTS"].isEnabled())
        self.assertFalse(self.win.test_tasten["UNTEN"].isEnabled())
        self.assertTrue(self.win.test_tasten["OBEN"].isEnabled())

    def test_stopp_und_protokoll_links_unter_komponententest(self):
        self.win.resize(1150,720); self.win.show(); self.win.btn_test.click()
        self.win.test_stack.setCurrentIndex(6); self.app.processEvents()
        self.assertTrue(self.win.stop_btn.isVisible())
        self.assertTrue(self.win.log.isVisible())
        self.assertEqual(self.win.stop_btn.parentWidget(),self.win.log.parentWidget())
        self.assertLess(self.win.stop_btn.geometry().bottom(),self.win.log.geometry().top())
        self.assertEqual(self.win.stop_btn.parentWidget(),self.win.btn_test.parentWidget())
        self.assertLess(self.win.btn_test.geometry().bottom(),self.win.stop_btn.geometry().top())
        self.assertEqual(self.win.stop_btn.parentWidget(),self.win.centralWidget().layout().itemAt(0).widget())

    def test_lcd_keine_falsche_hardwaremeldung(self):
        self.win.lcd_preview_only()
        self.assertIsNone(self.win.core.link)
        self.assertIn("keine",self.win.meldungen[-1])

    def test_haltemodus_loslassen_stoppt(self):
        vorbereiten(self.win.core)
        self.win.radio_hold.setChecked(True)
        self.win.begin_hold("az",1)
        self.win.tick()
        self.win.stop_hold()
        self.assertIn(b" STOP",self.win.core.link.port.gesendet[-1])
        self.assertIsNone(self.win.hold_axis)

    def test_motortest_stopp_taste(self):
        vorbereiten(self.win.core)
        page=self.win.test_stack.widget(1)
        stop=next(b for b in page.findChildren(QPushButton) if b.text()=="STOP")
        stop.click()
        self.assertIn(b" STOP",self.win.core.link.port.gesendet[-1])


    def test_ort_wird_gesendet(self):
        vorbereiten(self.win.core)
        c=self.win.core
        c.werte["land"]="Deutschland"; c.werte["stadt"]="Bad Vilbel"
        c.status["ort_supported"]=True
        c.konfiguration_senden()
        befehle=[b.decode() for b in c.link.port.gesendet]
        self.assertTrue(any(" ORT " in b for b in befehle))
        self.assertTrue(any("CONF 50.187 8.739" in b for b in befehle))

    def test_ort_ohne_firmware_kein_befehl(self):
        vorbereiten(self.win.core)
        c=self.win.core
        c.werte["stadt"]="Bad Vilbel"
        c.status.pop("ort_supported",None)
        anfang=len(c.link.port.gesendet)
        c.konfiguration_senden()
        self.assertFalse(any(b" ORT " in b for b in c.link.port.gesendet[anfang:]))

    def test_ort_gespeichert_und_geladen(self):
        c=self.win.core
        import tempfile
        from pathlib import Path
        p=Path(tempfile.mkdtemp())/"e.json"
        c.speichern(p,{**c.werte,"land":"Deutschland","stadt":"Bad Vilbel"})
        c2=Steuerzentrale(); c2.laden(p)
        self.assertEqual(c2.werte["land"],"Deutschland")
        self.assertEqual(c2.werte["stadt"],"Bad Vilbel")


class WeltkartenTests(unittest.TestCase):
    def test_equator_nullpunkt(self):
        from weltkarte import kartenpunkt
        fx,fy=kartenpunkt(0,0)
        self.assertAlmostEqual(fx,0.5); self.assertAlmostEqual(fy,0.5)

    def test_ecken(self):
        from weltkarte import kartenpunkt
        self.assertAlmostEqual(kartenpunkt(90,-180)[0],0.0); self.assertAlmostEqual(kartenpunkt(90,-180)[1],0.0)
        self.assertAlmostEqual(kartenpunkt(-90,180)[0],1.0); self.assertAlmostEqual(kartenpunkt(-90,180)[1],1.0)

    def test_standort_bad_vilbel(self):
        from weltkarte import kartenpunkt
        fx,fy=kartenpunkt(50.187,8.739)
        self.assertTrue(0.5<fx<0.55)
        self.assertTrue(0.2<fy<0.25)

    def test_umkehrprojektion(self):
        from weltkarte import ort_aus_bildanteil
        self.assertAlmostEqual(ort_aus_bildanteil(0.5,0.5)[0],0.0)
        self.assertAlmostEqual(ort_aus_bildanteil(0.5,0.5)[1],0.0)
        self.assertAlmostEqual(ort_aus_bildanteil(0.0,0.0)[0],90.0)
        self.assertAlmostEqual(ort_aus_bildanteil(0.0,0.0)[1],-180.0)
        self.assertAlmostEqual(ort_aus_bildanteil(1.0,1.0)[0],-90.0)
        self.assertAlmostEqual(ort_aus_bildanteil(1.0,1.0)[1],180.0)

    def test_rundlauf_projektion(self):
        from weltkarte import kartenpunkt, ort_aus_bildanteil
        for breite,laenge in ((50.187,8.739),(0.0,0.0),(-33.9,151.2),(47.5,-122.3)):
            b,l=ort_aus_bildanteil(*kartenpunkt(breite,laenge))
            self.assertAlmostEqual(b,breite,places=6)
            self.assertAlmostEqual(l,laenge,places=6)


if __name__=="__main__": unittest.main()
