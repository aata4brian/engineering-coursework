import csv
from pathlib import Path

from sklearn.exceptions import NotFittedError

from experiment import KNNManual, SVMManual, run


def rejects(error, operation):
    try:
        operation()
    except error:
        return
    raise AssertionError(f"Expected {error.__name__}")


X, y = [[-1.0], [1.0]], [-1, 1]
assert KNNManual(k=2).fit(X, y).predict([[0.0]]).tolist() == [-1]
assert KNNManual(k=1, metric="cosine").fit(X, y).predict([[0.0]]).tolist() == [-1]
rejects(ValueError, lambda: KNNManual(k=3).fit(X, y))
rejects(ValueError, lambda: KNNManual().fit([[float("nan")], [1]], y))
rejects(NotFittedError, lambda: KNNManual().predict(X))
rejects(ValueError, lambda: SVMManual().fit(X, [0, 1]))
rejects(NotFittedError, lambda: SVMManual().predict(X))

with Path(__file__).with_name("results.csv").open(newline="") as file:
    recorded = list(csv.reader(file))[1:]
assert [list(map(str, row)) for row in run()] == recorded
print("15 hasil cocok; aturan seri, vektor nol, dan input invalid lulus.")
