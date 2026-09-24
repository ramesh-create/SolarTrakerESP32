"""PC-Steuerung 0.6.7: Hardwarezustand, Prueffreigaben und NOAA-Nachfuehrung.

GUI-unabhaengig. Eingabe: Bedienbefehle und Protokoll 3; Ausgabe: Status/Ereignisse.
Keine simulierten Endschalter oder Motor-Istwerte. Poll muss alle 50 ms laufen.
"""
from datetime import datetime, timedelta
import json
from pathlib import Path
import time
import math
from verbindung import Verbindung
from betriebsspeicher import BetriebsSpeicher
from sonne import sonnenstand
from tageslauf import sonnenfenster, aktuelles_sonnenfenster, startziel, tagesziel, elevationsziel

STANDARD = dict(breite=50.187, laenge=8.739, az_null=90.0, el_neigung=90.0)
PHASEN = ("Bereit", "Fahrt", "Suche MIN", "Entlaste MIN", "Suche MAX",
          "Entlaste MAX", "Richtungstest", "Entlastung", "Grenztest MIN",
          "Grenztest MAX", "Grenztest Rueckkehr")


def pruefe_einstellungen(werte):
    daten = {k: float(werte[k]) for k in STANDARD}
    grenzen = dict(breite=(-90,90), laenge=(-180,180), az_null=(0,360), el_neigung=(0,180))
    for k, wert in daten.items():
        if not math.isfinite(wert) or not grenzen[k][0] <= wert <= grenzen[k][1]:
            raise ValueError(f"Ungueltiger Wert: {k}")
    for k in ("land", "stadt"):
        text = str(werte.get(k, "")).strip()
        if any(ord(c) < 32 for c in text):
            raise ValueError(f"Ungueltiger Text: {k}")
        daten[k] = text[:40]
    return daten


def grenztest_fehler(status, index):
    """Alle konkreten Sperrgruende, statt pauschal fehlende Tests zu behaupten."""
    if status is None:
        return ["Keine aktuelle ESP32-Verbindung"]
    a = status["axes"][index]
    name = ("Azimut", "Elevation")[index]
    fehler = []
    if status["switch_testing"]:
        fehler.append("Automatischer Endschaltertest laeuft noch")
    elif status["switch_test"] != 4:
        fehler.append(f"Endschaltertest: ESP32 meldet {status['switch_test']}/4")
    if not a["calibrated"]:
        fehler.append(f"{name}: keine gueltigen Endlagen gespeichert")
    if not a["referenced"]:
        fehler.append(f"{name}: aktuelle Position unbekannt (Referenz fehlt)")
    for key in ("min", "max"):
        if a[key]:
            fehler.append(f"{name} {key.upper()}: Eingang meldet GEDRUECKT")
    return fehler


def status_text(status):
    if status is None:
        return "Kein ESP32-Status vorhanden"
    zeilen = [f"Endschaltertest {status['switch_test']}/4; Firmware {status['version']}"]
    for name, a in zip(("Azimut", "Elevation"), status["axes"]):
        zeilen.append(f"{name}: Endlagen={'gespeichert' if a['calibrated'] else 'fehlen'}, "
                      f"Referenz={'OK' if a['referenced'] else 'fehlt'}, "
                      f"Grenztest={'OK' if a['limits_ok'] else 'offen'}, "
                      f"MIN={int(a['min'])}, MAX={int(a['max'])}, "
                      f"Position={a['position']}, Spanne={a['span']}, Phase={PHASEN[a['state']]}")
    if "auto_mode" in status:
        zeilen.append("Autonomer Betrieb: " + ("aktiv" if status["auto_mode"] else "aus")
                      + "; Konfiguration=" + ("OK" if status.get("conf_ok") else "fehlt"))
    return "\n".join(zeilen)


