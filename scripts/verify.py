"""Checks that do not require lab hardware or the downloaded AI4I dataset."""
import csv
import io
import json
import math
import py_compile
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / 'projects').rglob('*.py'):
    py_compile.compile(str(p), doraise=True)
print('PASS: Python syntax')
for name in ['receiver', 'transmitter']:
    assert (ROOT / 'projects/serial-irrigation' / name / 'control.h').read_bytes() == (ROOT / 'projects/serial-irrigation/control.h').read_bytes()

machine = ROOT / 'projects/machine-failure/reference-results'
reference = json.loads((machine / 'hasil_eksperimen.json').read_text())
rows = list(csv.DictReader((machine / 'prediksi_test.csv').open()))
counts = {(a, p): sum(int(r['aktual']) == a and int(r['prediksi']) == p for r in rows)
          for a in [0, 1] for p in [0, 1]}
assert len(rows) == 2000
assert counts == {(0, 0): 1925, (0, 1): 7, (1, 0): 38, (1, 1): 30}
tp, fp, fn = counts[1, 1], counts[0, 1], counts[1, 0]
assert math.isclose(2 * tp / (2 * tp + fp + fn), reference['test']['f1'])
assert math.isclose(tp / (tp + fn), reference['test']['recall'])
print('PASS: archived machine-failure predictions agree with reported metrics')

ensemble = ROOT / 'projects/ensemble-learning/reference-results'
for row in csv.DictReader((ensemble / 'soal3_evaluasi_pilihan_cv.csv').open()):
    tp, fp, fn, tn = (int(row[k]) for k in ['TP', 'FP', 'FN', 'TN'])
    assert tp + fp + fn + tn == 114
    assert math.isclose(2 * tp / (2 * tp + fp + fn), float(row['F1']))
print('PASS: archived ensemble counts agree with reported F1')

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    for project, source in [('bookstore', 'test_bookstore.cpp'),
                            ('serial-irrigation', 'test_control.cpp')]:
        exe = tmp / project
        subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra',
                        str(ROOT / 'projects' / project / source), '-o', str(exe)], check=True)
        subprocess.run([str(exe)], check=True, cwd=tmp)
    exe = tmp / 'bookstore-cli'
    subprocess.run(['g++', '-std=c++17', str(ROOT / 'projects/bookstore/main.cpp'), '-o', str(exe)], check=True)
    fixtures = [
        ((ROOT / 'projects/bookstore/sample-input.txt').read_text(), ['Saldo sisa: Rp260000', 'Poin loyalitas: 240']),
        ('3\nD\nDemo\n5000000\n5\nD\nBK001\n11\n0\n0\n', ['Stok item']),
        ('3\nD\nDemo\n0\n5\nD\nBK001\n1\n0\n0\n', ['saldo cuma']),
        ('hello\n0\n', ['Pilihan harus berupa angka.']),
        ('', ['Terima kasih']),
        ('3\nD\nDemo\nabc\n0\n', ['Input tidak sesuai']),
        ('3\nD\nDemo\n', ['Terima kasih']),
        ('3\nD\nDemo\n500000\n3\nD\nLain\n1\n0\n', ['ID member sudah terdaftar']),
        ('1\n9\nX\nDemo\n100\n0\n', ['Tipe item tidak dikenal'])]
    for text, checks in fixtures:
        result = subprocess.run([str(exe)], input=text, text=True, capture_output=True, cwd=tmp, timeout=5, check=True)
        assert all(c in result.stdout + result.stderr for c in checks)
print('PASS: C++ transactions, failure rollback, duplicate IDs, active loans, double returns, loyalty boundaries, nine CLI flows, valve timeout and rollover')

result = subprocess.run(['python', str(ROOT / 'projects/clustering/experiment.py')],
                        capture_output=True, text=True, check=True)
assert result.stdout.count('Silhouette Score = 0.675267') == 2
assert 'Partisi kedua metode identik: True' in result.stdout
print('PASS: clustering executes and manual silhouette matches the library')

