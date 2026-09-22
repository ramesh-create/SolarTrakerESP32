#include <Arduino.h>

#define JOY_X 35
#define JOY_Y 32
#define JOY_SW 12

#define RANGE 150
#define SAMPLE_MS 500

float midX = 512.0f;
float midY = 512.0f;

// Normalisierte Achsenrichtungs-Vektoren aus der Kalibrierung
float vertVx = 0.0f;
float vertVy = 0.0f;
float horizVx = 0.0f;
float horizVy = 0.0f;

bool waitPress() {
  while (digitalRead(JOY_SW) != LOW) { delay(10); }
  delay(50);
  return true;
}

void waitRelease() {
  while (digitalRead(JOY_SW) == LOW) { delay(10); }
  delay(100);
}

void sample(int* outX, int* outY) {
  long sx = 0, sy = 0;
  int n = 0;
  unsigned long t = millis();
  while (millis() - t < SAMPLE_MS) {
    sx += analogRead(JOY_X);
    sy += analogRead(JOY_Y);
    n++;
    delay(2);
  }
  *outX = (int)(sx / n);
  *outY = (int)(sy / n);
}

int centerX = 0, centerY = 0;
int upX, upY, downX, downY, leftX, leftY, rightX, rightY;

void calStep(const char* msg, int* x, int* y) {
  Serial.print("Halte jetzt: ");
  Serial.println(msg);
  Serial.println("  und druecke ENTER zum Bestaetigen ...");
  waitPress();
  sample(x, y);
  Serial.print("  gemessen X=");
  Serial.print(*x);
  Serial.print(" Y=");
  Serial.println(*y);
  waitRelease();
}

void setup() {
  Serial.begin(115200);
  while (!Serial) {}
  analogReadResolution(10);
  pinMode(JOY_X, INPUT);
  pinMode(JOY_Y, INPUT);
  pinMode(JOY_SW, INPUT_PULLUP);

  Serial.println("");
  Serial.println("===== Joystick Auto-Kalibrierung (Vektor) =====");
  Serial.println("X=35 Y=32 SW=12");
  Serial.println("Befolge die Anweisungen. ENTER = Taster am Stick.");
  Serial.println("");

  calStep("MITTE (Ruhelage)", &centerX, &centerY);
  calStep("OBEN (gerade nach oben)", &upX, &upY);
  calStep("UNTER (gerade nach unten)", &downX, &downY);
  calStep("RECHTS (gerade nach rechts)", &rightX, &rightY);
  calStep("LINKS (gerade nach links)", &leftX, &leftY);

  midX = (centerX == 0) ? 512.0f : (float)centerX;
  midY = (centerY == 0) ? 512.0f : (float)centerY;

  // Vertikale Achse aus OBEN - UNTER
  float vx = (float)(upX - downX);
  float vy = (float)(upY - downY);
  float vl = sqrt(vx * vx + vy * vy);
  if (vl > 0) { vertVx = vx / vl; vertVy = vy / vl; }

  // Horizontale Achse aus RECHTS - LINKS
  float hx = (float)(rightX - leftX);
  float hy = (float)(rightY - leftY);
  float hl = sqrt(hx * hx + hy * hy);
  if (hl > 0) { horizVx = hx / hl; horizVy = hy / hl; }

  Serial.println("");
  Serial.println("===== Kalibrierung fertig =====");
  Serial.print("Mitte: X=");
  Serial.print((int)midX);
  Serial.print(" Y=");
  Serial.println((int)midY);
  Serial.println("Achsen-Vektoren berechnet.");
  Serial.println("");
  Serial.println("Live-Test (bewege den Stick):");
}

void loop() {
  float x = (float)analogRead(JOY_X);
  float y = (float)analogRead(JOY_Y);
  bool pressed = (digitalRead(JOY_SW) == LOW);

  float dx = x - midX;
  float dy = y - midY;

  // Projektion auf die beiden kalibrierten Achsen
  float pv = dx * vertVx + dy * vertVy;   // positiv = OBEN
  float ph = dx * horizVx + dy * horizVy; // positiv = RECHTS

  Serial.print("X=");
  Serial.print((int)x);
  Serial.print(" Y=");
  Serial.print((int)y);
  Serial.print("  => ");

  if (pressed) {
    Serial.println("ENTER");
  } else if (abs(pv) > RANGE || abs(ph) > RANGE) {
    if (abs(pv) >= abs(ph)) {
      Serial.println(pv > 0 ? "UP" : "DOWN");
    } else {
      Serial.println(ph > 0 ? "RIGHT" : "LEFT");
    }
  } else {
    Serial.println("Mitte");
  }
  delay(100);
}