#include <iostream>
#include <optional>
#include <sstream>
#include <string>
using namespace std; // biar gak perlu std:: di depan cout, cin

#define MAKS 5 // maksimal 5 elemen

// QUEUE LINEAR
class QueueLinear {
private:
    int data[MAKS];
    int kepala, ekor; // kepala itu front, ekor itu rear

public:
    QueueLinear() { kepala = ekor = -1; } // konstruktor, queue awalnya kosong

    bool kosong() { return ekor == -1; } // queue kosong kalau ekor -1
    bool penuh() { return ekor == MAKS - 1; } // queue penuh kalau ekor di indeks terakhir

    void masuk(int nilai) {
        if (penuh()) cout << "Queue Linear penuh!\n"; // kalau penuh, tampil pesan
        else { // kalau gak penuh, masukin data
            if (kosong()) kepala = ekor = 0; // kalau kosong, kepala dan ekor jadi 0
            else ekor++; // kalau gak kosong, ekor maju 1
            data[ekor] = nilai;
            cout << nilai << " masuk ke Queue Linear.\n";
        }
    }

    optional<int> keluar() {
        if (kosong()) { // kalau kosong, tampil pesan
            cout << "Queue Linear kosong!\n";
            return nullopt;
        }
        int nilai = data[kepala]; // ambil nilai di kepala
        for (int i = kepala; i < ekor; i++) data[i] = data[i+1]; // geser data ke kiri
        ekor--; // ekor mundur 1
        if (ekor < 0) kepala = -1; // kalau ekor < 0, berarti queue kosong
        return nilai; // kembalikan nilai yang keluar
    }

    void tampil() { 
        if (kosong()) cout << "Queue Linear kosong!\n";
        else {
            cout << "Isi Queue Linear: ";
            for (int i = kepala; i <= ekor; i++) cout << data[i] << " "; // tampil data dari kepala ke ekor
            cout << endl;
        }
    }

    // fungsi tambahan
    long long total() {
        if (kosong()) return 0;
        long long t = 0; 
        for (int i = kepala; i <= ekor; i++) t += data[i]; // jumlahkan semua elemen
        return t; // kembalikan total
    }
    double rata() {
        if (kosong()) return 0; // kalau kosong, rata-rata 0
        return static_cast<double>(total()) / (ekor - kepala + 1); // total dibagi jumlah elemen
    }
    optional<int> maks() {
        if (kosong()) return nullopt;
        int m = data[kepala]; // anggap elemen pertama sebagai maksimum
        for (int i = kepala; i <= ekor; i++) if (data[i] > m) m = data[i]; // cari maksimum
        return m; // kembalikan maksimum
    }
    optional<int> min() {
        if (kosong()) return nullopt;
        int m = data[kepala]; // anggap elemen pertama sebagai minimum
        for (int i = kepala; i <= ekor; i++) if (data[i] < m) m = data[i]; // cari minimum
        return m; // kembalikan minimum
    }
};

// QUEUE CIRCULAR
class QueueCircular {
private:
    int data[MAKS];
    int kepala, ekor;

public:
    QueueCircular() { kepala = ekor = -1; } // konstruktor, queue awalnya kosong

    bool kosong() { return kepala == -1; } // queue kosong kalau kepala -1
    bool penuh() { return ((ekor + 1) % MAKS == kepala); } // queue penuh kalau ekor + 1 mod MAKS == kepala

    void masuk(int nilai) {
        if (penuh()) cout << "Queue Circular penuh!\n"; // kalau penuh, tampil pesan
        else {
            if (kosong()) kepala = ekor = 0; // kalau kosong, kepala dan ekor jadi 0
            else ekor = (ekor + 1) % MAKS; // kalau gak kosong, ekor maju 1 mod MAKS
            data[ekor] = nilai; // simpan nilai di ekor
            cout << nilai << " masuk ke Queue Circular.\n";
        }
    }

    optional<int> keluar() {
        if (kosong()) { // kalau kosong, tampil pesan
            cout << "Queue Circular kosong!\n";
            return nullopt;
        }
        int nilai = data[kepala]; // ambil nilai di kepala
        if (kepala == ekor) kepala = ekor = -1; // kalau cuma ada 1 elemen, jadi kosong
        else kepala = (kepala + 1) % MAKS; // kepala maju 1 mod MAKS
        return nilai; 
    }

    void tampil() {
        if (kosong()) cout << "Queue Circular kosong!\n"; // kalau kosong, tampil pesan
        else { // kalau gak kosong, tampil data
            cout << "Isi Queue Circular: ";
            int i = kepala; // mulai dari kepala
            while (true) { // loop terus sampai break
                cout << data[i] << " "; // tampil data
                if (i == ekor) break; // kalau sudah sampai ekor, berhenti
                i = (i + 1) % MAKS; // i maju 1 mod MAKS
            }
            cout << endl;
        }
    }
};

