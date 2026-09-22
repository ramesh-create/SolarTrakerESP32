// Version 0.5.0: NOAA-Naeherung und Zielabbildung (siehe Sonne.h).
#include "Sonne.h"
#include <math.h>

namespace {
constexpr float PI_F = 3.14159265358979f;

struct Zeit { int jahr, monat, tag, stunde, minute, sekunde, wochentag; };

uint32_t tageAusDatum(int y, int m, int d) {
  y -= m <= 2;
  int era = (y >= 0 ? y : y - 399) / 400;
  unsigned yoe = unsigned(y - era * 400);
  unsigned doy = (153u * (m + (m > 2 ? -3 : 9)) + 2u) / 5u + unsigned(d) - 1u;
  unsigned doe = yoe * 365u + yoe / 4u - yoe / 100u + doy;
  return uint32_t(era * 146097 + int(doe) - 719468);
}

Zeit zeitAusEpoch(uint32_t t) {
  uint32_t tage = t / 86400u, rest = t % 86400u;
  int z = int(tage) + 719468;
  int era = (z >= 0 ? z : z - 146096) / 146097;
  unsigned doe = unsigned(z - era * 146097);
  unsigned yoe = (doe - doe / 1460u + doe / 36524u - doe / 146096u) / 365u;
  int y = int(yoe) + era * 400;
  unsigned doy = doe - (365u * yoe + yoe / 4u - yoe / 100u);
  unsigned mp = (5u * doy + 2u) / 153u;
  unsigned d = doy - (153u * mp + 2u) / 5u + 1u;
  unsigned m = mp + (mp < 10u ? 3u : -9u);
  y += (m <= 2);
  Zeit zt;
  zt.jahr = y; zt.monat = int(m); zt.tag = int(d);
  zt.stunde = int(rest / 3600u); zt.minute = int((rest % 3600u) / 60u); zt.sekunde = int(rest % 60u);
  zt.wochentag = int((tage + 4u) % 7u); // 0 = Sonntag
  return zt;
}

bool schaltjahr(int jahr) { return jahr % 4 == 0 && (jahr % 100 != 0 || jahr % 400 == 0); }

int tagImJahr(int jahr, int monat, int tag) {
  static const int vor[] = {0, 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334};
  return vor[monat] + tag + ((monat > 2 && schaltjahr(jahr)) ? 1 : 0);
}

int letzterSonntag(int jahr, int monat) {
  int tag = (monat == 3 || monat == 10) ? 31 : 30;
  if (monat == 2) tag = schaltjahr(jahr) ? 29 : 28;
  for (int d = tag; d >= 1; --d) {
    Zeit z = zeitAusEpoch(tageAusDatum(jahr, monat, d) * 86400u);
    if (z.wochentag == 0) return d;
  }
  return tag;
}

float begrenze(float wert, float unten, float oben) {
  return wert < unten ? unten : (wert > oben ? oben : wert);
}
}

int tagesversatz(uint32_t utc) {
  Zeit z = zeitAusEpoch(utc);
  uint32_t start = tageAusDatum(z.jahr, 3, letzterSonntag(z.jahr, 3)) * 86400u + 3600u;
  uint32_t ende = tageAusDatum(z.jahr, 10, letzterSonntag(z.jahr, 10)) * 86400u + 3600u;
  return (utc >= start && utc < ende) ? 2 : 1;
}

Sonnenwerte sonnenstand(uint32_t utc, int versatz, float breite, float laenge) {
  Zeit z = zeitAusEpoch(utc + uint32_t(versatz) * 3600u);
  int doy = tagImJahr(z.jahr, z.monat, z.tag);
  float stunde = z.stunde + z.minute / 60.0f + z.sekunde / 3600.0f;
  float gamma = 2.0f * PI_F / (schaltjahr(z.jahr) ? 366.0f : 365.0f) * (doy - 1 + (stunde - 12.0f) / 24.0f);
  float c = cosf(gamma), s = sinf(gamma);
  float zeitgleichung = 229.18f * (0.000075f + 0.001868f * c - 0.032077f * s - 0.014615f * cosf(2 * gamma) - 0.040849f * sinf(2 * gamma));
  float deklination = 0.006918f - 0.399912f * c + 0.070257f * s - 0.006758f * cosf(2 * gamma)
                      + 0.000907f * sinf(2 * gamma) - 0.002697f * cosf(3 * gamma) + 0.00148f * sinf(3 * gamma);
  float sonnenzeit = fmodf(stunde * 60.0f + zeitgleichung + 4.0f * laenge - 60.0f * versatz, 1440.0f);
  if (sonnenzeit < 0) sonnenzeit += 1440.0f;
  float winkel = (sonnenzeit / 4.0f - 180.0f) * PI_F / 180.0f;
  float phi = breite * PI_F / 180.0f;
  float hoehe = asinf(begrenze(sinf(phi) * sinf(deklination) + cosf(phi) * cosf(deklination) * cosf(winkel), -1.0f, 1.0f)) * 180.0f / PI_F;
  float azimut = fmodf(atan2f(sinf(winkel), cosf(winkel) * sinf(phi) - tanf(deklination) * cosf(phi)) * 180.0f / PI_F + 180.0f, 360.0f);
  if (azimut < 0) azimut += 360.0f;
  Sonnenwerte w; w.azimut = azimut; w.hoehe = hoehe; return w;
}

int zielAzimut(const Sonnenwerte& s, float azNull, int spanne, int abstand) {
  float unten = abstand * 360.0f / 4096.0f, oben = (spanne - abstand) * 360.0f / 4096.0f;
  float delta = s.azimut - azNull;
  float kandidaten[3] = {delta - 360.0f, delta, delta + 360.0f};
  float ziel = unten + delta;
  for (float k : kandidaten) {
    float p = unten + k;
    if (p >= unten && p <= oben) { ziel = p; break; }
  }
  return lroundf(begrenze(ziel, unten, oben) * 4096.0f / 360.0f);
}

int zielElevation(float sonnenhoehe, float elNeigung, int spanne, int abstand) {
  float unten = abstand * 360.0f / 4096.0f, oben = (spanne - abstand) * 360.0f / 4096.0f;
  float zielneigung = 90.0f - begrenze(sonnenhoehe, 0.0f, 90.0f);
  float ziel = unten + (elNeigung - zielneigung);
  return lroundf(begrenze(ziel, unten, oben) * 4096.0f / 360.0f);
}
