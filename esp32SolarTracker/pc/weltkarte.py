"""Weltkarte 0.2.0: Panel-Standort als Punkt, mit Zoom, Pan und Drag & Drop.

Eingabe: Breite/Laenge (Grad) oder Maus. Ausgabe: gezeichneter Marker und
Signal ortGeaendert. Offline, kein Netz.
Das Bild `weltkarte.png` ist eine vom Nutzer bereitgestellte Plexus-Weltkarte
(2:1, dunkler Hintergrund, equirectangular, randlos).
"""
from pathlib import Path
from PySide6.QtCore import Qt, QRectF, Signal, QPointF
from PySide6.QtGui import QPainter, QPixmap, QColor, QPen, QFont, QBrush, QCursor
from PySide6.QtWidgets import QWidget

BILD = Path(__file__).resolve().parent / "weltkarte.png"
ZOOM_MAX = 16.0
GREIFRADIUS = 14


def kartenpunkt(breite, laenge):
    """Equirectangular: Bildanteile (0..1) fuer Breite/Laenge. Nord/links = 0."""
    fx = (float(laenge) + 180.0) / 360.0
    fy = (90.0 - float(breite)) / 180.0
    return min(1.0, max(0.0, fx)), min(1.0, max(0.0, fy))


def ort_aus_bildanteil(fx, fy):
    """Umkehrung: Bildanteile (0..1) -> Breite/Laenge (Grad)."""
    breite = 90.0 - min(1.0, max(0.0, float(fy))) * 180.0
    laenge = min(1.0, max(0.0, float(fx))) * 360.0 - 180.0
    return breite, laenge


