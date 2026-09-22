"""Version 0.3.0: nicht blockierende serielle Verbindung fuer die Tk-Ereignisschleife.

Eingabe: Befehle, Port; Ausgabe: gepruefte JSON-Nachrichten oder Verbindungsfehler.
Keine Motorbefehle beim Oeffnen. Beispiel: senden('JOG', 'AZ', 1).
"""
import json
import time


def status_pruefen(nachricht):
    if nachricht.get("protocol") != 3 or len(nachricht.get("axes", [])) != 2:
        raise ValueError("Unpassende Firmware / Protokollversion")
    if type(nachricht.get("switch_test")) is not int or not 0 <= nachricht["switch_test"] <= 4:
        raise ValueError("Ungueltiger Schaltertest")
    for feld in ("rtc_present", "rtc_valid", "switch_testing"):
        if type(nachricht.get(feld)) is not bool:
            raise ValueError("Ungueltiger RTC-/Pruefstatus")
    if type(nachricht.get("rtc_epoch")) is not int or not 0 <= nachricht["rtc_epoch"] <= 4102444799:
        raise ValueError("Ungueltige RTC-Zeit")
    if "auto_supported" in nachricht:
        for feld in ("auto_supported","auto_testing","auto_ok","storage_ok","lcd_present"):
            if type(nachricht.get(feld)) is not bool:
                raise ValueError("Ungueltiger Auto-Kalibrierstatus")
        if not isinstance(nachricht.get("auto_message"),str):
            raise ValueError("Ungueltige Auto-Kalibriermeldung")
    for achse in nachricht["axes"]:
        for feld in ("position", "span", "margin", "state"):
            if type(achse.get(feld)) is not int:
                raise ValueError("Ungueltige Achsendaten")
        for feld in ("calibrated", "referenced", "min", "max", "limits_ok"):
            if type(achse.get(feld)) is not bool:
                raise ValueError("Ungueltiger Achsenzustand")
        if not (0 <= achse["span"] <= 4096 and achse["margin"] == 114 and 0 <= achse["state"] <= 10):
            raise ValueError("Ungueltige Bewegungsgrenzen")
        if achse["calibrated"] != (achse["span"] > 228) or (achse["referenced"] and not achse["calibrated"]):
            raise ValueError("Widerspruechliche Kalibrierung")
    return nachricht


class Verbindung:
    def __init__(self, port=None, uhr=time.monotonic):
        self.port = port
        self.uhr = uhr
        self.puffer = bytearray()
        self.nummer = 0
        self.offen = {}
        self.bereit = False
        self.hallo = False
        self.status = None
        self.letzte_antwort = self.uhr()
        self.letzter_ping = 0

    def oeffnen(self, name):
        import serial
        self.port = serial.Serial(port=None, baudrate=115200, timeout=0, write_timeout=0.2)
        self.port.dtr = False
        self.port.rts = False
        self.port.port = name
        self.port.open()
        self.port.reset_input_buffer()
        self.letzte_antwort = self.uhr()
        self.senden("HELLO", 3)

    def senden(self, befehl, *argumente):
        if self.port is None:
            raise ConnectionError("Kein ESP32 verbunden")
        self.nummer += 1
        text = " ".join(map(str, (self.nummer, befehl, *argumente))) + "\n"
        daten = text.encode("ascii")
        if self.port.write(daten) != len(daten):
            raise ConnectionError("Befehl nicht vollstaendig gesendet")
        self.offen[self.nummer] = (self.uhr(), befehl)
        return self.nummer

    def lesen(self):
        if self.port is None:
            return []
        jetzt = self.uhr()
        if jetzt - self.letzter_ping >= 0.5:
            self.senden("PING")
            self.letzter_ping = jetzt
        self.puffer.extend(self.port.read(min(self.port.in_waiting, 8192)))
        if len(self.puffer) > 16384:
            raise ConnectionError("Serieller Empfangspuffer uebergelaufen")
        ergebnisse = []
        for _ in range(100):
            if b"\n" not in self.puffer:
                break
            zeile, _, self.puffer = self.puffer.partition(b"\n")
            try:
                nachricht = json.loads(zeile.decode("utf-8"))
            except (UnicodeError, ValueError):
                continue  # ESP32-Bootmeldungen sind kein Protokoll.
            if not isinstance(nachricht, dict):
                continue
            typ = nachricht.get("type")
            if typ == "status":
                self.status = status_pruefen(nachricht)
            elif typ == "ack":
                if type(nachricht.get("id")) is not int or type(nachricht.get("ok")) is not bool:
                    raise ConnectionError("Ungueltige Bestaetigung")
                eintrag = self.offen.pop(nachricht["id"], None)
                if eintrag and eintrag[1] == "HELLO" and nachricht["ok"]:
                    self.hallo = True
            elif typ not in ("fault", "event"):
                continue
            self.letzte_antwort = jetzt
            self.bereit = self.hallo and self.status is not None
            ergebnisse.append(nachricht)
        if jetzt - self.letzte_antwort > 2.5 or any(jetzt - beginn > 2.5 for beginn, _ in self.offen.values()):
            raise ConnectionError("ESP32 antwortet nicht. Verbindung wird getrennt.")
        return ergebnisse

    def schliessen(self):
        if self.port is not None:
            try:
                self.senden("STOP")
            except Exception:
                pass
            finally:
                self.port.close()
                self.port = None
        self.bereit = False
