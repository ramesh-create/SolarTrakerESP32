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

const int PIN_IN1 = 25;
const int PIN_IN2 = 26;
const int PIN_IN3 = 27;
const int PIN_IN4 = 14;

const int SW_MIN = 15;
const int SW_MAX = 12;

const int STEP_DELAY_MS = 3;
const int BACKOFF_MAX_STEPS = 512;

int stepIndex = 0;
int phase = 0;

// Faehrt schrittweise so lange in awayDir, bis der Schalter wieder offen (HIGH) ist.
void backOffUntilOpen(int awayDir, const char* name, int switchPin) {
  int steps = 0;
  while (digitalRead(switchPin) == LOW && steps < BACKOFF_MAX_STEPS) {
    moveSteps(awayDir);
    steps += abs(awayDir);
    if (steps % 50 == 0) {
      Serial.print("  Entlastung ... ");
      Serial.print(steps);
      Serial.println(" Schritte");
    }
  }
  Serial.print(name);
  Serial.print(" entlastet, freigegeben nach ");
  Serial.print(steps);
  Serial.println(" Schritten.");
}

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
  Serial.println("===== MotorTest Elevation (beide Endschalter) =====");
  Serial.println("IN1=25 IN2=26 IN3=27 IN4=14");
  Serial.println("Endschalter: MIN=15 MAX=12 (LOW=gedrueckt)");
  Serial.println("Phase 1: Richtung MAX fahren.");
  Serial.println("Phase 2: Richtung MIN fahren.");
  Serial.println("Phase 3: Stillstand.");
  Serial.println("");
}

void loop() {
  if (phase == 0) {
    if (digitalRead(SW_MAX) == LOW) {
      Serial.println("MAX ausgeloest -> Entlastung (zurueck bis Schalter offen)");
      backOffUntilOpen(-1, "MAX", SW_MAX);
      delay(2000);
      phase = 1;
    } else {
      moveSteps(1);
    }
  } else if (phase == 1) {
    if (digitalRead(SW_MIN) == LOW) {
      Serial.println("MIN ausgeloest -> Entlastung (vor bis Schalter offen)");
      backOffUntilOpen(1, "MIN", SW_MIN);
      Serial.println("Fertig. Stillstand");
      phase = 2;
    } else {
      moveSteps(-1);
    }
  } else {
    while (true) { delay(10000); }
  }
}