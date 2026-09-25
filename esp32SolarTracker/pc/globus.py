"""Globus 0.1.0: interaktive 3D-Weltkugel (QtQuick3D).

Drehen per Ziehen, Zoom per Mausrad, Klick setzt den Standort (lat/lon).
Marker und Beschriftung (Name, Breite, Laenge, Ortszeit) kommen aus Python.
"""
from pathlib import Path
from PySide6.QtCore import QUrl, Signal
from PySide6.QtQuickWidgets import QQuickWidget

QML = Path(__file__).resolve().parent / "globus.qml"


class Globus(QQuickWidget):
    ortGeaendert = Signal(float, float)

    def __init__(self):
        super().__init__()
        self.setResizeMode(QQuickWidget.SizeRootObjectToView)
        self.setMinimumHeight(360)
        self.setSource(QUrl.fromLocalFile(str(QML)))
        root = self.rootObject()
        if root is not None:
            root.ortGeklickt.connect(lambda lat, lon: self.ortGeaendert.emit(float(lat), float(lon)))

    def set_ort(self, breite, laenge, name="", zeit=""):
        root = self.rootObject()
        if root is None:
            return
        root.setProperty("markerLat", float(breite))
        root.setProperty("markerLon", float(laenge))
        root.setProperty("ortName", str(name))
        root.setProperty("ortZeit", str(zeit))

    def reset_ansicht(self):
        root = self.rootObject()
        if root is not None:
            root.resetAnsicht()

    def wheelEvent(self, event):
        # Zoom nur auf der Kugel; nicht an den umgebenden Scrollbereich weitergeben.
        super().wheelEvent(event)
        event.accept()
