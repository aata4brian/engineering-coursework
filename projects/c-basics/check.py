import math
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

with TemporaryDirectory() as tmp:
    exe = Path(tmp) / "integral"
    source = Path(__file__).with_name("integral.c")
    subprocess.run(["cc", "-std=c17", "-Wall", "-Wextra", "-Werror",
                    "-fsanitize=undefined", "-fno-sanitize-recover=all",
                    str(source), "-o", str(exe)], check=True)
    print("n,approximation,absolute_error")
    for n in (1, 10, 100, 1000):
        values = []
        for mode in ("value", "pointer"):
            result = subprocess.run([exe, mode], input=f"{n}\n", capture_output=True,
                                    text=True, check=True, timeout=3)
            values.append(float(result.stdout.rsplit("=", 1)[1]))
        assert values[0] == values[1]
        error = 10.5 - values[0]
        assert math.isclose(error, 4.5 / n, abs_tol=1e-8)
        print(f"{n},{values[0]:.8f},{error:.8f}")

    for value in ("", "0\n", "-1\n", "3x\n", "1.5\n", "1000001\n", "9" * 80 + "\n"):
        for mode in ("value", "pointer"):
            result = subprocess.run([exe, mode], input=value, capture_output=True,
                                    text=True, timeout=3)
            assert result.returncode == 1 and result.stderr
