# Dasar C: integral dengan nilai dan pointer

Di kuis Dasar Pemrograman saya membuat dua versi untuk menghitung integral f(x) = x + 2 dari 0 sampai 3. Keduanya menjumlahkan tinggi persegi panjang di titik kiri setiap interval. Versi pertama mengirim nilai x, sementara versi kedua mengirim alamat x yang dibaca lewat pointer.

Saat dirapikan, kedua versi digabung dalam satu program. Jumlah interval diperiksa sebelum dipakai sebagai pembagi, dan tipe hitung diganti dari float ke double.

```sh
cc -std=c17 -Wall -Wextra integral.c -o integral
printf '100\n' | ./integral value
printf '100\n' | ./integral pointer
python check.py
```

Nilai analitiknya 10,5. Kedua cara menghasilkan 10,05 pada 10 interval dan 10,455 pada 100 interval. Uji CLI juga memeriksa masukan kosong, nol, negatif, pecahan, teks, dan batas interval. Contoh ini memakai satu fungsi dan rentang tetap sehingga selisih terhadap nilai analitik mudah dicek.
