# %% 1. Pustaka dan pengaturan
"""Perbandingan SVM default, tuning C, dan PCA pada AI4I 2020."""
from pathlib import Path
import hashlib
import io
import json
import platform
import urllib.request
import zipfile

import numpy as np
import pandas as pd
import matplotlib
if "get_ipython" not in globals():
    matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sklearn
from sklearn.decomposition import PCA
from sklearn.metrics import (
    classification_report, confusion_matrix, ConfusionMatrixDisplay,
    precision_score, recall_score, f1_score,
)
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

BASE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
DATA = BASE / "data" / "predictive_maintenance.csv"
OUT = BASE / "hasil"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 42
FEATURES = [
    "Air temperature [K]", "Process temperature [K]",
    "Rotational speed [rpm]", "Torque [Nm]", "Tool wear [min]",
]
SOURCE = "https://www.kaggle.com/datasets/shivamb/machine-predictive-maintenance-classification"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 130})
print("Random state:", SEED)
print("scikit-learn:", sklearn.__version__)

# %% 2. Membaca dan memeriksa dataset
# File mentah disimpan agar percobaan dapat diulang tanpa unduhan baru.
if not DATA.exists():
    DATA.parent.mkdir(parents=True, exist_ok=True)
    url = "https://www.kaggle.com/api/v1/datasets/download/shivamb/machine-predictive-maintenance-classification"
    with urllib.request.urlopen(url, timeout=60) as response:
        archive = zipfile.ZipFile(io.BytesIO(response.read()))
    names = [name for name in archive.namelist() if name.endswith(".csv")]
    if len(names) != 1:
        raise ValueError("Arsip dataset tidak berisi tepat satu CSV.")
    DATA.write_bytes(archive.read(names[0]))

df = pd.read_csv(DATA)
X = df[FEATURES].copy()  # Kolom ID, Type, dan Failure Type tidak digunakan.
y = df["Target"].astype(int)
assert len(df) == 10000, "Periksa kembali versi dataset."
assert set(y.unique()) == {0, 1}
assert X.shape[1] == 5 and X.isna().sum().sum() == 0
assert np.isfinite(X.to_numpy()).all()
assert "Failure Type" not in X.columns
print("Ukuran data:", df.shape)
print("Fitur yang digunakan:", ", ".join(FEATURES))
print("Nilai kosong pada lima fitur:", X.isna().sum().sum())
print("Duplikat baris lengkap:", df.duplicated().sum())
print("Jumlah kelas:", y.value_counts().sort_index().to_dict())
print("Persentase gagal: {:.2f}%".format(100 * y.mean()))

# %% 3. Membagi data dan menyiapkan validasi
# Split dilakukan sebelum standardisasi dan PCA.
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, stratify=y, random_state=SEED
)
assert set(X_train.index).isdisjoint(X_test.index)
split_info = pd.DataFrame({
    "Bagian": ["Train", "Test"],
    "Jumlah": [len(y_train), len(y_test)],
    "Tidak gagal": [int((y_train == 0).sum()), int((y_test == 0).sum())],
    "Gagal": [int(y_train.sum()), int(y_test.sum())],
})
print(split_info.to_string(index=False))
split_info.to_csv(OUT / "pembagian_data.csv", index=False)
# Indeks fold yang sama digunakan untuk seluruh konfigurasi.
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
folds = list(cv.split(X_train, y_train))
pd.DataFrame({
    "baris_csv": np.arange(len(df)) + 2,
    "bagian": np.where(df.index.isin(X_test.index), "test", "train"),
}).to_csv(OUT / "indeks_split.csv", index=False)

