# Deteksi warna dari ESP32-CAM

Pada prototipe robot beroda, saya menyiapkan kamera sebagai sumber gambar dan meminta pengolahan dipindah ke laptop. Dashboard memutar gambar 90° ke kanan, menyaring lima warna pada ruang HSV, lalu mengurutkan objek menurut jarak tepi bawah kotaknya ke tepi bawah gambar. Paket dashboard awal dibuat dengan bantuan asisten sesuai kebutuhan prototipe.

Saat kurasi, tampilan dan API diperbaiki supaya deteksi dari frame lama hilang ketika koneksi putus atau frame berumur lima detik. Perubahan pengaturan juga diperiksa sekaligus agar permintaan yang ditolak tidak mengubah sebagian pengaturan.

## Cara mencoba

```sh
python -m pip install -r requirements.txt
python check.py
```

Untuk memakai kamera dengan firmware MJPEG yang sudah aktif, jalankan `python app.py --ip IP_KAMERA`, lalu buka `http://127.0.0.1:5000`. Kamera dan laptop perlu berada di jaringan yang sama. Secara bawaan, aplikasi membaca port 81 dengan jalur `/stream`. Server dashboard hanya mendengarkan koneksi lokal.

## Hasil pengujian

Pada satu frame sintetis yang sudah diputar, objek merah berada 20 piksel dari tepi bawah dan objek biru 70 piksel. Bintik hijau kecil terbuang. Uji juga mencakup filter warna, frame tanpa objek, data basi, dan respons HTTP untuk pengaturan valid serta tidak valid.

Jarak piksel menunjukkan posisi pada gambar. Nilainya bergantung pada sudut kamera dan tidak dikonversi ke sentimeter. Uji memakai frame sintetis dan server lokal di Linux. Pengujian stream kamera asli, firmware, pin motor, serta robot fisik masih diperlukan.
