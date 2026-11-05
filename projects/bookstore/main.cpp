#include <iostream> // biar bisa pakai cout, cin
#include <vector> // biar bisa pakai vector
#include <memory> // biar bisa pakai unique_ptr
#include <string> // biar bisa pakai string
#include <fstream> // biar bisa pakai ofstream
#include <iomanip> // biar bisa pakai setprecision
#include <ctime> // biar bisa pakai time
#include <map>
#include <limits>
#include <algorithm>
#include <cmath>

using namespace std; // biar gak usah std::

// ini buat exception dasar
class StoreException : public exception {
protected:
    string pesan;
public:
    StoreException(const string& msg) : pesan(msg) {}
    const char* what() const noexcept override { return pesan.c_str(); }
};

// ini buat stok habis
class OutOfStock : public StoreException {
public:
    OutOfStock(const string& id) : StoreException("Stok item '" + id + "' habis! Gagal beli.") {}
};

// ini buat saldo gak cukup
class InsufficientBalance : public StoreException {
public:
    InsufficientBalance(double butuh, double punya)
        : StoreException("Butuh Rp" + to_string(butuh) + ", tapi saldo cuma Rp" + to_string(punya)) {}
};

// ini buat operasi gak valid
class InvalidOperation : public StoreException {
public:
    InvalidOperation(const string& alasan) : StoreException(alasan) {}
};

class InputClosed : public exception {};

template<typename T>
void readValue(T& value) {
    if (cin >> value) return;
    if (cin.eof()) throw InputClosed();
    cin.clear();
    cin.ignore(numeric_limits<streamsize>::max(), '\n');
    throw InvalidOperation("Input tidak sesuai. Kembali ke menu utama.");
}

// item dasar (abstract)
class Item {
protected:
    string id;
    string judul;
    double harga;
    int stok;

public:
    Item(string id, string judul, double harga, int stok)
        : id(id), judul(judul), harga(harga), stok(stok) {
        if (id.empty() || judul.empty() || !isfinite(harga) || harga < 0 || stok < 0)
            throw InvalidOperation("Identitas, harga, atau stok item tidak valid.");
    }

    virtual ~Item() = default; // virtual destructor buat safety

    string getId() const { return id; }
    string getJudul() const { return judul; }
    double getHarga() const { return harga; }
    int getStok() const { return stok; }
    void setStok(int s) { stok = s; }

    virtual double purchasePrice(int qty) const = 0;
    virtual unique_ptr<Item> clone() const = 0;
    virtual string getType() const = 0;
    virtual bool bisaDipinjam() const = 0;
};

// buku fisik
class Buku : public Item {
private:
    string penulis;
    int halaman;

public:
    Buku(string id, string judul, double harga, int stok, string penulis, int halaman)
        : Item(id, judul, harga, stok), penulis(penulis), halaman(halaman) {}

    // diskon 10% kalau beli lebih dari 10
    double purchasePrice(int qty) const override {
        double total = harga * qty;
        if (qty > 10) total *= 0.9;
        return total;
    }

    // cloning buat catalog
    unique_ptr<Item> clone() const override {
        return make_unique<Buku>(*this);
    }

    // tipe item
    string getType() const override { return "Buku"; }
    bool bisaDipinjam() const override { return true; }

    string getPenulis() const { return penulis; }
    int getHalaman() const { return halaman; }
};

// ebook
class EBook : public Item {
private:
    double ukuranFileMB;

public:
    EBook(string id, string judul, double harga, double ukuran)
        : Item(id, judul, harga, 999999), ukuranFileMB(ukuran) {}

    // harga tetap tanpa diskon
    double purchasePrice(int qty) const override {
        return harga * qty;
    }

    // cloning buat catalog
    unique_ptr<Item> clone() const override {
        return make_unique<EBook>(*this);
    }

    // tipe item
    string getType() const override { return "EBook"; }
    bool bisaDipinjam() const override { return false; }

    // getter ukuran file
    double getUkuranFileMB() const { return ukuranFileMB; }
};