# %% 4. Membandingkan tiga percobaan pada data train
# SVC() memakai kernel RBF, C=1, gamma='scale', dan class_weight=None.
# Hanya C dan jumlah komponen PCA yang dituning sesuai ruang pencarian soal.
experiments = [
    ("SVM default", Pipeline([("scaler", StandardScaler()), ("svm", SVC())]), {}),
    ("SVM tuning", Pipeline([("scaler", StandardScaler()), ("svm", SVC())]),
     {"svm__C": [0.1, 1, 10]}),
    ("PCA + SVM tuning",
     Pipeline([("scaler", StandardScaler()), ("pca", PCA(svd_solver="full")),
               ("svm", SVC())]),
     {"pca__n_components": [2, 3, 4], "svm__C": [0.1, 1, 10]}),
]
searches = {}
summary_rows = []
all_rows = []
for name, pipeline, grid in experiments:
    search = GridSearchCV(
        pipeline, grid, scoring="f1", cv=folds, refit=True,
        n_jobs=2, return_train_score=False, error_score="raise",
    )
    search.fit(X_train, y_train)
    searches[name] = search
    results = pd.DataFrame(search.cv_results_)
    best_idx = search.best_index_
    params = search.best_params_
    summary_rows.append({
        "Percobaan": name,
        "C": params.get("svm__C", 1.0),
        "Komponen PCA": params.get("pca__n_components", 0),
        "F1 CV mean": float(search.best_score_),
        "F1 CV std": float(results.loc[best_idx, "std_test_score"]),
    })
    for i, row in results.iterrows():
        record = {
            "Percobaan": name,
            "C": row["params"].get("svm__C", 1.0),
            "Komponen PCA": row["params"].get("pca__n_components", 0),
            "F1 CV mean": float(row["mean_test_score"]),
            "F1 CV std": float(row["std_test_score"]),
        }
        record.update({f"F1 fold {k+1}": float(row[f"split{k}_test_score"]) for k in range(5)})
        all_rows.append(record)
    print(name, "| parameter:", params or "default",
          "| F1 CV: {:.4f} +/- {:.4f}".format(
              search.best_score_, results.loc[best_idx, "std_test_score"]))
summary = pd.DataFrame(summary_rows)
candidates = pd.DataFrame(all_rows)
summary.to_csv(OUT / "ringkasan_validasi.csv", index=False)
candidates.to_csv(OUT / "seluruh_konfigurasi.csv", index=False)

# %% 5. Memilih model sebelum membuka hasil test
# Jika skor persis sama, urutan percobaan mendahulukan model tanpa PCA.
winner_idx = int(summary["F1 CV mean"].to_numpy().argmax())
winner_name = summary.iloc[winner_idx]["Percobaan"]
selected = searches[winner_name].best_estimator_
# GridSearchCV telah melakukan refit pada seluruh 80% data train.
print("Model terpilih berdasarkan validasi:", winner_name)
print(selected)

# %% 6. Evaluasi akhir pada data test
# Hanya model terpilih yang diprediksi pada test; hasil test tidak dipakai tuning.
y_pred = selected.predict(X_test)
cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
tn, fp, fn, tp = [int(value) for value in cm.ravel()]
metrics = {
    "precision": float(precision_score(y_test, y_pred, pos_label=1, zero_division=0)),
    "recall": float(recall_score(y_test, y_pred, pos_label=1, zero_division=0)),
    "f1": float(f1_score(y_test, y_pred, pos_label=1, zero_division=0)),
    "tn": tn, "fp": fp, "fn": fn, "tp": tp,
}
print(classification_report(y_test, y_pred, labels=[0, 1],
                            target_names=["Tidak gagal", "Gagal"], digits=4,
                            zero_division=0))
print("Confusion matrix (baris=aktual, kolom=prediksi):")
print(cm)
report = classification_report(y_test, y_pred, labels=[0, 1],
                              target_names=["Tidak gagal", "Gagal"],
                              output_dict=True, zero_division=0)
pd.DataFrame(report).T.to_csv(OUT / "classification_report.csv")
pd.DataFrame(cm, index=["Aktual 0", "Aktual 1"],
             columns=["Prediksi 0", "Prediksi 1"]).to_csv(OUT / "confusion_matrix.csv")
