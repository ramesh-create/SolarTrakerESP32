// Version 0.4.0: atomarer Achsdatensatz, getrennt von den alten Spannen-Schluesseln.
#pragma once
#include <stdint.h>
#include <initializer_list>
struct PositionsDaten {
  uint32_t kennung=0x53545031, spanne=0;
  int32_t position=0;
  uint32_t phase=0, flags=0, generation=0, reserve=0, summe=0;
};
constexpr uint32_t REF_OK=1, TEST_OK=2, IN_FAHRT=4;
constexpr uint32_t pruefsumme(const PositionsDaten& d) {
  uint32_t hash=2166136261u;
  for (auto v : {d.kennung,d.spanne,uint32_t(d.position),d.phase,d.flags,d.generation,d.reserve}) {
    for (int i=0;i<4;++i) { hash=(hash^(v&255))*16777619u; v>>=8; }
  }
  return hash;
}
constexpr PositionsDaten positionsDaten(int spanne,int position,int phase,bool referenz,bool test,bool fahrt,uint32_t generation) {
  PositionsDaten d;
  d.spanne=spanne; d.position=position; d.phase=phase;
  d.flags=(referenz?REF_OK:0)|(test?TEST_OK:0)|(fahrt?IN_FAHRT:0);
  d.generation=generation; d.summe=pruefsumme(d); return d;
}
constexpr bool datenGueltig(const PositionsDaten& d) {
  if (d.kennung!=0x53545031 || d.summe!=pruefsumme(d) || d.phase>7 || d.flags>7 || d.reserve) return false;
  if (d.spanne && (d.spanne<=228 || d.spanne>4096)) return false;
  if ((d.flags&(REF_OK|TEST_OK)) && !d.spanne) return false;
  if ((d.flags&REF_OK) && (d.position<114 || d.position>int(d.spanne)-114)) return false;
  return true;
}
constexpr bool referenzLaden(const PositionsDaten& d) {
  return datenGueltig(d) && (d.flags&REF_OK) && !(d.flags&IN_FAHRT);
}
constexpr bool testsLaden(const PositionsDaten& d) {
  return datenGueltig(d) && (d.flags&TEST_OK);
}
constexpr bool speicherPruefung() {
  auto d=positionsDaten(2145,700,3,true,true,false,8);
  if (!referenzLaden(d) || !testsLaden(d)) return false;
  auto bewegt=positionsDaten(2145,700,3,true,true,true,8);
  if (referenzLaden(bewegt) || !testsLaden(bewegt)) return false;
  d.position++; if (datenGueltig(d)) return false; // Beschaedigter Datensatz.
  auto falsch=positionsDaten(2145,10,3,true,true,false,8);
  if (datenGueltig(falsch)) return false;
  auto unbekannt=positionsDaten(2145,0,0,false,true,false,8);
  if (referenzLaden(unbekannt) || !testsLaden(unbekannt)) return false;
  return !datenGueltig(positionsDaten(0,0,0,true,true,false,0));
}
static_assert(sizeof(PositionsDaten)==32,"Speicherformat muss 32 Byte bleiben");
static_assert(speicherPruefung(),"Positionsspeicher: Wiederherstellung ungueltig");
