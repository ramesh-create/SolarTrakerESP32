"""Version 0.1.0: Sonnenstand und Abbildung auf kalibrierte Motorwinkel.

Eingabe: Datum mit Zeitzone, Standort; Ausgabe: Grad (Nord=0, Ost=90).
NOAA-Naeherung aus dem bestehenden NOAA.cpp, ohne feste Sommerzeit.
"""
from datetime import datetime
import calendar
import math


def sonnenstand(zeit: datetime, breite: float, laenge: float) -> tuple[float, float]:
    if zeit.utcoffset() is None:
        raise ValueError("Datum braucht einen UTC-Versatz")
    if not (math.isfinite(breite) and math.isfinite(laenge) and -90 <= breite <= 90 and -180 <= laenge <= 180):
        raise ValueError("Standort ausserhalb des Wertebereichs")
    stunde = zeit.hour + zeit.minute / 60 + zeit.second / 3600
    gamma = 2 * math.pi / (366 if calendar.isleap(zeit.year) else 365) * (zeit.timetuple().tm_yday - 1 + (stunde - 12) / 24)
    c, s = math.cos, math.sin
    zeitgleichung = 229.18 * (0.000075 + 0.001868*c(gamma) - 0.032077*s(gamma) - 0.014615*c(2*gamma) - 0.040849*s(2*gamma))
    deklination = (0.006918 - 0.399912*c(gamma) + 0.070257*s(gamma)
                   - 0.006758*c(2*gamma) + 0.000907*s(2*gamma)
                   - 0.002697*c(3*gamma) + 0.00148*s(3*gamma))
    versatz = zeit.utcoffset().total_seconds() / 3600
    sonnenzeit = (stunde*60 + zeitgleichung + 4*laenge - 60*versatz) % 1440
    winkel = math.radians(sonnenzeit/4 - 180)
    phi = math.radians(breite)
    hoehe = math.degrees(math.asin(max(-1, min(1, s(phi)*s(deklination) + c(phi)*c(deklination)*c(winkel)))))
    azimut = (math.degrees(math.atan2(s(winkel), c(winkel)*s(phi) - math.tan(deklination)*c(phi))) + 180) % 360
    return azimut, hoehe


def motorziel(weltwinkel: float, nullpunkt: float, status: dict, kreis: bool = False) -> float:
    """Nur erreichbare Ziele zulassen; Grenzen kommen vom ESP32 (Schritte)."""
    if not status["calibrated"] or not status["referenced"]:
        raise ValueError("Achse zuerst kalibrieren und referenzieren")
    if not all(math.isfinite(v) for v in (weltwinkel, nullpunkt)):
        raise ValueError("Ungueltiger Winkel")
    ziel = weltwinkel - nullpunkt
    kandidaten = [ziel - 360, ziel, ziel + 360] if kreis else [ziel]
    unten = status["margin"] * 360 / 4096
    oben = (status["span"] - status["margin"]) * 360 / 4096
    for kandidat in kandidaten:
        if unten <= kandidat <= oben:
            return kandidat
    raise ValueError("Sonnenposition ausserhalb des kalibrierten 10-Grad-Bereichs")
