#pragma once
// Bagian logika yang dapat diperiksa tanpa perangkat Arduino.
inline int moisturePercent(int raw) {
    return raw * 100 / 1023;
}
inline char irrigationCommand(int raw, int threshold = 30) {
    return moisturePercent(raw) < threshold ? '1' : '0';
}
struct ValveControl {
    bool open = false;
    bool received = false;
    unsigned long lastReceived = 0;
    void receive(char command, unsigned long now) {
        if (command != '0' && command != '1') { open = false; return; }
        open = command == '1'; received = true; lastReceived = now;
    }
    bool update(unsigned long now) {
        if (!received || now - lastReceived > 1000UL) open = false;
        return open;
    }
};
