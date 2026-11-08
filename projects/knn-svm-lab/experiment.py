import csv
import sys

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.datasets import make_blobs, make_circles, make_moons
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.utils.validation import check_is_fitted, validate_data


class KNNManual(ClassifierMixin, BaseEstimator):
    def __init__(self, k=3, metric="minkowski", p=2):
        self.k = k
        self.metric = metric
        self.p = p

    def fit(self, X, y):
        X, y = validate_data(self, X, y, dtype=float)
        if not isinstance(self.k, (int, np.integer)) or not 1 <= self.k <= len(X):
            raise ValueError("k harus bilangan bulat antara 1 dan jumlah data latih.")
        if self.metric not in ["minkowski", "cosine"] or self.p < 1:
            raise ValueError("Periksa metric dan p (p minimal 1).")
        self.X_train_ = np.asarray(X, dtype=float).copy()
        self.y_train_ = np.asarray(y).copy()
        self.classes_ = np.unique(y)
        self.n_features_in_ = self.X_train_.shape[1]
        return self

    def predict(self, X):
        check_is_fitted(self, ["X_train_", "y_train_"])
        hasil = []
        for x in validate_data(self, X, dtype=float, reset=False):
            if self.metric == "cosine":
                pembagi = np.linalg.norm(self.X_train_, axis=1) * np.linalg.norm(x)
                kemiripan = np.divide(self.X_train_ @ x, pembagi,
                                     out=np.zeros(len(pembagi)), where=pembagi > 0)
                jarak = 1 - np.clip(kemiripan, -1, 1)
            else:
                jarak = np.sum(np.abs(self.X_train_ - x) ** self.p, axis=1) ** (1 / self.p)
            indeks = np.argsort(jarak, kind="stable")[:self.k]
            label, jumlah = np.unique(self.y_train_[indeks], return_counts=True)
            hasil.append(label[np.argmax(jumlah)])
        return np.asarray(hasil)


class SVMManual(ClassifierMixin, BaseEstimator):
    def __init__(self, alpha=0.001, lambda_=0.01, n_iterations=1000):
        self.alpha = alpha
        self.lambda_ = lambda_
        self.n_iterations = n_iterations

    def fit(self, X, y):
        X, y = validate_data(self, X, y, dtype=float)
        self.classes_ = np.unique(y)
        if not np.array_equal(self.classes_, [-1, 1]):
            raise ValueError("SVM manual menerima dua label: -1 dan 1.")
        self.w_ = np.zeros(X.shape[1])
        self.b_ = 0.0
        for _ in range(self.n_iterations):
            for x, label in zip(X, y):
                kondisi = label * (np.dot(x, self.w_) - self.b_)
                if kondisi >= 1:
                    self.w_ -= self.alpha * (2 * self.lambda_ * self.w_)
                else:
                    self.w_ -= self.alpha * (2 * self.lambda_ * self.w_ - label * x)
                    self.b_ -= self.alpha * label
        return self

    def decision_function(self, X):
        check_is_fitted(self, ["w_", "b_"])
        return validate_data(self, X, dtype=float, reset=False) @ self.w_ - self.b_

    def predict(self, X):
        return np.where(self.decision_function(X) > 0, 1, -1)


def run():
    datasets = {
        "Blobs": make_blobs(n_samples=200, centers=2, random_state=0, cluster_std=0.60),
        "Moons": make_moons(n_samples=200, noise=0.05, random_state=42),
        "Circles": make_circles(n_samples=200, factor=0.5, noise=0.05, random_state=42),
    }
    models = {
        "KNN manual": KNNManual(k=3),
        "KNN sklearn": KNeighborsClassifier(n_neighbors=3),
        "SVM manual": SVMManual(),
        "SVC linear": SVC(kernel="linear", C=1),
        "SVC RBF": SVC(kernel="rbf", C=1),
    }
    for name, (X, target) in datasets.items():
        y = np.where(target == 0, -1, 1)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y,
        )
        for method, model in models.items():
            pipeline = make_pipeline(StandardScaler(), model)
            pred = pipeline.fit(X_train, y_train).predict(X_test)
            yield (name, method, int((pred == y_test).sum()), len(y_test),
                   f"{accuracy_score(y_test, pred):.4f}",
                   f"{f1_score(y_test, pred, average='macro'):.4f}")


if __name__ == "__main__":
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(("dataset", "model", "correct", "test_n", "accuracy", "f1_macro"))
    writer.writerows(run())