// QUEUE LINKED LIST
struct Node {
    int data; // data integer
    Node *berikutnya; // pointer ke node berikutnya
};

class QueueLinked {
private:
    Node *kepala, *ekor; // kepala itu front, ekor itu rear

public:
    QueueLinked() { kepala = ekor = nullptr; }
    QueueLinked(const QueueLinked&) = delete;
    QueueLinked& operator=(const QueueLinked&) = delete;
    ~QueueLinked() {
        while (!kosong()) keluar();
    }

    bool kosong() { return kepala == nullptr; } // queue kosong kalau kepala nullptr

    void masuk(int nilai) {
        Node *baru = new Node; // buat node baru
        baru->data = nilai; // isi data
        baru->berikutnya = nullptr; // berikutnya nullptr
        if (kosong()) kepala = ekor = baru; // kalau kosong, kepala dan ekor jadi node baru
        else { // kalau gak kosong, ekor berikutnya jadi node baru, ekor jadi node baru
            ekor->berikutnya = baru;
            ekor = baru;
        }
        cout << nilai << " masuk ke Queue Linked List.\n";
    }

    optional<int> keluar() {
        if (kosong()) { // kalau kosong, tampil pesan
            cout << "Queue Linked List kosong!\n"; 
            return nullopt;
        }
        int nilai = kepala->data; // ambil nilai di kepala
        Node *hapus = kepala; // simpan node kepala untuk dihapus
        kepala = kepala->berikutnya; // kepala maju ke berikutnya
        delete hapus; // hapus node lama
        if (kepala == nullptr) ekor = nullptr; // kalau kepala nullptr, ekor juga nullptr
        return nilai; // kembalikan nilai yang keluar
    }

    void tampil() {
        if (kosong()) cout << "Queue Linked List kosong!\n"; // kalau kosong, tampil pesan
        else { // kalau gak kosong, tampil data
            cout << "Isi Queue Linked List: ";
            Node *bantu = kepala; // mulai dari kepala
            while (bantu != nullptr) { // loop sampai bantu nullptr
                cout << bantu->data << " "; // tampil data
                bantu = bantu->berikutnya; // maju ke berikutnya
            }
            cout << endl;
        }
    }
};

// Baca satu baris agar masukan seperti 4abc tidak diterima sebagai 4.
bool bacaInt(int& nilai) {
    string baris;
    if (!getline(cin, baris)) return false;
    istringstream input(baris);
    char sisa;
    if (!(input >> nilai) || (input >> sisa)) {
        cout << "Masukkan bilangan bulat.\n";
        return false;
    }
    return true;
}

void cetakKeluar(optional<int> nilai) {
    if (nilai) cout << *nilai << " keluar.\n";
}

// PROGRAM UTAMA
int main() { 
    QueueLinear ql; // buat objek QueueLinear
    QueueCircular qc; // buat objek QueueCircular
    QueueLinked qll; // buat objek QueueLinked
    int pilih = -1, nilai; // variabel untuk pilihan menu dan nilai

    while (true) {
        cout << "\n=== MENU QUEUE ===\n";
        cout << "1. Enqueue Linear\n";
        cout << "2. Dequeue Linear\n";
        cout << "3. Tampil Linear\n";
        cout << "4. Statistik Linear (total/rata/maks/min)\n";
        cout << "5. Enqueue Circular\n";
        cout << "6. Dequeue Circular\n";
        cout << "7. Tampil Circular\n";
        cout << "8. Enqueue Linked List\n";
        cout << "9. Dequeue Linked List\n";
        cout << "10. Tampil Linked List\n";
        cout << "0. Keluar\n";
        cout << "Pilih menu: ";
        if (!bacaInt(pilih)) {
            if (!cin) break;
            continue;
        }
        if (pilih == 0) break;

        switch(pilih) {
            case 1: cout << "Masukkan nilai: "; if (bacaInt(nilai)) ql.masuk(nilai); break;
            case 2: cetakKeluar(ql.keluar()); break;
            case 3: ql.tampil(); break;
            case 4: 
                if (!ql.kosong()) {
                    cout << "Total: " << ql.total() << endl;
                    cout << "Rata-rata: " << ql.rata() << endl;
                    cout << "Maksimum: " << *ql.maks() << endl;
                    cout << "Minimum: " << *ql.min() << endl;
                } else cout << "Queue Linear kosong!\n";
                break;
            case 5: cout << "Masukkan nilai: "; if (bacaInt(nilai)) qc.masuk(nilai); break;
            case 6: cetakKeluar(qc.keluar()); break;
            case 7: qc.tampil(); break;
            case 8: cout << "Masukkan nilai: "; if (bacaInt(nilai)) qll.masuk(nilai); break;
            case 9: cetakKeluar(qll.keluar()); break;
            case 10: qll.tampil(); break;
            default: cout << "Pilihan tidak tersedia.\n";
        }
        if (!cin) break;
    }

    return 0;
}
