#include <SoftwareSerial.h>
#include "control.h"

SoftwareSerial link(2, 3);
const int valvePin = 9;
ValveControl valve;

void setup() {
  pinMode(valvePin, OUTPUT); digitalWrite(valvePin, LOW);
  Serial.begin(9600); link.begin(9600);
}
void loop() {
  while (link.available()) valve.receive(link.read(), millis());
  digitalWrite(valvePin, valve.update(millis()) ? HIGH : LOW);
}
