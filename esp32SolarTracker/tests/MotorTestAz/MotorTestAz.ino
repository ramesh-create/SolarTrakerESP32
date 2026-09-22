const uint8_t HALF_STEP_SEQUENCE[8][4] = {
  {1, 0, 0, 0},
  {1, 1, 0, 0},
  {0, 1, 0, 0},
  {0, 1, 1, 0},
  {0, 0, 1, 0},
  {0, 0, 1, 1},
  {0, 0, 0, 1},
  {1, 0, 0, 1}
};

const int PIN_IN1 = 16;
const int PIN_IN2 = 17;
const int PIN_IN3 = 18;
const int PIN_IN4 = 19;

const int SW_MIN = 4;
const int SW_MAX = 5;

const int STEP_DELAY_MS = 3;
const int BACKOFF_STEPS = 10;

int stepIndex = 0;
int phase = 0;

void writeStep(int idx) {
  digitalWrite(PIN_IN1, HALF_STEP_SEQUENCE[idx][0]);
  digitalWrite(PIN_IN2, HALF_STEP_SEQUENCE[idx][1]);
  digitalWrite(PIN_IN3, HALF_STEP_SEQUENCE[idx][2]);
  digitalWrite(PIN_IN4, HALF_STEP_SEQUENCE[idx][3]);
}

void releaseAxis() {
  digitalWrite(PIN_IN1, LOW);
  digitalWrite(PIN_IN2, LOW);
  digitalWrite(PIN_IN3, LOW);
  digitalWrite(PIN_IN4, LOW);
}

void moveSteps(int steps) {
  int dir = (steps >= 0) ? 1 : -1;
  int total = abs(steps);
  for (int i = 0; i < total; i++) {
    stepIndex += dir;
    if (stepIndex > 7) stepIndex = 0;
    if (stepIndex < 0) stepIndex = 7;
    writeStep(stepIndex);
    delay(STEP_DELAY_MS);
  }
  releaseAxis();
}

void setup() {
  Serial.begin(115200);
  delay(300);
  pinMode(PIN_IN1, OUTPUT);
  pinMode(PIN_IN2, OUTPUT);
  pinMode(PIN_IN3, OUTPUT);
  pinMode(PIN_IN4, OUTPUT);
  pinMode(SW_MIN, INPUT_PULLUP);
  pinMode(SW_MAX, INPUT_PULLUP);
  releaseAxis();

  Serial.println("");
  Serial.println("===== MotorTest Azimut (beeide Endschalter) =====");
  Serial.println("IN1=16 IN2=17 IN3=18 IN4=19");
  Serial.println("Endschalter: MIN=4 MAX=5 (LOW=gedrueckt)");
  Serial.println("Phase 1: Richtung MAX fahren bis Ausloesung,");
  Serial.println("  dann 10 Schritte zurueck (Entlastung).");
  Serial.println("Phase 2: Richtung MIN fahren bis Ausloesung,");
  Serial.println("  dann 10 Schritte zurueck.");
  Serial.println("Phase 3: Stillstand.");
  Serial.println("");
}

void loop() {
  if (phase == 0) {
    if (digitalRead(SW_MAX) == LOW) {
      Serial.println("MAX ausgeloest -> Entlastung");
      moveSteps(-BACKOFF_STEPS);
      Serial.println("MAX erreicht. Starte Richtung MIN (2s Pause)");
      delay(2000);
      phase = 1;
    } else {
      moveSteps(1);
    }
  } else if (phase == 1) {
    if (digitalRead(SW_MIN) == LOW) {
      Serial.println("MIN ausgeloest -> Entlastung");
      moveSteps(BACKOFF_STEPS);
      Serial.println("MIN erreicht. Fertig. Stillstand");
      phase = 2;
    } else {
      moveSteps(-1);
    }
  } else {
    while (true) { delay(10000); }
  }
}