# Tiga cara membuat antrean FIFO di C++

Di praktikum Struktur Data, saya membandingkan tiga cara menyimpan antrean bilangan bulat: array linear, array melingkar, dan linked list. Array linear menggeser isi setelah elemen depan keluar. Array melingkar cukup menggeser indeks dengan modulo. Linked list menambah atau menghapus node sesuai isi antrean.

Di versi kurasi, hasil dequeue memakai `std::optional` supaya nilai `-1` tetap bisa masuk dan keluar sebagai data. Saya juga menambahkan penanganan input yang keliru atau berakhir, memperlebar tipe total untuk penjumlahan, dan membebaskan node yang masih tersisa saat program ditutup.

## Cara menjalankan

```sh
g++ -std=c++17 -Wall -Wextra queue.cpp -o queue
./queue
python check.py
```

Uji CLI di Linux memakai GCC dan UndefinedBehaviorSanitizer. Pada array melingkar, angka 10 keluar terlebih dahulu. Setelah slotnya dipakai ulang untuk angka 60, urutan keluar berikutnya tetap 20, 30, 40, 50, 60. Uji juga mencakup antrean kosong dan penuh, nilai negatif, input rusak, dan akhir masukan.

Kedua antrean array sengaja dibatasi lima elemen agar putaran indeks mudah diperiksa. Program berjalan satu sesi di terminal, tanpa penyimpanan data atau pengukuran kinerja.
