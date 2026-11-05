"""Ekspor sel kode notebook kuliah; hasil gambar disimpan di hasil/."""
from pathlib import Path
import os
import matplotlib
matplotlib.use("Agg")

def display(value):
    print(value.to_string() if hasattr(value,"to_string") else value)

out=Path(__file__).resolve().parent/"hasil"
out.mkdir(exist_ok=True)
os.chdir(out)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from scipy.spatial.distance import cdist, pdist, squareform
from scipy.cluster.hierarchy import linkage, cut_tree, dendrogram
from sklearn.metrics import silhouette_score

pd.set_option('display.precision', 6)

data_1 = np.array([
    [2, 9], [3, 8], [4, 7],
    [8, 2], [9, 3], [7, 4],
    [1, 5], [6, 1], [2, 6]
], dtype=float)

pusat_1 = data_1[[0, 3, 7]].copy()
cluster_sebelumnya = None

for iterasi in range(1, 21):
    jarak = cdist(data_1, pusat_1, metric='euclidean')
    cluster_1 = np.argmin(jarak, axis=1)

    print(f'Iterasi {iterasi}: pusat sebelum pengelompokan =')
    display(pd.DataFrame(pusat_1, columns=['X', 'Y'], index=['C1', 'C2', 'C3']))
    display(pd.DataFrame({
        'Data': np.arange(1, 10),
        'd(C1)': jarak[:, 0],
        'd(C2)': jarak[:, 1],
        'd(C3)': jarak[:, 2],
        'Cluster': cluster_1 + 1
    }).set_index('Data'))

    pusat_baru = np.array([
        data_1[cluster_1 == j].mean(axis=0) for j in range(3)
    ])
    print('Pusat setelah diperbarui:')
    display(pd.DataFrame(pusat_baru, columns=['X', 'Y'], index=['C1', 'C2', 'C3']))

    if cluster_sebelumnya is not None and np.array_equal(cluster_1, cluster_sebelumnya):
        print('Anggota cluster sudah tetap. Iterasi selesai.')
        break

    cluster_sebelumnya = cluster_1.copy()
    pusat_1 = pusat_baru

print('Hasil akhir:')
for j in range(3):
    anggota = (np.flatnonzero(cluster_1 == j) + 1).tolist()
    print(f'C{j + 1}: Data {anggota}, pusat = {pusat_baru[j].tolist()}')

data_2 = np.array([
    [12, 18], [8, 14], [15, 20], [4, 12], [6, 10],
    [10, 17], [3, 4], [8, 6], [2, 2], [9, 7]
], dtype=float)

U = np.array([
    [0.7, 0.2, 0.1], [0.6, 0.3, 0.1],
    [0.8, 0.1, 0.1], [0.2, 0.7, 0.1],
    [0.2, 0.7, 0.1], [0.6, 0.3, 0.1],
    [0.1, 0.2, 0.7], [0.1, 0.3, 0.6],
    [0.1, 0.1, 0.8], [0.1, 0.4, 0.5]
], dtype=float)

assert np.allclose(U.sum(axis=1), 1)
display(pd.DataFrame(U, columns=['u1 awal', 'u2 awal', 'u3 awal'],
                     index=np.arange(1, 11)))

riwayat = []
toleransi = 1e-6

for iterasi in range(1, 21):
    # Bobot m=2 digunakan untuk menghitung ketiga pusat.
    bobot = U ** 2
    pusat_2 = (bobot.T @ data_2) / bobot.sum(axis=0)[:, None]
    jarak = cdist(data_2, pusat_2)

    # Rumus FCM untuk m=2: (1 / d_ij^2) dibagi jumlahnya per baris.
    kebalikan_kuadrat = 1 / np.maximum(jarak, 1e-12) ** 2
    U_baru = kebalikan_kuadrat / kebalikan_kuadrat.sum(axis=1, keepdims=True)

    # Jika ada titik tepat pada pusat, keanggotaannya dibuat pasti.
    for i in range(len(data_2)):
        pusat_berimpit = np.flatnonzero(jarak[i] < 1e-12)
        if len(pusat_berimpit):
            U_baru[i] = 0
            U_baru[i, pusat_berimpit] = 1 / len(pusat_berimpit)

    objektif = np.sum(U ** 2 * jarak ** 2)
    perubahan = np.max(np.abs(U_baru - U))
    riwayat.append([
        iterasi, *pusat_2[0], *pusat_2[1], *pusat_2[2],
        objektif, perubahan
    ])

    if iterasi == 1:
        print('Jarak Data-1 ke pusat pada iterasi pertama:', np.round(jarak[0], 6))
        print('Keanggotaan baru setelah iterasi pertama:')
        display(pd.DataFrame(U_baru, columns=['u1', 'u2', 'u3'],
                             index=np.arange(1, 11)))

    U = U_baru
    if perubahan < toleransi:
        print(f'Konvergen pada iterasi {iterasi}.')
        break
