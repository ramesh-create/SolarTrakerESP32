#include <Wire.h>
#include <RTClib.h>

#define I2C_SDA 21
#define I2C_SCL 22

RTC_DS3231 rtc;

void setup() {
  Serial.begin(115200);
  delay(500);
  Wire.begin(I2C_SDA, I2C_SCL);

  if (!rtc.begin()) {
    Serial.println("FEHLER: DS3231 nicht gefunden.");
    while (true) { delay(1000); }
  }

  Serial.println("Setze RTC auf PC-Zeit (Kompilierzeit)...");
  rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  Serial.println("RTC gesetzt.");
}

void loop() {
  DateTime now = rtc.now();
  Serial.print("Aktuelle RTC: ");
  Serial.print((now.day() < 10) ? "0" : "");
  Serial.print(now.day());
  Serial.print(".");
  Serial.print((now.month() < 10) ? "0" : "");
  Serial.print(now.month());
  Serial.print(".");
  Serial.print(now.year());
  Serial.print("  ");
  Serial.print((now.hour() < 10) ? "0" : "");
  Serial.print(now.hour());
  Serial.print(":");
  Serial.print((now.minute() < 10) ? "0" : "");
  Serial.print(now.minute());
  Serial.print(":");
  Serial.print((now.second() < 10) ? "0" : "");
  Serial.println(now.second());
  delay(1000);
}