#include <Arduino.h>

const char* name_AZ_MIN = "AZ_MIN [GPIO 4]";
const char* name_AZ_MAX = "AZ_MAX [GPIO 5]";
const char* name_EL_MIN = "EL_MIN [GPIO 15]";
const char* name_EL_MAX = "EL_MAX [GPIO 12]";

void setup() {
  Serial.begin(115200);
  while(!Serial) { }
  pinMode(4, INPUT_PULLUP);
  pinMode(5, INPUT_PULLUP);
  pinMode(15, INPUT_PULLUP);
  pinMode(12, INPUT_PULLUP);
  Serial.println("");
  Serial.println("===== Endschalter Test gestartet =====");
  Serial.println("Schalter gegen GND => LOW = GEDRUECKT");
}

void printSwitch(int pin, const char* name) {
  bool gedrueckt = (digitalRead(pin) == LOW);
  Serial.print(name);
  Serial.print(": ");
  Serial.println(gedrueckt ? "GEDRUECKT" : "offen");
}

void loop() {
  Serial.println("");
  Serial.println("----- Endschalter -----");
  printSwitch(4, name_AZ_MIN);
  printSwitch(5, name_AZ_MAX);
  printSwitch(15, name_EL_MIN);
  printSwitch(12, name_EL_MAX);
  delay(100);
}