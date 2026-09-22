// LCD-Anbindung 0.3.2: zwei ASCII-Zeilen als Hex, je 16 Zeichen.
#pragma once
const char* lcdTextSenden(const char* zeile1, const char* zeile2);
bool lcdErreichbar();