else:
    print('Berhenti karena mencapai batas 20 iterasi.')

kolom = ['Iterasi', 'v1-x', 'v1-y', 'v2-x', 'v2-y',
         'v3-x', 'v3-y', 'J', 'Perubahan maksimum']
display(pd.DataFrame(riwayat, columns=kolom).set_index('Iterasi'))

# Pusat dihitung lagi dari U terakhir agar pusat dan partisi akhir sesuai.
bobot_akhir = U ** 2
pusat_akhir_2 = (bobot_akhir.T @ data_2) / bobot_akhir.sum(axis=0)[:, None]
dominan_2 = np.argmax(U, axis=1) + 1

print('Keanggotaan dan cluster dominan akhir:')
display(pd.DataFrame({
    'u1': U[:, 0], 'u2': U[:, 1], 'u3': U[:, 2],
    'Cluster dominan': dominan_2
}, index=np.arange(1, 11)))
print('Pusat akhir:', np.round(pusat_akhir_2, 6))
print('Perubahan terakhir:', perubahan)

data_3 = np.array([
    [55, 420], [62, 510], [58, 470], [120, 980], [125, 1050],
    [130, 1100], [40, 310], [45, 330], [135, 1150], [48, 360]
], dtype=float)
nama_kota = list('ABCDEFGHIJ')

matriks_jarak_kota = squareform(pdist(data_3, metric='euclidean'))
print('Matriks jarak antarkota:')
display(pd.DataFrame(matriks_jarak_kota,
                     index=nama_kota, columns=nama_kota))

Z3 = linkage(data_3, method='complete', metric='euclidean')
anggota_node = {i: [nama_kota[i]] for i in range(10)}

for tahap, (kiri, kanan, tinggi, jumlah) in enumerate(Z3, start=1):
    kiri, kanan = int(kiri), int(kanan)
    anggota_node[10 + tahap - 1] = anggota_node[kiri] + anggota_node[kanan]
    print(f'Tahap {tahap}: {anggota_node[kiri]} + {anggota_node[kanan]} '
          f'-> {anggota_node[10 + tahap - 1]}, jarak = {tinggi:.4f}')

cluster_kota = cut_tree(Z3, n_clusters=3).ravel()
print('Tiga cluster akhir:')
for j in sorted(np.unique(cluster_kota)):
    print(f'Cluster {int(j)+1}:',
          [nama_kota[i] for i in np.flatnonzero(cluster_kota == j)])

# Di soal ini tinggi penggabungan ke-7 dan ke-8 berbeda,
# jadi ambang di tengahnya tepat menunjukkan tiga cluster.
ambang_kota = (Z3[6, 2] + Z3[7, 2]) / 2
plt.figure(figsize=(10, 4.5))
dendrogram(Z3, labels=nama_kota, color_threshold=ambang_kota)
plt.axhline(ambang_kota, color='gray', linestyle='--', linewidth=1)
plt.title('Complete linkage - kota (3 cluster)')
plt.ylabel('Jarak Euclidean')
plt.tight_layout()
plt.savefig('dendrogram_kota.png', dpi=200, bbox_inches='tight')
plt.show()

data_4 = np.array([
    [3, 2], [4, 3], [5, 4], [15, 20], [16, 22],
    [17, 24], [8, 10], [9, 12], [20, 30], [21, 32]
], dtype=float)
nama_pelanggan = [f'P{i}' for i in range(1, 11)]

pusat_4 = data_4[[0, 3, 8]].copy()
cluster_sebelumnya = None

for iterasi in range(1, 21):
    jarak = cdist(data_4, pusat_4)
    cluster_kmeans = np.argmin(jarak, axis=1)

    print(f'K-Means, iterasi {iterasi}:')
    display(pd.DataFrame({
        'd(C1)': jarak[:, 0], 'd(C2)': jarak[:, 1],
        'd(C3)': jarak[:, 2], 'Cluster': cluster_kmeans + 1
    }, index=nama_pelanggan))

    pusat_baru = np.array([
        data_4[cluster_kmeans == j].mean(axis=0) for j in range(3)
    ])
    print('Pusat baru:', pusat_baru.tolist())

    if cluster_sebelumnya is not None and np.array_equal(cluster_kmeans, cluster_sebelumnya):
        print('Cluster sudah tetap.')
        break

    cluster_sebelumnya = cluster_kmeans.copy()
    pusat_4 = pusat_baru

print('Anggota K-Means:')
for j in range(3):
    print(f'Cluster {j+1}:',
          [nama_pelanggan[i] for i in np.flatnonzero(cluster_kmeans == j)])

