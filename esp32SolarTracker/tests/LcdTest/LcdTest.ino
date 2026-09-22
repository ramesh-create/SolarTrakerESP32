#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#define I2C_SDA 21
#define I2C_SCL 22
#define LCD_ADDR 0x27

const char TEST_VERSION[] = "0.2";
LiquidCrystal_I2C lcd(LCD_ADDR, 16, 2);
bool lcdInitialisiert = false;

void pruefeLcd() {
  Wire.beginTransmission(LCD_ADDR);
  const uint8_t fehler = Wire.endTransmission();
  if (fehler != 0) {
    lcdInitialisiert = false;
    Serial.print("LCD 0x27 antwortet nicht. I2C-Fehler: ");
    Serial.println(fehler);
    return;
  }

  if (!lcdInitialisiert) {
    // init() setzt auch den internen Ausgangszustand der Bibliothek.
    lcd.init();
    lcd.backlight();
    lcd.display();
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("SolarTracker");
    lcd.setCursor(0, 1);
    lcd.print("LCD Test OK");
    lcdInitialisiert = true;
  }
  // Eine I2C-Antwort bestaetigt noch nicht die sichtbare Textausgabe.
  Serial.println("I2C 0x27 erreichbar; Text gesendet. Sichtpruefung am LCD erforderlich.");
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.print("SolarTracker - LCD-Test Version ");
  Serial.println(TEST_VERSION);
  Wire.begin(I2C_SDA, I2C_SCL, 100000);
  Wire.setTimeOut(50);
  Serial.println("I2C-Suche: SDA GPIO21, SCL GPIO22");
  uint8_t gefunden = 0;
  for (uint8_t adresse = 1; adresse < 127; adresse++) {
    Wire.beginTransmission(adresse);
    if (Wire.endTransmission() == 0) {
      Serial.print("I2C-Geraet gefunden: 0x");
      if (adresse < 16) Serial.print('0');
      Serial.println(adresse, HEX);
      gefunden++;
    }
  }
  if (gefunden == 0) Serial.println("Kein I2C-Geraet gefunden: Verkabelung und Versorgung pruefen.");
  pruefeLcd();
}

void loop() {
  delay(3000);
  pruefeLcd();
}
