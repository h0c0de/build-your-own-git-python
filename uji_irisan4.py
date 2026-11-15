# uji_irisan4.py — Bukti Irisan 4: index, ls-files, check-ignore, status.
# Repo git asli dengan keadaan campur: staged baru/ubah/hapus, unstaged
# ubah/hapus, untracked, dan ignored (termasuk negasi & .gitignore subdir).
# Vonis wyag dibandingkan dengan `git status --porcelain` git asli.

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


tmp = tempfile.mkdtemp(prefix='wyag-uji4-')
repo = os.path.join(tmp, 'repo')
jalan(['git', 'init', '-q', repo])


def tulis(rel, isi):
    p = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w') as f:
        f.write(isi)


# --- keadaan awal: satu commit bersih ---
tulis('.gitignore', '*.log\n!penting.log\n')
tulis('sub/.gitignore', '*.tmp\n')
tulis('a.txt', 'a versi 1\n')
tulis('stagedmod.txt', 'sm versi 1\n')
tulis('dihapus-staged.txt', 'akan dihapus staged\n')
tulis('dihapus-worktree.txt', 'akan dihapus worktree\n')
tulis('sub/jaga.txt', 'tetap\n')
jalan(['git', '-C', repo, 'add', '-A'], env=ENV)
jalan(['git', '-C', repo, 'commit', '-q', '-m', 'awal'], env=ENV)

# --- buat keadaan campur ---
tulis('a.txt', 'a versi 2\n')                      # unstaged modified
tulis('stagedmod.txt', 'sm versi 2\n')
jalan(['git', '-C', repo, 'add', 'stagedmod.txt'], env=ENV)   # staged modified
tulis('staged.txt', 'baru dan ter-stage\n')
jalan(['git', '-C', repo, 'add', 'staged.txt'], env=ENV)      # staged added
jalan(['git', '-C', repo, 'rm', '-q', 'dihapus-staged.txt'], env=ENV)  # staged deleted
os.remove(os.path.join(repo, 'dihapus-worktree.txt'))          # unstaged deleted
tulis('baru.txt', 'belum terlacak\n')                          # untracked
tulis('sampah.log', 'diabaikan\n')                             # ignored (*.log)
tulis('penting.log', 'negasi: tidak diabaikan\n')              # untracked (!penting.log)
tulis('sub/x.tmp', 'diabaikan oleh sub/.gitignore\n')          # ignored scoped
tulis('x.tmp', 'tidak diabaikan di root\n')                    # untracked

# --- 1. ls-files ---
w = jalan([WYAG, 'ls-files'], cwd=repo).stdout.decode()
g = jalan(['git', '-C', repo, 'ls-files']).stdout.decode()
cek('ls-files wyag == git', w == g, '' if w == g else '\nwyag:\n%s\ngit:\n%s' % (w, g))
baris1 = jalan([WYAG, 'ls-files', '--verbose'], cwd=repo).stdout.decode().splitlines()[0]
cek('ls-files --verbose kepala benar',
    baris1 == 'Index file format v2, containing %d entries.' % len(g.strip().splitlines()),
    baris1)

# --- 2. check-ignore ---
calon = ['sampah.log', 'penting.log', 'sub/x.tmp', 'x.tmp', 'a.txt']
w = jalan([WYAG, 'check-ignore'] + calon, cwd=repo).stdout.decode().split()
g = jalan(['git', '-C', repo, 'check-ignore'] + calon).stdout.decode().split()
cek('check-ignore wyag == git', sorted(w) == sorted(g) == ['sampah.log', 'sub/x.tmp'],
    'wyag=%s git=%s' % (w, g))

# --- 3. status: urai keluaran wyag menjadi tiga himpunan ---
out = jalan([WYAG, 'status'], cwd=repo).stdout.decode()
cek('status: baris branch', out.startswith('On branch master.'), out.splitlines()[0])


def urai(teks, kepala):
    hasil = {'added': set(), 'modified': set(), 'deleted': set(), 'plain': set()}
    aktif = False
    for baris in teks.splitlines():
        if baris.strip() == kepala:
            aktif = True
            continue
        if aktif:
            b = baris.strip()
            if not b:
                if kepala != 'Untracked files:':
                    aktif = False
                continue
            if b.startswith('added:'):
                hasil['added'].add(b.split(None, 1)[1].strip())
            elif b.startswith('modified:'):
                hasil['modified'].add(b.split(None, 1)[1].strip())
            elif b.startswith('deleted:'):
                hasil['deleted'].add(b.split(None, 1)[1].strip())
            elif kepala == 'Untracked files:':
                hasil['plain'].add(b)
            else:
                aktif = False
    return hasil


staged = urai(out, 'Changes to be committed:')
unstaged = urai(out, 'Changes not staged for commit:')
untracked = urai(out, 'Untracked files:')['plain']

# --- bandingkan dengan git status --porcelain ---
porc = jalan(['git', '-C', repo, 'status', '--porcelain']).stdout.decode().splitlines()
g_staged = {'added': set(), 'modified': set(), 'deleted': set()}
g_unstaged = {'modified': set(), 'deleted': set()}
g_untracked = set()
for baris in porc:
    x, y, nama = baris[0], baris[1], baris[3:]
    if x == 'A':
        g_staged['added'].add(nama)
    elif x == 'M':
        g_staged['modified'].add(nama)
    elif x == 'D':
        g_staged['deleted'].add(nama)
    if y == 'M':
        g_unstaged['modified'].add(nama)
    elif y == 'D':
        g_unstaged['deleted'].add(nama)
    if x == '?' and y == '?':
        g_untracked.add(nama)

cek('status staged == git', all(staged[k] == g_staged[k] for k in g_staged),
    'wyag=%s git=%s' % (staged, g_staged))
cek('status unstaged == git',
    unstaged['modified'] == g_unstaged['modified'] and unstaged['deleted'] == g_unstaged['deleted'],
    'wyag=%s git=%s' % (unstaged, g_unstaged))
cek('status untracked == git', untracked == g_untracked,
    'wyag=%s git=%s' % (sorted(untracked), sorted(g_untracked)))
cek('ignored tak muncul di untracked',
    'sampah.log' not in untracked and 'sub/x.tmp' not in untracked)

print()
if gagal:
    print('GAGAL:', ', '.join(gagal))
    sys.exit(1)
print('SEMUA PASS — Irisan 4 terbukti.')
print('Folder uji:', tmp)
