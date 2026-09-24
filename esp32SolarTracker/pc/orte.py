"""Orte 0.1.0: naechstgelegener Ort/Land aus einer Offline-Liste.

Quelle: Natural Earth `ne_110m_populated_places` (public domain), 243 Orte.
Nur ein Vorschlag, keine Gewaehr; der Bediener kann den Text aendern.
"""
import json
import math
from pathlib import Path

DATEI = Path(__file__).resolve().parent / "orte.json"


def _laden():
    try:
        daten = json.loads(DATEI.read_text(encoding="utf-8"))
        return [(str(n), str(l), float(b), float(g)) for n, l, b, g in daten.get("orte", [])]
    except (OSError, ValueError, TypeError):
        return []


_ORTE = _laden()


def vorschlag(breite, laenge):
    """Naechsten Ort als (Stadt, Land) zu Breite/Laenge; None ohne Daten."""
    if not _ORTE or not (math.isfinite(breite) and math.isfinite(laenge)):
        return None
    best = None
    for stadt, land, b, g in _ORTE:
        dx = (g - laenge) * math.cos(math.radians((b + breite) / 2.0))
        dy = b - breite
        d = dx * dx + dy * dy
        if best is None or d < best[0]:
            best = (d, stadt, land)
    return best[1], best[2]
