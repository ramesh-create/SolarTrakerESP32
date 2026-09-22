#include <Arduino.h>

#define JOY_X 35
#define JOY_Y 32
#define JOY_SW 12
#define RANGE 150

int midX = 780;
int midY = 740;

void setup() {
  Serial.begin(115200);
  while (!Serial) {}
  analogReadResolution(10);
  pinMode(JOY_X, INPUT);
  pinMode(JOY_Y, INPUT);
  pinMode(JOY_SW, INPUT_PULLUP);

  Serial.println("");
  Serial.println("===== Joystick Test (fest: vertikal=X, horizontal=Y) =====");
  Serial.println("X=35 Y=32 SW=12");
  Serial.println("");
}

void loop() {
  int x = analogRead(JOY_X);
  int y = analogRead(JOY_Y);
  bool pressed = (digitalRead(JOY_SW) == LOW);

  int dx = x - midX;
  int dy = y - midY;

  Serial.print("X=");
  Serial.print(x);
  Serial.print(" Y=");
  Serial.print(y);
  Serial.print("  => ");

  if (pressed) {
    Serial.println("ENTER");
  } else if (abs(dx) > RANGE || abs(dy) > RANGE) {
    if (abs(dx) >= abs(dy)) {
      Serial.println(dx > 0 ? "UP" : "DOWN");
    } else {
      Serial.println(dy > 0 ? "RIGHT" : "LEFT");
    }
  } else {
    Serial.println("Mitte");
  }
  delay(100);
}