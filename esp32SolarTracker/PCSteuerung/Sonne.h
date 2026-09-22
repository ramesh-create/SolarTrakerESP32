#pragma once
#include <stdint.h>
// Version 0.5.0: Sonnenstand und Zielabbildung fuer den autonomen Betrieb.
// Portiert aus pc/sonne.py und pc/tageslauf.py, damit PC und ESP32 gleich rechnen.
struct Sonnenwerte { float azimut, hoehe; };
struct Kalender { int jahr, monat, tag, stunde, minute, sekunde; };
// Kalenderdaten aus UTC + Zeitzonenversatz (fuer die LCD-Anzeige).
Kalender kalenderZeit(uint32_t utcSekunden, int versatz);
// EU-Zeitzone aus UTC: +2 (MESZ) zwischen letztem So. Maerz und letztem So. Oktober, sonst +1.
int tagesversatz(uint32_t utcSekunden);
Sonnenwerte sonnenstand(uint32_t utcSekunden, int versatz, float breite, float laenge);
// Motorziel in Schritten, innerhalb [abstand, spanne-abstand] begrenzt.
int zielAzimut(const Sonnenwerte& s, float azNull, int spanne, int abstand);
int zielElevation(float sonnenhoehe, float elNeigung, int spanne, int abstand);
