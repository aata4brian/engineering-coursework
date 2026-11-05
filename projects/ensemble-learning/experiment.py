# %% 1. Pustaka dan pengaturan
from pathlib import Path
from collections import Counter
import platform

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sklearn
from sklearn.base import clone
from sklearn.datasets import load_breast_cancer
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import (RandomForestClassifier, AdaBoostClassifier,
                              GradientBoostingClassifier)
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             confusion_matrix, ConfusionMatrixDisplay, make_scorer)

folder = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
hasil = folder / 'hasil'
hasil.mkdir(exist_ok=True)
pd.set_option('display.width', 160)
pd.set_option('display.max_columns', 20)
np.set_printoptions(precision=9, suppress=True)
plt.rcParams.update({'font.size': 10, 'figure.dpi': 110})
print('Python:', platform.python_version())
print('scikit-learn:', sklearn.__version__)


def simpan_gambar(nama):
    plt.tight_layout()
    plt.savefig(hasil / (nama + '.png'), dpi=150, bbox_inches='tight')
    plt.show()
    plt.close()

# %% 2. Soal 1: hard voting dan akurasi
transaksi = pd.DataFrame({
    'Data': ['D' + str(i) for i in range(1, 11)],
    'Aktual': ['Fraud', 'Legitimate', 'Fraud', 'Legitimate', 'Fraud',
               'Legitimate', 'Fraud', 'Legitimate', 'Fraud', 'Legitimate'],
    'A': ['Fraud', 'Legitimate', 'Legitimate', 'Legitimate', 'Fraud',
          'Fraud', 'Fraud', 'Legitimate', 'Legitimate', 'Legitimate'],
    'B': ['Fraud', 'Fraud', 'Fraud', 'Legitimate', 'Legitimate',
          'Legitimate', 'Fraud', 'Legitimate', 'Fraud', 'Fraud'],
    'C': ['Legitimate', 'Legitimate', 'Fraud', 'Fraud', 'Fraud',
          'Legitimate', 'Legitimate', 'Legitimate', 'Legitimate', 'Legitimate']})

voting = []
for _, baris in transaksi.iterrows():
    suara = Counter(baris[['A', 'B', 'C']])
    urut = suara.most_common()
    if len(urut) > 1 and urut[0][1] == urut[1][1]:
        prediksi = 'Belum dapat ditentukan'
    else:
        prediksi = urut[0][0]
    voting.append([suara['Fraud'], suara['Legitimate'], prediksi])
transaksi[['Suara Fraud', 'Suara Legitimate', 'Hard Voting']] = voting
print(transaksi.to_string(index=False))

akurasi_voting = []
for nama in ['A', 'B', 'C', 'Hard Voting']:
    benar = int((transaksi[nama] == transaksi.Aktual).sum())
    akurasi_voting.append([nama, benar, 10 - benar, benar / len(transaksi)])
akurasi_voting = pd.DataFrame(akurasi_voting, columns=['Model', 'Benar', 'Salah', 'Accuracy'])
print('\nAkurasi setiap model:')
print(akurasi_voting.to_string(index=False, float_format=lambda v: f'{v:.6f}'))
transaksi.to_csv(hasil / 'soal1_voting.csv', index=False)
akurasi_voting.to_csv(hasil / 'soal1_akurasi.csv', index=False)

plt.figure(figsize=(6, 3.4))
plt.bar(akurasi_voting.Model, akurasi_voting.Accuracy, color=['#4c718e'] * 3 + ['#c87946'])
plt.ylim(0, 1.05)
plt.ylabel('Accuracy')
plt.title('Akurasi model dan hard voting')
simpan_gambar('soal1_akurasi')

# %% 3. Soal 1: soft voting dan kesalahan antar-model
probabilitas = np.array([0.80, 0.55, 0.30])
bobot_model = np.array([0.5, 0.3, 0.2])
prob_fraud = float(np.sum(bobot_model * probabilitas) / bobot_model.sum())
kelas_soft = 'Fraud' if prob_fraud >= 0.5 else 'Legitimate'
print('Kontribusi tiap model:', bobot_model * probabilitas)
print('Probabilitas Fraud:', prob_fraud)
print('Probabilitas Legitimate:', 1 - prob_fraud)
print('Prediksi soft voting:', kelas_soft)

