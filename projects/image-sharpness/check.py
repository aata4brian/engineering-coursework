import csv
from pathlib import Path

import numpy as np
from scipy.signal import correlate2d

from sharpness import measure

constant = measure(np.full((13, 17), 100.0))
assert all(value == 0 for value in constant.values())
image = np.random.default_rng(42).normal(size=(11, 13))
scores = measure(image)
doubled = measure(2 * image)
for method in scores:
    np.testing.assert_allclose(doubled[method], 4 * scores[method])

gx = correlate2d(image, [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], mode="valid")
gy = correlate2d(image, [[-1, -2, -1], [0, 0, 0], [1, 2, 1]], mode="valid")
np.testing.assert_allclose(scores["Tenenbaum"], np.sum(gx * gx + gy * gy))
kernel = np.outer([1, 1, -1, -1], [1, 1, -1, -1])
np.testing.assert_allclose(scores["MDCT"], np.sum(correlate2d(image, kernel, mode="valid") ** 2))
for name, gap in [("Brenner", 2), ("Squared gradient", 1)]:
    scalar = sum((image[y, x + gap] - image[y, x]) ** 2
                 for y in range(11) for x in range(13 - gap))
    np.testing.assert_allclose(scores[name], scalar)

for invalid in (np.zeros((3, 8)), np.zeros((4, 4, 3)), np.full((4, 4), np.inf)):
    try:
        measure(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid image accepted")

with Path(__file__).with_name("reference-scores.csv").open() as file:
    rows = list(csv.DictReader(file))
for row in rows:
    first, second, percent = map(float, [row["Skor Citra 1"], row["Skor Citra 2"], row["Kenaikan Citra 2 (%)"]])
    np.testing.assert_allclose(percent, (second / first - 1) * 100)
assert len(rows) == 4
print("PASS: four focus measures, direct kernels, invalid inputs and archived ratios")
