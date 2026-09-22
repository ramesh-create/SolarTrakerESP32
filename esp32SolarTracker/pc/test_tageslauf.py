"""Version 0.5.1: Tageslauf und sichere Rueckfahrt ohne echte Motoren."""
from datetime import datetime, timedelta, timezone
import tempfile
from pathlib import Path
import json
import unittest
from unittest.mock import patch
from tageslauf import sonnenfenster, tagesziel, elevationsziel, panelneigung
from sonne import sonnenstand
from steuerzentrale import Steuerzentrale
from test_design import vorbereiten

TAG = datetime(2026,9,16,12,tzinfo=timezone(timedelta(hours=2)))


class TageslaufTests(unittest.TestCase):
    def setUp(self):
        self.zeit=100.0
        self.log=[]
        self.c=Steuerzentrale(self.log.append,lambda:self.zeit)
        vorbereiten(self.c)
        self.c.link.uhr=lambda:self.zeit
        self.c.link.letzte_antwort=self.zeit
        self.c.link.offen.clear()
        self.c.werte.update(az_null=90,el_neigung=90)
        self.c.status["axes"][0]["span"]=2282
        self.c.status["axes"][1]["span"]=1248

    def tick(self, sek=0.5):
        self.zeit+=sek
        if self.c.pending:
            cmd=next(b.decode().split()[1:] for b in self.c.link.port.gesendet if b.startswith(f"{self.c.pending} ".encode()))
            if cmd[0]=="AUTO":
                self.c.status["axes"][0 if cmd[1]=="AZ" else 1]["state"]=1
        self.c.link.port.antwort(dict(type="status",**{k:v for k,v in self.c.status.items() if k!="type"}))
        for nummer in list(self.c.link.offen):
            self.c.link.port.antwort(dict(type="ack",id=nummer,ok=True))
        self.c.poll()

    def fertig(self):
        cmd=next(b.decode().split()[1:] for b in self.c.link.port.gesendet if b.startswith(f"{self.c.pending} ".encode()))
        i=0 if cmd[1]=="AZ" else 1
        self.c.status["axes"][i]["position"]=round(float(cmd[2])*4096/360)
        self.c.status["axes"][i]["state"]=0
        self.c.empfangen(dict(type="ack",id=self.c.pending,ok=True))
        self.c.empfangen(self.c.status)

    def starten(self):
        with patch("steuerzentrale.datetime") as datum:
            datum.now.return_value=TAG
            self.c.starten("Simulation",3600)

    def test_simulation_nachts_folgetag(self):
        from tageslauf import aktuelles_sonnenfenster
        nacht=datetime(2026,9,16,23,0,tzinfo=timezone(timedelta(hours=2)))
        auf,unter=aktuelles_sonnenfenster(nacht,50.187,8.739)
        self.assertEqual(auf.date(),nacht.date()+timedelta(days=1))
        with patch("steuerzentrale.datetime") as datum:
            datum.now.return_value=nacht
            self.c.starten("Simulation",3600)
        self.assertEqual(self.c.simstart.date(),nacht.date()+timedelta(days=1))

    def test_sonnenstunden_und_horizont(self):
        auf,unter=sonnenfenster(TAG,50.187,8.739)
        self.assertTrue(6 <= auf.hour <= 8)
        self.assertTrue(18 <= unter.hour <= 20)
        self.assertGreater(sonnenstand(auf+timedelta(seconds=2),50.187,8.739)[1],0)
        self.assertLess(sonnenstand(auf-timedelta(seconds=2),50.187,8.739)[1],0)
        self.assertLess(sonnenstand(unter+timedelta(seconds=2),50.187,8.739)[1],0)

    def test_polarnacht_ohne_motorstart(self):
        with self.assertRaises(ValueError):
            sonnenfenster(TAG.replace(month=12,day=21),89,0)

    def test_osten_und_sichere_grenzen(self):
        a=self.c.status["axes"][0]
        ziel,begrenzt=tagesziel(90,90,a,True)
        self.assertEqual(round(ziel*4096/360),114)
        self.assertFalse(begrenzt)
        ziel,begrenzt=tagesziel(60,90,a,True)
        self.assertEqual(round(ziel*4096/360),114)
        self.assertTrue(begrenzt)
        ziel,_=tagesziel(180,90,a,True)
        self.assertAlmostEqual(ziel,90+114*360/4096)

    def test_senkrechtes_panel_folgt_sonnenhoehe(self):
        a=self.c.status["axes"][1].copy()
        a["span"]=2048
        for hoehe in (0,30,60,90):
            ziel,begrenzt=elevationsziel(hoehe,90,a)
            self.assertAlmostEqual(ziel,114*360/4096+hoehe)
            self.assertFalse(begrenzt)
            a["position"]=round(ziel*4096/360)
            self.assertAlmostEqual(panelneigung(90,a),90-hoehe,delta=0.05)

    def test_panelneigung_ohne_referenz_unbekannt(self):
        a=self.c.status["axes"][1].copy()
        a["referenced"]=False
        self.assertIsNone(panelneigung(90,a))

    def test_schema_zwei_wird_panelneigung(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"einstellungen.json"
            p.write_text(json.dumps(dict(version=2,az_null=90,el_null=0)))
            self.c.laden(p)
            self.assertEqual(self.c.werte["el_neigung"],90)
            self.assertEqual(self.c.werte["az_null"],90)

    def test_startposition_vor_sonnenlauf(self):
        for a in self.c.status["axes"]: a["position"]=500
        self.starten(); start=self.c.simzeit
        self.tick(); self.assertIn("AUTO AZ",self.c.kommandos[self.c.pending])
        self.tick(); self.assertEqual(self.c.simzeit,start)
        self.fertig(); self.tick()
        self.assertIn("AUTO EL",self.c.kommandos[self.c.pending])
        self.fertig(); self.tick()
        self.assertEqual(self.c.ablauf,"Sonnenlauf")
        self.assertEqual(self.c.simzeit,start)

    def test_sonnenuntergang_rueckfahrt_bis_beide_fertig(self):
        self.starten()
        self.c.ablauf="Sonnenlauf"
        self.c.simzeit=self.c.simende-timedelta(seconds=1)
        for a in self.c.status["axes"]: a["position"]=500
        self.tick(); self.assertEqual(self.c.ablauf,"Rueckfahrt")
        self.tick(); self.assertIn("AUTO AZ",self.c.kommandos[self.c.pending])
        self.assertEqual(self.c.modus,"Simulation")
        self.fertig(); self.tick()
        self.assertIn("AUTO EL",self.c.kommandos[self.c.pending])
        self.fertig(); self.tick()
        self.assertEqual(self.c.modus,"Pause")
        self.assertTrue(all(a["position"]==114 for a in self.c.status["axes"]))

    def test_stopp_bricht_rueckfahrt_ab(self):
        self.starten(); self.c.ablauf="Rueckfahrt"
        self.c.status["axes"][0]["position"]=500
        self.tick(); self.c.stopp(); anzahl=len(self.c.link.port.gesendet)
        self.tick()
        self.assertEqual(self.c.modus,"Pause")
        self.assertFalse(any(b" AUTO " in b for b in self.c.link.port.gesendet[anzahl:]))

    def test_gesamter_tag_ohne_grenzverletzung(self):
        self.starten(); zeiten=[]; fahrten=[]
        for _ in range(2000):
            self.tick(1)
            zeiten.append(self.c.simzeit)
            if self.c.pending:
                cmd=self.c.kommandos[self.c.pending].split()
                if cmd[0]=="AUTO":
                    i=0 if cmd[1]=="AZ" else 1
                    schritte=round(float(cmd[2])*4096/360)
                    self.assertGreaterEqual(schritte,114)
                    self.assertLessEqual(schritte,self.c.status["axes"][i]["span"]-114)
                    fahrten.append((i,schritte)); self.fertig()
            if self.c.modus=="Pause": break
        self.assertEqual(self.c.ablauf,"Beendet: Startposition erreicht")
        self.assertGreater(len(fahrten),10)
        self.assertTrue(all(self.c.simstart <= t <= self.c.simende for t in zeiten))
        self.assertTrue(all(a["position"]==114 for a in self.c.status["axes"]))

    def test_alte_einstellungen_migrieren(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"einstellungen.json"
            p.write_text(json.dumps(dict(version=1,az_null=0,el_null=0)))
            self.c.laden(p)
            self.assertAlmostEqual(self.c.werte["az_null"],114*360/4096)
            self.c.speichern(p,self.c.werte)
            self.assertEqual(json.loads(p.read_text())["version"],3)

    def test_normalbetrieb_nacht_parkt(self):
        self.c.modus="Normalbetrieb"; self.c.ablauf="Sonnenlauf"
        self.c.status["axes"][0]["position"]=500
        with patch("steuerzentrale.datetime") as datum:
            datum.now.return_value=TAG.replace(hour=23)
            self.tick(); self.assertEqual(self.c.ablauf,"Rueckfahrt")
            self.tick(); self.fertig(); self.tick()
        self.assertEqual(self.c.ablauf,"Nacht: Startposition")
        self.assertEqual(self.c.modus,"Normalbetrieb")


if __name__=="__main__": unittest.main()
