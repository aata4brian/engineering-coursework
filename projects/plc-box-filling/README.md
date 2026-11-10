# Otomasi pengisian kotak

Pada tugas Otomasi Industri ini saya menentukan kebutuhan alur pengisian dan arahan tampilan HMI. Berkas PLC dan panel disusun dengan bantuan asisten. Versi portofolio ini memakai model Python terpisah untuk memeriksa urutan logika per scan.

Arsip CP2E menunjukkan dua konveyor. Konveyor barang C1 mengisi kotak saat sensor posisi aktif. Counter menghitung hingga 10 barang. Saat penuh, C1 berhenti dan C2 memindahkan kotak. Ketika kotak meninggalkan sensor, hitungan kembali ke nol. Start dan Stop bisa datang dari tombol fisik atau HMI pada versi arsip yang lebih baru.

Pada model kurasi, Stop menang pada scan yang sama dengan Start atau pulsa barang. Pulsa sensor dihitung saat naik dari OFF ke ON. Sensor yang masih ON ketika sistem dijalankan kembali tidak menambah hitungan. Indeks animasi logis mengikuti hitungan dari 0 sampai 10. Di arsip HMI, register D100 dihitung sebagai 11 dikurangi sisa counter. Pemetaan indeks itu ke panel asli masih perlu dicek di CX-Designer.

```sh
python check.py
python check.py --csv
```

Uji mencakup 30 scan, termasuk sensor tertahan, Stop bersamaan dengan pulsa, barang ke-10, pulsa tambahan, dan reset saat kotak pergi. Model ini tidak meniru timing perangkat atau seluruh perilaku runtime Omron. Pengujian dilakukan pada Python tanpa PLC fisik atau CX-Simulator.

[Rujukan instruksi CNT dan BIN pada Omron CP1E/CP2E, W483](https://www.omron.co.id/data_pdf/mnu/w483-e1-08_cp1e_cp2e.pdf?id=2064)
