# KNN dan SVM pada tiga bentuk data

Di praktikum Pembelajaran Mesin saya mencoba cara kerja voting tetangga pada KNN dan batas keputusan pada SVM. Versi kurasi mengambil implementasi manual dari dua skrip tugas dan membandingkannya dengan scikit-learn pada data sintetis yang sama. Hasil seri pada KNN manual memakai label terkecil. SVM manual memakai pembaruan bobot soft-margin linear.

```sh
python -m pip install -r requirements.txt
python experiment.py
python check.py
```

Setiap dataset berisi 200 titik. Model menerima 160 titik latih dan dinilai pada 40 titik uji yang sama. StandardScaler dilatih di dalam pipeline menggunakan data latih. Parameter ditetapkan sebelum evaluasi. CSV memuat jumlah prediksi benar, akurasi, dan macro-F1 untuk kelima konfigurasi.

Pada Circles, SVC linear menjawab benar 17 dari 40 titik. SVC RBF dan kedua versi KNN menjawab benar 40. Pada Blobs, semua konfigurasi benar 40 dari 40. Selisih di Circles menunjukkan pengaruh bentuk batas keputusan untuk data ini. Skor bergantung pada noise, ukuran sampel, dan satu pembagian tetap.

Uji mencakup voting seri, vektor nol untuk jarak cosine, k di luar rentang, fitur non-finite, label SVM yang salah, serta prediksi sebelum fit. Data praktikum cuaca dan berkas modul tidak diperlukan untuk menjalankan versi ini.
