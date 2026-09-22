"""SolarTracker PC 0.3.1: Bedienfenster mit gepruefter physischer Simulation.

Start: python bedienfeld.py. Simulation erfordert die gepruefte Hardware.
Eingaben: GUI/serielle Statusdaten; Ausgaben: Motorbefehle, lokale Einstellungen.
"""
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from sonne import sonnenstand, motorziel
from verbindung import Verbindung

VERSION = "0.3.1"
ORDNER = Path(__file__).resolve().parent
STANDARD = {"breite": 50.187, "laenge": 8.739, "az_null": 0.0, "el_null": 0.0}
ZUSTAENDE = ("Bereit", "Fahrt", "Suche MIN", "Entlaste MIN", "Suche MAX", "Entlaste MAX", "Richtungstest", "Entlastung", "Grenztest MIN", "Grenztest MAX", "Grenztest Rückkehr")


class Bedienfeld(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"SolarTracker • PC-Steuerung {VERSION}")
        self.geometry("1180x810")
        self.minsize(1000, 720)
        self.configure(background="#edf2f0")
        self.link = None
        self.achsen = None
        self.auftrag = None
        self.bestaetigt = False
        self.modus = "Pause"
        self.simzeit = datetime.now().astimezone()
        self.tickzeit = time.monotonic()
        self.regelzeit = 0
        self.sonnenziel = (0.0, 0.0)
        self.naechste_achse = 0
        self.kurve = []
        self.werte = {}
        self.pruefstatus = None
        self.rtc_gesendet = False
        self.grenzen_gesehen = tk.BooleanVar(value=False)
        self.prueftext = tk.StringVar(value="Start gesperrt: ESP32 verbinden und Prüfungen abschließen.")
        self.pcuhr = tk.StringVar()
        self.rtctext = tk.StringVar(value="RTC: noch nicht verbunden")
        self.ausrichtung = tk.BooleanVar(value=False)
        self.port = tk.StringVar(value="COM3")
        self.status = tk.StringVar(value="Offline · Tagesgrafik verfügbar")
        self.zeittext = tk.StringVar()
        self.sonnentext = tk.StringVar()
        self.achslabels = [tk.StringVar(value="Nicht verbunden"), tk.StringVar(value="Nicht verbunden")]
        self.schaltertext = tk.StringVar(value="Endschalter: kein Status")
        self.meldung = tk.StringVar(value="ESP32 verbinden, Endschalter prüfen, kalibrieren und Grenztest durchführen.")
        self._stil()
        self._aufbauen()
        self.laden()
        self.ports_lesen()
        self.grafik_berechnen()
        for key in STANDARD:
            self.werte[key].trace_add("write", self.einstellung_geaendert)
        self.protocol("WM_DELETE_WINDOW", self.beenden)
        self.bind("<Escape>", lambda _: self.stopp())
        self.after(50, self.tick)

    def _stil(self):
        stil = ttk.Style(self)
        stil.theme_use("clam")
        stil.configure("TFrame", background="#edf2f0")
        stil.configure("TLabel", background="#edf2f0", foreground="#173e3a", font=("Segoe UI", 10))
        stil.configure("Titel.TLabel", font=("Segoe UI", 23, "bold"))
        stil.configure("Wert.TLabel", font=("Segoe UI", 13, "bold"))
        stil.configure("TButton", padding=(12, 8), font=("Segoe UI", 10))
        stil.configure("TCheckbutton", background="#edf2f0", font=("Segoe UI", 10))
        stil.configure("TLabelframe", background="#edf2f0")
        stil.configure("TLabelframe.Label", background="#edf2f0", font=("Segoe UI", 11, "bold"))
        stil.configure("TNotebook.Tab", padding=(18, 9), font=("Segoe UI", 11))

    def _aufbauen(self):
        menue = tk.Menu(self)
        datei = tk.Menu(menue, tearoff=False)
        datei.add_command(label="Einstellungen speichern", command=self.speichern)
        datei.add_command(label="Einstellungen laden", command=self.laden)
        datei.add_command(label="Tagesgrafik als CSV exportieren", command=self.exportieren)
        datei.add_separator()
        datei.add_command(label="Beenden", command=self.beenden)
        menue.add_cascade(label="Datei", menu=datei)
        menue.add_command(label="STOPP (Esc)", command=self.stopp)
        menue.add_command(label="Bedienhinweise", command=lambda: messagebox.showinfo("Bedienung", "1. Firmware 0.3.1 verbinden.\n2. Drehrichtung mit begrenzten Tippfahrten kontrollieren.\n3. Endschaltertest startet automatisch Azimut, danach Elevation. Beide Achsen fahren MIN und MAX an und entlasten jeweils um 10 Grad.\n4. Danach beide Grenztests ausfuehren.\n5. Abstand und Ausrichtung bestaetigen, dann Simulation starten.\n\nSTOPP / Esc bricht die Bewegung ab."))
        self.config(menu=menue)
        kopf = ttk.Frame(self, padding=18)
        kopf.pack(fill="x")
        ttk.Label(kopf, text="SolarTracker", style="Titel.TLabel").pack(side="left")
        ttk.Label(kopf, text="  PC-BEDIENFELD  /  2 ACHSEN").pack(side="left", padx=12)
        tk.Button(kopf, text="■  STOPP", command=self.stopp, bg="#b83239", fg="white", font=("Segoe UI", 13, "bold"), padx=24, pady=8).pack(side="right")
        verbindung = ttk.Frame(self, padding=(18, 0, 18, 12))
        verbindung.pack(fill="x")
        ttk.Label(verbindung, text="Serieller Port").pack(side="left")
        self.portwahl = ttk.Combobox(verbindung, textvariable=self.port, width=12)
        self.portwahl.pack(side="left", padx=8)
        ttk.Button(verbindung, text="Suchen", command=self.ports_lesen).pack(side="left")
        self.verbinden_taste = ttk.Button(verbindung, text="Verbinden", command=self.umschalten)
        self.verbinden_taste.pack(side="left", padx=8)
        ttk.Label(verbindung, textvariable=self.status).pack(side="left", padx=12)
        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True, padx=18)
        betrieb, simulation, einstellungen, tests = [ttk.Frame(tabs, padding=16) for _ in range(4)]
        for tab, name in zip((betrieb, simulation, einstellungen, tests), ("Bedienfeld", "Simulation & Grafik", "Einstellungen", "Tests & Protokoll")):
            tabs.add(tab, text=name)
        for i, name in enumerate(("Azimut", "Elevation")):
            feld = ttk.LabelFrame(betrieb, text=name, padding=16)
            feld.grid(row=0, column=i, sticky="nsew", padx=8, pady=8)
            betrieb.columnconfigure(i, weight=1)
            ttk.Label(feld, textvariable=self.achslabels[i], style="Wert.TLabel", wraplength=400).pack(anchor="w", pady=8)
            tasten = ttk.Frame(feld)
            tasten.pack(fill="x")
            ttk.Button(tasten, text="− 1°", command=lambda a=i: self.jog(a, -1)).pack(side="left", padx=4)
            ttk.Button(tasten, text="+ 1°", command=lambda a=i: self.jog(a, 1)).pack(side="left", padx=4)
            ttk.Button(feld, text="Sichere Startposition fahren", command=lambda a=i: self.grenze(a, False)).pack(fill="x", pady=(16, 4))
            ttk.Button(feld, text="Sichere Endposition fahren", command=lambda a=i: self.grenze(a, True)).pack(fill="x", pady=4)
            ttk.Button(feld, text="Kalibrierung starten …", command=lambda a=i: self.kalibrieren(a)).pack(fill="x", pady=4)
            ttk.Button(feld, text="Markierte Startposition bestätigen …", command=lambda a=i: self.referenz(a)).pack(fill="x", pady=4)
        feld = ttk.LabelFrame(betrieb, text="Sonnenfahrt mit PC-Uhr", padding=16)
        feld.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=12)
        ttk.Label(feld, text="Der PC berechnet den Sonnenstand. Fahrziele müssen innerhalb beider kalibrierten Bereiche liegen.", wraplength=900).pack(anchor="w")
        ttk.Button(feld, text="Normalbetrieb starten", command=lambda: self.starten("Normalbetrieb")).pack(anchor="w", pady=12)
        ttk.Label(feld, textvariable=self.sonnentext, style="Wert.TLabel").pack(anchor="w")
        ttk.Label(betrieb, text="Angezeigte Motorposition = gezählte Schritte, keine Sensormessung.\nAzimut/Elevation am Motor werden ab dem jeweiligen mechanischen MIN gerechnet.").grid(row=2, column=0, columnspan=2, sticky="w", padx=8)
        leiste = ttk.Frame(simulation)
        leiste.pack(fill="x")
        ttk.Label(leiste, text="Geschwindigkeit ×").pack(side="left", padx=8)
        self.werte["tempo"] = tk.StringVar(value="60")
        ttk.Combobox(leiste, textvariable=self.werte["tempo"], values=(1,5,10,30,60,120,600), width=8).pack(side="left")
        ttk.Button(leiste, text="Tageskurve", command=self.grafik_berechnen).pack(side="left", padx=8)
        self.sim_taste = ttk.Button(leiste, text="Simulation starten · Grafik + Panel", command=lambda: self.starten("Simulation"), state="disabled")
        self.sim_taste.pack(side="left")
        ttk.Button(leiste, text="Pause", command=self.stopp).pack(side="left", padx=8)
        ttk.Label(simulation, textvariable=self.pcuhr).pack(anchor="w", pady=(12, 2))
        ttk.Label(simulation, textvariable=self.rtctext).pack(anchor="w")
        ttk.Label(simulation, textvariable=self.prueftext, wraplength=1000).pack(anchor="w", pady=8)
        ttk.Label(simulation, textvariable=self.zeittext, style="Wert.TLabel").pack(anchor="w")
        self.canvas = tk.Canvas(simulation, bg="#12332f", highlightthickness=0, height=330)
        self.canvas.pack(fill="both", expand=True, pady=12)
        self.canvas.bind("<Configure>", lambda _: self.zeichnen())
        ttk.Label(simulation, text="Gold: Sonnen-Azimut (linke Skala)   •   Türkis: Sonnenhöhe (rechte Skala)   •   Weiß: Simulationszeit").pack(anchor="w")
        for row, (key, label) in enumerate((("breite", "Breitengrad (−90 … 90)"), ("laenge", "Längengrad (−180 … 180, Ost positiv)"), ("az_null", "Kompassrichtung am mechanischen Azimut-MIN (0° = Nord)"), ("el_null", "Panelneigung am mechanischen Elevation-MIN"))):
            ttk.Label(einstellungen, text=label).grid(row=row, column=0, sticky="w", pady=12)
            self.werte[key] = tk.StringVar(value=str(STANDARD[key]))
            ttk.Entry(einstellungen, textvariable=self.werte[key], width=18).grid(row=row, column=1, padx=20)
        ttk.Checkbutton(einstellungen, text="Ausrichtung geprüft: positive Motorfahrt erhöht Kompasswinkel bzw. Panelneigung.", variable=self.ausrichtung, command=self.stopp).grid(row=5, column=0, columnspan=2, sticky="w", pady=12)
        ttk.Button(einstellungen, text="Einstellungen speichern", command=self.speichern).grid(row=6, column=0, sticky="w", pady=12)
        ttk.Button(einstellungen, text="Gespeicherte Werte laden", command=self.laden).grid(row=6, column=1)
        ttk.Label(einstellungen, text="Datum und Startzeit kommen automatisch vom PC einschließlich Zeitzone.\nBeim Verbinden erhält die DS3231-RTC die echte PC-Zeit (UTC).\nDie RTC läuft ohne PC weiter; die Simulation verändert ihre Uhrzeit nicht.\nStandort hier eingeben, Geschwindigkeit in Simulation wählen.\nNominal: 4096 Halbschritte = 360° am Panel, ohne zusätzliches Getriebe.", wraplength=850).grid(row=7, column=0, columnspan=2, sticky="w", pady=18)
        prueftasten = ttk.Frame(tests)
        prueftasten.pack(fill="x")
        ttk.Button(prueftasten, text="Endschaltertest starten - AZ + EL", command=self.schalterpruefung).pack(side="left", padx=4)
        for i, name in enumerate(("Azimut", "Elevation")):
            ttk.Button(prueftasten, text=f"Grenztest {name}", command=lambda a=i: self.grenzpruefung(a)).pack(side="left", padx=4)
        ttk.Checkbutton(tests, text="Grenzfahrten beobachtet: beide Achsen halten mit 10° Abstand vor MIN und MAX.", variable=self.grenzen_gesehen, command=self.grenzen_bestaetigen).pack(anchor="w", pady=6)
        ttk.Label(tests, textvariable=self.prueftext, wraplength=1000).pack(anchor="w", pady=6)
        ttk.Label(tests, textvariable=self.schaltertext, style="Wert.TLabel").pack(anchor="w", pady=12)
        ttk.Label(tests, text="Richtungstest ohne Referenz: nur ±5°. MIN muss bei Minusfahrt, MAX bei Plusfahrt liegen.").pack(anchor="w")
        reihe = ttk.Frame(tests)
        reihe.pack(fill="x", pady=12)
        for i, name in enumerate(("Azimut", "Elevation")):
            for grad in (-5, 5):
                ttk.Button(reihe, text=f"{name} {grad:+}° testen", command=lambda a=i, g=grad: self.jog(a, g, True)).pack(side="left", padx=4)
        self.log = tk.Text(tests, height=16, background="#12332f", foreground="#e4efea", font=("Consolas", 10), state="disabled", wrap="word")
        self.log.pack(fill="both", expand=True)
        ttk.Label(self, textvariable=self.meldung, padding=(18, 12), wraplength=1100).pack(fill="x")

    def protokoll(self, text):
        self.meldung.set(text)
        self.log.config(state="normal")
        self.log.insert("end", f"{datetime.now():%H:%M:%S}  {text}\n")
        if int(self.log.index("end-1c").split(".")[0]) > 500:
            self.log.delete("1.0", "100.0")
        self.log.see("end")
        self.log.config(state="disabled")

    def einstellungen(self):
        werte = {key: float(self.werte[key].get().replace(",", ".")) for key in STANDARD}
        grenzen = {"breite": (-90,90), "laenge": (-180,180), "utc": (-12,14), "az_null": (0,360), "el_null": (-90,90)}
        for key, wert in werte.items():
            if not math.isfinite(wert) or not grenzen[key][0] <= wert <= grenzen[key][1]:
                raise ValueError(f"Ungültiger Wert für {key}")
        return werte

    def einstellung_geaendert(self, *_):
        self.stopp()
        self.ausrichtung.set(False)

    def freigabe_fehler(self):
        if not self.link or not self.link.bereit or not self.pruefstatus:
            return "ESP32 mit Firmware 0.3.1 verbinden"
        n = self.pruefstatus
        if n["switch_test"] != 4:
            if n["switch_testing"]:
                axis = 0 if n["switch_test"] < 2 else 1
                name = "Azimut" if axis == 0 else "Elevation"
                phase = ZUSTAENDE[self.achsen[axis]["state"]]
                return f"Automatischer Test {n['switch_test']}/4: {name} - {phase}; bitte keine Schalter von Hand druecken"
            return "Automatischen Endschaltertest starten (Azimut und Elevation fahren los)"
        if any(not a["calibrated"] or not a["referenced"] for a in self.achsen):
            return "Beide Achsen kalibrieren bzw. gespeicherte Position referenzieren"
        if any(not a["limits_ok"] for a in self.achsen):
            return "Grenztests für Azimut und Elevation durchführen"
        if not self.grenzen_gesehen.get():
            return "Beobachteten 10°-Abstand im Testfeld bestätigen"
        if not self.ausrichtung.get():
            return "Standort und geografische Ausrichtung unter Einstellungen prüfen und bestätigen"
        if any(a["min"] or a["max"] for a in self.achsen):
            return "Endschalter aktiv – Start gesperrt"
        return None

    def pruefanzeige(self):
        fehler = self.freigabe_fehler()
        self.prueftext.set("Start gesperrt: " + fehler if fehler else "Prüfungen OK: Endschalter · Kalibrierung · Grenzen · Ausrichtung")
        self.sim_taste.config(state="disabled" if fehler or self.modus != "Pause" or self.auftrag else "normal")

    def schalterpruefung(self):
        def ausfuehren():
            self.voraussetzungen(False)
            self.modus = "Pause"
            self.grenzen_gesehen.set(False)
            self.auftrag = self.link.senden("SWTEST")
            self.bestaetigt = False
            self.protokoll("Automatischer Endschaltertest: Azimut, danach Elevation; beide Endlagen mit 10 Grad Entlastung.")
        self.aktion(ausfuehren)

    def grenzpruefung(self, achse):
        def ausfuehren():
            self.voraussetzungen(False)
            if not self.pruefstatus or self.pruefstatus["switch_test"] != 4:
                raise ValueError("Zuerst alle vier Endschalter prüfen")
            if messagebox.askyesno("Grenztest", "Diese Achse fährt zur sicheren MIN-Position, zu MAX und zurück zu MIN.\n\nBeobachte, ob sie jeweils 10° vor den Schaltern hält. Test jetzt starten?"):
                self.modus = "Pause"
                self.grenzen_gesehen.set(False)
                self.senden("LIMIT", achse)
        self.aktion(ausfuehren)

    def grenzen_bestaetigen(self):
        if not self.achsen or any(not a["limits_ok"] for a in self.achsen):
            self.grenzen_gesehen.set(False)
            self.protokoll("Zuerst beide Grenztests erfolgreich abschließen.")
        self.pruefanzeige()

    def speichern(self):
        try:
            daten = self.einstellungen()
            pfad = ORDNER / "einstellungen.json"
            temp = pfad.with_suffix(".tmp")
            temp.write_text(json.dumps({"version": 1, **daten}, indent=2), encoding="utf-8")
            temp.replace(pfad)
            self.protokoll("Standort und Ausrichtung gespeichert.")
        except (ValueError, OSError) as exc:
            messagebox.showerror("Einstellungen", str(exc))

    def laden(self):
        self.stopp()
        try:
            pfad = ORDNER / "einstellungen.json"
            daten = json.loads(pfad.read_text(encoding="utf-8")) if pfad.exists() else STANDARD
            if not isinstance(daten, dict) or daten.get("version", 1) != 1:
                raise ValueError("Unbekannte Einstellungsdatei")
            vorher = {key: self.werte[key].get() for key in STANDARD}
            try:
                for key in STANDARD:
                    self.werte[key].set(str(daten.get(key, STANDARD[key])))
                self.einstellungen()
            except (ValueError, TypeError):
                for key, wert in vorher.items():
                    self.werte[key].set(wert)
                raise ValueError("Einstellungsdatei enthält ungültige Werte")
            self.ausrichtung.set(False)
        except (ValueError, OSError) as exc:
            self.protokoll(f"Einstellungen konnten nicht geladen werden: {exc}")

    def ports_lesen(self):
        try:
            from serial.tools import list_ports
            ports = [p.device for p in list_ports.comports()]
            self.portwahl["values"] = ports
            if ports and self.port.get() not in ports:
                self.port.set(ports[0])
        except ImportError:
            self.protokoll("pyserial fehlt: Einrichtung.ps1 ausführen. Tagesgrafik ist verfügbar.")

    def umschalten(self):
        if self.link:
            self.trennen()
            return
        try:
            self.link = Verbindung()
            self.link.oeffnen(self.port.get())
            self.status.set("Firmware wird geprüft …")
            self.verbinden_taste.config(text="Trennen")
        except Exception as exc:
            self.trennen()
            self.protokoll(f"Verbindung fehlgeschlagen: {exc}")

    def trennen(self):
        self.modus = "Pause"
        self.auftrag = None
        if self.link:
            try:
                self.link.schliessen()
            except Exception:
                pass
        self.link = None
        self.achsen = None
        self.pruefstatus = None
        self.rtc_gesendet = False
        self.grenzen_gesehen.set(False)
        self.rtctext.set("RTC: Verbindung getrennt; Modul läuft mit Batterie weiter")
        self.status.set("Offline · Tagesgrafik verfügbar")
        self.verbinden_taste.config(text="Verbinden")
        for label in self.achslabels:
            label.set("Nicht verbunden – Position unbekannt")
        self.schaltertext.set("Endschalter: kein Status")

    def stopp(self):
        self.modus = "Pause"
        self.auftrag = None
        if self.link:
            try:
                self.link.senden("STOP")
            except Exception as exc:
                self.trennen()
                self.protokoll(str(exc))

    def voraussetzungen(self, referenz=True):
        if not self.link or not self.link.bereit or self.achsen is None:
            raise ValueError("Zuerst den ESP32 mit PCSteuerung-Firmware verbinden")
        if self.auftrag or (self.pruefstatus and self.pruefstatus["switch_testing"]) or any(a["state"] != 0 for a in self.achsen):
            raise ValueError("Eine Bewegung läuft noch")
        if referenz and any(not a["referenced"] for a in self.achsen):
            raise ValueError("Beide Achsen zuerst kalibrieren und referenzieren")

    def senden(self, cmd, achse, wert=None):
        self.voraussetzungen(False)
        args = ["AZ" if achse == 0 else "EL"]
        if wert is not None:
            args.append(f"{wert:.5f}")
        self.auftrag = self.link.senden(cmd, *args)
        self.bestaetigt = False
        self.protokoll(f"Gesendet: {cmd} {' '.join(args)}")

    def aktion(self, funktion):
        try:
            funktion()
        except Exception as exc:
            self.protokoll(str(exc))
            messagebox.showerror("Aktion nicht möglich", str(exc))

    def jog(self, achse, grad, test=False):
        def ausfuehren():
            self.voraussetzungen(False)
            if not test and not self.achsen[achse]["referenced"]:
                raise ValueError("Achse nicht referenziert. Zuerst Richtungstest/Kalibrierung verwenden.")
            self.modus = "Pause"
            self.senden("JOG", achse, grad)
        self.aktion(ausfuehren)

    def grenze(self, achse, oben):
        def ausfuehren():
            self.voraussetzungen(False)
            a = self.achsen[achse]
            if not a["referenced"]:
                raise ValueError("Achse zuerst referenzieren")
            self.modus = "Pause"
            self.senden("MOVE", achse, ((a["span"]-a["margin"]) if oben else a["margin"]) * 360/4096)
        self.aktion(ausfuehren)

    def kalibrieren(self, achse):
        def ausfuehren():
            self.voraussetzungen(False)
            if not self.pruefstatus or self.pruefstatus["switch_test"] != 4:
                raise ValueError("Zuerst Endschalterprüfung im Testfeld abschließen")
            if messagebox.askyesno("Kalibrierung", "Richtung und beide Endschalter dieser Achse getestet?\n\nDie Achse fährt jetzt MIN und MAX an und entlastet jeweils um 10°. Die bisherige Kalibrierung dieser Achse wird ersetzt."):
                self.modus = "Pause"
                self.senden("CAL", achse)
        self.aktion(ausfuehren)

    def referenz(self, achse):
        def ausfuehren():
            self.voraussetzungen(False)
            if messagebox.askyesno("Tatsächliche Position bestätigen", "Steht die Achse genau auf der zuvor markierten sicheren Startposition (10° nach mechanischem MIN)?\n\nNur bestätigen, wenn das Panel tatsächlich dort steht. Diese Taste fährt den Motor nicht."):
                self.modus = "Pause"
                self.senden("REF", achse)
        self.aktion(ausfuehren)

    def sim_startzeit(self):
        return datetime.now().astimezone()

    def grafik_berechnen(self):
        try:
            werte = self.einstellungen()
            start = self.simzeit.replace(hour=0, minute=0, second=0, microsecond=0)
            self.kurve = [(minute/60, *sonnenstand(start + timedelta(minutes=minute), werte["breite"], werte["laenge"])) for minute in range(0,1441,10)]
            self.zeichnen()
        except ValueError as exc:
            self.protokoll(f"Grafik: {exc}")

    def starten(self, modus):
        def ausfuehren():
            self.einstellungen()
            self.voraussetzungen()
            fehler = self.freigabe_fehler()
            if fehler:
                raise ValueError(fehler)
            self.simzeit = self.sim_startzeit()
            if modus == "Simulation":
                tempo = float(self.werte["tempo"].get())
                if not math.isfinite(tempo) or not 1 <= tempo <= 3600:
                    raise ValueError("Simulationstempo muss zwischen 1 und 3600 liegen")
                self.simzeit = self.sim_startzeit()
                self.grafik_berechnen()
            self.modus = modus
            self.tickzeit = time.monotonic()
            self.protokoll(f"{modus} gestartet – Grafik und echtes Panel, Startzeit vom PC")
        self.aktion(ausfuehren)

    def zeichnen(self):
        c = self.canvas
        c.delete("all")
        w, h = max(c.winfo_width(), 600), max(c.winfo_height(), 220)
        links, rechts, oben, unten = 48, w-48, 24, h-36
        x = lambda stunde: links + stunde/24*(rechts-links)
        yaz = lambda grad: unten-grad/360*(unten-oben)
        yel = lambda grad: unten-(grad+90)/180*(unten-oben)
        for stunde in range(0,25,3):
            c.create_line(x(stunde), oben, x(stunde), unten, fill="#29514a")
            c.create_text(x(stunde), unten+18, text=f"{stunde:02}:00", fill="#d5e6dd")
        for grad in range(0,361,90):
            y = yaz(grad)
            c.create_line(links,y,rechts,y,fill="#29514a")
            c.create_text(links-24,y,text=f"{grad}°",fill="#f4c76b")
            c.create_text(rechts+24,y,text=f"{grad/2-90:g}°",fill="#61dcc5")
        for vorher, jetzt in zip(self.kurve, self.kurve[1:]):
            if abs(vorher[1]-jetzt[1]) < 180:
                c.create_line(x(vorher[0]),yaz(vorher[1]),x(jetzt[0]),yaz(jetzt[1]),fill="#f4c76b",width=2)
            c.create_line(x(vorher[0]),yel(vorher[2]),x(jetzt[0]),yel(jetzt[2]),fill="#61dcc5",width=2)
        t = self.simzeit.hour + self.simzeit.minute/60 + self.simzeit.second/3600
        c.create_line(x(t),oben,x(t),unten,fill="white",dash=(4,3),width=2)

    def empfangen(self, n):
        if n["type"] == "event":
            self.modus = "Pause"
            self.protokoll("ESP32: " + str(n.get("message", "Ereignis")))
        elif n["type"] == "fault" or (n["type"] == "ack" and not n["ok"]):
            self.stopp()
            text = "ESP32: " + str(n.get("message", "Fehler"))
            if "axis" in n:
                achse = {"az": "Azimut", "el": "Elevation"}.get(n["axis"], n["axis"])
                phase = n.get("phase")
                phasentext = ZUSTAENDE[phase] if type(phase) is int and 0 <= phase < len(ZUSTAENDE) else "unbekannt"
                richtung = "MAX" if n.get("direction", 0) > 0 else "MIN"
                text += f" | {achse}: {phasentext}, Richtung {richtung}, Schritte {n.get('steps', '?')}, MIN={n.get('min', '?')}, MAX={n.get('max', '?')}"
            self.protokoll(text)
        elif n["type"] == "ack" and n["id"] == self.auftrag:
            self.bestaetigt = True
        elif n["type"] == "status":
            self.achsen = n["axes"]
            self.pruefstatus = n
            if any(not a["limits_ok"] for a in self.achsen):
                self.grenzen_gesehen.set(False)
            if n["rtc_valid"]:
                rtczeit = datetime.fromtimestamp(n["rtc_epoch"], timezone.utc).astimezone()
                self.rtctext.set(f"DS3231: {rtczeit:%d.%m.%Y %H:%M:%S %z}")
            else:
                self.rtctext.set("DS3231: Zeit ungültig" if n["rtc_present"] else "DS3231: nicht erreichbar")
            if self.link.bereit and not self.rtc_gesendet:
                self.rtc_gesendet = True
                self.link.senden("TIME", int(time.time()))
            if self.link.bereit:
                self.status.set(f"Verbunden · {self.port.get()} · ESP32 {n['version']}")
            for i, a in enumerate(self.achsen):
                position = f"{a['position']*360/4096:.1f}°" if a["referenced"] else "Position unbekannt"
                kal = "kalibriert" if a["calibrated"] else "nicht kalibriert"
                self.achslabels[i].set(f"{position}  ·  {ZUSTAENDE[a['state']]}\n{kal}")
            self.schaltertext.set("   |   ".join(f"{name}: {'GEDRÜCKT' if self.achsen[i][key] else 'offen'}" for i,key,name in ((0,"min","Az MIN"),(0,"max","Az MAX"),(1,"min","El MIN"),(1,"max","El MAX"))))
            if self.bestaetigt and not n["switch_testing"] and all(a["state"] == 0 for a in self.achsen):
                self.auftrag = None

    def nachfuehren(self, az, el, werte):
        if self.auftrag or (self.pruefstatus and self.pruefstatus["switch_testing"]) or any(a["state"] != 0 for a in self.achsen):
            return
        if el <= 0:
            self.meldung.set("Sonne unter dem Horizont – keine Fahrt.")
            return
        ziele = [motorziel(az, werte["az_null"], self.achsen[0], True), motorziel(el, werte["el_null"], self.achsen[1])]
        for i in (self.naechste_achse, 1-self.naechste_achse):
            ziel = ziele[i]
            if abs(ziel-self.achsen[i]["position"]*360/4096) >= 0.25:
                self.senden("AUTO", i, ziel)
                self.naechste_achse = 1-i
                break

    def tick(self):
        jetzt = time.monotonic()
        dt = jetzt-self.tickzeit
        self.tickzeit = jetzt
        try:
            if self.link:
                for nachricht in self.link.lesen():
                    self.empfangen(nachricht)
        except Exception as exc:
            self.trennen()
            self.protokoll(f"Verbindung beendet: {exc}")
        try:
            if self.modus == "Simulation":
                tempo = float(self.werte["tempo"].get())
                if not math.isfinite(tempo) or not 1 <= tempo <= 3600:
                    raise ValueError("Simulationstempo: 1 bis 3600")
                # Grafik wartet bei laufender Fahrt auf das Panel, statt davonzulaufen.
                wartet = self.auftrag or (self.achsen and any(a["state"] != 0 for a in self.achsen))
                neu = self.simzeit + timedelta(seconds=0 if wartet else dt*tempo)
                if neu.date() != self.simzeit.date():
                    self.stopp()
                    self.protokoll("Simulation am Tagesende beendet.")
                else:
                    self.simzeit = neu
            elif self.modus == "Normalbetrieb":
                self.simzeit = datetime.now().astimezone()
            if jetzt-self.regelzeit >= 0.5:
                self.regelzeit = jetzt
                self.pcuhr.set(f"PC-Zeit: {datetime.now().astimezone():%d.%m.%Y %H:%M:%S %z} · Startzeit wird beim Start übernommen")
                self.pruefanzeige()
                werte = self.einstellungen()
                az, el = sonnenstand(self.simzeit, werte["breite"], werte["laenge"])
                self.sonnenziel = (az,el)
                self.zeittext.set(f"{self.modus}  ·  {self.simzeit:%d.%m.%Y  %H:%M:%S %z}  ·  Az {az:.1f}° / El {el:.1f}°")
                self.sonnentext.set(f"Sonnenposition: Azimut {az:.1f}°  ·  Elevation {el:.1f}°")
                self.zeichnen()
                if self.modus in ("Normalbetrieb", "Simulation"):
                    if not self.link or not self.link.bereit or not self.ausrichtung.get():
                        raise ValueError("Sonnenfahrt: Verbindung oder Ausrichtung fehlt")
                    fehler = self.freigabe_fehler()
                    if fehler:
                        raise ValueError(fehler)
                    self.nachfuehren(az,el,werte)
        except (ValueError, OverflowError, OSError) as exc:
            if self.modus != "Pause":
                self.stopp()
                self.protokoll(f"Betrieb angehalten: {exc}")
        self.after(50, self.tick)

    def exportieren(self):
        pfad = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV-Tabelle", "*.csv")])
        if pfad:
            try:
                Path(pfad).write_text("Stunde;Sonnenazimut_Grad;Sonnenhoehe_Grad\n" + "\n".join(f"{t:.4f};{az:.4f};{el:.4f}" for t,az,el in self.kurve), encoding="utf-8-sig")
                self.protokoll("Tageskurve als CSV gespeichert.")
            except OSError as exc:
                messagebox.showerror("Export", str(exc))

    def beenden(self):
        self.trennen()
        self.destroy()


if __name__ == "__main__":
    Bedienfeld().mainloop()
