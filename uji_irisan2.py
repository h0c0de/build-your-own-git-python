# uji_irisan2.py — Bukti Irisan 2: wyag membaca sejarah repo git ASLI.
# Repo uji dibuat seluruhnya oleh git asli (3 commit, subdirektori 2 tingkat).
# 1. Round-trip commit & tree lewat wyag cat-file == byte git cat-file.
# 2. wyag log (graphviz) memuat 3 node + 2 panah parent yang benar.
# 3. wyag ls-tree (datar & -r) == git ls-tree baris per baris.
# 4. wyag checkout commit pertama & HEAD: isi berkas == keadaan git asli.

import os
import subprocess
import sys
import tempfile

WYAG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wyag')
gagal = []
ENV = dict(os.environ,
           GIT_AUTHOR_NAME='Uji Wyag', GIT_AUTHOR_EMAIL='uji@wyag.local',
           GIT_COMMITTER_NAME='Uji Wyag', GIT_COMMITTER_EMAIL='uji@wyag.local',
           GIT_AUTHOR_DATE='2026-11-15T12:00:00+08:00',
           GIT_COMMITTER_DATE='2026-11-15T12:00:00+08:00')


def jalan(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, env=env)


def cek(nama, kondisi, detail=''):
    print(('PASS' if kondisi else 'FAIL'), nama, detail)
    if not kondisi:
        gagal.append(nama)


tmp = tempfile.mkdtemp(prefix='wyag-uji2-')
repo = os.path.join(tmp, 'repo')
jalan(['git', 'init', '-q', repo])

def tulis(rel, isi):
    p = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w') as f:
        f.write(isi)

def commit(pesan):
    jalan(['git', '-C', repo, 'add', '-A'], env=ENV)
    jalan(['git', '-C', repo, 'commit', '-q', '-m', pesan], env=ENV)
    return jalan(['git', '-C', repo, 'rev-parse', 'HEAD']).stdout.decode().strip()

tulis('a.txt', 'versi 1\n')
tulis('sub/b.txt', 'berkas b\n')
tulis('sub/dalam/c.txt', 'berkas c\n')
c1 = commit('commit pertama')
tulis('a.txt', 'versi 2\n')
c2 = commit('commit kedua')
tulis('d.txt', 'berkas d\n')
c3 = commit('commit ketiga')
cek('repo git asli: 3 commit terbangun', all(len(c) == 40 for c in (c1, c2, c3)))

# 1. round-trip objek lewat parser wyag
r_w = jalan([WYAG, 'cat-file', 'commit', c3], cwd=repo)
r_g = jalan(['git', '-C', repo, 'cat-file', 'commit', c3])
cek('cat-file commit wyag == git (byte)', r_w.stdout == r_g.stdout)
tree3 = jalan(['git', '-C', repo, 'rev-parse', 'HEAD^{tree}']).stdout.decode().strip()
r_w = jalan([WYAG, 'cat-file', 'tree', tree3], cwd=repo)
r_g = jalan(['git', '-C', repo, 'cat-file', 'tree', tree3])
cek('cat-file tree wyag == git (byte biner)', r_w.stdout == r_g.stdout)

# 2. log graphviz
out = jalan([WYAG, 'log', c3], cwd=repo).stdout.decode()
for c, pesan in [(c1, 'commit pertama'), (c2, 'commit kedua'), (c3, 'commit ketiga')]:
    cek('log memuat node %s' % pesan, ('c_%s [label="%s: %s"]' % (c, c[:7], pesan)) in out)
cek('log panah c3->c2', ('c_%s -> c_%s;' % (c3, c2)) in out)
cek('log panah c2->c1', ('c_%s -> c_%s;' % (c2, c1)) in out)

# 3. ls-tree datar & rekursif
for ekstra, label in [([], 'datar'), (['-r'], 'rekursif')]:
    w = jalan([WYAG, 'ls-tree'] + ekstra + [tree3], cwd=repo).stdout.decode()
    g = jalan(['git', '-C', repo, 'ls-tree'] + ekstra + [tree3]).stdout.decode()
    cek('ls-tree %s wyag == git' % label, w == g,
        '' if w == g else '\nwyag:\n%s\ngit:\n%s' % (w, g))

# 4. checkout dua titik sejarah
def isi_pohon(akar):
    hasil = {}
    for dp, dn, fn in os.walk(akar):
        for f in fn:
            p = os.path.join(dp, f)
            hasil[os.path.relpath(p, akar)] = open(p, 'rb').read()
    return hasil

keluar1 = os.path.join(tmp, 'keluar-c1')
r = jalan([WYAG, 'checkout', c1, keluar1], cwd=repo)
cek('wyag checkout c1 jalan', r.returncode == 0, r.stderr.decode()[:120])
cek('isi checkout c1 benar', isi_pohon(keluar1) == {
    'a.txt': b'versi 1\n',
    os.path.join('sub', 'b.txt'): b'berkas b\n',
    os.path.join('sub', 'dalam', 'c.txt'): b'berkas c\n',
})
keluar3 = os.path.join(tmp, 'keluar-c3')
r = jalan([WYAG, 'checkout', c3, keluar3], cwd=repo)
cek('wyag checkout c3 jalan', r.returncode == 0, r.stderr.decode()[:120])
cek('isi checkout c3 benar', isi_pohon(keluar3) == {
    'a.txt': b'versi 2\n',
    'd.txt': b'berkas d\n',
    os.path.join('sub', 'b.txt'): b'berkas b\n',
    os.path.join('sub', 'dalam', 'c.txt'): b'berkas c\n',
})

print()
if gagal:
    print('GAGAL:', ', '.join(gagal))
    sys.exit(1)
print('SEMUA PASS — Irisan 2 terbukti.')
print('Folder uji:', tmp)
