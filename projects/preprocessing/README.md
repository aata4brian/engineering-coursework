# Preprocessing sebelum data masuk ke model

Di tugas Pembelajaran Mesin, saya membersihkan tabel pelanggan dengan imputasi median, pembatasan outlier IQR, standardisasi, dan one-hot encoding. Praktikum TM1–3 juga mencakup eksplorasi distribusi, perapian tabel, serta pemeriksaan nilai hilang. Skrip tugas menghitung statistik dari seluruh tabel untuk membuat tabel bersih. Jika tabel itu dipakai mengevaluasi model, statistiknya perlu dihitung setelah data dipisah.

Di versi portofolio, saya pakai satu contoh pelanggan fiktif untuk menunjukkan perbedaan itu. Lima baris latih menentukan median usia, batas pengeluaran, skala, dan kolom kategori. Dua baris uji menggunakan statistik yang sama. Kategori baru menghasilkan nol pada kedua kolom kategori.

## Menjalankan contoh

```sh
python -m pip install -r requirements.txt
python preprocessing.py
python check.py
```

Median usia latih adalah 27 tahun. Batas IQR pengeluaran adalah 60 sampai 220 satuan contoh. Pengeluaran latih 1.000 dan pengeluaran uji 5.000 sama-sama dipotong menjadi 220 sebelum standardisasi. Uji juga memeriksa usia kosong, kategori baru, kolom latih kosong, dan nilai tak hingga. Output tersimpan di `example-results.json`.

Contoh ini hanya menguji transformasi. Tidak ada model atau skor prediksi, dan tujuh baris fiktif belum mewakili distribusi pelanggan. Notebook serta tabel sumber tetap di arsip kuliah.
