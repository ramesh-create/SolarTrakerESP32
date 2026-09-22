"""Version 0.5.1: Tageslichtfenster und Ziele ab der sicheren Startposition."""
from datetime import timedelta
from sonne import sonnenstand
import math


def sonnenfenster(tag, breite, laenge):
    """Geometrischer Horizont (Sonnenhoehe 0 Grad), auf eine Sekunde aufgeloest.

    Nur Tage mit Auf- und Untergang; Polartag/-nacht werden explizit gemeldet.
    Die bestehende NOAA-Naeherung bleibt die einzige Sonnenberechnung.
    """
    start = tag.replace(hour=0, minute=0, second=0, microsecond=0)
    vorher = start
    hell = sonnenstand(vorher, breite, laenge)[1] > 0
    auf = unter = None
    for minute in range(1, 1441):
        jetzt = start + timedelta(minutes=minute)
        neu = sonnenstand(jetzt, breite, laenge)[1] > 0
        if neu != hell:
            links, rechts = vorher, jetzt
            while (rechts-links).total_seconds() > 1:
                mitte = links + (rechts-links)/2
                if (sonnenstand(mitte, breite, laenge)[1] > 0) == hell:
                    links = mitte
                else:
                    rechts = mitte
            if neu:
                auf = rechts
            elif auf is not None:
                unter = rechts
                break
        vorher, hell = jetzt, neu
    if auf is None or unter is None:
        raise ValueError("Kein vollstaendiger Sonnenauf- und -untergang an diesem Datum (Polartag/-nacht oder Tagesgrenze).")
    return auf, unter


def startziel(achse):
    if not achse["calibrated"] or not achse["referenced"]:
        raise ValueError("Achse zuerst kalibrieren und referenzieren")
    return achse["margin"] * 360 / 4096


def tagesziel(winkel, startwinkel, achse, kreis=False):
    """Startwinkel gilt an sicherer MIN, nicht am gedrueckten Endschalter.

    Nicht erreichbare Sonnenwinkel werden an der sicheren Fahrgrenze begrenzt.
    Rueckgabe: Motorwinkel und Kennzeichen fuer die Begrenzung.
    """
    unten = startziel(achse)
    oben = (achse["span"]-achse["margin"]) * 360 / 4096
    if not math.isfinite(winkel) or not math.isfinite(startwinkel):
        raise ValueError("Ungueltiger Sonnenwinkel")
    delta = winkel-startwinkel
    if kreis:
        # Zum erreichbaren Bogen naechste Darstellung, auch ueber Norden hinweg.
        delta = min((delta-360, delta, delta+360),
                    key=lambda d: abs(d-min(oben-unten, max(0,d))))
    ziel = unten+delta
    begrenzt = min(oben,max(unten,ziel))
    return begrenzt, abs(begrenzt-ziel) > 1e-7


def elevationsziel(sonnenhoehe, startneigung, achse):
    """Panel senkrecht = 90 Grad Neigung; Sonnenhoehe = Winkel der Flaechennormale.

    Die Panelneigung fuer senkrechten Lichteinfall ist 90 - Sonnenhoehe.
    Positive Motorschritte kippen von senkrecht in Richtung waagerecht.
    """
    zielneigung = 90-max(0,min(90,sonnenhoehe))
    return tagesziel(startneigung-zielneigung,0,achse)


def panelneigung(startneigung, achse):
    """Tatsaechliche Neigung aus referenzierten Schritten, keine Sensormessung."""
    if not achse["referenced"]:
        return None
    return startneigung-(achse["position"]-achse["margin"])*360/4096
