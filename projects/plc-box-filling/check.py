import csv
from pathlib import Path
import sys

from simulator import BoxFilling


def verify():
    line = BoxFilling()
    records = []

    def step(name, **inputs):
        state = line.scan(**inputs)
        assert not (state["c1_items"] and state["c2_boxes"])
        assert 0 <= state["image_index"] <= 10
        records.append(dict(event=name, **state))
        return state

    assert not step("idle")["c2_boxes"]
    assert step("start_no_box", start=True)["c2_boxes"]
    assert step("box_arrives", box=True)["c1_items"]
    assert step("item_1", box=True, item=True)["count"] == 1
    assert step("held_sensor", box=True, item=True)["count"] == 1
    step("sensor_clears", box=True)
    stopped = step("start_stop_and_pulse", box=True, item=True, start=True, stop=True)
    assert not stopped["running"] and not stopped["c1_items"] and not stopped["c2_boxes"]
    assert stopped["count"] == 1
    assert step("restart_sensor_held", box=True, item=True, start=True)["count"] == 1
    for count in range(2, 11):
        step("sensor_clears", box=True)
        state = step(f"item_{count}", box=True, item=True)
        assert state["count"] == count
        assert state["c1_items"] == (count < 10)
        assert state["c2_boxes"] == (count == 10)
    step("sensor_clears_full", box=True)
    assert step("extra_item_full", box=True, item=True)["count"] == 10
    assert step("box_leaves", item=True)["count"] == 0
    assert step("next_box_sensor_held", box=True, item=True)["count"] == 0
    return records


if __name__ == "__main__":
    rows = verify()
    if "--csv" in sys.argv:
        writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    else:
        with Path(__file__).with_name("scenario.csv").open(newline="") as reference:
            expected = list(csv.DictReader(reference))
        assert [{key: str(value) for key, value in row.items()} for row in rows] == expected
        print(f"PASS: {len(rows)} scans; stop priority, held sensor, capacity and reset")