class Steuerzentrale:
    def __init__(self, protokoll=lambda text: None, uhr=time.monotonic, speicherpfad=None):
        self.link = None
        self.status = None
        self.uhr = uhr
        self.protokoll = protokoll
        self.modus = "Pause"
        self.pending = None
        self.ack = False
        self.kommandos = {}
        self.rtc_sync = False
        self.lcd_meldung = "LCD noch nicht getestet"
        self.grenzen_bestaetigt = False
        self.ausrichtung_bestaetigt = False
        self.werte = STANDARD.copy()
        self.simzeit = datetime.now().astimezone()
        self.simstart = self.simzeit
        self.simende = self.simzeit
        self.ablauf = "Bereit"
        self.sonnenziele = None
        self.begrenzt = False
        self.tempo = 60.0
        self.naechste_achse = 0
        self.letzter_tick = self.uhr()
        self.letzte_regelung = 0
        try:
            self.betriebsspeicher=BetriebsSpeicher(speicherpfad)
        except (OSError,ValueError,TypeError) as exc:
            self.protokoll(f"PC-Betriebsdaten nicht lesbar: {exc}")
            self.betriebsspeicher=BetriebsSpeicher()
        self.fortsetzung=self.betriebsspeicher.daten["simulation"]


    def betriebsdaten_sichern(self,feld,wert):
        try:
            self.betriebsspeicher.setzen(feld,wert)
        except (OSError,ValueError) as exc:
            self.protokoll(f"PC-Betriebsdaten nicht gespeichert: {exc}")

    def kalibrierkennung(self):
        n=self.status
        if not n or not n.get("device_id") or not all(a["calibrated"] for a in n["axes"]):
            return None
        return dict(geraet=n["device_id"],achsen=[[a["span"],a.get("calibration_id",0)] for a in n["axes"]])

    def bestaetige_grenzen(self,wert):
        self.grenzen_bestaetigt=bool(wert and self.status and all(a["limits_ok"] for a in self.status["axes"]))
        self.betriebsdaten_sichern("grenzen",self.kalibrierkennung() if self.grenzen_bestaetigt else None)

    def bestaetige_ausrichtung(self,wert):
        self.ausrichtung_bestaetigt=bool(wert)
        self.betriebsdaten_sichern("ausrichtung",self.werte.copy() if wert else None)

    def simulation_merken(self):
        if self.modus!="Simulation": return
        self.fortsetzung=dict(zeit=self.simzeit.isoformat(),start=self.simstart.isoformat(),ende=self.simende.isoformat(),
            ablauf=self.ablauf,werte=self.werte.copy(),tempo=self.tempo,kennung=self.kalibrierkennung())
        self.betriebsdaten_sichern("simulation",self.fortsetzung)

    def fortsetzung_laden(self):
        d=self.fortsetzung
        if not isinstance(d,dict) or d.get("werte")!=self.werte or d.get("kennung")!=self.kalibrierkennung():
            return False
        try:
            start,zeit,ende=(datetime.fromisoformat(d[k]) for k in ("start","zeit","ende"))
            if any(t.utcoffset() is None for t in (start,zeit,ende)) or not start<=zeit<=ende: return False
            if d["ablauf"] not in ("Startposition anfahren","Sonnenlauf","Rueckfahrt"): return False
            self.simstart,self.simzeit,self.simende=start,zeit,ende
            self.ablauf=d["ablauf"]
            return True
        except (ValueError,TypeError,KeyError):
            return False

    @property
    def bereit(self):
        return bool(self.link and self.link.bereit and self.status)

    @property
    def beschaeftigt(self):
        return bool(self.pending or (self.status and (self.status.get("auto_testing",False) or self.status["switch_testing"] or
                    any(a["state"] for a in self.status["axes"]))))

    def verbinden(self, port):
        if self.link:
            self.trennen()
        self.link = Verbindung()
        try:
            self.link.oeffnen(port)
        except Exception:
            self.trennen()
            raise
        self.protokoll(f"Verbinde {port}, pruefe Firmware ...")

    def trennen(self):
        self.simulation_merken()
        link = self.link
        self.modus = "Pause"
        self.link = None
        self.status = None
        self.pending = None
        self.kommandos.clear()
        self.rtc_sync = False
        self.lcd_meldung = "LCD noch nicht getestet"
        self.grenzen_bestaetigt = False
        if link:
            link.schliessen()

    def senden(self, cmd, *args, bewegung=False):
        if not self.bereit:
            raise ValueError("Zuerst den ESP32 verbinden")
        if bewegung and self.beschaeftigt:
            raise ValueError("Eine Fahrt laeuft noch")
        nummer = self.link.senden(cmd, *args)
        self.kommandos[nummer] = " ".join(map(str, (cmd,*args)))
        if bewegung:
            self.pending, self.ack = nummer, False
        self.protokoll("Gesendet: " + self.kommandos[nummer])
        return nummer

    def stopp(self):
        self.simulation_merken()
        self.modus = "Pause"
        # Auftrag bleibt bis zu Status in Ruhe gesperrt; keine Fahrt aus altem Status.
        if self.link and self.link.bereit:
            self.pending = self.link.senden("STOP")
            self.kommandos[self.pending] = "STOP"
            self.ack = False

    def rtc_setzen(self):
        if self.beschaeftigt:
            raise ValueError("RTC-Synchronisierung erst bei stillstehenden Achsen")
        self.senden("TIME", int(time.time()))

    def lcd_senden(self, zeile1, zeile2):
        if not self.bereit:
            raise ValueError("Zuerst ESP32 verbinden")
        if not self.status.get("lcd_supported",False):
            raise ValueError("LCD-Uebertragung braucht Firmware 0.3.2. Die verbundene Firmware bietet nur die PC-Vorschau.")
        if self.beschaeftigt or self.modus != "Pause":
            raise ValueError("LCD-Test erst bei stillstehenden Achsen und pausiertem Betrieb")
        texte=[]
        for text in (zeile1,zeile2):
            for alt,neu in (("\u00e4","ae"),("\u00f6","oe"),("\u00fc","ue"),("\u00c4","Ae"),("\u00d6","Oe"),("\u00dc","Ue"),("\u00df","ss"),("\u00b0"," Grad")):
                text=text.replace(alt,neu)
            if any(ord(c)<32 or ord(c)>126 for c in text):
                raise ValueError("LCD: nur druckbare Zeichen; Umlaute werden als ae/oe/ue gesendet")
            if len(text)>16:
                raise ValueError("LCD: maximal 16 Zeichen je Zeile, nach Umlaut-Ersetzung")
            texte.append(text.ljust(16))
        self.senden("LCD",*(t.encode("ascii").hex() for t in texte),bewegung=True)
        self.lcd_meldung="Text wird zum LCD uebertragen ..."
        return texte

    def auto_kalibrierung(self):
        if not self.bereit:
            raise ValueError("Zuerst ESP32 verbinden")
        if not self.status.get("auto_supported",False):
            raise ValueError("Auto Kalibrierung benoetigt Firmware 0.4.1")
        if self.modus!="Pause":
            raise ValueError("Zuerst Betrieb oder Simulation stoppen")
        if not self.ausrichtung_bestaetigt:
            raise ValueError("Zuerst Standort und Ausrichtung unter Einstellungen bestaetigen")
        self.senden("AUTOCAL",bewegung=True)
        self.status={**self.status,"auto_ok":False}
        self.bestaetige_grenzen(False)
        self.protokoll("Auto Kalibrierung: LCD, RTC, alle vier Endschalter, Grenztests und Rueckkehr zu sicherer MIN")

    def konfiguration_senden(self):
        if not self.bereit:
            raise ValueError("Zuerst ESP32 verbinden")
        if self.beschaeftigt:
            raise ValueError("Konfiguration erst bei stillstehenden Achsen")
        w=self.werte
        self.senden("CONF",f"{w['breite']:.3f}",f"{w['laenge']:.3f}",f"{w['az_null']:.2f}",f"{w['el_neigung']:.2f}")
        self.ort_senden()
        self.protokoll("Standort und Ausrichtung an den ESP32 uebertragen")

    def ort_senden(self):
        """Ortsname (Stadt, Land) fuer das LCD an den ESP32 senden."""
        if not self.bereit or not self.status.get("ort_supported",False):
            return
        text = ", ".join(t for t in (self.werte.get("stadt",""), self.werte.get("land","")) if t)
        if not text:
            return
        for alt,neu in (("\u00e4","ae"),("\u00f6","oe"),("\u00fc","ue"),("\u00c4","Ae"),("\u00d6","Oe"),("\u00dc","Ue"),("\u00df","ss")):
            text = text.replace(alt,neu)
        text = text[:16].ljust(16)
        if any(ord(c) < 32 or ord(c) > 126 for c in text):
            raise ValueError("Ort: nur druckbare Zeichen (Umlaute werden ae/oe/ue)")
        self.senden("ORT", text.encode("ascii").hex())
        self.protokoll("Ort an ESP32 uebertragen: " + text.strip())

    def autonom(self,ein):
        if not self.bereit:
            raise ValueError("Zuerst ESP32 verbinden")
        if ein:
            if self.modus!="Pause":
                raise ValueError("Zuerst Betrieb oder Simulation stoppen")
            if self.beschaeftigt:
                raise ValueError("Fahrt/Auftrag laeuft - Abschluss abwarten")
            if not self.ausrichtung_bestaetigt:
                raise ValueError("Zuerst Standort und Ausrichtung unter Einstellungen bestaetigen")
            if not self.status.get("auto_ok",False):
                raise ValueError("Autonomer Betrieb braucht den bestandenen Gesamttest (Auto Kalibrierung)")
            fehler=self.freigabe()
            if fehler:
                raise ValueError("Autonomer Betrieb gesperrt:\n"+"\n".join(fehler))
            self.konfiguration_senden()
            self.senden("AUTOON")
            self.protokoll("Autonomer Betrieb angefordert: ESP32 fuehrt die Sonne ohne PC nach")
        else:
            self.senden("AUTOOFF")
            self.protokoll("Autonomer Betrieb deaktiviert")

    def kalibrieren(self, index):
        if not self.bereit:
            raise ValueError("Zuerst ESP32 verbinden")
        if self.modus != "Pause":
            raise ValueError("Zuerst Betrieb oder Simulation stoppen")
        if self.beschaeftigt:
            raise ValueError("Fahrt/Auftrag laeuft - Abschluss abwarten")
        if self.status.get("switch_test") != 4:
            raise ValueError("Zuerst alle vier Endschalter pruefen")
        self.senden("CAL", ("AZ","EL")[index], bewegung=True)
        self.status = {**self.status, "auto_ok": False}
        self.protokoll(f"Einzelkalibrierung {('Azimut','Elevation')[index]} gestartet")

    def befehl_senden(self, text):
        if not self.bereit:
            raise ValueError("Zuerst ESP32 verbinden")
        teile = text.split()
        if not teile:
            raise ValueError("Befehl fehlt")
        self.senden(teile[0].upper(), *teile[1:])
        self.protokoll("Direktbefehl gesendet: " + " ".join(teile))

    def endschaltertest(self):
        if self.status and all(a["calibrated"] for a in self.status["axes"]):
            self.protokoll("Endlagen bereits gespeichert: keine neue Kalibrierfahrt erforderlich")
            return
        self.modus = "Pause"
        self.grenzen_bestaetigt = False
        self.senden("SWTEST", bewegung=True)

    def grenztest(self, index):
        if self.status and self.status["axes"][index]["limits_ok"]:
            self.protokoll("Grenztest bereits bestanden und gespeichert: keine erneute Testfahrt erforderlich")
            return
        fehler = grenztest_fehler(self.status,index)
        if fehler:
            raise ValueError("\n".join(fehler))
        self.modus = "Pause"
        self.senden("LIMIT", ("AZ","EL")[index], bewegung=True)

    def referenzfahrt(self,index):
        if not self.bereit or not self.status.get("position_storage",False):
            raise ValueError("Automatische Positionswiederherstellung braucht Firmware 0.4.0")
        a=self.status["axes"][index]
        if a["referenced"]:
            self.protokoll("Position bereits bekannt: keine Referenzfahrt erforderlich")
            return
        if not a["calibrated"]:
            raise ValueError("Nur fehlende Endlagen zuerst kalibrieren")
        self.modus="Pause"
        self.senden("HOME",("AZ","EL")[index],bewegung=True)

    def referenz(self, index):
        if not self.bereit:
            raise ValueError("Zuerst verbinden")
        a = self.status["axes"][index]
        if not a["calibrated"] or a["min"] or a["max"]:
            raise ValueError("Gespeicherte Kalibrierung fehlt oder Schalter aktiv")
        if a["referenced"]:
            raise ValueError("Referenz bereits OK. Keine erneute Bestaetigung erforderlich; Grenztest bleibt erhalten.")
        self.modus = "Pause"
        self.senden("REF", ("AZ","EL")[index], bewegung=True)

    def manuell(self, index, grad, test=False):
        if not math.isfinite(grad) or not 0 < abs(grad) <= 10:
            raise ValueError("Schrittweite: groesser 0 bis 10 Grad")
        if not self.bereit:
            raise ValueError("Zuerst verbinden")
        a = self.status["axes"][index]
        self.modus = "Pause"
        achse = ("AZ","EL")[index]
        if test:
            if abs(grad) > 5:
                raise ValueError("Richtungstest maximal 5 Grad")
            self.senden("JOG",achse,f"{grad:.5f}",bewegung=True)
        else:
            if not a["referenced"]:
                raise ValueError("Aktuelle Position unbekannt. Kalibrieren oder markierte Position bestaetigen.")
            ziel = a["position"]*360/4096 + grad
            if not a["margin"] <= round(ziel*4096/360) <= a["span"]-a["margin"]:
                raise ValueError("Ziel liegt ausserhalb des sicheren 10-Grad-Bereichs")
            self.senden("MOVE",achse,f"{ziel:.5f}",bewegung=True)

    def freigabe(self):
        if not self.bereit:
            return ["Zuerst ESP32 verbinden"]
        fehler = list(dict.fromkeys(grenztest_fehler(self.status,0)+grenztest_fehler(self.status,1)))
        for name,a in zip(("Azimut","Elevation"),self.status["axes"]):
            if not a["limits_ok"]:
                fehler.append(f"Grenztest {name} noch offen")
        if self.status.get("storage_ok") is False:
            fehler.append("ESP32-Positionsspeicher nicht bereit")
        if self.status.get("auto_supported",False):
            if self.status.get("auto_testing",False) or not self.status.get("auto_ok",False):
                fehler.append("Auto Kalibrierung noch nicht erfolgreich abgeschlossen")
            if not self.status.get("lcd_present",False):
                fehler.append("LCD-Test fehlt")
            if not self.status["rtc_present"] or not self.status["rtc_valid"]:
                fehler.append("RTC-Test fehlt oder Zeit ungueltig")
        if not self.grenzen_bestaetigt:
            fehler.append("Beobachteten 10-Grad-Abstand bestaetigen")
        if not self.ausrichtung_bestaetigt:
            fehler.append("Standort und Ausrichtung bestaetigen")
        return fehler

    def starten(self, modus, tempo=60, neu=False):
        fehler = self.freigabe()
        if fehler:
            raise ValueError("\n".join(fehler))
        if self.beschaeftigt:
            raise ValueError("Eine Fahrt laeuft noch")
        if modus not in ("Simulation","Normalbetrieb") or not math.isfinite(tempo) or not 1 <= tempo <= 3600:
            raise ValueError("Ungueltiger Modus oder Geschwindigkeit (1 bis 3600)")
        if modus=="Simulation" and not neu and self.fortsetzung_laden():
            self.modus=modus; self.tempo=tempo; self.letzter_tick=self.uhr(); self.sonnenziele=None
            self.protokoll(f"Simulation fortgesetzt bei {self.simzeit:%H:%M:%S}, Positionen bleiben erhalten")
            return
        self.fortsetzung=None
        self.betriebsdaten_sichern("simulation",None)
        jetzt = datetime.now().astimezone()
        if modus == "Simulation":
            auf, unter = aktuelles_sonnenfenster(jetzt,self.werte["breite"],self.werte["laenge"])
        else:
            auf, unter = sonnenfenster(jetzt,self.werte["breite"],self.werte["laenge"])
        self.simstart, self.simende = auf, unter
        self.simzeit = auf if modus == "Simulation" else jetzt
        self.letzter_tick = self.uhr()
        self.tempo = tempo
        self.modus = modus
        self.ablauf = "Startposition anfahren" if modus == "Simulation" else "Sonnenlauf"
        self.sonnenziele = None
        self.begrenzt = False
        self.protokoll(f"{modus}: Sonnenstunden {auf:%H:%M} bis {unter:%H:%M}; Start/Rueckkehr an sichere MIN beider Achsen")

    def zielpaar_fahren(self, ziele):
        """Jeweils nur eine Achse; Abschluss erst nach Quittung und Ruhestatus."""
        if self.beschaeftigt:
            return False
        for i in (0,1):
            a = self.status["axes"][i]
            if a["position"] != round(ziele[i]*4096/360):
                self.senden("AUTO",("AZ","EL")[i],f"{ziele[i]:.5f}",bewegung=True)
                return False
        return True

    def empfangen(self, n):
        typ = n["type"]
        if typ == "status":
            alt=self.status
            if alt:
                for name,vorher,neu in zip(("Azimut","Elevation"),alt["axes"],n["axes"]):
                    if neu["limits_ok"] and not vorher["limits_ok"]:
                        self.protokoll(f"Grenztest {name} erfolgreich abgeschlossen")
                    if vorher["referenced"] and not neu["referenced"]:
                        self.protokoll(f"{name}: Positionsreferenz nicht mehr gueltig (Kalibrierung, Stromverlust oder Kontaktfehler)")
                if alt["switch_testing"] and not n["switch_testing"] and n["switch_test"]==4 and all(a["referenced"] for a in n["axes"]):
                    self.protokoll("Endschaltertest abgeschlossen: beide Achsen kalibriert, Endlagen gespeichert. Als Naechstes die beiden Grenztests fahren.")
            self.status = n
            if n.get("auto_supported",False):
                if not alt or alt.get("auto_message")!=n.get("auto_message"):
                    self.protokoll("Auto Kalibrierung: "+n.get("auto_message",""))
                if n.get("auto_ok",False) and not n.get("auto_testing",False):
                    self.bestaetige_grenzen(True)
            if any(not a["limits_ok"] for a in n["axes"]):
                self.grenzen_bestaetigt = False
            elif self.kalibrierkennung() and self.betriebsspeicher.daten["grenzen"]==self.kalibrierkennung():
                self.grenzen_bestaetigt=True
            if self.ack and not n.get("auto_testing",False) and not n["switch_testing"] and all(a["state"] == 0 for a in n["axes"]):
                self.pending = None
            if self.bereit and not self.rtc_sync and not self.beschaeftigt:
                self.rtc_sync = True
                self.rtc_setzen()
        elif typ == "ack":
            cmd = self.kommandos.pop(n["id"],"")
            if n["id"] == self.pending:
                self.ack = n["ok"]
            if cmd.startswith("LCD "):
                self.lcd_meldung=("Text zum LCD gesendet. Bitte sichtbare Zeichen am Display pruefen." if n["ok"] else "LCD: "+n.get("message","Uebertragung fehlgeschlagen"))
                self.protokoll(self.lcd_meldung)
            if not n["ok"]:
                if n["id"] == self.pending:
                    self.pending = None
                self.modus = "Pause"
                self.protokoll(f"ESP32 lehnt {cmd or 'Befehl'} ab: {n.get('message','Fehler')}")
                self.protokoll("Letzter empfangener Status:\n" + status_text(self.status))
                # Eine abgelehnte Fahrt wird nicht durch STOP zu einer verlorenen Referenz.
                if self.link:
                    self.link.senden("STATUS")
            elif cmd:
                self.protokoll("ESP32 angenommen: " + cmd)
        elif typ == "event":
            self.modus = "Pause"
            self.protokoll("ESP32: " + n.get("message","Ereignis"))
        elif typ == "fault":
            self.stopp()
            details = {k:n[k] for k in ("axis","phase","direction","steps","min","max") if k in n}
            self.protokoll("ESP32: " + n.get("message","Fehler") + " " + json.dumps(details))

    def poll(self):
        jetzt = self.uhr()
        dt = jetzt-self.letzter_tick
        self.letzter_tick = jetzt
        if self.link:
            try:
                for n in self.link.lesen():
                    self.empfangen(n)
            except Exception as exc:
                self.trennen()
                self.protokoll(f"Verbindung beendet: {exc}")
        if self.modus == "Pause":
            return
        try:
            fehler = self.freigabe()
            if fehler:
                raise ValueError("; ".join(fehler))
            if self.beschaeftigt:
                return
            if self.modus == "Normalbetrieb":
                self.simzeit = datetime.now().astimezone()
            startziele = [startziel(a) for a in self.status["axes"]]
            if self.ablauf == "Startposition anfahren":
                if self.zielpaar_fahren(startziele):
                    self.ablauf = "Sonnenlauf"
                    self.protokoll("Startposition erreicht: AZ-MIN / EL-MIN mit 10 Grad Abstand")
                return
            if self.ablauf == "Rueckfahrt":
                if self.zielpaar_fahren(startziele):
                    self.sonnenziele = None
                    if self.modus == "Simulation":
                        self.modus = "Pause"
                        self.fortsetzung=None
                        self.betriebsdaten_sichern("simulation",None)
                        self.ablauf = "Beendet: Startposition erreicht"
                    else:
                        self.ablauf = "Nacht: Startposition"
                    self.protokoll("Sonnenuntergang: Rueckfahrt abgeschlossen, beide Achsen an sicherer MIN")
                return
            if self.modus == "Normalbetrieb":
                # Auch beim naechsten Sonnenaufgang ohne Neustart weiterfuehren.
                _, hoehe = sonnenstand(self.simzeit,self.werte["breite"],self.werte["laenge"])
                if hoehe <= 0:
                    if self.ablauf != "Nacht: Startposition":
                        self.sonnenziele = None
                        self.ablauf = "Rueckfahrt"
                        self.protokoll("Sonne unter dem Horizont: Rueckfahrt zu AZ-MIN und EL-MIN")
                    return
                self.ablauf = "Sonnenlauf"
            if self.sonnenziele is not None:
                if self.zielpaar_fahren(self.sonnenziele):
                    self.sonnenziele = None
                return
            if self.modus == "Simulation":
                self.simzeit = min(self.simende,self.simzeit+timedelta(seconds=max(0,dt)*self.tempo))
                if self.simzeit >= self.simende:
                    self.ablauf = "Rueckfahrt"
                    self.protokoll("Sonnenuntergang erreicht: Rueckfahrt zu AZ-MIN und EL-MIN")
                    return
            if jetzt-self.letzte_regelung < 0.5:
                return
            self.letzte_regelung = jetzt
            az,el = sonnenstand(self.simzeit,self.werte["breite"],self.werte["laenge"])
            paare = [tagesziel(az,self.werte["az_null"],self.status["axes"][0],True),
                     elevationsziel(el,self.werte["el_neigung"],self.status["axes"][1])]
            begrenzt = any(p[1] for p in paare)
            if begrenzt != self.begrenzt:
                self.protokoll("Sonnenziel durch sichere Fahrgrenze begrenzt" if begrenzt else "Sonnenziel wieder vollstaendig erreichbar")
            self.begrenzt = begrenzt
            self.sonnenziele = [p[0] for p in paare]
            self.zielpaar_fahren(self.sonnenziele)
        except (ValueError,OSError) as exc:
            self.stopp()
            self.protokoll(f"Betrieb angehalten: {exc}")

    def laden(self, pfad):
        pfad = Path(pfad)
        if pfad.exists():
            daten = json.loads(pfad.read_text(encoding="utf-8"))
            if not isinstance(daten,dict) or daten.get("version",1) not in (1,2,3):
                raise ValueError("Unbekannte Einstellungsdatei")
            if daten.get("version",1) == 1:
                # Altes Schema bezog die Ausrichtung auf den mechanischen Kontakt.
                daten = dict(daten)
                daten["az_null"] = (float(daten.get("az_null",0))+114*360/4096) % 360
                daten["el_null"] = min(90,float(daten.get("el_null",0))+114*360/4096)
                self.protokoll("Alte Ausrichtung auf sichere MIN umgerechnet; Ausrichtung vor Start pruefen")
            if daten.get("version",1) in (1,2):
                daten = dict(daten)
                daten["el_neigung"] = 90-float(daten.get("el_null",0))
            self.werte = pruefe_einstellungen({**STANDARD,**daten})
        self.ausrichtung_bestaetigt=self.betriebsspeicher.daten["ausrichtung"]==self.werte

    def speichern(self, pfad, werte):
        daten = pruefe_einstellungen(werte)
        pfad = Path(pfad)
        temp = pfad.with_suffix(".tmp")
        temp.write_text(json.dumps(dict(version=3,**daten),indent=2),encoding="utf-8")
        temp.replace(pfad)
        self.werte = daten