pd.DataFrame({"baris_csv": X_test.index + 2, "aktual": y_test.to_numpy(),
              "prediksi": y_pred}).sort_values("baris_csv").to_csv(
                  OUT / "prediksi_test.csv", index=False)
assert tp + fn == int(y_test.sum()) and tn + fp == int((y_test == 0).sum())
assert len(y_pred) == 2000

# %% 7. Visualisasi hasil
fig, ax = plt.subplots(figsize=(6.8, 3.4))
bars = ax.bar(summary["Percobaan"], summary["F1 CV mean"],
              yerr=summary["F1 CV std"], capsize=5,
              color=["#9BA8B7", "#21618C", "#55A59D"], width=0.58)
ax.set(ylabel="F1-score kelas gagal", ylim=(0, 1),
       title="Perbandingan pada 5-fold cross-validation")
ax.grid(axis="y", alpha=0.18)
ax.set_axisbelow(True)
for bar, value in zip(bars, summary["F1 CV mean"]):
    ax.text(bar.get_x() + bar.get_width()/2, value + 0.055,
            f"{value:.4f}", ha="center", fontsize=10)
fig.text(0.5, 0.015, "Garis galat: simpangan baku antarfold, bukan interval kepercayaan.",
          ha="center", fontsize=8, color="#555555")
fig.tight_layout(rect=(0, 0.055, 1, 1))
fig.savefig(OUT / "perbandingan_validasi.png", dpi=180)
plt.show()
plt.close(fig)

fig, ax = plt.subplots(figsize=(5.3, 4.1))
ConfusionMatrixDisplay(cm, display_labels=["Tidak gagal", "Gagal"]).plot(
    ax=ax, cmap="Blues", colorbar=False, values_format="d")
ax.set(title=f"Data test - {winner_name}", xlabel="Prediksi", ylabel="Kelas aktual")
fig.tight_layout()
fig.savefig(OUT / "confusion_matrix.png", dpi=180)
plt.show()
plt.close(fig)

# %% 8. Menyimpan hasil dan menarik kesimpulan
# Analisis variansi PCA hanya menggunakan data train.
scaled_train = StandardScaler().fit_transform(X_train)
pca_diagnostic = PCA(svd_solver="full").fit(scaled_train)
variance = np.cumsum(pca_diagnostic.explained_variance_ratio_)
result = {
    "dataset_source": SOURCE,
    "dataset_sha256": hashlib.sha256(DATA.read_bytes()).hexdigest(),
    "seed": SEED, "features": FEATURES,
    "n_rows": len(df), "class_counts": {str(k): int(v) for k, v in y.value_counts().items()},
    "split": split_info.to_dict(orient="records"),
    "cv": summary.to_dict(orient="records"),
    "candidates": candidates.to_dict(orient="records"),
    "winner": winner_name,
    "winner_params": searches[winner_name].best_params_,
    "test": metrics,
    "pca_train_cumulative_variance": variance.tolist(),
    "versions": {"python": platform.python_version(), "numpy": np.__version__,
                 "pandas": pd.__version__, "scikit-learn": sklearn.__version__,
                 "matplotlib": matplotlib.__version__},
}
(OUT / "hasil_eksperimen.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
baseline_f1 = float(summary.iloc[0]["F1 CV mean"])
tuned_f1 = float(summary.iloc[1]["F1 CV mean"])
pca_f1 = float(summary.iloc[2]["F1 CV mean"])
print("Perubahan F1 CV setelah tuning C: {:+.4f}".format(tuned_f1-baseline_f1))
print("Perubahan F1 CV dengan PCA dibanding SVM tuning: {:+.4f}".format(pca_f1-tuned_f1))
print("Dari", tp+fn, "kasus gagal pada test,", tp, "terdeteksi dan", fn, "terlewat.")
print("Hasil ini berlaku untuk satu split pada dataset sintetis,")
print("sehingga belum membuktikan kinerja pada mesin industri sebenarnya.")
print("Variansi kumulatif PCA pada train:", np.round(variance, 4))