Z4 = linkage(data_4, method='single', metric='euclidean')
anggota_node = {i: [nama_pelanggan[i]] for i in range(10)}

for tahap, (kiri, kanan, tinggi, jumlah) in enumerate(Z4, start=1):
    kiri, kanan = int(kiri), int(kanan)
    anggota_node[10 + tahap - 1] = anggota_node[kiri] + anggota_node[kanan]
    print(f'Tahap {tahap}: {anggota_node[kiri]} + {anggota_node[kanan]} '
          f'-> {anggota_node[10 + tahap - 1]}, jarak = {tinggi:.4f}')

cluster_single = cut_tree(Z4, n_clusters=3).ravel()
print('Anggota single linkage ketika tersisa tiga cluster:')
for j in sorted(np.unique(cluster_single)):
    print(f'Cluster {int(j)+1}:',
          [nama_pelanggan[i] for i in np.flatnonzero(cluster_single == j)])

# Penggabungan ke-7 dan ke-8 sama tinggi. Garis horizontal saja
# tidak dapat menandai tepat tiga cluster, jadi cabang diwarnai
# menurut keanggotaan hasil potongan setelah penggabungan ke-7.
warna = ['#2563eb', '#16a34a', '#dc2626']
isi_cabang = {i: {i} for i in range(10)}
for i, (kiri, kanan, _, _) in enumerate(Z4):
    isi_cabang[10 + i] = isi_cabang[int(kiri)] | isi_cabang[int(kanan)]

def warna_cabang(nomor):
    kelompok = {int(cluster_single[i]) for i in isi_cabang[int(nomor)]}
    return warna[kelompok.pop()] if len(kelompok) == 1 else '#6b7280'

fig, ax = plt.subplots(figsize=(10, 4.5))
dendrogram(Z4, labels=nama_pelanggan,
           link_color_func=warna_cabang, ax=ax)
ax.set_title('Single linkage - pelanggan (3 cluster)')
ax.set_ylabel('Jarak Euclidean')
legenda = []
for j in sorted(np.unique(cluster_single)):
    isi = ', '.join(nama_pelanggan[i]
                    for i in np.flatnonzero(cluster_single == j))
    legenda.append(Patch(facecolor=warna[int(j)],
                         label=f'Cluster {int(j)+1}: {isi}'))
ax.legend(handles=legenda, fontsize=8, loc='upper right')
fig.tight_layout()
fig.savefig('dendrogram_pelanggan.png', dpi=200, bbox_inches='tight')
plt.show()

for metode, label in [('K-Means', cluster_kmeans),
                      ('Single linkage', cluster_single)]:
    rincian = []

    for i in range(10):
        anggota_sendiri = np.flatnonzero(label == label[i])
        anggota_sendiri = anggota_sendiri[anggota_sendiri != i]

        # Rata-rata jarak dalam cluster sendiri, tanpa menghitung diri sendiri.
        a = np.mean(np.linalg.norm(data_4[anggota_sendiri] - data_4[i], axis=1))

        # Cari rata-rata jarak terkecil ke cluster lain.
        b = min(
            np.mean(np.linalg.norm(data_4[label == j] - data_4[i], axis=1))
            for j in np.unique(label) if j != label[i]
        )
        s_i = (b - a) / max(a, b)
        rincian.append([nama_pelanggan[i], int(label[i]) + 1,
                        a, b, s_i])

    print()
    print(metode)
    display(pd.DataFrame(rincian,
                         columns=['Pelanggan', 'Cluster', 'a(i)', 'b(i)', 's(i)'])
            .set_index('Pelanggan'))
    skor_manual = np.mean([baris[-1] for baris in rincian])
    skor_pustaka = silhouette_score(data_4, label)
    assert np.isclose(skor_manual, skor_pustaka)
    print(f'Silhouette Score = {skor_manual:.6f}')

# Nomor cluster boleh berbeda, tetapi pasangan pelanggan dalam cluster
# harus sama jika ingin menyebut hasil kedua metode identik.
anggota_kmeans = {frozenset(np.flatnonzero(cluster_kmeans == j))
                 for j in np.unique(cluster_kmeans)}
anggota_single = {frozenset(np.flatnonzero(cluster_single == j))
                 for j in np.unique(cluster_single)}
print()
print('Partisi kedua metode identik:', anggota_kmeans == anggota_single)

print()
print('Rata-rata fitur per cluster K-Means:')
for j in np.unique(cluster_kmeans):
    indeks = np.flatnonzero(cluster_kmeans == j)
    rerata = data_4[indeks].mean(axis=0)
    print(f'Cluster {int(j)+1}: {[nama_pelanggan[i] for i in indeks]}, '
          f'transaksi {rerata[0]:.2f}, pembelian Rp{rerata[1]:.2f} juta')
