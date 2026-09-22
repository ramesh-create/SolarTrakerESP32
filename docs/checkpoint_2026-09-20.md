# Projektstand 2026-09-20

## Aktueller Stand

Aktive Linie: **esp32SolarTracker** (ESP32-WROOM-32).
PC-Bedienfeld **0.6.1**, Firmware **PCSteuerung 0.4.3**, Dokumentation **0.28**.
Der alte Arduino-Uno-Stand unter `software/` ist archiviert.

## Am Modell bestaetigt

Am 20.09.2026 wurde Firmware 0.4.3 geladen und die **Auto Kalibrierung** erstmals
vollstaendig am Modell durchgefuehrt:

- LCD-Test und RTC-Zeitfortschritt OK.
- AZ und EL je MIN/MAX mit 114 Schritten Entlastung und Speicherung.
- Beide Grenztests und Rueckkehr zur sicheren MIN.
- Ergebnis `auto_ok=true`; Spannen **AZ=2202 / EL=1258**; Referenz und
  Grenztests gesetzt.

## Autonomer Betrieb (Firmware 0.5.0)

Ebenfalls am 20.09.2026 geprueft: `CONF` gesetzt (`conf_ok=true`), `AUTOON`
aktiviert. Beide Achsen fuhren selbststaendig zur Sonnenposition
(AZ 114 -> 297, EL 114 -> 277). `AUTOOFF` beendete den Betrieb; Referenz,
Grenztests und Spannen blieben erhalten. 102 PC-Tests bestanden.

## Behobene Fehler

- **0.4.2** Entprellung der Richtungs-Endschalter (30 ms stabil Low,
  `Entprellung.h`). Vorher loesten Prellimpulse MIN-Suche/Grenztest vorzeitig aus.
- **0.4.3** Schritttakt 3 ms -> **5 ms**. Bei 3 ms verlor der belastete 28BYJ-48
  Schritte und der Zaehler driftete.

## Wichtige Dateien

- `esp32SolarTracker/PCSteuerung/` – Firmware 0.5.1 (Protokoll 3).
- `esp32SolarTracker/pc/` – PC-Bedienfeld 0.6.2.
- `esp32SolarTracker/SolarTracker/` – Standalone-Firmware v0.8 (LCD/Joystick, seriell fernbedienbar).
- `esp32SolarTracker/tests/` – Hardwaretests.

## Naechster sinnvoller Schritt

- Autonomen Betrieb ueber laengere Zeit beobachten (Sonnenlauf, Nachtpark an
  AZ-MIN/EL-MIN, Verhalten ueber Tagesgrenzen).
- Gelegentliche Kontrolle von Endschaltern und 10-Grad-Abstand am Modell.
- PC-Bedienfeld: Autonomie-Status und `CONF` im Ablauf verifizieren.
