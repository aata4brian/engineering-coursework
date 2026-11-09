#pragma once
// Bagian logika yang dapat diperiksa tanpa perangkat Arduino.
inline int moisturePercent(int raw) {
    if (raw < 0 || raw > 1023) return -1;
    return static_cast<int>(raw * 100L / 1023);
}
inline char irrigationCommand(int raw, int threshold = 30) {
    const int percent = moisturePercent(raw);
    return percent >= 0 && percent < threshold ? '1' : '0';
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
