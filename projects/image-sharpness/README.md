# Empat ukuran ketajaman citra PCB

Pada UTS Visi Komputer saya membandingkan Brenner, Tenenbaum, squared gradient, dan filter MDCT sesuai persamaan tugas. Versi kurasi memisahkan fungsi pengukuran dari skrip eksperimen, menambahkan pemeriksaan masukan, serta membandingkan implementasi vektor dengan perhitungan skalar dan kernel langsung.

```sh
python -m pip install -r requirements.txt
python check.py
python sharpness.py gambar.jpg
```

Delapan skor dari dua citra PCB 640 × 480 pada arsip berhasil dihitung ulang. Semua operator memberi skor lebih tinggi pada citra kedua, dengan kenaikan 18,79–34,05%. Gambar sumber adalah bahan tugas dan tetap di arsip privat. Uji otomatis publik memakai matriks sintetis.

Skor sangat dipengaruhi intensitas dan tekstur. Uji menunjukkan penggandaan intensitas menaikkan skor menjadi empat kali lipat. Dua contoh PCB belum cukup untuk menilai kemampuan umum operator pada foto yang berbeda.

Arsip juga berisi benchmark 500 pengulangan. Rentang waktu median pada CSV adalah sekitar 0,312–1,717 ms, sedangkan PDF laporan menyebut sekitar 0,340–1,952 ms. Versi portofolio menampilkan rasio skor yang sudah dicocokkan, sementara asal perbedaan timing masih perlu ditelusuri.
