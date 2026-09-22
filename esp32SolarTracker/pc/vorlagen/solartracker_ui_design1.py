import sys
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QComboBox, QDoubleSpinBox, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPushButton, QRadioButton, QSpinBox, QStackedWidget, QVBoxLayout, QWidget
)


# ============================================================
#  SolarTracker UI - Design 1
#  Reine PC-Demo ohne Hardware / COM-Anbindung
# ============================================================


AZ_MIN = 0.0
AZ_MAX = 180.0
EL_MIN = 0.0
EL_MAX = 90.0
BACKOFF_DEG = 10.0
STEP_DEG = 10.0


class AxisGauge(QWidget):
    """Einfache grafische Achsanzeige."""
    def __init__(self, title, minimum, maximum, accent="#3aa6ff", parent=None):
        super().__init__(parent)
        self.title = title
        self.minimum = minimum
        self.maximum = maximum
        self.value = minimum
        self.accent = QColor(accent)
        self.setMinimumHeight(180)

    def set_value(self, value):
        self.value = max(self.minimum, min(self.maximum, float(value)))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        p.setPen(QColor("#d8e2ef"))
        p.setFont(QFont("Segoe UI", 11, QFont.Bold))
        p.drawText(12, 24, self.title)

        # Skala
        x0, x1 = 22, w - 22
        y = h - 45
        p.setPen(QPen(QColor("#526273"), 3))
        p.drawLine(x0, y, x1, y)

        # Ticks
        p.setFont(QFont("Segoe UI", 8))
        for i in range(6):
            x = x0 + (x1 - x0) * i / 5
            p.setPen(QPen(QColor("#526273"), 1))
            p.drawLine(int(x), y - 7, int(x), y + 7)
            val = self.minimum + (self.maximum - self.minimum) * i / 5
            p.setPen(QColor("#97a8bb"))
            p.drawText(int(x - 16), y + 24, 40, 15, Qt.AlignCenter, f"{val:.0f}°")

        ratio = (self.value - self.minimum) / max(1e-9, (self.maximum - self.minimum))
        x = x0 + (x1 - x0) * ratio

        # Marker
        p.setPen(Qt.NoPen)
        p.setBrush(self.accent)
        p.drawEllipse(int(x - 8), int(y - 8), 16, 16)

        # Wert
        p.setPen(self.accent)
        p.setFont(QFont("Segoe UI", 26, QFont.Bold))
        p.drawText(10, 55, w - 20, 50, Qt.AlignCenter, f"{self.value:.1f}°")


class SolarTrackerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SolarTracker - Bedienpanel")
        self.resize(1450, 900)

        # Simulationszustände
        self.azimuth = 90.0
        self.elevation = 30.0
        self.operation_active = False
        self.connected = False

        self.sim_timer = QTimer(self)
        self.sim_timer.timeout.connect(self.simulation_tick)
        self.sim_elapsed = 0.0
        self.sim_duration = 60.0

        self.hold_timer = QTimer(self)
        self.hold_timer.timeout.connect(self.hold_move_tick)
        self.hold_axis = None
        self.hold_direction = 0

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)

        self.build_ui()
        self.apply_style()
        self.update_all_status()

    # --------------------------------------------------------
    # UI Grundaufbau
    # --------------------------------------------------------
    def build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        main = QHBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # LINKS: Navigation
        nav = QFrame()
        nav.setObjectName("nav")
        nav.setFixedWidth(240)
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(20, 25, 20, 25)
        nav_layout.setSpacing(12)

        logo = QLabel("SOLAR\nTRACKER")
        logo.setObjectName("logo")
        nav_layout.addWidget(logo)

        sub = QLabel("PC BEDIENPANEL")
        sub.setObjectName("muted")
        nav_layout.addWidget(sub)
        nav_layout.addSpacing(25)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        self.btn_oper = self.make_nav_button("☀  Betrieb")
        self.btn_sim = self.make_nav_button("▶  Simulation")
        self.btn_settings = self.make_nav_button("⚙  Einstellungen")
        self.btn_test = self.make_nav_button("🧪  Komponententest")

        for i, btn in enumerate([self.btn_oper, self.btn_sim, self.btn_settings, self.btn_test]):
            self.nav_group.addButton(btn, i)
            nav_layout.addWidget(btn)
            btn.clicked.connect(lambda checked=False, index=i: self.pages.setCurrentIndex(index))

        nav_layout.addStretch()

        hint = QLabel("Design 1\nDemo ohne Hardware")
        hint.setObjectName("muted")
        nav_layout.addWidget(hint)

        main.addWidget(nav)

        # MITTE
        center = QFrame()
        center.setObjectName("center")
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(26, 22, 26, 22)
        center_layout.setSpacing(18)

        center_layout.addWidget(self.build_topbar())

        self.pages = QStackedWidget()
        self.pages.addWidget(self.page_operation())
        self.pages.addWidget(self.page_simulation())
        self.pages.addWidget(self.page_settings())
        self.pages.addWidget(self.page_component_test())
        center_layout.addWidget(self.pages, 1)

        main.addWidget(center, 1)

        # RECHTS: Daueranzeige
        right = self.build_right_status()
        right.setFixedWidth(360)
        main.addWidget(right)

        self.btn_oper.setChecked(True)

    def make_nav_button(self, text):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumHeight(52)
        return btn

    def build_topbar(self):
        frame = QFrame()
        frame.setObjectName("card")
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(18, 12, 18, 12)

        title = QLabel("SolarTracker Steuerzentrale")
        title.setObjectName("h2")
        lay.addWidget(title)

        lay.addStretch()

        self.port_combo = QComboBox()
        self.port_combo.addItems(["COM3", "COM4", "COM5", "COM9"])
        self.port_combo.setFixedWidth(110)
        lay.addWidget(self.port_combo)

        self.connect_btn = QPushButton("Verbindung herstellen")
        self.connect_btn.setObjectName("primary")
        self.connect_btn.clicked.connect(self.toggle_connection)
        lay.addWidget(self.connect_btn)

        self.connection_label = QLabel("● getrennt")
        self.connection_label.setObjectName("dangerText")
        lay.addWidget(self.connection_label)

        return frame

    # --------------------------------------------------------
    # Seite Betrieb
    # --------------------------------------------------------
    def page_operation(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(18)

        header = QLabel("Betrieb")
        header.setObjectName("h1")
        layout.addWidget(header)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(18)

        status_card = self.card()
        sl = QVBoxLayout(status_card)
        sl.addWidget(self.section_title("Status"))

        self.operation_status = QLabel("Betrieb nicht aktiv")
        self.operation_status.setObjectName("bigStatus")
        sl.addWidget(self.operation_status)

        self.operation_info = QLabel(
            "Die Echtzeit-Nachführung wird später mit dem ESP32 verbunden.\n"
            "In dieser Demo werden nur Oberfläche und Zustände getestet."
        )
        self.operation_info.setWordWrap(True)
        self.operation_info.setObjectName("muted")
        sl.addWidget(self.operation_info)

        self.operation_btn = QPushButton("Betrieb aktivieren")
        self.operation_btn.setObjectName("success")
        self.operation_btn.setMinimumHeight(52)
        self.operation_btn.clicked.connect(self.toggle_operation)
        sl.addWidget(self.operation_btn)

        grid.addWidget(status_card, 0, 0)

        values = self.card()
        vl = QVBoxLayout(values)
        vl.addWidget(self.section_title("Live-Werte"))
        self.oper_time = QLabel("--:--:--")
        self.oper_time.setObjectName("value")
        self.oper_az = QLabel("Azimut: 0.0°")
        self.oper_el = QLabel("Elevation: 0.0°")
        self.oper_az.setObjectName("accentAz")
        self.oper_el.setObjectName("accentEl")
        vl.addWidget(self.oper_time)
        vl.addWidget(self.oper_az)
        vl.addWidget(self.oper_el)
        vl.addStretch()

        grid.addWidget(values, 0, 1)

        layout.addLayout(grid)
        layout.addStretch()
        return page

    # --------------------------------------------------------
    # Seite Simulation
    # --------------------------------------------------------
    def page_simulation(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(18)

        header = QLabel("Simulation")
        header.setObjectName("h1")
        layout.addWidget(header)

        card = self.card()
        cl = QVBoxLayout(card)
        cl.addWidget(self.section_title("Simulationsstufe auswählen"))

        row = QHBoxLayout()
        self.sim_buttons = []
        for label, sec in [("Stufe 1\n30 Sekunden", 30), ("Stufe 2\n60 Sekunden", 60), ("Stufe 3\n120 Sekunden", 120)]:
            b = QPushButton(label)
            b.setMinimumHeight(72)
            b.clicked.connect(lambda checked=False, s=sec: self.start_simulation(s))
            row.addWidget(b)
            self.sim_buttons.append(b)
        cl.addLayout(row)

        self.sim_status = QLabel("Simulation bereit")
        self.sim_status.setObjectName("bigStatus")
        cl.addWidget(self.sim_status)

        self.sim_progress = QLabel("Tagesverlauf: 0 %")
        self.sim_progress.setObjectName("muted")
        cl.addWidget(self.sim_progress)

        stop = QPushButton("Simulation stoppen")
        stop.setObjectName("danger")
        stop.clicked.connect(self.stop_simulation)
        cl.addWidget(stop)

        layout.addWidget(card)

        info = self.card()
        il = QVBoxLayout(info)
        il.addWidget(self.section_title("Funktion"))
        t = QLabel(
            "Die Simulation bildet einen kompletten Sonnentag ab. "
            "Azimut und Elevation werden dabei live auf der rechten Seite dargestellt. "
            "Später werden dieselben Sollpositionen zusätzlich an die Motoren übertragen."
        )
        t.setWordWrap(True)
        il.addWidget(t)
        layout.addWidget(info)
        layout.addStretch()

        return page

    # --------------------------------------------------------
    # Seite Einstellungen
    # --------------------------------------------------------
    def page_settings(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(18)

        header = QLabel("Einstellungen & manuelle Achssteuerung")
        header.setObjectName("h1")
        layout.addWidget(header)

        top = QHBoxLayout()

        # Steuerkreuz
        control = self.card()
        ctl = QVBoxLayout(control)
        ctl.addWidget(self.section_title("Manuelle Steuerung"))

        modes = QHBoxLayout()
        self.radio_step = QRadioButton("Schrittmodus 10°")
        self.radio_hold = QRadioButton("Haltemodus")
        self.radio_step.setChecked(True)
        modes.addWidget(self.radio_step)
        modes.addWidget(self.radio_hold)
        ctl.addLayout(modes)

        pad = QGridLayout()
        self.btn_up = QPushButton("▲\nOBEN")
        self.btn_left = QPushButton("◀ LINKS")
        self.btn_enter = QPushButton("ENTER")
        self.btn_right = QPushButton("RECHTS ▶")
        self.btn_down = QPushButton("UNTEN\n▼")

        for b in [self.btn_up, self.btn_left, self.btn_enter, self.btn_right, self.btn_down]:
            b.setMinimumSize(115, 70)

        pad.addWidget(self.btn_up, 0, 1)
        pad.addWidget(self.btn_left, 1, 0)
        pad.addWidget(self.btn_enter, 1, 1)
        pad.addWidget(self.btn_right, 1, 2)
        pad.addWidget(self.btn_down, 2, 1)
        ctl.addLayout(pad)

        self.bind_direction_button(self.btn_right, "az", +1)
        self.bind_direction_button(self.btn_left, "az", -1)
        self.bind_direction_button(self.btn_up, "el", +1)
        self.bind_direction_button(self.btn_down, "el", -1)
        self.btn_enter.clicked.connect(lambda: self.flash_message("ENTER bestätigt"))

        note = QLabel(
            "Schrittmodus: 10° pro Tastendruck.\n"
            "Haltemodus: konstante Bewegung, solange die Taste gehalten wird.\n"
            "Endschalter: bei Erreichen automatisch 10° zurück zum Entlasten."
        )
        note.setWordWrap(True)
        note.setObjectName("muted")
        ctl.addWidget(note)

        top.addWidget(control, 2)

        # Standort / Zeit
        settings = self.card()
        st = QVBoxLayout(settings)
        st.addWidget(self.section_title("Zeit & Standort"))

        self.time_edit = QLineEdit(datetime.now().strftime("%H:%M:%S"))
        self.date_edit = QLineEdit(datetime.now().strftime("%d.%m.%Y"))

        self.lat = QDoubleSpinBox()
        self.lat.setRange(-90.0, 90.0)
        self.lat.setDecimals(6)
        self.lat.setValue(50.1109)

        self.lon = QDoubleSpinBox()
        self.lon.setRange(-180.0, 180.0)
        self.lon.setDecimals(6)
        self.lon.setValue(8.6821)

        self.lang = QComboBox()
        self.lang.addItems(["Deutsch", "English"])

        form = QGridLayout()
        form.addWidget(QLabel("Datum"), 0, 0)
        form.addWidget(self.date_edit, 0, 1)
        form.addWidget(QLabel("Uhrzeit"), 1, 0)
        form.addWidget(self.time_edit, 1, 1)
        form.addWidget(QLabel("Breitengrad"), 2, 0)
        form.addWidget(self.lat, 2, 1)
        form.addWidget(QLabel("Längengrad"), 3, 0)
        form.addWidget(self.lon, 3, 1)
        form.addWidget(QLabel("Sprache"), 4, 0)
        form.addWidget(self.lang, 4, 1)
        st.addLayout(form)

        save = QPushButton("Einstellungen übernehmen")
        save.setObjectName("primary")
        save.clicked.connect(lambda: self.flash_message("Einstellungen übernommen"))
        st.addWidget(save)
        st.addStretch()

        top.addWidget(settings, 1)

        layout.addLayout(top)
        return page

    # --------------------------------------------------------
    # Seite Komponententest
    # --------------------------------------------------------
    def page_component_test(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(18)

        header = QLabel("Komponententest")
        header.setObjectName("h1")
        layout.addWidget(header)

        desc = QLabel(
            "Jede Komponente kann hier unabhängig vom normalen Betriebsprogramm getestet werden."
        )
        desc.setObjectName("muted")
        layout.addWidget(desc)

        self.test_stack = QStackedWidget()

        selector = self.card()
        sl = QVBoxLayout(selector)
        sl.addWidget(self.section_title("Komponente auswählen"))

        grid = QGridLayout()
        tests = [
            ("Azimut-Motor", 1),
            ("Elevations-Motor", 2),
            ("Endschalter", 3),
            ("RTC DS3231", 4),
            ("LCD 16x2", 5),
            ("Bedientasten", 6),
        ]
        for i, (name, idx) in enumerate(tests):
            b = QPushButton(name)
            b.setMinimumHeight(60)
            b.clicked.connect(lambda checked=False, x=idx: self.test_stack.setCurrentIndex(x))
            grid.addWidget(b, i // 3, i % 3)
        sl.addLayout(grid)
        self.test_stack.addWidget(selector)

        self.test_stack.addWidget(self.motor_test_page("Azimut-Motor", "az"))
        self.test_stack.addWidget(self.motor_test_page("Elevations-Motor", "el"))
        self.test_stack.addWidget(self.endstop_test_page())
        self.test_stack.addWidget(self.rtc_test_page())
        self.test_stack.addWidget(self.lcd_test_page())
        self.test_stack.addWidget(self.button_test_page())

        layout.addWidget(self.test_stack, 1)
        return page

    def motor_test_page(self, title, axis):
        page = self.card()
        l = QVBoxLayout(page)
        l.addWidget(self.section_title(title))

        value = QLabel("Isolierter Motortest")
        value.setObjectName("bigStatus")
        l.addWidget(value)

        row = QHBoxLayout()
        minus = QPushButton("Rückwärts")
        plus = QPushButton("Vorwärts")
        stop = QPushButton("STOP")
        stop.setObjectName("danger")
        row.addWidget(minus)
        row.addWidget(stop)
        row.addWidget(plus)
        l.addLayout(row)

        minus.clicked.connect(lambda: self.move_axis(axis, -1, 10))
        plus.clicked.connect(lambda: self.move_axis(axis, +1, 10))
        stop.clicked.connect(self.stop_hold)

        back = QPushButton("← Zur Komponentenauswahl")
        back.clicked.connect(lambda: self.test_stack.setCurrentIndex(0))
        l.addWidget(back)
        l.addStretch()
        return page

    def endstop_test_page(self):
        page = self.card()
        l = QVBoxLayout(page)
        l.addWidget(self.section_title("Endschalter-Test"))

        self.end_labels = {}
        for key, text in [
            ("az_min", "Azimut MIN"),
            ("az_max", "Azimut MAX"),
            ("el_min", "Elevation MIN"),
            ("el_max", "Elevation MAX"),
        ]:
            row = QHBoxLayout()
            lab = QLabel(f"{text}: FREI")
            lab.setObjectName("successText")
            btn = QPushButton("Schalter antippen")
            btn.clicked.connect(lambda checked=False, k=key, la=lab, tx=text: self.fake_endstop(k, la, tx))
            row.addWidget(lab)
            row.addStretch()
            row.addWidget(btn)
            l.addLayout(row)
            self.end_labels[key] = lab

        back = QPushButton("← Zur Komponentenauswahl")
        back.clicked.connect(lambda: self.test_stack.setCurrentIndex(0))
        l.addWidget(back)
        l.addStretch()
        return page

    def rtc_test_page(self):
        page = self.card()
        l = QVBoxLayout(page)
        l.addWidget(self.section_title("RTC DS3231 Test"))

        self.rtc_value = QLabel("Noch nicht ausgelesen")
        self.rtc_value.setObjectName("value")
        l.addWidget(self.rtc_value)

        b = QPushButton("RTC auslesen")
        b.clicked.connect(self.read_fake_rtc)
        l.addWidget(b)

        note = QLabel("Demo: aktuell wird die PC-Systemzeit verwendet. Später wird der DS3231 über den ESP32 ausgelesen.")
        note.setWordWrap(True)
        note.setObjectName("muted")
        l.addWidget(note)

        back = QPushButton("← Zur Komponentenauswahl")
        back.clicked.connect(lambda: self.test_stack.setCurrentIndex(0))
        l.addWidget(back)
        l.addStretch()
        return page

    def lcd_test_page(self):
        page = self.card()
        l = QVBoxLayout(page)
        l.addWidget(self.section_title("LCD 16x2 Test"))

        self.lcd_line1 = QLineEdit("SolarTracker")
        self.lcd_line2 = QLineEdit("LCD Test OK")
        self.lcd_preview = QLabel("SolarTracker\nLCD Test OK")
        self.lcd_preview.setObjectName("lcd")
        self.lcd_preview.setAlignment(Qt.AlignCenter)
        self.lcd_preview.setMinimumHeight(95)

        l.addWidget(QLabel("Zeile 1"))
        l.addWidget(self.lcd_line1)
        l.addWidget(QLabel("Zeile 2"))
        l.addWidget(self.lcd_line2)
        l.addWidget(self.lcd_preview)

        send = QPushButton("Text ans LCD senden")
        send.clicked.connect(self.fake_lcd_send)
        l.addWidget(send)

        back = QPushButton("← Zur Komponentenauswahl")
        back.clicked.connect(lambda: self.test_stack.setCurrentIndex(0))
        l.addWidget(back)
        l.addStretch()
        return page

    def button_test_page(self):
        page = self.card()
        l = QVBoxLayout(page)
        l.addWidget(self.section_title("Bedientasten-Test"))

        self.button_test_value = QLabel("Noch keine Taste gedrückt")
        self.button_test_value.setObjectName("bigStatus")
        l.addWidget(self.button_test_value)

        grid = QGridLayout()
        for text, r, c in [
            ("OBEN", 0, 1), ("LINKS", 1, 0), ("ENTER", 1, 1),
            ("RECHTS", 1, 2), ("UNTEN", 2, 1)
        ]:
            b = QPushButton(text)
            b.setMinimumHeight(55)
            b.clicked.connect(lambda checked=False, t=text: self.button_test_value.setText(f"Taste erkannt: {t}"))
            grid.addWidget(b, r, c)
        l.addLayout(grid)

        back = QPushButton("← Zur Komponentenauswahl")
        back.clicked.connect(lambda: self.test_stack.setCurrentIndex(0))
        l.addWidget(back)
        l.addStretch()
        return page

    # --------------------------------------------------------
    # Rechte Daueranzeige
    # --------------------------------------------------------
    def build_right_status(self):
        frame = QFrame()
        frame.setObjectName("rightpanel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 22, 18, 22)
        layout.setSpacing(14)

        title = QLabel("LIVE POSITION")
        title.setObjectName("h2")
        layout.addWidget(title)

        self.mode_label = QLabel("Modus: Standby")
        self.mode_label.setObjectName("muted")
        layout.addWidget(self.mode_label)

        self.az_gauge = AxisGauge("AZIMUT", AZ_MIN, AZ_MAX, "#3aa6ff")
        self.el_gauge = AxisGauge("ELEVATION", EL_MIN, EL_MAX, "#ffb347")
        layout.addWidget(self.az_gauge)
        layout.addWidget(self.el_gauge)

        pos = self.card()
        pl = QVBoxLayout(pos)
        self.az_value = QLabel("Azimut 90.0°")
        self.el_value = QLabel("Elevation 30.0°")
        self.az_value.setObjectName("accentAz")
        self.el_value.setObjectName("accentEl")
        self.az_value.setFont(QFont("Segoe UI", 15, QFont.Bold))
        self.el_value.setFont(QFont("Segoe UI", 15, QFont.Bold))
        pl.addWidget(self.az_value)
        pl.addWidget(self.el_value)

        self.endstop_status = QLabel("Endschalter: frei")
        self.endstop_status.setObjectName("successText")
        pl.addWidget(self.endstop_status)
        layout.addWidget(pos)

        layout.addStretch()
        return frame

    # --------------------------------------------------------
    # Logik
    # --------------------------------------------------------
    def card(self):
        f = QFrame()
        f.setObjectName("card")
        return f

    def section_title(self, text):
        l = QLabel(text)
        l.setObjectName("h2")
        return l

    def toggle_connection(self):
        self.connected = not self.connected
        if self.connected:
            self.connection_label.setText(f"● verbunden ({self.port_combo.currentText()})")
            self.connection_label.setObjectName("successText")
            self.connect_btn.setText("Verbindung trennen")
        else:
            self.connection_label.setText("● getrennt")
            self.connection_label.setObjectName("dangerText")
            self.connect_btn.setText("Verbindung herstellen")
        self.connection_label.style().unpolish(self.connection_label)
        self.connection_label.style().polish(self.connection_label)

    def toggle_operation(self):
        self.operation_active = not self.operation_active
        if self.operation_active:
            self.operation_status.setText("Betrieb AKTIV")
            self.operation_btn.setText("Betrieb stoppen")
            self.operation_btn.setObjectName("danger")
            self.mode_label.setText("Modus: Betrieb")
        else:
            self.operation_status.setText("Betrieb nicht aktiv")
            self.operation_btn.setText("Betrieb aktivieren")
            self.operation_btn.setObjectName("success")
            self.mode_label.setText("Modus: Standby")
        self.operation_btn.style().unpolish(self.operation_btn)
        self.operation_btn.style().polish(self.operation_btn)

    def start_simulation(self, duration):
        self.stop_hold()
        self.operation_active = False
        self.sim_duration = float(duration)
        self.sim_elapsed = 0.0
        self.azimuth = AZ_MIN + BACKOFF_DEG
        self.elevation = EL_MIN + BACKOFF_DEG
        self.sim_status.setText(f"Simulation läuft: kompletter Tag in {duration} s")
        self.mode_label.setText(f"Modus: Simulation {duration}s")
        self.sim_timer.start(100)  # 10 FPS
        self.update_all_status()

    def simulation_tick(self):
        self.sim_elapsed += 0.1
        progress = min(1.0, self.sim_elapsed / self.sim_duration)

        # Demonstrationskurven:
        # Azimut läuft von 10° bis 170°
        self.azimuth = (AZ_MIN + BACKOFF_DEG) + (AZ_MAX - 2 * BACKOFF_DEG) * progress

        # Elevation: Sonne steigt bis zur Tagesmitte und sinkt wieder
        if progress <= 0.5:
            self.elevation = (EL_MIN + BACKOFF_DEG) + (EL_MAX - BACKOFF_DEG) * (progress / 0.5)
        else:
            self.elevation = EL_MAX - (EL_MAX - BACKOFF_DEG) * ((progress - 0.5) / 0.5)

        self.sim_progress.setText(f"Tagesverlauf: {int(progress * 100)} %")
        self.update_all_status()

        if progress >= 1.0:
            self.stop_simulation(completed=True)

    def stop_simulation(self, completed=False):
        self.sim_timer.stop()
        if completed:
            self.sim_status.setText("Simulation abgeschlossen")
            self.sim_progress.setText("Tagesverlauf: 100 %")
        else:
            self.sim_status.setText("Simulation gestoppt")
        self.mode_label.setText("Modus: Standby")

    def bind_direction_button(self, button, axis, direction):
        button.clicked.connect(lambda checked=False, a=axis, d=direction: self.step_or_click(a, d))
        button.pressed.connect(lambda a=axis, d=direction: self.begin_hold_if_needed(a, d))
        button.released.connect(self.stop_hold)

    def step_or_click(self, axis, direction):
        if self.radio_step.isChecked():
            self.move_axis(axis, direction, STEP_DEG)

    def begin_hold_if_needed(self, axis, direction):
        if self.radio_hold.isChecked():
            self.hold_axis = axis
            self.hold_direction = direction
            self.hold_timer.start(120)

    def hold_move_tick(self):
        if self.hold_axis:
            self.move_axis(self.hold_axis, self.hold_direction, 2.0)

    def stop_hold(self):
        self.hold_timer.stop()
        self.hold_axis = None
        self.hold_direction = 0

    def move_axis(self, axis, direction, amount):
        if axis == "az":
            new_val = self.azimuth + direction * amount
            if new_val <= AZ_MIN:
                self.azimuth = AZ_MIN + BACKOFF_DEG
                self.show_endstop("Azimut MIN")
            elif new_val >= AZ_MAX:
                self.azimuth = AZ_MAX - BACKOFF_DEG
                self.show_endstop("Azimut MAX")
            else:
                self.azimuth = new_val
                self.clear_endstop()
        else:
            new_val = self.elevation + direction * amount
            if new_val <= EL_MIN:
                self.elevation = EL_MIN + BACKOFF_DEG
                self.show_endstop("Elevation MIN")
            elif new_val >= EL_MAX:
                self.elevation = EL_MAX - BACKOFF_DEG
                self.show_endstop("Elevation MAX")
            else:
                self.elevation = new_val
                self.clear_endstop()

        self.update_all_status()

    def show_endstop(self, name):
        self.endstop_status.setText(f"Endschalter: {name} → 10° zurück")
        self.endstop_status.setObjectName("dangerText")
        self.endstop_status.style().unpolish(self.endstop_status)
        self.endstop_status.style().polish(self.endstop_status)

    def clear_endstop(self):
        self.endstop_status.setText("Endschalter: frei")
        self.endstop_status.setObjectName("successText")
        self.endstop_status.style().unpolish(self.endstop_status)
        self.endstop_status.style().polish(self.endstop_status)

    def fake_endstop(self, key, label, text):
        label.setText(f"{text}: BETÄTIGT")
        label.setObjectName("dangerText")
        label.style().unpolish(label)
        label.style().polish(label)
        QTimer.singleShot(800, lambda: self.reset_endstop_label(label, text))

    def reset_endstop_label(self, label, text):
        label.setText(f"{text}: FREI")
        label.setObjectName("successText")
        label.style().unpolish(label)
        label.style().polish(label)

    def read_fake_rtc(self):
        self.rtc_value.setText(datetime.now().strftime("%d.%m.%Y   %H:%M:%S"))

    def fake_lcd_send(self):
        line1 = self.lcd_line1.text()[:16]
        line2 = self.lcd_line2.text()[:16]
        self.lcd_preview.setText(f"{line1}\n{line2}")
        self.flash_message("LCD-Testtext übernommen (Demo)")

    def flash_message(self, text):
        self.statusBar().showMessage(text, 2500)

    def update_clock(self):
        now = datetime.now()
        self.oper_time.setText(now.strftime("%d.%m.%Y   %H:%M:%S"))

    def update_all_status(self):
        self.azimuth = max(AZ_MIN, min(AZ_MAX, self.azimuth))
        self.elevation = max(EL_MIN, min(EL_MAX, self.elevation))

        self.az_gauge.set_value(self.azimuth)
        self.el_gauge.set_value(self.elevation)

        self.az_value.setText(f"Azimut      {self.azimuth:6.1f}°")
        self.el_value.setText(f"Elevation   {self.elevation:6.1f}°")

        self.oper_az.setText(f"Azimut: {self.azimuth:.1f}°")
        self.oper_el.setText(f"Elevation: {self.elevation:.1f}°")

    # --------------------------------------------------------
    # Style
    # --------------------------------------------------------
    def apply_style(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background: #0d1117;
                color: #e7edf5;
                font-family: "Segoe UI";
                font-size: 14px;
            }

            QFrame#nav {
                background: #111820;
                border-right: 1px solid #243140;
            }

            QFrame#center {
                background: #0d1117;
            }

            QFrame#rightpanel {
                background: #111820;
                border-left: 1px solid #243140;
            }

            QFrame#card {
                background: #151d27;
                border: 1px solid #263546;
                border-radius: 14px;
            }

            QLabel#logo {
                color: #65b7ff;
                font-size: 25px;
                font-weight: 800;
                letter-spacing: 2px;
            }

            QLabel#h1 {
                font-size: 26px;
                font-weight: 800;
                color: #f4f8fc;
            }

            QLabel#h2 {
                font-size: 17px;
                font-weight: 700;
                color: #dfe9f5;
            }

            QLabel#muted {
                color: #8fa1b4;
            }

            QLabel#bigStatus {
                font-size: 22px;
                font-weight: 800;
                color: #ffffff;
            }

            QLabel#value {
                font-size: 22px;
                font-weight: 700;
                color: #ffffff;
            }

            QLabel#accentAz {
                color: #3aa6ff;
                font-weight: 700;
            }

            QLabel#accentEl {
                color: #ffb347;
                font-weight: 700;
            }

            QLabel#successText {
                color: #52d273;
                font-weight: 700;
            }

            QLabel#dangerText {
                color: #ff6b6b;
                font-weight: 700;
            }

            QLabel#lcd {
                background: #b7cf8d;
                color: #1b2a13;
                border: 4px solid #283327;
                border-radius: 8px;
                font-family: Consolas;
                font-size: 20px;
                font-weight: 700;
                padding: 10px;
            }

            QPushButton {
                background: #1b2734;
                color: #eaf2fa;
                border: 1px solid #31445a;
                border-radius: 9px;
                padding: 10px 14px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #25364a;
                border-color: #4d6d8f;
            }

            QPushButton:pressed {
                background: #101820;
            }

            QPushButton:checked {
                background: #1d4d73;
                border-color: #3aa6ff;
                color: white;
            }

            QPushButton#primary {
                background: #1769aa;
                border-color: #318cd1;
            }

            QPushButton#success {
                background: #1f7a43;
                border-color: #39a960;
            }

            QPushButton#danger {
                background: #8d2d35;
                border-color: #c14b55;
            }

            QComboBox, QLineEdit, QDoubleSpinBox, QSpinBox {
                background: #0f1620;
                color: #edf4fb;
                border: 1px solid #31445a;
                border-radius: 8px;
                padding: 8px;
                min-height: 24px;
            }

            QRadioButton {
                spacing: 7px;
            }

            QStatusBar {
                background: #101720;
                color: #9fb2c6;
            }
        """)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SolarTracker")
    win = SolarTrackerWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
