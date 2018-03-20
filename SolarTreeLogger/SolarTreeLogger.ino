#define DELAY 1000
#define NUM_SAMPLES 100
#define RESISTOR_RATIO 11

#define PAUSE (DELAY / NUM_SAMPLES)

float voltageSum1, voltageSum2;
float voltage1, voltage2;
int n;

void setup() {
  Serial.begin(9600);
}

void loop() {
  while (true) {
    n = 0;
    voltageSum1 = 0;
    voltageSum2 = 0;
    while (n++ < NUM_SAMPLES) {
      voltageSum1 += analogRead(A0);
      voltageSum2 += analogRead(A1);
      delay(PAUSE);
    }
    voltage1 = ((voltageSum1 / NUM_SAMPLES) * RESISTOR_RATIO * 5) / 1024;
    voltage2 = ((voltageSum2 / NUM_SAMPLES) * RESISTOR_RATIO * 5) / 1024;
    Serial.print(voltage1, 2);
    Serial.print(',');
    Serial.println(voltage2);
  }
}
