from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory

source = Path(__file__).with_name("queue.cpp")
with TemporaryDirectory() as directory:
    binary = Path(directory) / "queue"
    subprocess.run([
        "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
        "-fsanitize=undefined", "-fno-sanitize-recover=all",
        str(source), "-o", str(binary),
    ], check=True)

    def run(*lines):
        result = subprocess.run(
            [binary], input="\n".join(map(str, lines)) + "\n",
            capture_output=True, text=True, check=True, timeout=3,
        )
        return result.stdout

    def removed(output):
        return list(map(int, re.findall(r"(-?\d+) keluar\.", output)))

    linear = run(2, 4, 1, -1, 1, 20, 4, 2, 2, 2, 0)
    assert removed(linear) == [-1, 20]
    assert "Total: 19" in linear and "Rata-rata: 9.5" in linear
    assert "Maksimum: 20" in linear and "Minimum: -1" in linear
    assert linear.count("Queue Linear kosong!") == 3
    assert "Total: 4294967294" in run(1, 2147483647, 1, 2147483647, 4, 0)
    full = run(1, 1, 1, 2, 1, 3, 1, 4, 1, 5, 1, 6, 2, 1, 6, 3, 0)
    assert "Queue Linear penuh!" in full and "Isi Queue Linear: 2 3 4 5 6" in full

    circular = run(5, 10, 5, 20, 5, 30, 5, 40, 5, 50, 5, 60,
                   6, 5, 60, 7, 6, 6, 6, 6, 6, 6, 0)
    assert "Queue Circular penuh!" in circular
    assert "Isi Queue Circular: 20 30 40 50 60" in circular
    assert removed(circular) == [10, 20, 30, 40, 50, 60]
    assert "Queue Circular kosong!" in circular

    linked = run(9, 8, -1, 9, 8, 9, 8, 8, 9, 8, 100, 10, 0)
    assert removed(linked) == [-1, 9]
    assert "Isi Queue Linked List: 8 100" in linked
    invalid = run("3x", 1, "abc", 1, 20, 2, 42, 5)
    assert invalid.count("Masukkan bilangan bulat.") == 2
    assert removed(invalid) == [20] and "Pilihan tidak tersedia." in invalid

print("Linear: -1, 20 | total 19 | rata-rata 9.5")
print("Circular: 10, 20, 30, 40, 50, 60 | wrap-around lulus")
print("Linked: -1, 9 | 2 node tersisa saat keluar")
print("Input invalid, EOF, dan total di atas rentang int: lulus")
