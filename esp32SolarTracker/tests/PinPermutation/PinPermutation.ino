const uint8_t SEQ[8][4] = {
  {1,0,0,0},{1,1,0,0},{0,1,0,0},{0,1,1,0},
  {0,0,1,0},{0,0,1,1},{0,0,0,1},{1,0,0,1}
};

const int BASE[4] = {25, 26, 27, 14};
const int STEP_DELAY_MS = 3;
bool found = false;

void writeStep(int idx, int* order) {
  digitalWrite(order[0], SEQ[idx][0]);
  digitalWrite(order[1], SEQ[idx][1]);
  digitalWrite(order[2], SEQ[idx][2]);
  digitalWrite(order[3], SEQ[idx][3]);
}

void release(int* order) {
  for (int i = 0; i < 4; i++) digitalWrite(order[i], LOW);
}

// Drehe 100 Schritte; true wenn die Drehung vorankommt ist schwer festzustellen,
// daher lassen wir es visuell pruefen und stoppen nach jedem Test kurz.
void spin(int* order) {
  int s = 0;
  for (int i = 0; i < 200; i++) {
    s++; if (s > 7) s = 0;
    writeStep(s, order);
    delay(STEP_DELAY_MS);
  }
  release(order);
}

void setup() {
  for (int i = 0; i < 4; i++) pinMode(BASE[i], OUTPUT);
  Serial.begin(115200);
  delay(300);
  Serial.println("PinPermutation Elevation:");
  Serial.println("Probiert 024 Permutationen von 25/26/27/14.");
  Serial.println("Beobachte, bei welcher Reihenfolge der Motor dreht.");
  for (int a = 0; a < 4 && !found; a++)
    for (int b = 0; b < 4 && !found; b++) {
      if (b == a) continue;
      for (int c = 0; c < 4 && !found; c++) {
        if (c == a || c == b) continue;
        int d = 6 - a - b - c;
        int order[4] = {BASE[a], BASE[b], BASE[c], BASE[d]};
        Serial.print("Teste: ");
        Serial.print(order[0]); Serial.print(" "); Serial.print(order[1]);
        Serial.print(" "); Serial.print(order[2]); Serial.println(order[3]);
        spin(order);
        delay(1500);
      }
    }
  Serial.println("Alle Permutationen durch. Reset und such die letzte gute an.");
  while (true) { delay(10000); }
}

void loop() {
}