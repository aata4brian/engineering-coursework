"""Model logika pengisian kotak per scan, tanpa koneksi ke PLC."""

from dataclasses import dataclass

TARGET = 10


@dataclass
class BoxFilling:
    running: bool = False
    count: int = 0
    previous_item: bool = False

    def scan(self, *, box=False, item=False, start=False, stop=False):
        self.running = (self.running or start) and not stop
        rising_item = item and not self.previous_item
        self.previous_item = item

        if not box:
            self.count = 0
        elif self.running and self.count < TARGET and rising_item:
            self.count += 1

        full = self.count == TARGET
        return {
            "running": self.running,
            "count": self.count,
            "full": full,
            "c1_items": self.running and box and not full,
            "c2_boxes": self.running and (not box or full),
            "image_index": self.count,
        }