salah = pd.DataFrame({'Data': transaksi.Data})
for nama in ['A', 'B', 'C']:
    salah[nama] = (transaksi[nama] != transaksi.Aktual).astype(int)
print('\nIndikator kesalahan (1 = salah):')
print(salah.to_string(index=False))
pasangan = []
for a, b in [('A', 'B'), ('A', 'C'), ('B', 'C')]:
    bersama = transaksi.loc[(salah[a] == 1) & (salah[b] == 1), 'Data'].tolist()
    pasangan.append([a + '-' + b, ', '.join(bersama) if bersama else '-',
                     len(bersama), float(np.corrcoef(salah[a], salah[b])[0, 1])])
pasangan = pd.DataFrame(pasangan, columns=['Pasangan', 'Salah bersama', 'Jumlah', 'Korelasi error'])
print('\nKesalahan bersama dan korelasi error:')
print(pasangan.to_string(index=False, float_format=lambda v: f'{v:.9f}'))
salah.to_csv(hasil / 'soal1_kesalahan.csv', index=False)
pasangan.to_csv(hasil / 'soal1_korelasi.csv', index=False)

# %% 4. Soal 2: pembaruan bobot AdaBoost dua iterasi
y_ada = np.array([1, 1, 1, -1, -1, -1])
h1 = np.array([1, 1, -1, -1, 1, -1])
h2 = np.array([1, -1, 1, -1, -1, 1])
w = np.full(6, 1 / 6)
alpha = []
rekap_ada = []
for t, h in enumerate([h1, h2], 1):
    error = float(w[h != y_ada].sum())
    a = 0.5 * np.log((1 - error) / error)
    faktor = np.exp(-a * y_ada * h)
    belum_normal = w * faktor
    Z = float(belum_normal.sum())
    baru = belum_normal / Z
    tabel = pd.DataFrame({'Data': ['D' + str(i) for i in range(1, 7)],
                          'y': y_ada, 'h': h, 'Salah': h != y_ada,
                          'w awal': w, 'Faktor': faktor,
                          'Belum normal': belum_normal, 'w baru': baru})
    print('\nIterasi', t)
    print('Weighted error:', f'{error:.9f}')
    print('Alpha:', f'{a:.9f}', '| Z:', f'{Z:.9f}')
    print(tabel.to_string(index=False, float_format=lambda v: f'{v:.9f}'))
    print('Jumlah bobot baru:', f'{baru.sum():.12f}')
    tabel.to_csv(hasil / f'soal2_iterasi_{t}.csv', index=False)
    rekap_ada.append([t, error, a, Z])
    alpha.append(a)
    w = baru

rekap_ada = pd.DataFrame(rekap_ada, columns=['Iterasi', 'Error', 'Alpha', 'Z'])
rekap_ada.to_csv(hasil / 'soal2_ringkasan.csv', index=False)
skor_ada = alpha[0] * h1 + alpha[1] * h2
# Jika skor tepat nol, kelas +1 digunakan sebagai aturan pemecah seri.
pred_ada = np.where(skor_ada >= 0, 1, -1)
akhir_ada = pd.DataFrame({'Data': ['D' + str(i) for i in range(1, 7)],
                          'y': y_ada, 'h1': h1, 'h2': h2,
                          'alpha1*h1': alpha[0] * h1,
                          'alpha2*h2': alpha[1] * h2,
                          'Skor': skor_ada, 'Prediksi': pred_ada})
print('\nPrediksi ensemble dua iterasi:')
print(akhir_ada.to_string(index=False, float_format=lambda v: f'{v:.9f}'))
print('Akurasi ensemble:', f'{accuracy_score(y_ada, pred_ada):.9f}')
akhir_ada.to_csv(hasil / 'soal2_prediksi_akhir.csv', index=False)

