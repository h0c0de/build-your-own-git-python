# uji_irisan1.py — Bukti Irisan 1: interop dua arah wyag <-> git asli.
# 1. wyag init menghasilkan repo yang dikenali git asli.
# 2. Hash wyag == hash git untuk berkas yang sama (teks & biner).
# 3. Objek tulisan wyag (-w) dibaca balik oleh git cat-file.
# 4. Objek tulisan git (-w) dibaca balik oleh wyag cat-file.
# 5. repo_find bekerja dari subdirektori dalam.

import os
import subprocess
import sys
import tempfile

WYAG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wyag')
gagal = []


def jalan(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True)


def cek(nama, kondisi, detail=''):
    print(('PASS' if kondisi else 'FAIL'), nama, detail)
    if not kondisi:
        gagal.append(nama)


tmp = tempfile.mkdtemp(prefix='wyag-uji1-')
repo = os.path.join(tmp, 'repoA')

r = jalan([WYAG, 'init', repo])
cek('wyag init jalan', r.returncode == 0, r.stderr.decode()[:100])
for bagian in ['objects', 'refs/heads', 'refs/tags', 'HEAD', 'config', 'description']:
    cek('struktur .git/%s' % bagian, os.path.exists(os.path.join(repo, '.git', bagian)))
cek('HEAD menunjuk master',
    open(os.path.join(repo, '.git', 'HEAD')).read() == 'ref: refs/heads/master\n')

r = jalan(['git', '-C', repo, 'status', '--porcelain'])
cek('git asli mengenali repo wyag (status)', r.returncode == 0, r.stderr.decode()[:100])
r = jalan(['git', '-C', repo, 'rev-parse', '--git-dir'])
cek('git rev-parse .git', r.returncode == 0 and r.stdout.decode().strip() == '.git')

isi_teks = b'Halo dari wyag!\nBaris kedua.\n'
isi_biner = bytes(range(256)) * 4
f1 = os.path.join(tmp, 'teks.txt')
f2 = os.path.join(tmp, 'biner.bin')
open(f1, 'wb').write(isi_teks)
open(f2, 'wb').write(isi_biner)

for f, isi, label in [(f1, isi_teks, 'teks'), (f2, isi_biner, 'biner')]:
    sha_wyag = jalan([WYAG, 'hash-object', f]).stdout.decode().strip()
    sha_git = jalan(['git', 'hash-object', f]).stdout.decode().strip()
    cek('hash %s identik wyag==git' % label, sha_wyag == sha_git, sha_wyag[:12])

    sha_w = jalan([WYAG, 'hash-object', '-w', f], cwd=repo).stdout.decode().strip()
    cek('hash -w %s sama' % label, sha_w == sha_git)
    r = jalan(['git', '-C', repo, 'cat-file', '-p', sha_w])
    cek('git cat-file membaca objek tulisan wyag (%s)' % label, r.stdout == isi)
    r = jalan(['git', '-C', repo, 'cat-file', '-t', sha_w])
    cek('git cat-file -t = blob (%s)' % label, r.stdout.decode().strip() == 'blob')

    sha_g = jalan(['git', '-C', repo, 'hash-object', '-w', f]).stdout.decode().strip()
    r = jalan([WYAG, 'cat-file', 'blob', sha_g], cwd=repo)
    cek('wyag cat-file membaca objek tulisan git (%s)' % label, r.stdout == isi)

dalam = os.path.join(repo, 'sub', 'direktori')
os.makedirs(dalam)
sha_g = jalan(['git', '-C', repo, 'hash-object', '-w', f1]).stdout.decode().strip()
r = jalan([WYAG, 'cat-file', 'blob', sha_g], cwd=dalam)
cek('repo_find dari subdirektori', r.returncode == 0 and r.stdout == isi_teks)

print()
if gagal:
    print('GAGAL:', ', '.join(gagal))
    sys.exit(1)
print('SEMUA PASS — Irisan 1 terbukti interop dua arah.')
print('Folder uji:', tmp)