// audiobook
class AudioBook : public Item {
private:
    int durasiMenit;

public:
    AudioBook(string id, string judul, double harga, int stok, int durasi)
        : Item(id, judul, harga, stok), durasiMenit(durasi) {}

    // kena biaya tambahan Rp10.000 kalau durasi lebih dari 300 menit
    double purchasePrice(int qty) const override {
        double total = harga * qty;
        if (durasiMenit > 300) total += 10000 * qty;
        return total;
    }

    // cloning buat catalog
    unique_ptr<Item> clone() const override {
        return make_unique<AudioBook>(*this);
    }

    // tipe item
    string getType() const override { return "AudioBook"; }
    bool bisaDipinjam() const override { return false; }

    // getter durasi
    int getDurasiMenit() const { return durasiMenit; }
};

// logger sederhana
class Logger {
private:
    ofstream fileLog;

public:
    Logger(const string& namaFile = "log_aata.txt")
        : fileLog(namaFile, ios::app) {
        if (!fileLog.is_open()) {
            throw runtime_error("Gagal buka log file – cek folder write permission!");
        }
    }

    // destructor
    ~Logger() = default;

    // fungsi log
    void log(const string& pesan) {
        auto now = time(nullptr);
        fileLog << "[" << put_time(localtime(&now), "%Y-%m-%d %H:%M:%S")
                << "] " << pesan << "\n";
        fileLog.flush();
    }
};

// riwayat transaksi
struct RiwayatTransaksi {
    string idItem;
    int jumlah;
    double totalBayar;
    string jenis;
    time_t waktu;
    string catatan;
};

// member toko
class Member {
private:
    string id;
    string nama;
    double saldo;
    int poinLoyal;
    vector<RiwayatTransaksi> riwayat;
    map<string, vector<int>> pinjamanAktif;

    // fungsi bantu tambah riwayat
    void tambahRiwayat(const RiwayatTransaksi& rec) {
        riwayat.push_back(rec);
    }

    // fungsi bantu hitung denda
    double hitungDenda(int hariPinjam, int hariKembali) const {
        if (hariKembali <= hariPinjam) return 0.0;
        return (hariKembali - hariPinjam) * 2000;
    }

public:
    // TIDAK ADA default constructor → aman untuk map tanpa operator[]
    Member(string id, string nama, double saldoAwal = 0.0)
        : id(id), nama(nama), saldo(saldoAwal), poinLoyal(0) {
        if (id.empty() || nama.empty() || !isfinite(saldoAwal) || saldoAwal < 0)
            throw InvalidOperation("Identitas atau saldo awal tidak valid.");
    }

    string getId() const { return id; }
    string getNama() const { return nama; }
    double getSaldo() const { return saldo; }
    int getPoinLoyal() const { return poinLoyal; }
    const auto& getRiwayat() const { return riwayat; }

    // fungsi top-up saldo
    void topUp(double jumlah) {
        if (!isfinite(jumlah) || jumlah <= 0 || !isfinite(saldo + jumlah))
            throw InvalidOperation("Top-up harus positif dan berada dalam rentang saldo.");
        saldo += jumlah;
    }

    // fungsi beli item
    void purchase(Item& item, int qty) {
        purchase(item, qty, false);
    }

    // fungsi beli item dengan opsi pakai poin
    void purchase(Item& item, int qty, bool usePoints) {
        if (qty <= 0) throw StoreException("Jumlah beli harus positif!");
        if (!dynamic_cast<EBook*>(&item) && item.getStok() < qty)
            throw OutOfStock(item.getId());

        double total = item.purchasePrice(qty);
        if (!isfinite(total) || total < 0 || total / 1000 > numeric_limits<int>::max() - poinLoyal)
            throw InvalidOperation("Nilai transaksi melampaui rentang program.");
        double diskon = 0.0;

        // pakai poin loyalitas
        if (usePoints && poinLoyal >= 100) {
            // Penukaran selalu per 100 poin, dengan batas 50% harga.
            int blok = min(poinLoyal / 100, static_cast<int>(min(total * 0.5 / 5000, double(numeric_limits<int>::max()))));
            diskon = blok * 5000.0;
            total -= diskon;
            // Poin baru dipotong setelah saldo dinyatakan cukup.
        }

        // cek saldo
        if (saldo < total) throw InsufficientBalance(total, saldo);

        // proses pembelian
        poinLoyal -= static_cast<int>(diskon / 5000) * 100;
        saldo -= total;
        if (!dynamic_cast<EBook*>(&item)) item.setStok(item.getStok() - qty);
        poinLoyal += static_cast<int>(total / 1000);

        // tambah riwayat
        RiwayatTransaksi rec{
            item.getId(), qty, total, "beli", time(nullptr),
            "Pakai poin: " + to_string(diskon)
        };
        tambahRiwayat(rec);
    }