# %% 5. Soal 3: data breast cancer dan pembagian train-test
dataset = load_breast_cancer(as_frame=True)
X = dataset.data
y = dataset.target
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)
print('Dataset:', X.shape, '| 0 = malignant, 1 = benign')
print('Data ini pengganti data churn; labelnya tetap malignant dan benign.')
print('Nilai kosong:', int(X.isna().sum().sum()))
pembagian = pd.DataFrame({
    'Bagian': ['Seluruh data', 'Train', 'Test'],
    'Malignant (0)': [int((v == 0).sum()) for v in [y, y_train, y_test]],
    'Benign (1)': [int((v == 1).sum()) for v in [y, y_train, y_test]]})
pembagian['Total'] = pembagian['Malignant (0)'] + pembagian['Benign (1)']
print(pembagian.to_string(index=False))
statistik = X_train.agg(['mean', 'std', 'min', 'max']).T
print('\nStatistik seluruh fitur pada data train:')
print(statistik.to_string(float_format=lambda v: f'{v:.6f}'))
pembagian.to_csv(hasil / 'soal3_pembagian.csv', index=False)
statistik.to_csv(hasil / 'soal3_statistik_fitur.csv')

plt.figure(figsize=(6, 3.4))
plt.bar(['Malignant (0)', 'Benign (1)'], y.value_counts().sort_index(), color=['#c87946', '#4c718e'])
plt.ylabel('Jumlah data')
plt.title('Distribusi kelas dataset breast cancer')
simpan_gambar('soal3_distribusi')

# %% 6. Konfigurasi model dan validasi pada data train
model_awal = {
    'Decision Tree': DecisionTreeClassifier(
        criterion='gini', splitter='best', max_depth=None,
        min_samples_split=2, min_samples_leaf=1, random_state=42),
    'Random Forest': RandomForestClassifier(
        n_estimators=100, criterion='gini', max_depth=None,
        max_features='sqrt', bootstrap=True, random_state=42, n_jobs=2)}

konfigurasi = dict(model_awal)
for n in [10, 50, 100]:
    konfigurasi[f'AdaBoost {n}'] = AdaBoostClassifier(
        estimator=DecisionTreeClassifier(max_depth=1, random_state=42),
        n_estimators=n, learning_rate=1.0, random_state=42)
    konfigurasi[f'Gradient Boosting {n}'] = GradientBoostingClassifier(
        loss='log_loss', n_estimators=n, learning_rate=0.1,
        max_depth=3, subsample=1.0, random_state=42)

cv = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=42).split(X_train, y_train))
# Kelas positif adalah malignant (0) pada seluruh metrik dan seluruh model.
penilaian = {'f1': make_scorer(f1_score, pos_label=0, zero_division=0),
             'accuracy': 'accuracy'}
hasil_cv = []
model_latih = {}
fold_cv = []
for nama, model in konfigurasi.items():
    skor = cross_validate(model, X_train, y_train, cv=cv,
                          scoring=penilaian, return_train_score=True, n_jobs=2)
    hasil_cv.append([nama, skor['train_f1'].mean(), skor['test_f1'].mean(),
                     skor['test_f1'].std(ddof=0), skor['test_accuracy'].mean()])
    for i in range(5):
        fold_cv.append([nama, i + 1, skor['train_f1'][i],
                        skor['test_f1'][i], skor['test_accuracy'][i]])
    model_latih[nama] = clone(model).fit(X_train, y_train)
    print(nama, '| rata-rata F1 validasi:', f"{skor['test_f1'].mean():.6f}")
hasil_cv = pd.DataFrame(hasil_cv, columns=['Model', 'F1 train CV', 'F1 validasi', 'SD F1', 'Accuracy validasi'])
fold_cv = pd.DataFrame(fold_cv, columns=['Model', 'Fold', 'F1 train', 'F1 validasi', 'Accuracy validasi'])
print('\nRincian semua fold:')
print(fold_cv.to_string(index=False, float_format=lambda v: f'{v:.6f}'))
hasil_cv.to_csv(hasil / 'soal3_cv_ringkasan.csv', index=False)
fold_cv.to_csv(hasil / 'soal3_cv_per_fold.csv', index=False)

