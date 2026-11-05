# Validation — 5 November 2026

| Proyek | Pemeriksaan | Hasil |
| --- | --- | --- |
| Machine Failure | Eksekusi penuh di AATA, data AI4I 10.000 baris, checksum cocok | Exit 0; seluruh JSON hasil cocok dengan arsip, termasuk F1 test 0,5714286 |
| Ensemble Learning | Eksekusi penuh di AATA, data publik bawaan scikit-learn | Exit 0; AdaBoost 100 menghasilkan F1 0,9382716, TP=38, FN=4, FP=1, TN=71 |
| Camera Calibration | Eksekusi CLI v2 di AATA memakai foto checkerboard asli | Exit 0; 15 foto valid, resolusi 2448×2048, RMS 1,625767 px |
| Clustering | Eksekusi ekspor Python di Linux, pembandingan silhouette manual dan pustaka | Lulus; silhouette kedua partisi 0,675267, partisi identik untuk data latihan ini |
| Serial Irrigation | Kompilasi C++17 dan uji batas ambang, startup, input tak valid, timeout, rollover waktu | Lulus pada host; belum kompilasi Arduino maupun pengujian rangkaian fisik |
| AATA Bookstore | Kompilasi C++17, pembelian, stok habis, saldo kurang, EOF, input menu, ID ganda, rollback poin | Lulus; uji pengembalian ganda, hari rencana tidak cocok, diskon pecahan, serta input submenu/EOF lulus; penyimpanan antarsesi belum dibuat |

Jalankan pemeriksaan tanpa perangkat lab:

```sh
python -m pip install -r projects/clustering/requirements.txt
python scripts/verify.py
```

Pemeriksaan otomatis GitHub memakai perintah yang sama. Eksperimen ML penuh dan foto kalibrasi tidak dijalankan di CI; foto asli tidak dibagikan ke publik. Ringkasan eksekusi penuh terdapat di `reproduction.json`.

Versi untuk reproduksi ML di AATA: Python 3.12.10, NumPy 1.26.4, pandas 2.2.3, scikit-learn 1.6.1, Matplotlib 3.10.1. Pemeriksaan host Linux memakai Python 3.12.14 dan scikit-learn 1.8.0.

RMS kalibrasi bukan bukti akurasi pose dunia nyata. Koefisien distorsi besar menunjukkan perlunya memeriksa stabilitas fit dengan cakupan papan dan sudut pengambilan yang lebih beragam. Ukuran kotak dan panjang fokus nominal lensa belum diukur; angka fisik turunan tidak dijadikan klaim portofolio.