class Weltkarte(QWidget):
    ortGeaendert = Signal(float, float)

    def __init__(self, kompakt=False):
        super().__init__()
        self.breite = None
        self.laenge = None
        self.kompakt = kompakt
        self.bearbeitbar = False
        self.bild = QPixmap(str(BILD)) if BILD.exists() else QPixmap()
        # Sichtbarer Ausschnitt im Bildanteils-Raum (quadratisch -> 2:1 bleibt).
        self.ansicht = QRectF(0.0, 0.0, 1.0, 1.0)
        self._modus = None
        self._start = QPointF()
        self._ansicht_start = QRectF(self.ansicht)
        self.setMinimumHeight(120 if kompakt else 220)
        self.setToolTip("Panel-Standort aus Breite/Laenge; Punkt aus den Koordinaten berechnet")

    # --- Steuerung von aussen -------------------------------------------------
    def set_bearbeitbar(self, wert):
        self.bearbeitbar = bool(wert)
        self.setMouseTracking(self.bearbeitbar)
        self.setCursor(QCursor(Qt.CrossCursor if self.bearbeitbar else Qt.ArrowCursor))

    def set_ort(self, breite, laenge):
        if getattr(self, "_modus", None) == "marker":
            return  # waehrend des Ziehens keine externen Updates
        try:
            self.breite = float(breite)
            self.laenge = float(laenge)
        except (TypeError, ValueError):
            self.breite = self.laenge = None
        self.update()

    def reset_ansicht(self):
        self.ansicht = QRectF(0.0, 0.0, 1.0, 1.0)
        self.update()

    # --- Geometrie ------------------------------------------------------------
    def kartenrechteck(self, w, h):
        if w / max(1, h) >= 2:
            mh = h
            mw = 2 * h
        else:
            mw = w
            mh = w / 2
        return (w - mw) / 2, (h - mh) / 2, mw, mh

    def _begrenzen(self):
        bw, bh = self.ansicht.width(), self.ansicht.height()
        x = min(max(0.0, self.ansicht.x()), 1.0 - bw)
        y = min(max(0.0, self.ansicht.y()), 1.0 - bh)
        self.ansicht = QRectF(x, y, bw, bh)

    def maus_bildanteil(self, pos):
        x0, y0, mw, mh = self.kartenrechteck(self.width(), self.height())
        if not (x0 <= pos.x() <= x0 + mw and y0 <= pos.y() <= y0 + mh):
            return None
        fx = self.ansicht.x() + (pos.x() - x0) / mw * self.ansicht.width()
        fy = self.ansicht.y() + (pos.y() - y0) / mh * self.ansicht.height()
        return min(1.0, max(0.0, fx)), min(1.0, max(0.0, fy))

    def bildanteil_bildschirm(self, fx, fy):
        x0, y0, mw, mh = self.kartenrechteck(self.width(), self.height())
        mx = x0 + (fx - self.ansicht.x()) / self.ansicht.width() * mw
        my = y0 + (fy - self.ansicht.y()) / self.ansicht.height() * mh
        return mx, my

    # --- Maus -----------------------------------------------------------------
    def mousePressEvent(self, event):
        if not self.bearbeitbar or event.button() != Qt.LeftButton:
            return super().mousePressEvent(event)
        self._start = event.position()
        self._ansicht_start = QRectF(self.ansicht)
        x0, y0, mw, mh = self.kartenrechteck(self.width(), self.height())
        nah = False
        if self.breite is not None and self.laenge is not None:
            fx, fy = kartenpunkt(self.breite, self.laenge)
            mx, my = self.bildanteil_bildschirm(fx, fy)
            nah = (QPointF(mx, my) - self._start).manhattanLength() <= GREIFRADIUS
        self._modus = "marker" if nah else "pan"

    def mouseMoveEvent(self, event):
        if not self.bearbeitbar or self._modus is None:
            return super().mouseMoveEvent(event)
        if self._modus == "marker":
            anteil = self.maus_bildanteil(event.position())
            if anteil:
                self.breite, self.laenge = ort_aus_bildanteil(*anteil)
                self.update()
        else:
            x0, y0, mw, mh = self.kartenrechteck(self.width(), self.height())
            dx = (event.position().x() - self._start.x()) / mw * self._ansicht_start.width()
            dy = (event.position().y() - self._start.y()) / mh * self._ansicht_start.height()
            self.ansicht = QRectF(self._ansicht_start.x() - dx, self._ansicht_start.y() - dy,
                                  self._ansicht_start.width(), self._ansicht_start.height())
            self._begrenzen()
            self.update()

    def mouseReleaseEvent(self, event):
        if not self.bearbeitbar:
            return super().mouseReleaseEvent(event)
        modus = self._modus
        self._modus = None
        if modus == "marker" and self.breite is not None and self.laenge is not None:
            self.ortGeaendert.emit(self.breite, self.laenge)

    def mouseDoubleClickEvent(self, event):
        if self.bearbeitbar:
            self.reset_ansicht()
        else:
            super().mouseDoubleClickEvent(event)

    def wheelEvent(self, event):
        if not self.bearbeitbar:
            return super().wheelEvent(event)
        anteil = self.maus_bildanteil(event.position())
        if not anteil:
            return
        faktor = 1.25 if event.angleDelta().y() > 0 else 1 / 1.25
        neu = min(ZOOM_MAX, max(1.0, 1.0 / self.ansicht.width() * faktor))
        relx = (anteil[0] - self.ansicht.x()) / self.ansicht.width()
        rely = (anteil[1] - self.ansicht.y()) / self.ansicht.height()
        nw = 1.0 / neu
        self.ansicht = QRectF(anteil[0] - relx * nw, anteil[1] - rely * nw, nw, nw)
        self._begrenzen()
        self.update()

    # --- Zeichnen -------------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor("#0d1117"))
        if self.bild.isNull():
            p.setPen(QColor("#97a8bb"))
            p.drawText(self.rect(), Qt.AlignCenter, "Kartenbild weltkarte.png fehlt")
            return
        x0, y0, mw, mh = self.kartenrechteck(w, h)
        iw, ih = self.bild.width(), self.bild.height()
        quelle = QRectF(self.ansicht.x() * iw, self.ansicht.y() * ih,
                        self.ansicht.width() * iw, self.ansicht.height() * ih)
        p.drawPixmap(QRectF(x0, y0, mw, mh), self.bild, quelle)
        p.setPen(QPen(QColor("#243140"), 1)); p.setBrush(Qt.NoBrush)
        p.drawRect(QRectF(x0, y0, mw, mh))
        if self.bearbeitbar:
            p.setPen(QColor("#97a8bb")); p.setFont(QFont("Segoe UI", 8))
            p.drawText(int(x0 + 6), int(y0 + 14), f"{1.0/self.ansicht.width():.1f}x  (Rad=Zoom, Doppelklick=Reset)")
        if self.breite is None or self.laenge is None:
            p.setPen(QColor("#97a8bb"))
            p.drawText(self.rect(), Qt.AlignBottom | Qt.AlignHCenter, "Standort unbekannt")
            return
        fx, fy = kartenpunkt(self.breite, self.laenge)
        mx, my = x0 + (fx - self.ansicht.x()) / self.ansicht.width() * mw, y0 + (fy - self.ansicht.y()) / self.ansicht.height() * mh
        if not (x0 - 2 <= mx <= x0 + mw + 2 and y0 - 2 <= my <= y0 + mh + 2):
            return
        r = 4 if self.kompakt else 6
        p.setPen(QPen(QColor("#000000"), 2)); p.setBrush(QBrush(QColor("#ff5252")))
        p.drawEllipse(QRectF(mx - r, my - r, 2 * r, 2 * r))
        p.setPen(QPen(QColor("#ff5252"), 2))
        p.drawLine(int(mx - 2 * r), int(my), int(mx + 2 * r), int(my))
        p.drawLine(int(mx), int(my - 2 * r), int(mx), int(my + 2 * r))
        if not self.kompakt:
            p.setFont(QFont("Segoe UI", 9, QFont.Bold)); p.setPen(QColor("#ffffff"))
            p.drawText(int(mx) + 10, int(my) - 8, f"{self.breite:.3f}, {self.laenge:.3f}")