# Jumlah estimator dipilih dari validasi sebelum prediksi test dihitung.
pilihan = {}
for metode in ['AdaBoost', 'Gradient Boosting']:
    calon = hasil_cv[hasil_cv.Model.str.startswith(metode)].copy()
    calon['n'] = calon.Model.str.split().str[-1].astype(int)
    terbaik = calon.sort_values(['F1 validasi', 'n'], ascending=[False, True]).iloc[0]
    pilihan[metode] = {'n_estimators': int(terbaik.n), 'F1 validasi': float(terbaik['F1 validasi'])}
print('\nPilihan jumlah estimator dari CV:', pilihan)
pd.DataFrame([{'Metode': k, **v} for k, v in pilihan.items()]).to_csv(
    hasil / 'soal3_pilihan_cv.csv', index=False)

# %% 7. Evaluasi keempat model awal pada test yang sama
nama_awal = ['Decision Tree', 'Random Forest', 'AdaBoost 100', 'Gradient Boosting 100']
evaluasi = []
matriks = {}
prediksi_test = pd.DataFrame({'Indeks data': X_test.index, 'Aktual': y_test.to_numpy()})
for nama in nama_awal:
    model = model_latih[nama]
    pred = model.predict(X_test)
    prediksi_test[nama] = pred
    # Urutan [1, 0] memberi susunan [[TN, FP], [FN, TP]] untuk positif = 0.
    cm = confusion_matrix(y_test, pred, labels=[1, 0])
    matriks[nama] = cm
    tn, fp, fn, tp = cm.ravel()
    evaluasi.append([nama, accuracy_score(y_test, pred),
                     precision_score(y_test, pred, pos_label=0, zero_division=0),
                     recall_score(y_test, pred, pos_label=0, zero_division=0),
                     f1_score(y_test, pred, pos_label=0, zero_division=0),
                     int(tn), int(fp), int(fn), int(tp)])
evaluasi = pd.DataFrame(evaluasi, columns=['Model', 'Accuracy', 'Precision', 'Recall', 'F1', 'TN', 'FP', 'FN', 'TP'])
print(evaluasi.to_string(index=False, float_format=lambda v: f'{v:.6f}'))
print('\nF1 test tertinggi:', evaluasi.loc[evaluasi.F1 == evaluasi.F1.max(), 'Model'].tolist())
print('Accuracy test tertinggi:', evaluasi.loc[evaluasi.Accuracy == evaluasi.Accuracy.max(), 'Model'].tolist())
evaluasi.to_csv(hasil / 'soal3_evaluasi_model.csv', index=False)

# %% 8. Visualisasi F1 dan confusion matrix
plt.figure(figsize=(7, 3.8))
posisi = np.arange(4)
plt.bar(posisi, evaluasi.F1, color=['#4c718e', '#5b8c6f', '#c87946', '#92799e'])
plt.xticks(posisi, ['Decision\nTree', 'Random\nForest', 'AdaBoost', 'Gradient\nBoosting'])
for i, nilai in enumerate(evaluasi.F1):
    plt.text(i, nilai + 0.015, f'{nilai:.4f}', ha='center')
plt.ylim(0, 1.08)
plt.ylabel('F1 kelas malignant (0)')
plt.title('Perbandingan F1 pada data test')
simpan_gambar('soal3_f1_model')

fig, axes = plt.subplots(2, 2, figsize=(8, 7))
for ax, (nama, cm) in zip(axes.ravel(), matriks.items()):
    ConfusionMatrixDisplay(cm, display_labels=['Benign (1)', 'Malignant (0)']).plot(
        ax=ax, cmap='Blues', colorbar=False, values_format='d')
    ax.set_title(nama)
    ax.set_xlabel('Prediksi')
    ax.set_ylabel('Aktual')
simpan_gambar('soal3_confusion_matrix')

