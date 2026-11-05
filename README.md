# Engineering Coursework

Enam proyek yang dirapikan dari tugas kuliah saya di Teknik Robotika dan Kecerdasan Buatan, Universitas Airlangga. Saya mengumpulkan kode yang sebelumnya tersebar di laptop dan Google Drive agar metode, hasil, dan kekurangannya bisa diperiksa dari satu tempat.

| Proyek | Yang dikerjakan | Bukti |
| --- | --- | --- |
| [Machine Failure](projects/machine-failure) | SVM, tuning C, PCA; data sensor sintetis | Skor CV, prediksi test, confusion matrix, checksum dataset |
| [Ensemble Learning](projects/ensemble-learning) | Voting, AdaBoost manual, ensemble pohon | Hasil per-fold, pilihan estimator, prediksi test |
| [Clustering](projects/clustering) | K-Means, FCM, hierarchical clustering | Notebook, ekspor Python, pemeriksaan silhouette |
| [Camera Calibration](projects/camera-calibration) | Chessboard 9×6, error per-view, undistortion | CLI dari notebook v2; foto asli tidak disertakan |
| [Serial Irrigation](projects/serial-irrigation) | Sensor dan kontrol katup dua board | Firmware, uji logika host, timeout komunikasi |
| [AATA Bookstore](projects/bookstore) | OOP C++, katalog, transaksi, peminjaman | Program CLI, contoh input; brief berasal dari tugas kelompok |

Lihat [halaman proyek dan grafiknya](https://moch-brian-mursyidan-baldan-portfol.vercel.app/coursework.html).

## Cara membaca hasil

`reference-results/` menyimpan hasil yang sudah ada dalam arsip tugas. Hasil tersebut bukan otomatis hasil eksekusi terbaru. Program menulis hasil baru ke `hasil/`. Catatan pengecekan kurasi tersedia di [VALIDATION.md](VALIDATION.md).

Setiap folder mempunyai petunjuk menjalankan, asal arsip, dan batasan. Notebook placeholder, modul dosen, folder angkatan lain, serta berkas yang kepemilikannya tidak jelas tidak dimasukkan. Dataset medis pada ensemble adalah dataset publik bawaan scikit-learn; programnya merupakan latihan klasifikasi.

Nama penulis: Moch. Brian Mursyidan Baldan · [@aata4brian](https://github.com/aata4brian)
