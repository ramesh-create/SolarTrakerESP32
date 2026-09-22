#include <Wire.h>
#include <RTClib.h>

#define I2C_SDA 21
#define I2C_SCL 22

RTC_DS3231 rtc;

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("==============================");
  Serial.println("SolarTracker - DS3231 RTC Test");
  Serial.println("==============================");

  Wire.begin(I2C_SDA, I2C_SCL);

  Serial.println("Suche DS3231...");

  if (!rtc.begin()) {
    Serial.println("FEHLER: DS3231 nicht gefunden!");
    Serial.println();
    Serial.println("Bitte pruefen:");
    Serial.println("VCC -> 3.3V");
    Serial.println("GND -> GND");
    Serial.println("SDA -> GPIO21");
    Serial.println("SCL -> GPIO22");

    while (true) {
      delay(1000);
    }
  }

  Serial.println("DS3231 gefunden!");

  if (rtc.lostPower()) {
    Serial.println("WARNUNG: RTC hat ihre Uhrzeit verloren.");
    Serial.println("Setze Uhrzeit auf Kompilierzeit...");
    rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
    Serial.println("Uhrzeit gesetzt.");
  }

  Serial.println();
  Serial.println("RTC-Test gestartet.");
  Serial.println();
}

void loop() {
  DateTime now = rtc.now();

  Serial.print("Datum: ");
  print2digits(now.day());
  Serial.print(".");
  print2digits(now.month());
  Serial.print(".");
  Serial.print(now.year());

  Serial.print("   Uhrzeit: ");
  print2digits(now.hour());
  Serial.print(":");
  print2digits(now.minute());
  Serial.print(":");
 print2digits(now.second());

 Serial.print("   Temperatur: ");
 Serial.print(rtc.getTemperature(),  1);
 Serial.println(" C");

 delay(1000);
}



void print2digits(int number) {
  if (number <  10) {
    Serial.print("0");
  }
 Serial.print(number);
}