# %% 9. Pengaruh jumlah estimator dan indikasi overfitting
parameter = []
for metode in ['AdaBoost', 'Gradient Boosting']:
    for n in [10, 50, 100]:
        nama = f'{metode} {n}'
        model = model_latih[nama]
        baris_cv = hasil_cv[hasil_cv.Model == nama].iloc[0]
        parameter.append([metode, n,
                          f1_score(y_train, model.predict(X_train), pos_label=0),
                          baris_cv['F1 train CV'], baris_cv['F1 validasi'], baris_cv['SD F1'],
                          f1_score(y_test, model.predict(X_test), pos_label=0),
                          n == pilihan[metode]['n_estimators']])
parameter = pd.DataFrame(parameter, columns=[
    'Metode', 'n_estimators', 'F1 train penuh', 'F1 train CV',
    'F1 validasi', 'SD F1', 'F1 test', 'Dipilih dari CV'])
parameter['Selisih train-validasi CV'] = parameter['F1 train CV'] - parameter['F1 validasi']
print(parameter.to_string(index=False, float_format=lambda v: f'{v:.6f}'))
parameter.to_csv(hasil / 'soal3_jumlah_estimator.csv', index=False)

model_pilihan = []
for metode, pilih in pilihan.items():
    nama = f"{metode} {pilih['n_estimators']}"
    pred = model_latih[nama].predict(X_test)
    prediksi_test[nama] = pred
    tn, fp, fn, tp = confusion_matrix(y_test, pred, labels=[1, 0]).ravel()
    model_pilihan.append([
        nama, accuracy_score(y_test, pred),
        precision_score(y_test, pred, pos_label=0, zero_division=0),
        recall_score(y_test, pred, pos_label=0, zero_division=0),
        f1_score(y_test, pred, pos_label=0, zero_division=0),
        int(tn), int(fp), int(fn), int(tp)])
model_pilihan = pd.DataFrame(model_pilihan, columns=evaluasi.columns)
print('\nEvaluasi konfigurasi pilihan CV:')
print(model_pilihan.to_string(index=False, float_format=lambda v: f'{v:.6f}'))
print('\nPrediksi test model awal dan model pilihan CV:')
print(prediksi_test.to_string(index=False))
model_pilihan.to_csv(hasil / 'soal3_evaluasi_pilihan_cv.csv', index=False)
prediksi_test.to_csv(hasil / 'soal3_prediksi_test.csv', index=False)

fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
for ax, metode in zip(axes, ['AdaBoost', 'Gradient Boosting']):
    t = parameter[parameter.Metode == metode]
    ax.plot(t.n_estimators, t['F1 train CV'], 'o-', label='Train CV', color='#4c718e')
    ax.errorbar(t.n_estimators, t['F1 validasi'], yerr=t['SD F1'], fmt='s-',
                 capsize=3, label='Validasi CV', color='#5b8c6f')
    ax.plot(t.n_estimators, t['F1 test'], '^-', label='Test', color='#c87946')
    ax.set_xticks([10, 50, 100])
    ax.set_ylim(0.75, 1.02)
    ax.set_title(metode)
    ax.set_xlabel('Jumlah estimator')
    ax.grid(alpha=0.2)
    ax.legend(fontsize=8)
axes[0].set_ylabel('F1 kelas malignant (0)')
simpan_gambar('soal3_jumlah_estimator')

# %% 10. Ringkasan hasil
print('Hard voting:', f"{akurasi_voting.loc[akurasi_voting.Model == 'Hard Voting', 'Accuracy'].iloc[0]:.6f}")
print('Soft voting: P(Fraud) =', f'{prob_fraud:.6f}', '->', kelas_soft)
print('Alpha AdaBoost manual:', [round(a, 9) for a in alpha])
print('Kelas positif Soal 3: malignant (0).')
print('Parameter dipilih dari lima fold pada train; test dipakai setelah pilihan ditetapkan.')
print('Hasil ini berlaku untuk dataset breast cancer, bukan perilaku pelanggan churn.')
