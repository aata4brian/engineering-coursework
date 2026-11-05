#define main bookstore_cli_main
#include "main.cpp"
#undef main
#include <cassert>

int main() {
    Buku book("B", "Demo", 100000, 10, "Demo", 100);
    Member member("D", "Demo", 250000);
    member.purchase(book, 1);
    assert(member.getSaldo() == 150000 && book.getStok() == 9);
    assert(member.getPoinLoyal() == 100);
    try { member.purchase(book, 2, true); assert(false); }
    catch (const InsufficientBalance&) {}
    assert(member.getSaldo() == 150000 && member.getPoinLoyal() == 100);
    assert(book.getStok() == 9);
    member.purchase(book, 1, true);
    assert(member.getSaldo() == 55000 && member.getPoinLoyal() == 95);
    assert(book.getStok() == 8);
    Catalog catalog;
    catalog.addItem(make_unique<Buku>("B", "Demo", 100000, 1, "Demo", 100));
    try {
        catalog.addItem(make_unique<Buku>("B", "Duplicate", 100000, 1, "Demo", 100));
        assert(false);
    } catch (const InvalidOperation&) {}
    assert(catalog.findItemById("B")->getJudul() == "Demo");
    Member borrower("P", "Peminjam", 10000);
    borrower.borrow(book, 3);
    int stockBorrowed = book.getStok();
    try { borrower.returnBook(book, 2, 4); assert(false); }
    catch (const InvalidOperation&) {}
    assert(book.getStok() == stockBorrowed);
    borrower.returnBook(book, 3, 5);
    assert(borrower.getSaldo() == 6000 && book.getStok() == stockBorrowed + 1);
    try { borrower.returnBook(book, 3, 5); assert(false); }
    catch (const InvalidOperation&) {}
    assert(book.getStok() == stockBorrowed + 1);
    try { member.topUp(-1); assert(false); }
    catch (const InvalidOperation&) {}
    // Barang murah tidak boleh memperoleh diskon pecahan blok tanpa membayar poin.
    Member saver("S", "Demo", 1000000);
    saver.purchase(book, 2);
    EBook cheap("E", "Murah", 3000, 1);
    int pointsBefore = saver.getPoinLoyal();
    double balanceBefore = saver.getSaldo();
    saver.purchase(cheap, 1, true);
    assert(saver.getSaldo() == balanceBefore - 3000);
    assert(saver.getPoinLoyal() == pointsBefore + 3);
}
