"""Version 0.6.0: PC-Freigaben und unterbrochene Simulation atomar speichern."""
import json
from pathlib import Path

class BetriebsSpeicher:
    def __init__(self,pfad=None):
        self.pfad=Path(pfad) if pfad else None
        self.daten={"version":1,"ausrichtung":None,"grenzen":None,"simulation":None}
        if self.pfad and self.pfad.exists():
            daten=json.loads(self.pfad.read_text(encoding="utf-8"))
            if not isinstance(daten,dict) or daten.get("version")!=1:
                raise ValueError("Unbekanntes PC-Betriebsspeicherformat")
            self.daten.update({k:daten.get(k) for k in ("ausrichtung","grenzen","simulation")})

    def setzen(self,feld,wert):
        if self.daten[feld]==wert: return
        neu={**self.daten,feld:wert}
        if self.pfad:
            temp=self.pfad.with_suffix(".tmp")
            temp.write_text(json.dumps(neu,indent=2,allow_nan=False),encoding="utf-8")
            temp.replace(self.pfad)
        self.daten=neu