    // fungsi pinjam buku
    void borrow(Buku& buku, int hari) {
        if (hari <= 0) throw StoreException("Minimal pinjam 1 hari!");
        if (buku.getStok() <= 0) throw OutOfStock(buku.getId());
        pinjamanAktif[buku.getId()].push_back(hari);
        buku.setStok(buku.getStok() - 1);
        RiwayatTransaksi rec{
            buku.getId(), 1, 0, "pinjam", time(nullptr),
            "Dipinjam " + to_string(hari) + " hari"
        };
        tambahRiwayat(rec);
    }

    // fungsi kembalikan buku
    void returnBook(Buku& buku, int hariPinjam, int hariKembali) {
        if (hariPinjam <= 0 || hariKembali < 0)
            throw InvalidOperation("Durasi pengembalian tidak valid.");
        auto it = pinjamanAktif.find(buku.getId());
        if (it == pinjamanAktif.end())
            throw InvalidOperation("Tidak ada pinjaman aktif untuk buku ini.");
        auto jadwal = find(it->second.begin(), it->second.end(), hariPinjam);
        if (jadwal == it->second.end())
            throw InvalidOperation("Rencana hari tidak sesuai catatan pinjaman.");
        double denda = hitungDenda(hariPinjam, hariKembali);
        if (denda > 0 && saldo < denda)
            throw InsufficientBalance(denda, saldo);
        if (denda > 0) saldo -= denda;
        it->second.erase(jadwal);
        if (it->second.empty()) pinjamanAktif.erase(it);
        buku.setStok(buku.getStok() + 1);
        RiwayatTransaksi rec{
            buku.getId(), 1, denda, "kembali", time(nullptr),
            "Telat " + to_string(max(0, hariKembali - hariPinjam)) + " hari"
        };
        tambahRiwayat(rec);
    }
};

// katalog toko
class Catalog {
private:
    vector<unique_ptr<Item>> items;

public:
    void addItem(unique_ptr<Item> item) {
        if (!item || findItemById(item->getId()))
            throw InvalidOperation("ID item sudah terdaftar atau item kosong.");
        items.push_back(move(item));
    }

    // cari item berdasarkan ID
    Item* findItemById(const string& id) {
        for (auto& item : items) {
            if (item->getId() == id) return item.get();
        }
        return nullptr;
    }

    // tampilkan semua item
    void displayAll() const {
        if (items.empty()) {
            cout << "Katalog masih kosong.\n";
            return;
        }
        cout << "\n--- KATALOG TOKO BUKU AATA ---\n";
        for (const auto& item : items) {
            cout << "[" << item->getType() << "] ID: " << item->getId()
                 << " | Judul: " << item->getJudul()
                 << " | Harga: Rp" << fixed << setprecision(0) << item->getHarga()
                 << " | Stok: " << item->getStok() << "\n";
            if (item->getType() == "Buku") {
                Buku* b = static_cast<Buku*>(item.get());
                cout << "  → Penulis: " << b->getPenulis() << ", Halaman: " << b->getHalaman() << "\n";
            } else if (item->getType() == "EBook") {
                EBook* e = static_cast<EBook*>(item.get());
                cout << "  → Ukuran: " << e->getUkuranFileMB() << " MB\n";
            } else if (item->getType() == "AudioBook") {
                AudioBook* a = static_cast<AudioBook*>(item.get());
                cout << "  → Durasi: " << a->getDurasiMenit() << " menit\n";
            }
        }
        cout << "-------------------------------\n";
    }
};

