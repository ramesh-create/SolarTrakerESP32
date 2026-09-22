// Reine Protokollpruefung, Version 0.3.2. Kein Zugriff auf Hardware.
#pragma once
constexpr int hexZiffer(char c) {
  return c >= '0' && c <= '9' ? c-'0' :
         c >= 'a' && c <= 'f' ? c-'a'+10 :
         c >= 'A' && c <= 'F' ? c-'A'+10 : -1;
}
constexpr bool lcdZeileGueltig(const char* text) {
  if (!text) return false;
  for (int i=0; i<16; ++i) {
    if (!text[2*i] || !text[2*i+1]) return false;
    int oben=hexZiffer(text[2*i]), unten=hexZiffer(text[2*i+1]);
    if (oben<0 || unten<0 || oben*16+unten<32 || oben*16+unten>126) return false;
  }
  return text[32]==0;
}
static_assert(lcdZeileGueltig("536f6c6172547261636b657220202020"), "16 Zeichen erlaubt");
static_assert(!lcdZeileGueltig("20"), "Zu kurz ablehnen");
static_assert(!lcdZeileGueltig("2020202020202020202020202020202020"), "Zu lang ablehnen");
static_assert(!lcdZeileGueltig("0020202020202020202020202020202020"), "Steuerzeichen ablehnen");
static_assert(!lcdZeileGueltig("zz20202020202020202020202020202020"), "Kein Hex ablehnen");
