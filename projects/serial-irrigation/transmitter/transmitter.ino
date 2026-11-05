#include <SoftwareSerial.h>
#include "control.h"

SoftwareSerial link(2, 3); // RX, TX. Hubungkan TX ke RX dan ground bersama.
const int sensorPin = A0;

void setup() { Serial.begin(9600); link.begin(9600); }
void loop() {
  int raw = analogRead(sensorPin);
  link.write(irrigationCommand(raw));
  Serial.println(moisturePercent(raw));
  delay(100);
}
