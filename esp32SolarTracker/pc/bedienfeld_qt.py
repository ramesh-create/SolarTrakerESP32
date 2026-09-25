"""SolarTracker 0.7.5: Benutzervorlage Design 1 mit echter ESP32-Anbindung.

Start: python bedienfeld_qt.py. Firmware 0.4.0 / Protokoll 3: Positionen und Tests bleiben gespeichert.
"""
import sys
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QShortcut, QKeySequence
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QCheckBox, QDoubleSpinBox,
    QPlainTextEdit, QLineEdit, QMessageBox, QScrollArea, QFileDialog, QStackedWidget)
from serial.tools import list_ports
from design_basis import DesignFenster
from steuerzentrale import Steuerzentrale, STANDARD, PHASEN, grenztest_fehler, status_text
from sonne import sonnenstand
from tageslauf import sonnenfenster, aktuelles_sonnenfenster, panelneigung
from weltkarte import Weltkarte
from globus import Globus
from orte import vorschlag, zonenversatz

VERSION = "0.7.5"
ORDNER = Path(__file__).resolve().parent


class Tagesgrafik(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(440,210)
        self.punkte = []
        self.zeit = datetime.now().astimezone()
        self.beginn, self.ende = 0, 24
        self.hinweis = ""

    def berechnen(self, zeit, werte):
        self.zeit = zeit
        try:
            auf, unter = sonnenfenster(zeit,werte["breite"],werte["laenge"])
            stunde = lambda t: t.hour+t.minute/60+t.second/3600+t.microsecond/3600000000
            self.beginn,self.ende = stunde(auf),stunde(unter)
            zeiten = [auf+(unter-auf)*i/144 for i in range(145)]
            self.punkte = [(stunde(t),*sonnenstand(t,werte["breite"],werte["laenge"])) for t in zeiten]
            self.hinweis = ""
        except ValueError as exc:
            self.punkte = []
            self.hinweis = str(exc)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w,h = self.width(),self.height()
        x = lambda t: 38+(t-self.beginn)/max(0.01,self.ende-self.beginn)*(w-76)
        y = lambda a: h-30-a/360*(h-50)
        p.setFont(QFont("Segoe UI",8))
        if self.hinweis:
            p.setPen(QColor("#97a8bb"))
            p.drawText(self.rect(),Qt.AlignCenter | Qt.TextWordWrap,self.hinweis)
            return
        for i in range(7):
            t=self.beginn+(self.ende-self.beginn)*i/6
            p.setPen(QColor("#263546")); p.drawLine(int(x(t)),20,int(x(t)),h-30)
            minute=round(t*60)
            p.setPen(QColor("#97a8bb")); p.drawText(int(x(t))-18,h-8,f"{minute//60:02}:{minute%60:02}")
        for a in range(0,361,90):
            p.setPen(QColor("#263546")); p.drawLine(38,int(y(a)),w-38,int(y(a)))
            p.setPen(QColor("#3aa6ff")); p.drawText(0,int(y(a))+4,str(a))
            p.setPen(QColor("#ffb347")); p.drawText(w-32,int(y(a))+4,f"{a/4:g}")
        for v,n in zip(self.punkte,self.punkte[1:]):
            if abs(v[1]-n[1]) < 180:
                p.setPen(QPen(QColor("#3aa6ff"),2))
                p.drawLine(int(x(v[0])),int(y(v[1])),int(x(n[0])),int(y(n[1])))
            p.setPen(QPen(QColor("#ffb347"),2))
            p.drawLine(int(x(v[0])),int(y(max(0,v[2])*4)),int(x(n[0])),int(y(max(0,n[2])*4)))
        t=self.zeit.hour+self.zeit.minute/60+self.zeit.second/3600
        if self.beginn <= t <= self.ende:
            p.setPen(QPen(QColor("#e7edf5"),1,Qt.DashLine)); p.drawLine(int(x(t)),20,int(x(t)),h-30)


class Bedienpanel(DesignFenster):
    def __init__(self,datenordner=ORDNER):
        self.meldungen = []
        self.motor_controls = {}
        self.datenordner=Path(datenordner)
        self.core = Steuerzentrale(self.protokoll,speicherpfad=self.datenordner/"betrieb.json")
        self.hold_axis = None
        self.hold_direction = 0
        self.refresh_count = 0
        self.anzeige_bereit = False
        super().__init__()
        self.setStyleSheet(self.styleSheet()+"\nQLabel { background: transparent; } QPushButton:disabled { color: #697b8e; background: #151b24; border-color: #263546; }")
        self.setWindowTitle(f"SolarTracker • Design 1 • {VERSION}")
        screen = QApplication.primaryScreen().availableGeometry()
        self.setMinimumSize(min(1050,screen.width()-20),min(650,screen.height()-20))
        self.resize(min(1450,screen.width()-40),min(900,screen.height()-60))
        self.operation_info.setText("NOAA-Nachführung mit PC-Zeit. Motorpositionen und Endschalter werden vom ESP32 gemeldet. Start erst nach bestandenen Prüfungen.")
        self.operation_info.setWordWrap(True)
        self.time_edit.setReadOnly(True); self.date_edit.setReadOnly(True)
        try:
            self.core.laden(self.datenordner/"einstellungen.json")
        except (OSError,ValueError,TypeError) as exc:
            self.protokoll(f"Einstellungen: {exc}")
        self.lat.setValue(self.core.werte["breite"]); self.lon.setValue(self.core.werte["laenge"])
        self.az_null.setValue(self.core.werte["az_null"]); self.el_null.setValue(self.core.werte["el_neigung"])
        self.land.setText(self.core.werte.get("land","")); self.stadt.setText(self.core.werte.get("stadt",""))
        self.zeitzone.setValue(self.core.werte.get("zeitzone",0.0))
        for widget in (self.lat,self.lon,self.az_null,self.el_null):
            widget.valueChanged.connect(self.einstellung_geaendert)
        self.lat.valueChanged.connect(self.ortspruefung)
        self.lon.valueChanged.connect(self.ortspruefung)
        self.ausrichtung.stateChanged.connect(self.ausrichtung_geaendert)
        self.anzeige_bereit = True
        self.ortspruefung()
        self.scan_ports()
        self.chart.berechnen(self.core.simzeit,self.core.werte)
        self.timer = QTimer(self); self.timer.timeout.connect(self.tick); self.timer.start(50)
        self.esc = QShortcut(QKeySequence("Escape"),self); self.esc.activated.connect(self.stop_all)
        QApplication.instance().applicationStateChanged.connect(self.app_state)
        self.update_all_status()

    def build_ui(self):
        super().build_ui()
        nav=self.centralWidget().layout().itemAt(0).widget().layout()
        stelle=nav.indexOf(self.btn_test)+1
        nav.insertWidget(stelle,self.stop_btn)
        nav.insertWidget(stelle+1,self.log,1)
        self.seitenbreite_anpassen(self.width())
        # Die Vorlage bleibt dreispaltig; Seiten sind auf kleineren Monitoren scrollbar.
        for i in range(self.pages.count()):
            if i == 3:
                continue  # Testauswahl und Zurueck bleiben ausserhalb des Scrollbereichs.
            page = self.pages.widget(i)
            self.pages.removeWidget(page)
            scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QScrollArea.NoFrame)
            scroll.setWidget(page); self.pages.insertWidget(i,scroll)
        self.pages.setCurrentIndex(0)
        self.pages.currentChanged.connect(lambda _: self.stop_hold() if self.hold_axis is not None else None)

    def resizeEvent(self,event):
        super().resizeEvent(event)
        if hasattr(self,"stop_btn"):
            self.seitenbreite_anpassen(event.size().width())

    def seitenbreite_anpassen(self,breite):
        kompakt=breite<1150
        if getattr(self,"_kompakt",None)==kompakt:
            return
        self._kompakt=kompakt
        haupt=self.centralWidget().layout()
        nav=haupt.itemAt(0).widget()
        nav.setFixedWidth(180 if kompakt else 240)
        nav.layout().setContentsMargins(10 if kompakt else 20,10 if kompakt else 20,10 if kompakt else 20,10 if kompakt else 20)
        nav.layout().setSpacing(6 if kompakt else 12)
        for label in nav.findChildren(QLabel):
            if label.text()=="PC BEDIENPANEL" or label.text().startswith("Design 1"):
                label.setVisible(not kompakt)
        self.stop_btn.setMinimumHeight(44 if kompakt else 52)
        self.log.setMinimumHeight(60 if kompakt else 100)
        for btn in (self.btn_oper,self.btn_sim,self.btn_settings,self.btn_test):
            btn.setMinimumHeight(40 if kompakt else 52)
            btn.setStyleSheet("font-size: 13px; padding: 8px;" if kompakt else "")
        haupt.itemAt(haupt.count()-1).widget().setFixedWidth(240 if kompakt else 300)
        self.port_combo.setFixedWidth(90 if kompakt else 110)
        self.scan_btn.setText("Ports" if kompakt else "Ports suchen")
        for btn in (self.scan_btn,self.connect_btn):
            btn.setStyleSheet("font-size: 12px; padding: 8px 6px;" if kompakt else "")

    def build_topbar(self):
        frame = super().build_topbar()
        frame.layout().itemAt(0).widget().hide()
        scan = QPushButton("Ports suchen"); self.scan_btn=scan; scan.setToolTip("Verfuegbare serielle Ports suchen"); scan.clicked.connect(self.scan_ports)
        frame.layout().insertWidget(3,scan)
        return frame

    def build_right_status(self):
        frame = super().build_right_status()
        layout = frame.layout()
        teile=[]
        while layout.count():
            item=layout.takeAt(0)
            if item.widget(): teile.append(item.widget())
        titel,modus,az,el,position=teile
        self.az_value.setWordWrap(True); self.el_value.setWordWrap(True); self.endstop_status.setWordWrap(True)
        titel.setText("LIVE POSITION")
        layout.addWidget(titel); layout.addWidget(modus)
        self.stop_btn=QPushButton("STOPP / ESC")
        self.stop_btn.setObjectName("danger"); self.stop_btn.setMinimumHeight(52)
        self.stop_btn.clicked.connect(self.stop_all)
        self.log=QPlainTextEdit(); self.log.setReadOnly(True); self.log.setMaximumBlockCount(400)
        self.log.setMinimumHeight(120); self.log.setMaximumHeight(180)
        self.log.setPlaceholderText("Protokoll: Verbindung, Fahrbefehle und Fehler")
        # STOP und Protokoll werden unter Komponententest in die linke Leiste eingesetzt.
        status=QWidget(); sl=QVBoxLayout(status); sl.setContentsMargins(0,0,0,0)
        sl.addWidget(az); sl.addWidget(el); sl.addWidget(position)
        self.freigabe_label=QLabel(); self.freigabe_label.setWordWrap(True)
        sl.addWidget(self.freigabe_label); sl.addStretch()
        scroll=QScrollArea(); scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setWidgetResizable(True); scroll.setWidget(status)
        layout.addWidget(scroll,1)
        self.weltkarte_klein=Weltkarte(kompakt=True)
        layout.addWidget(self.weltkarte_klein)
        return frame

    def page_simulation(self):
        page=QWidget(); layout=QVBoxLayout(page)
        title=QLabel("Simulation"); title.setObjectName("h1"); layout.addWidget(title)
        card=self.card(); cl=QVBoxLayout(card)
        cl.addWidget(self.section_title("Simulationsstufe auswählen"))
        row=QHBoxLayout(); self.sim_buttons=[]
        for sec in (30,60,120):
            btn=QPushButton(f"{sec} s*"); btn.setMinimumHeight(60)
            btn.clicked.connect(lambda checked=False,s=sec:self.start_simulation(s))
            row.addWidget(btn); self.sim_buttons.append(btn)
        cl.addLayout(row)
        tempo_row=QHBoxLayout(); tempo_row.addWidget(QLabel("Eigene Geschwindigkeit ×"))
        self.tempo=QDoubleSpinBox(); self.tempo.setRange(1,3600); self.tempo.setValue(60)
        tempo_row.addWidget(self.tempo)
        cl.addLayout(tempo_row)
        self.sim_start=QPushButton("Simulation starten · Grafik + Panel"); self.sim_start.setObjectName("primary")
        self.sim_start.clicked.connect(lambda:self.start_simulation(None)); cl.addWidget(self.sim_start)
        self.sim_neu=QPushButton("Neuen Sonnentag starten")
        self.sim_neu.clicked.connect(lambda:self.start_simulation(None,neu=True)); cl.addWidget(self.sim_neu)
        self.sim_status=QLabel("Simulation gesperrt: Prüfungen erforderlich"); self.sim_status.setWordWrap(True)
        self.sim_status.setObjectName("bigStatus"); cl.addWidget(self.sim_status)
        self.sim_progress=QLabel(); self.sim_progress.setWordWrap(True); cl.addWidget(self.sim_progress)
        stop=QPushButton("Simulation pausieren / STOP"); stop.setObjectName("danger"); stop.clicked.connect(self.stop_all); cl.addWidget(stop)
        layout.addWidget(card)
        self.chart=Tagesgrafik(); layout.addWidget(self.chart,1)
        self.weltkarte_gross=Weltkarte()
        self.weltkarte_gross.set_bearbeitbar(True)
        self.weltkarte_gross.ortGeaendert.connect(self.standort_aus_karte)
        self.globus=Globus()
        self.globus.ortGeaendert.connect(self.standort_aus_karte)
        self.ansicht_stack=QStackedWidget()
        self.ansicht_stack.addWidget(self.weltkarte_gross)
        self.ansicht_stack.addWidget(self.globus)
        umschalt=QHBoxLayout()
        self.btn_karte=QPushButton("Karte"); self.btn_globus=QPushButton("Globus")
        self.btn_karte.clicked.connect(lambda:self.ansicht_stack.setCurrentIndex(0))
        self.btn_globus.clicked.connect(lambda:self.ansicht_stack.setCurrentIndex(1))
        umschalt.addWidget(self.btn_karte); umschalt.addWidget(self.btn_globus); umschalt.addStretch()
        layout.addLayout(umschalt)
        kartenbereich=QWidget(); grid=QGridLayout(kartenbereich); grid.setContentsMargins(0,0,0,0)
        grid.addWidget(self.ansicht_stack,0,0)
        self.reset_btn=QPushButton("Ansicht zurücksetzen")
        self.reset_btn.setObjectName("primary")
        self.reset_btn.setToolTip("Zoom und Drehung von Karte/Globus zurücksetzen")
        self.reset_btn.clicked.connect(self.ansicht_reset)
        grid.addWidget(self.reset_btn,0,0,Qt.AlignRight|Qt.AlignBottom)
        layout.addWidget(kartenbereich)
        self.ort_btn=QPushButton("Ort aus Koordinaten übernehmen")
        self.ort_btn.setToolTip("Setzt Land/Stadt auf den naechstgelegenen Ort (offline, Natural Earth) und die Zeitzone aus der Laenge")
        self.ort_btn.clicked.connect(self.ort_vorschlagen)
        layout.addWidget(self.ort_btn)
        note=QLabel("Nur Sonnenstunden des heutigen PC-Datums. Blau: Sonnenazimut, Orange: Sonnenhoehe (0-90 Grad).\nZuerst sichere MIN, dann Sonnenlauf, bei Sonnenuntergang Rueckfahrt zu beiden MIN.\n*Fahrzeiten kommen hinzu. Unerreichbare Sonnenziele werden an den sicheren Grenzen begrenzt.")
        note.setWordWrap(True); layout.addWidget(note)
        export=QPushButton("Tageskurve als CSV speichern"); export.clicked.connect(self.export_csv); layout.addWidget(export)
        return page

    def page_settings(self):
        page=super().page_settings()
        extra=self.card(); lay=QGridLayout(extra)
        self.az_null=QDoubleSpinBox(); self.az_null.setRange(0,360); self.az_null.setDecimals(2)
        self.el_null=QDoubleSpinBox(); self.el_null.setRange(0,180); self.el_null.setDecimals(2)
        lay.addWidget(QLabel("Kompasswinkel an sicherer AZ-MIN (Osten = 90 Grad)"),0,0); lay.addWidget(self.az_null,0,1)
        lay.addWidget(QLabel("Panelneigung an sicherer EL-MIN (senkrecht = 90 Grad)"),1,0); lay.addWidget(self.el_null,1,1)
        self.ausrichtung=QCheckBox("Ausrichtung geprueft: AZ+ nach Westen, EL+ kippt Richtung waagerecht")
        lay.addWidget(self.ausrichtung,2,0,1,2)
        self.auto_cal_btn=QPushButton("Auto Kalibrierung")
        self.auto_cal_btn.clicked.connect(lambda:self.aktion(self.core.auto_kalibrierung))
        auto_card=self.card(); auto_lay=QVBoxLayout(auto_card)
        auto_lay.addWidget(self.auto_cal_btn)
        self.auto_cal_status=QLabel("LCD, RTC, alle Endlagen, Grenztests und Startposition pruefen")
        self.auto_cal_status.setWordWrap(True); auto_lay.addWidget(self.auto_cal_status)
        self.auto_mode_btn=QPushButton("Autonomer Betrieb starten")
        self.auto_mode_btn.clicked.connect(self.autonom_umschalten)
        auto_lay.addWidget(self.auto_mode_btn)
        self.auto_mode_status=QLabel("ESP32 fuehrt die Sonne ohne PC nach. Voraussetzung: bestandener Gesamttest, Referenz, Grenztests und gueltige RTC. Nachts Park an sicherer AZ-MIN/EL-MIN.")
        self.auto_mode_status.setWordWrap(True); auto_lay.addWidget(self.auto_mode_status)
        cal_row=QHBoxLayout(); self.cal_buttons=[]
        for i,name in enumerate(("AZ","EL")):
            b=QPushButton(f"{name} einzeln kalibrieren")
            b.clicked.connect(lambda checked=False,i=i:self.aktion(lambda:self.core.kalibrieren(i)))
            cal_row.addWidget(b); self.cal_buttons.append(b)
        auto_lay.addLayout(cal_row)
        hinweis=QLabel("Startet eine vollstaendige Neumessung beider Achsen. STOP/ESC bricht ab. LCD-Pruefung kontrolliert I2C und Textausgabe; sichtbare Zeichen bitte am Display pruefen.")
        hinweis.setWordWrap(True); auto_lay.addWidget(hinweis)
        page.layout().insertWidget(1,auto_card)
        conf_card=self.card(); conf_lay=QVBoxLayout(conf_card)
        conf_lay.addWidget(self.section_title("Standort/Ausrichtung im ESP32"))
        self.conf_btn=QPushButton("Konfiguration an ESP32 senden")
        self.conf_btn.clicked.connect(lambda:self.aktion(self.core.konfiguration_senden))
        conf_lay.addWidget(self.conf_btn)
        self.conf_status=QLabel("ESP32-Konfiguration: unbekannt")
        self.conf_status.setWordWrap(True); conf_lay.addWidget(self.conf_status)
        page.layout().insertWidget(2,conf_card)
        page.layout().addWidget(extra)
        return page

    def page_operation(self):
        page=super().page_operation()
        card=self.card(); lay=QVBoxLayout(card)
        lay.addWidget(self.section_title("Nachfuehrung (zentral)"))
        self.oper_auto_btn=QPushButton("Autonomer Betrieb starten")
        self.oper_auto_btn.setMinimumHeight(48)
        self.oper_auto_btn.clicked.connect(self.autonom_umschalten)
        lay.addWidget(self.oper_auto_btn)
        self.oper_auto_status=QLabel("Konfiguration und Autonomie zentral steuern.")
        self.oper_auto_status.setWordWrap(True); lay.addWidget(self.oper_auto_status)
        self.oper_target=QLabel("Sonnenziel: unbekannt")
        self.oper_target.setWordWrap(True); lay.addWidget(self.oper_target)
        konsole=QHBoxLayout()
        self.befehl_feld=QLineEdit(); self.befehl_feld.setPlaceholderText("Direktbefehl, z.B. STATUS, JOG AZ 5 oder JOG EL -5")
        konsole.addWidget(self.befehl_feld)
        self.befehl_btn=QPushButton("Senden")
        self.befehl_btn.clicked.connect(self.direktbefehl)
        konsole.addWidget(self.befehl_btn)
        lay.addLayout(konsole)
        page.layout().insertWidget(1, card)
        return page

    def direktbefehl(self):
        text=self.befehl_feld.text().strip()
        if not text:
            return
        self.aktion(lambda:self.core.befehl_senden(text))
        self.befehl_feld.clear()

    def page_component_test(self):
        page=super().page_component_test()
        # Originale sechs Auswahlkarten behalten. Jede Unterseite scrollt einzeln.
        self.test_stack.widget(0).layout().addStretch()
        layout=page.layout()
        titel=layout.takeAt(0).widget()
        kopf=QHBoxLayout(); kopf.addWidget(titel); kopf.addStretch()
        self.test_zurueck=QPushButton("Zur Auswahl")
        self.test_zurueck.setToolTip("Zur Komponentenauswahl")
        self.test_zurueck.clicked.connect(lambda:self.test_stack.setCurrentIndex(0))
        kopf.addWidget(self.test_zurueck); layout.insertLayout(0,kopf)
        for i in range(self.test_stack.count()):
            inhalt=self.test_stack.widget(i)
            self.test_stack.removeWidget(inhalt)
            # Doppelte Zurueck-Taste am Seitenende entfernen; oben bleibt sie sichtbar.
            for btn in inhalt.findChildren(QPushButton):
                if "Zur Komponentenauswahl" in btn.text():
                    btn.hide()
            scroll=QScrollArea(); scroll.setWidgetResizable(True)
            scroll.setFrameShape(QScrollArea.NoFrame); scroll.setWidget(inhalt)
            self.test_stack.insertWidget(i,scroll)
        self.test_beschreibung=layout.itemAt(1).widget()
        self.test_stack.setCurrentIndex(0)
        self.test_stack.currentChanged.connect(self.testseite_gewechselt)
        self.btn_test.clicked.connect(lambda:self.test_stack.setCurrentIndex(0))
        self.testseite_gewechselt(0)
        return page

    def testseite_gewechselt(self,index):
        self.test_zurueck.setVisible(index!=0)
        self.test_beschreibung.setVisible(index==0)
        scroll=self.test_stack.widget(index)
        if isinstance(scroll,QScrollArea):
            scroll.verticalScrollBar().setValue(0)
            scroll.horizontalScrollBar().setValue(0)

    def endstop_test_page(self):
        page=self.card(); lay=QVBoxLayout(page)
        lay.addWidget(self.section_title("Endschalter, Kalibrierung und Grenztests"))
        desc=QLabel("Automatisch: Azimut MIN/MAX → Elevation MIN/MAX. Nach jedem Kontakt 10° entlasten und Endlagen speichern.")
        desc.setWordWrap(True); lay.addWidget(desc)
        btn=QPushButton("Endschaltertest starten – AZ + EL"); btn.setObjectName("primary")
        btn.clicked.connect(lambda:self.aktion(self.core.endschaltertest)); lay.addWidget(btn)
        self.end_labels={}
        for key,name in (("az_min","Azimut MIN"),("az_max","Azimut MAX"),("el_min","Elevation MIN"),("el_max","Elevation MAX")):
            label=QLabel(name+": unbekannt"); self.end_labels[key]=label; lay.addWidget(label)
        self.pruef_details=QLabel(); self.pruef_details.setWordWrap(True); lay.addWidget(self.pruef_details)
        row=QHBoxLayout(); self.grenz_buttons=[]
        for index,name in enumerate(("Azimut","Elevation")):
            btn=QPushButton(f"Grenztest {name}")
            btn.clicked.connect(lambda checked=False,i=index:self.aktion(lambda:self.core.grenztest(i)))
            row.addWidget(btn); self.grenz_buttons.append(btn)
        lay.addLayout(row)
        row=QHBoxLayout(); self.ref_buttons=[]
        for index,name in enumerate(("Azimut","Elevation")):
            btn=QPushButton(f"{('AZ','EL')[index]}: Referenz wiederherstellen")
            btn.clicked.connect(lambda checked=False,i=index:self.referenz(i))
            row.addWidget(btn); self.ref_buttons.append(btn)
        lay.addLayout(row)
        hinweis=QLabel("Grenztests werden automatisch vom ESP32 bestaetigt. Referenz wiederherstellen ist nur bei verlorener Position erforderlich. STOP und Neuverbinden erhalten Positionen und Tests mit Firmware 0.4.0.")
        hinweis.setWordWrap(True); lay.addWidget(hinweis)
        self.grenzen=QCheckBox("10-Grad-Abstand geprueft (wird gespeichert)")
        self.grenzen.stateChanged.connect(self.grenzen_geaendert); lay.addWidget(self.grenzen)
        row=QHBoxLayout()
        refresh=QPushButton("Status abfragen"); refresh.clicked.connect(lambda:self.aktion(lambda:self.core.senden("STATUS"))); row.addWidget(refresh)
        copy=QPushButton("Diagnose kopieren"); copy.clicked.connect(self.copy_diagnose); row.addWidget(copy); lay.addLayout(row)
        self.back_button(lay); return page

    def rtc_test_page(self):
        page=self.card(); lay=QVBoxLayout(page); lay.addWidget(self.section_title("RTC DS3231"))
        self.rtc_value=QLabel("Noch nicht verbunden"); self.rtc_value.setObjectName("value"); lay.addWidget(self.rtc_value)
        for text,cb in (("RTC auslesen",self.read_rtc),("Echte PC-Zeit synchronisieren",lambda:self.aktion(self.core.rtc_setzen))):
            btn=QPushButton(text); btn.clicked.connect(cb); lay.addWidget(btn)
        note=QLabel("Anzeige aus dem ESP32-Status. Die DS3231 speichert UTC und läuft mit Batterie ohne PC weiter. Simulationszeit wird niemals übertragen.")
        note.setWordWrap(True); lay.addWidget(note); self.back_button(lay); return page

    def button_test_page(self):
        page=super().button_test_page()
        self.button_test_value.setText("Motorsteuerung: 5 Grad je Tastendruck")
        self.button_test_value.setObjectName("h2")
        self.button_test_value.setWordWrap(True)
        self.test_tasten={}
        for btn in page.findChildren(QPushButton):
            taste=btn.text()
            if taste in ("OBEN","UNTEN","LINKS","RECHTS","ENTER"):
                btn.clicked.disconnect()
                btn.clicked.connect(lambda checked=False,t=taste:self.bedientaste_fahren(t))
                self.test_tasten[taste]=btn
        self.test_tasten["ENTER"].setText("STOP / ENTER")
        self.test_tasten["ENTER"].setObjectName("danger")
        self.tasten_hinweis=QLabel("Links/rechts: Azimut -/+5 Grad. Oben/unten: Elevation +/-5 Grad. STOP/ENTER und Esc stoppen. Pro Klick eine begrenzte Fahrt.")
        self.tasten_hinweis.setWordWrap(True)
        page.layout().insertWidget(2,self.tasten_hinweis)
        return page

    def bedientaste_fahren(self,taste):
        if taste=="ENTER":
            self.stop_all()
            self.button_test_value.setText("STOP angefordert")
            return
        index,grad={"LINKS":(0,-5),"RECHTS":(0,5),"OBEN":(1,5),"UNTEN":(1,-5)}[taste]
        def action():
            try:
                self.core.manuell(index,grad,test=True)
                self.button_test_value.setText(f"{('Azimut','Elevation')[index]}: {grad:+d} Grad angefordert")
            except Exception as exc:
                self.button_test_value.setText(str(exc))
                raise
        self.aktion(action)

    def richtungstest_grund(self,index,grad):
        c=self.core
        if not c.bereit: return "Zuerst ESP32 verbinden"
        if c.beschaeftigt: return "Fahrt/Auftrag laeuft - Abschluss abwarten"
        a=c.status["axes"][index]
        if a["min"] and a["max"]: return "Beide Kontakte aktiv: Verkabelung pruefen"
        if a["referenced"]:
            ziel=a["position"]+round(grad*4096/360)
            if not a["margin"] <= ziel <= a["span"]-a["margin"]:
                return "Sichere Fahrgrenze: Gegenrichtung verwenden"
        return ""

    def motor_test_page(self,title,axis):
        page=super().motor_test_page(title,axis)
        buttons=page.findChildren(QPushButton)
        hinweis=QLabel(); hinweis.setWordWrap(True)
        page.layout().insertWidget(2,hinweis)
        self.motor_controls[0 if axis=="az" else 1]=(buttons[0],buttons[2],hinweis)
        return page

    def lcd_test_page(self):
        page=super().lcd_test_page()
        for edit in (self.lcd_line1,self.lcd_line2): edit.setMaxLength(16)
        self.lcd_send_btn=next(b for b in page.findChildren(QPushButton) if "Text ans LCD" in b.text())
        self.lcd_send_btn.clicked.disconnect()
        self.lcd_send_btn.clicked.connect(self.lcd_senden)
        preview=QPushButton("Nur PC-Vorschau aktualisieren")
        preview.clicked.connect(self.lcd_preview_only); page.layout().insertWidget(7,preview)
        self.lcd_status=QLabel(); self.lcd_status.setWordWrap(True); page.layout().insertWidget(1,self.lcd_status)
        return page

    def lcd_senden(self):
        def action():
            zeilen=self.core.lcd_senden(self.lcd_line1.text(),self.lcd_line2.text())
            self.lcd_preview.setText("\n".join(zeilen))
        self.aktion(action)

    def back_button(self,layout):
        btn=QPushButton("← Zur Komponentenauswahl"); btn.clicked.connect(lambda:self.test_stack.setCurrentIndex(0)); layout.addWidget(btn)
        layout.addStretch()

    def protokoll(self,text):
        line=f"{datetime.now():%H:%M:%S}  {text}"
        self.meldungen.append(line); self.meldungen=self.meldungen[-400:]
        if hasattr(self,"log"):
            self.log.appendPlainText(line); self.statusBar().showMessage(text,12000)

    def aktion(self,fn):
        try:
            fn()
        except Exception as exc:
            self.hold_axis=None
            self.protokoll(str(exc))
        self.update_all_status()

    def scan_ports(self):
        current=self.port_combo.currentText()
        ports=[p.device for p in list_ports.comports()]
        self.port_combo.clear(); self.port_combo.addItems(ports or ["COM3"])
        self.port_combo.setCurrentText(current if current in ports else (ports[0] if ports else "COM3"))

    def toggle_connection(self):
        def action():
            self.hold_axis=None
            if self.core.link: self.core.trennen()
            else: self.core.verbinden(self.port_combo.currentText())
        self.aktion(action)

    def toggle_operation(self):
        if self.core.modus=="Normalbetrieb": self.stop_all()
        else: self.aktion(lambda:self.core.starten("Normalbetrieb"))

    def start_simulation(self,duration,neu=False):
        def action():
            self.hold_axis=None
            tempo=self.tempo.value()
            if duration is not None:
                now=self.core.standort_zeit()
                auf,unter=aktuelles_sonnenfenster(now,self.core.werte["breite"],self.core.werte["laenge"])
                tempo=max(1,(unter-auf).total_seconds()/duration)
                self.tempo.setValue(tempo)
            self.core.starten("Simulation",tempo,neu=neu)
            self.chart.berechnen(self.core.simzeit,self.core.werte)
        self.aktion(action)

    def stop_all(self):
        self.hold_axis=None
        self.aktion(self.core.stopp)

    def autonom_umschalten(self):
        n=self.core.status
        laeuft=bool(n and n.get("auto_mode",False))
        def action():
            self.core.autonom(not laeuft)
        self.aktion(action)

    def bind_direction_button(self,button,axis,direction):
        button.clicked.connect(lambda checked=False:self.move_axis(axis,direction,10) if self.radio_step.isChecked() else None)
        button.pressed.connect(lambda:self.begin_hold(axis,direction))
        button.released.connect(self.stop_hold)

    def begin_hold(self,axis,direction):
        if self.radio_hold.isChecked():
            self.hold_axis=axis; self.hold_direction=direction

    def stop_hold(self):
        if self.hold_axis is not None:
            self.hold_axis=None; self.aktion(self.core.stopp)

    def move_axis(self,axis,direction,amount,test=False):
        self.aktion(lambda:self.core.manuell(0 if axis=="az" else 1,direction*amount,test))

    def einstellung_geaendert(self,*_):
        if self.anzeige_bereit:
            self.stop_all(); self.ausrichtung.setChecked(False)
            self.core.bestaetige_ausrichtung(False)

    def ausrichtung_geaendert(self,*_):
        self.core.ausrichtung_bestaetigt=False
        if self.ausrichtung.isChecked():
            self.save_settings()
            self.core.bestaetige_ausrichtung(self.core.werte==self.settings_values())
        else:
            self.core.bestaetige_ausrichtung(False)
            if self.core.modus!="Pause": self.stop_all()

    def settings_values(self):
        return dict(breite=self.lat.value(),laenge=self.lon.value(),az_null=self.az_null.value(),el_neigung=self.el_null.value(),land=self.land.text().strip(),stadt=self.stadt.text().strip(),zeitzone=self.zeitzone.value())

    def save_settings(self):
        def action():
            self.core.speichern(self.datenordner/"einstellungen.json",self.settings_values())
            self.chart.berechnen(self.core.simzeit,self.core.werte)
            self.protokoll("Standort und Ausrichtung gespeichert")
        self.aktion(action)

    def standort_aus_karte(self,breite,laenge):
        self.lat.setValue(round(float(breite),6))
        self.lon.setValue(round(float(laenge),6))
        self.zeitzone.setValue(zonenversatz(laenge))
        v=vorschlag(breite,laenge)
        if v:
            self.stadt.setText(v[0]); self.land.setText(v[1])
        def action():
            self.core.speichern(self.datenordner/"einstellungen.json",self.settings_values())
            self.chart.berechnen(self.core.simzeit,self.core.werte)
            self.ausrichtung.blockSignals(True); self.ausrichtung.setChecked(True); self.ausrichtung.blockSignals(False)
            self.core.bestaetige_ausrichtung(self.core.werte==self.settings_values())
            if self.core.bereit and not self.core.beschaeftigt:
                self.core.konfiguration_senden()
            self.protokoll("Standort per Karte gesetzt: %.6f, %.6f" % (breite,laenge))
        self.aktion(action)

    def ort_vorschlagen(self):
        v=vorschlag(self.lat.value(),self.lon.value())
        if not v:
            self.protokoll("Ortsvorschlag: keine Daten")
            return
        stadt,land=v
        self.stadt.setText(stadt)
        self.land.setText(land)
        self.zeitzone.setValue(zonenversatz(self.lon.value()))
        self.protokoll(f"Ortsvorschlag gesetzt: {stadt}, {land} (Zeitzone UTC{self.zeitzone.value():+g})")

    def ortspruefung(self,*_):
        if not self.land.text().strip() and not self.stadt.text().strip():
            v=vorschlag(self.lat.value(),self.lon.value())
            if v:
                self.stadt.setText(v[0]); self.land.setText(v[1])

    def ansicht_reset(self):
        self.weltkarte_gross.reset_ansicht()
        self.globus.reset_ansicht()

    def grenzen_geaendert(self,*_):
        okay=bool(self.core.status and all(a["limits_ok"] for a in self.core.status["axes"]))
        self.core.bestaetige_grenzen(self.grenzen.isChecked() and okay)
        if self.grenzen.isChecked() and not okay:
            self.grenzen.setChecked(False); self.protokoll("Zuerst beide Grenztests abschließen. Details stehen über den Tasten.")

    def referenz(self,index):
        if self.core.status and self.core.status.get("position_storage",False):
            self.aktion(lambda:self.core.referenzfahrt(index))
            return
        text=("Steht diese Achse tatsächlich an der zuvor markierten sicheren MIN-Position, 10° nach dem mechanischen MIN?\n\nDiese Bestätigung fährt den Motor nicht. Nach einem erfolgreichen Endschaltertest ist sie nicht nötig.")
        if QMessageBox.question(self,"Tatsächliche Position bestätigen",text)==QMessageBox.Yes:
            self.aktion(lambda:self.core.referenz(index))

    def read_rtc(self):
        self.aktion(lambda:self.core.senden("STATUS"))

    def lcd_preview_only(self):
        self.lcd_preview.setText(self.lcd_line1.text()[:16]+"\n"+self.lcd_line2.text()[:16])
        self.protokoll("LCD-Vorschau aktualisiert, keine Übertragung an Hardware")

    def flash_message(self,text): self.protokoll(text)

    def copy_diagnose(self):
        text=status_text(self.core.status)+"\n\n"+"\n".join(self.meldungen[-30:])
        QApplication.clipboard().setText(text)
        self.protokoll("Status und letzte Meldungen in Zwischenablage kopiert")

    def export_csv(self):
        pfad,_=QFileDialog.getSaveFileName(self,"Tageskurve speichern","sonnenverlauf.csv","CSV (*.csv)", options=QFileDialog.Option.DontUseNativeDialog)
        if pfad:
            self.aktion(lambda:Path(pfad).write_text("Stunde;Azimut;Elevation\n"+"\n".join(f"{t:.4f};{a:.4f};{e:.4f}" for t,a,e in self.chart.punkte),encoding="utf-8-sig"))

    def update_all_status(self):
        c=self.core; n=c.status
        self.connection_label.setText("● verbunden" if c.bereit else ("● Prüfung ..." if c.link else "● getrennt"))
        self.connection_label.setStyleSheet("color: "+("#52d273" if c.bereit else "#ffb347")+"; background: transparent;")
        self.connect_btn.setText("Trennen" if c.link else "Verbinden")
        self.port_combo.setEnabled(c.link is None)
        self.operation_status.setText("Betrieb AKTIV" if c.modus=="Normalbetrieb" else "Betrieb nicht aktiv")
        self.operation_btn.setText("Betrieb stoppen" if c.modus=="Normalbetrieb" else "Betrieb aktivieren")
        self.mode_label.setText("Modus: "+c.modus)
        self.pruef_details.setText(status_text(n))
        for i,name in enumerate(("Azimut","Elevation")):
            a=n["axes"][i] if n else None
            ref_ok=bool(a and a["referenced"])
            self.ref_buttons[i].setEnabled(bool(c.bereit and a and a["calibrated"] and not ref_ok and not c.beschaeftigt and (not a["min"] and not a["max"] or n.get("position_storage",False) and not (a["min"] and a["max"]))))
            self.ref_buttons[i].setText(f"{name}: Referenz OK" if ref_ok else f"{('AZ','EL')[i]}: Position ermitteln" if n and n.get("position_storage",False) else f"{('AZ','EL')[i]}: Referenz wiederherstellen")
            self.ref_buttons[i].setToolTip("Nur bei unbekannter Position: MIN anfahren und 10 Grad entlasten. Endlagen und bestandene Grenztests bleiben erhalten." if n and n.get("position_storage",False) else "Markierte sichere MIN-Position manuell bestaetigen")
            getestet=bool(a and a["limits_ok"])
            self.grenz_buttons[i].setText(f"{name}: bestanden (gespeichert)" if getestet else f"Grenztest {name} starten")
            self.grenz_buttons[i].setEnabled(bool(c.bereit and not c.beschaeftigt and not getestet and not grenztest_fehler(n,i)))
        for i,(minus,plus,hinweis) in self.motor_controls.items():
            a=n["axes"][i] if n else None
            gruende=[]
            if not c.bereit: gruende.append("Zuerst ESP32 verbinden")
            elif c.beschaeftigt: gruende.append("Fahrt/Auftrag laeuft - Abschluss abwarten")
            elif a["min"] and a["max"]: gruende.append("Beide Kontakte aktiv: Verkabelung pruefen")
            for btn,richtung in ((minus,-1),(plus,1)):
                grund="; ".join(gruende)
                if not grund and a["referenced"]:
                    ziel=a["position"]+richtung*round(5*4096/360)
                    if not a["margin"] <= ziel <= a["span"]-a["margin"]:
                        grund="Sichere Fahrgrenze: Gegenrichtung verwenden"
                btn.setEnabled(not grund); btn.setToolTip(grund or "Begrenzte Testfahrt: 5 Grad")
            hinweis.setText("; ".join(gruende) if gruende else
                ("Position bekannt. Grau = Fahrt wuerde die sichere Grenze verlassen." if a["referenced"] else
                 "Position unbekannt: begrenzte 5-Grad-Richtungstests sind moeglich. Sie ersetzen keine Kalibrierung."))
        for taste,index,grad in (("LINKS",0,-5),("RECHTS",0,5),("OBEN",1,5),("UNTEN",1,-5)):
            grund=self.richtungstest_grund(index,grad)
            self.test_tasten[taste].setEnabled(not grund)
            self.test_tasten[taste].setToolTip(grund or "Eine 5-Grad-Fahrt starten")
        self.lcd_send_btn.setEnabled(c.bereit and not c.beschaeftigt and c.modus=="Pause")
        self.lcd_status.setText(c.lcd_meldung if n and n.get("lcd_supported",False) else
            ("Firmware 0.3.2 fuer echte LCD-Uebertragung erforderlich" if n else "Zuerst ESP32 verbinden. Text ans LCD senden startet den Hardwaretest."))
        self.auto_cal_btn.setEnabled(c.bereit and not c.beschaeftigt and c.modus=="Pause")
        self.auto_cal_status.setText(n.get("auto_message","Firmware 0.4.1 erforderlich") if n else "Zuerst ESP32 verbinden")
        laeuft=bool(n and n.get("auto_mode",False))
        self.auto_mode_btn.setText("Autonomer Betrieb stoppen" if laeuft else "Autonomer Betrieb starten")
        self.auto_mode_btn.setEnabled(bool(c.bereit and not c.beschaeftigt))
        self.auto_mode_status.setText("Autonomer Betrieb aktiv: ESP32 fuehrt die Sonne ohne PC nach." if laeuft else
            ("Konfiguration im ESP32 " + ("OK" if n.get("conf_ok") else "fehlt (Standort/Ausrichtung bestaetigen)") + ". Start nur nach bestandenem Gesamttest." if n else "Zuerst ESP32 verbinden"))
        if hasattr(self,"oper_auto_btn"):
            self.oper_auto_btn.setText("Autonomer Betrieb stoppen" if laeuft else "Autonomer Betrieb starten")
            self.oper_auto_btn.setEnabled(bool(c.bereit and not c.beschaeftigt))
            self.oper_auto_status.setText("Autonomer Betrieb aktiv: ESP32 faehrt selbststaendig." if laeuft else
                ("Konfiguration " + ("OK" if n and n.get("conf_ok") else "fehlt") + "; Start nach bestandenem Gesamttest." if n else "Zuerst ESP32 verbinden"))
            sun_az=n.get("sun_az",-1) if n else -1
            sun_el=n.get("sun_el",-1) if n else -1
            if sun_az is not None and sun_az>=0:
                azw=c.werte["az_null"]+(sun_az-114)*360/4096
                neig=c.werte["el_neigung"]-(sun_el-114)*360/4096
                self.oper_target.setText(f"Sonnenziel: Azimut {azw:.1f} Grad / Panelneigung {neig:.1f} Grad")
            else:
                self.oper_target.setText("Sonnenziel: unbekannt (Konfiguration, Referenz oder RTC fehlt)")
            self.befehl_btn.setEnabled(bool(c.bereit))
        if hasattr(self,"conf_status"):
            if n and n.get("conf_ok"):
                self.conf_status.setText("ESP32: Breite %.3f, Laenge %.3f, AzNull %.2f, Neigung %.2f" % (n.get("lat",0),n.get("lon",0),n.get("az_null",0),n.get("el_neigung",0)))
            else:
                self.conf_status.setText("ESP32-Konfiguration fehlt: senden oder Auto Kalibrierung")
        for b in getattr(self,"cal_buttons",[]):
            b.setEnabled(bool(c.bereit and not c.beschaeftigt and c.modus=="Pause" and n and n.get("switch_test")==4))
        if hasattr(self,"lat"):
            lat,lon=self.lat.value(),self.lon.value()
            name=", ".join(t for t in (self.stadt.text().strip(),self.land.text().strip()) if t)
        elif n and n.get("conf_ok") and n.get("lat") is not None:
            lat,lon=n.get("lat"),n.get("lon"); name=""
        else:
            lat,lon=c.werte.get("breite"),c.werte.get("laenge"); name=""
        for karte in (getattr(self,"weltkarte_klein",None),getattr(self,"weltkarte_gross",None)):
            if karte is not None:
                karte.set_ort(lat,lon,name)
        if getattr(self,"globus",None) is not None:
            self.globus.set_ort(lat,lon,name,self.core.standort_zeit().strftime("%H:%M:%S"))
        fehler=c.freigabe(); self.freigabe_label.setText("Start gesperrt:\n"+"\n".join(fehler[:4]) if fehler else "Alle Startprüfungen OK")
        farbe="#208447" if not fehler and n and n.get("auto_ok",False) else "#101010"
        for knopf in [self.btn_oper,self.btn_sim,self.operation_btn,self.sim_start,self.sim_neu,*self.sim_buttons]:
            knopf.setStyleSheet(f"background-color: {farbe}; color: white;")
        self.operation_btn.setEnabled(c.modus=="Normalbetrieb" or (not fehler and not c.beschaeftigt and c.modus=="Pause"))
        self.freigabe_label.setToolTip("\n".join(fehler))
        for btn in [self.sim_start,self.sim_neu,*self.sim_buttons]: btn.setEnabled(not fehler and not c.beschaeftigt and c.modus=="Pause")
        self.sim_status.setText(c.ablauf if c.modus=="Simulation" or c.ablauf.startswith("Beendet") else ("Simulation bereit" if not fehler else "Simulation: Pruefungen erforderlich"))
        self.sim_progress.setText(f"Simulationszeit: {c.simzeit:%d.%m.%Y %H:%M:%S} | Tempo x{c.tempo:g}" + (" | Fahrgrenze erreicht" if c.begrenzt else ""))
        self.sim_start.setText("Simulation fortsetzen" if c.fortsetzung else "Simulation starten - Grafik + Panel")
        if c.grenzen_bestaetigt!=self.grenzen.isChecked():
            self.grenzen.blockSignals(True); self.grenzen.setChecked(c.grenzen_bestaetigt); self.grenzen.blockSignals(False)
        for i,(gauge,label,oper) in enumerate(((self.az_gauge,self.az_value,self.oper_az),(self.el_gauge,self.el_value,self.oper_el))):
            name=("Azimut","Panelneigung")[i]
            a=n["axes"][i] if n else None
            start=c.werte[("az_null","el_neigung")[i]]
            weg=(a["span"]-2*a["margin"])*360/4096 if a and a["calibrated"] else 90
            gauge.minimum=start if i==0 else start-weg
            gauge.maximum=start+weg if i==0 else start
            value=(start+(a["position"]-a["margin"])*360/4096 if i==0 else panelneigung(start,a)) if a and a["referenced"] else None
            gauge.title="Azimut" if i==0 else "Panelneigung"
            gauge.set_value(value)
            text=f"{name}: {value:.1f} Grad" if value is not None else f"{name}: Position unbekannt"
            label.setText(text); oper.setText(text)
            gauge.setToolTip("Winkel aus Startausrichtung und gezaehlten Schritten; sichere MIN = Startwinkel, kein Positionssensor")
        aktiv=[]
        for key,label in self.end_labels.items():
            axis,ende=key.split("_"); a=n["axes"][0 if axis=="az" else 1] if n else None
            value="unbekannt" if a is None else ("GEDRÜCKT" if a[ende] else "frei")
            label.setText(f"{axis.upper()} {ende.upper()}: {value}")
            if a and a[ende]: aktiv.append(key.upper())
        self.endstop_status.setText("Endschalter: unbekannt" if not n else ("Aktiv: "+", ".join(aktiv) if aktiv else "Endschalter: alle frei"))
        self.endstop_status.setStyleSheet("color: "+("#97a8bb" if not n else ("#ff6b6b" if aktiv else "#52d273"))+"; background: transparent;")
        if n and n["rtc_valid"]:
            self.rtc_value.setText(datetime.fromtimestamp(n["rtc_epoch"],timezone.utc).astimezone().strftime("%d.%m.%Y %H:%M:%S"))
        else: self.rtc_value.setText("RTC-Zeit ungültig" if n and n["rtc_present"] else "RTC nicht erreichbar / nicht verbunden")
        now=datetime.now().astimezone()
        self.oper_time.setText(now.strftime("%d.%m.%Y %H:%M:%S"))
        self.date_edit.setText(now.strftime("%d.%m.%Y")); self.time_edit.setText(now.strftime("%H:%M:%S"))

    def tick(self):
        try:
            self.core.poll()
            if self.hold_axis is not None and not self.core.beschaeftigt:
                self.core.manuell(0 if self.hold_axis=="az" else 1,self.hold_direction*1.0)
            self.refresh_count+=1
            if self.refresh_count%4==0:
                self.chart.zeit=self.core.simzeit; self.chart.update(); self.update_all_status()
        except Exception as exc:
            self.hold_axis=None
            try: self.core.stopp()
            except Exception: self.core.trennen()
            self.protokoll(str(exc))

    def app_state(self,state):
        if state!=Qt.ApplicationActive and self.hold_axis is not None: self.stop_hold()

    def closeEvent(self,event):
        self.timer.stop(); self.hold_axis=None
        try: self.core.trennen()
        except Exception: pass
        event.accept()


def main():
    app=QApplication(sys.argv)
    app.setApplicationName("SolarTracker")
    win=Bedienpanel(); win.show()
    sys.exit(app.exec())


if __name__=="__main__": main()