// main program
int main() {
    Catalog katalog;
    map<string, Member> members;
    Logger logger;

    // Isi awal sesuai kasus uji
    katalog.addItem(make_unique<Buku>("BK001", "Laskar Pelangi", 120000, 10, "Andrea Hirata", 529));
    katalog.addItem(make_unique<EBook>("EB001", "Atomic Habits", 80000, 5.2));
    katalog.addItem(make_unique<AudioBook>("AB001", "Think and Grow Rich", 100000, 5, 420));

    cout << "SELAMAT DATANG DI TOKO BUKU AATA\n";
    logger.log("Sistem Toko Buku AATA dimulai.");

    int pilihan = -1;
    do {
        cout << "\n=== MENU TOKO AATA ===\n";
        cout << "1. Tambah Item\n";
        cout << "2. Tampilkan Katalog\n";
        cout << "3. Registrasi Member\n";
        cout << "4. Top-up Saldo\n";
        cout << "5. Beli Item\n";
        cout << "6. Pinjam Buku\n";
        cout << "7. Kembalikan Buku\n";
        cout << "8. Lihat Riwayat Member\n";
        cout << "0. Keluar\n";
        cout << "Pilih: ";
        if (!(cin >> pilihan)) {
            if (cin.eof()) break;
            cin.clear();
            cin.ignore(numeric_limits<streamsize>::max(), '\n');
            cout << "Pilihan harus berupa angka.\n";
            continue;
        }

        // proses pilihan
        try {
            if (pilihan == 1) {
                int tipe; string id, judul; double harga;
                cout << "Tipe (1=Buku, 2=EBook, 3=AudioBook): "; readValue(tipe);
                cout << "ID: "; readValue(id);
                cout << "Judul: "; cin.ignore(); getline(cin, judul);
                cout << "Harga: "; readValue(harga);

                if (tipe == 1) {
                    string penulis; int hal, stk;
                    cout << "Penulis: "; cin >> ws; getline(cin, penulis);
                    cout << "Halaman: "; readValue(hal);
                    cout << "Stok: "; readValue(stk);
                    katalog.addItem(make_unique<Buku>(id, judul, harga, stk, penulis, hal));
                } else if (tipe == 2) {
                    double ukuran;
                    cout << "Ukuran (MB): "; readValue(ukuran);
                    katalog.addItem(make_unique<EBook>(id, judul, harga, ukuran));
                } else if (tipe == 3) {
                    int durasi, stk;
                    cout << "Durasi (menit): "; readValue(durasi);
                    cout << "Stok: "; readValue(stk);
                    katalog.addItem(make_unique<AudioBook>(id, judul, harga, stk, durasi));
                }
                else { throw InvalidOperation("Tipe item tidak dikenal."); }
                logger.log("Item ditambahkan: " + id);
                cout << "Item berhasil ditambahkan ke AATA!\n";

            } else if (pilihan == 2) {
                katalog.displayAll();

            } else if (pilihan == 3) {
                string id, nama; double saldo;
                cout << "ID Member: "; readValue(id);
                cout << "Nama: "; cin.ignore(); getline(cin, nama);
                cout << "Saldo Awal: "; readValue(saldo);
                if (members.count(id)) throw InvalidOperation("ID member sudah terdaftar.");
                members.emplace(id, Member(id, nama, saldo));
                logger.log("Member baru: " + id + " (" + nama + ")");
                cout << "Member " << nama << " berhasil terdaftar di AATA!\n";

            } else if (pilihan == 4) {
                string id; double jumlah;
                cout << "ID Member: "; readValue(id);
                cout << "Jumlah Top-up: "; readValue(jumlah);

                auto it = members.find(id);
                if (it != members.end()) {
                    it->second.topUp(jumlah);
                    logger.log("Top-up oleh " + id + ": Rp" + to_string(jumlah));
                    cout << "Saldo berhasil ditambah!\n";
                } else {
                    throw StoreException("Member tidak ditemukan di AATA!");
                }

            } else if (pilihan == 5) {
                string idMem, idItem; int qty; bool usePoints = false;
                cout << "ID Member: "; readValue(idMem);
                cout << "ID Item: "; readValue(idItem);
                cout << "Jumlah: "; readValue(qty);
                cout << "Pakai poin? (1=ya, 0=tidak): "; readValue(usePoints);

                auto it = members.find(idMem);
                if (it == members.end()) throw StoreException("Member tidak terdaftar!");
                Item* item = katalog.findItemById(idItem);
                if (!item) throw StoreException("Item tidak ditemukan di katalog AATA!");

                // proses pembelian
                it->second.purchase(*item, qty, usePoints);
                logger.log("Transaksi beli oleh " + idMem + " item " + idItem);
                cout << "Pembelian di AATA berhasil!\n";
                cout << "Saldo sisa: Rp" << it->second.getSaldo() << "\n";
                cout << "Poin loyalitas: " << it->second.getPoinLoyal() << "\n";

            } else if (pilihan == 6) {
                string idMem, idItem; int hari;
                cout << "ID Member: "; readValue(idMem);
                cout << "ID Buku: "; readValue(idItem);
                cout << "Hari Pinjam: "; readValue(hari);

                // cari member dan item
                auto it = members.find(idMem);
                if (it == members.end()) throw StoreException("Member tidak terdaftar!");
                Item* item = katalog.findItemById(idItem);
                if (!item || item->getType() != "Buku")
                    throw InvalidOperation("Hanya buku fisik yang bisa dipinjam di AATA!");
                Buku* buku = static_cast<Buku*>(item);
                it->second.borrow(*buku, hari);
                logger.log("Pinjam buku oleh " + idMem + " di AATA");
                cout << "Buku berhasil dipinjam dari AATA!\n";

            } else if (pilihan == 7) {
                string idMem, idItem; int hariPinjam, hariKembali;
                cout << "ID Member: "; readValue(idMem);
                cout << "ID Buku: "; readValue(idItem);
                cout << "Hari Pinjam (rencana): "; readValue(hariPinjam);
                cout << "Hari Kembali (aktual): "; readValue(hariKembali);

                // cari member dan item
                auto it = members.find(idMem);
                if (it == members.end()) throw StoreException("Member tidak terdaftar!");
                Item* item = katalog.findItemById(idItem);
                if (!item || item->getType() != "Buku")
                    throw InvalidOperation("Item bukan buku fisik!");
                Buku* buku = static_cast<Buku*>(item);
                it->second.returnBook(*buku, hariPinjam, hariKembali);
                logger.log("Pengembalian buku oleh " + idMem + " di AATA");
                cout << "Buku berhasil dikembalikan ke AATA!\n";

            } else if (pilihan == 8) {
                string id;
                cout << "ID Member: "; readValue(id);
                auto it = members.find(id);
                if (it == members.end()) {
                    cout << "Member tidak ditemukan di AATA.\n";
                    continue;
                }
                // tampilkan riwayat
                const auto& riw = it->second.getRiwayat();
                cout << "\n--- RIWAYAT MEMBER AATA: " << it->second.getNama() << " ---\n";
                for (const auto& r : riw) {
                    cout << "[" << put_time(localtime(&r.waktu), "%d/%m %H:%M")
                         << "] " << r.jenis << " " << r.jumlah << "x " << r.idItem
                         << " → Rp" << r.totalBayar << " (" << r.catatan << ")\n";
                }

            } else if (pilihan != 0) {
                cout << "Pilihan tidak valid.\n";
            }

        // penanganan exception
        } catch (const InputClosed&) {
            break;
        } catch (const StoreException& e) {
            cerr << "ERROR AATA: " << e.what() << "\n";
            logger.log("Exception: " + string(e.what()));
        } catch (const exception& e) {
            cerr << "SYSTEM ERROR: " << e.what() << "\n";
            logger.log("System error: " + string(e.what()));
        }
    } while (pilihan != 0);

    logger.log("Sistem Toko Buku AATA ditutup.");
    cout << "Terima kasih telah berbelanja di AATA!\n";
    return 0;
}
