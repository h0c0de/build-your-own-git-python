# uji_irisan5.py — Bukti final Irisan 5: repo LAHIR & berkomit oleh wyag.
# Seluruh siklus hidup repo ini digerakkan wyag (init/add/commit/rm);
# git asli hanya menjadi JURI: fsck, log, status, ls-files, write-tree.
# 1. Index tulisan wyag diterima git (ls-files terurut, status bersih).
# 2. Tree buatan wyag dari index == tree `git write-tree` atas index sama.
# 3. Tiga commit wyag membentuk rantai parent yang dibaca benar oleh git.

import os
import subprocess
import sys
import tempfile

WYAG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wyag')
gagal = []


def jalan(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, env=env)


def cek(nama, kondisi, detail=''):
    print(('PASS' if kondisi else 'FAIL'), nama, detail)
    if not kondisi:
        gagal.append(nama)


tmp = tempfile.mkdtemp(prefix='wyag-uji5-')
home = os.path.join(tmp, 'home')
os.makedirs(home)
with open(os.path.join(home, '.gitconfig'), 'w') as f:
    f.write('[user]\n\tname = Uji Wyag\n\temail = uji@wyag.local\n')
ENV = dict(os.environ, HOME=home)

repo = os.path.join(tmp, 'repo')
r = jalan([WYAG, 'init', repo], env=ENV)
cek('wyag init', r.returncode == 0, r.stderr.decode()[:100])


def tulis(rel, isi):
    p = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w') as f:
        f.write(isi)


def wyag(*args):
    return jalan([WYAG] + list(args), cwd=repo, env=ENV)


def git(*args):
    return jalan(['git', '-C', repo] + list(args), env=ENV)


# --- commit 1: add sengaja tidak menurut abjad (z dulu) ---
tulis('a.txt', 'a versi 1\n')
tulis('z.txt', 'z\n')
tulis('sub/b.txt', 'b\n')
tulis('sub/dalam/c.txt', 'c\n')
r = wyag('add', 'z.txt', 'a.txt', 'sub/b.txt', 'sub/dalam/c.txt')
cek('wyag add 4 berkas', r.returncode == 0, r.stderr.decode()[:120])
g = git('ls-files').stdout.decode().strip().splitlines()
cek('git membaca index wyag, terurut',
    g == ['a.txt', 'sub/b.txt', 'sub/dalam/c.txt', 'z.txt'], str(g))
tree_git = git('write-tree').stdout.decode().strip()
r = wyag('commit', '-m', 'commit pertama wyag')
cek('wyag commit 1', r.returncode == 0, r.stderr.decode()[:120])
tree_wyag = git('rev-parse', 'HEAD^{tree}').stdout.decode().strip()
cek('tree commit wyag == git write-tree', tree_wyag == tree_git,
    'wyag=%s git=%s' % (tree_wyag[:12], tree_git[:12]))
cek('git status bersih sesudah commit wyag',
    git('status', '--porcelain').stdout.decode() == '')
cek('git log: pesan commit 1',
    git('log', '-1', '--format=%s').stdout.decode().strip() == 'commit pertama wyag')
cek('git log: author dari gitconfig',
    'Uji Wyag <uji@wyag.local>' in git('log', '-1', '--format=%an <%ae>').stdout.decode())

# --- commit 2: ubah satu berkas ---
tulis('a.txt', 'a versi 2\n')
wyag('add', 'a.txt')
r = wyag('commit', '-m', 'commit kedua wyag')
cek('wyag commit 2', r.returncode == 0, r.stderr.decode()[:120])
cek('git: HEAD:a.txt versi 2',
    git('show', 'HEAD:a.txt').stdout.decode() == 'a versi 2\n')
cek('git: HEAD~1:a.txt versi 1',
    git('show', 'HEAD~1:a.txt').stdout.decode() == 'a versi 1\n')

# --- commit 3: rm ---
r = wyag('rm', 'sub/b.txt')
cek('wyag rm sub/b.txt', r.returncode == 0, r.stderr.decode()[:120])
cek('berkas sub/b.txt hilang dari worktree',
    not os.path.exists(os.path.join(repo, 'sub', 'b.txt')))
porc = git('status', '--porcelain').stdout.decode()
cek('git status: b.txt terhapus staged', porc.strip() == 'D  sub/b.txt', porc.strip())
r = wyag('commit', '-m', 'commit ketiga wyag')
cek('wyag commit 3', r.returncode == 0, r.stderr.decode()[:120])

# --- vonis juri git ---
cek('git rev-list --count HEAD = 3',
    git('rev-list', '--count', 'HEAD').stdout.decode().strip() == '3')
pesan = git('log', '--format=%s').stdout.decode().strip().splitlines()
cek('git log 3 pesan urut',
    pesan == ['commit ketiga wyag', 'commit kedua wyag', 'commit pertama wyag'], str(pesan))
r = git('fsck', '--strict')
cek('git fsck --strict bersih', r.returncode == 0 and r.stdout == b'' and r.stderr == b'',
    (r.stdout + r.stderr).decode()[:200])
cek('git status akhir bersih', git('status', '--porcelain').stdout.decode() == '')
cek('git ls-tree HEAD tanpa b.txt',
    'b.txt' not in git('ls-tree', '-r', 'HEAD').stdout.decode())
out = wyag('log').stdout.decode()
cek('wyag log membaca sejarahnya sendiri (3 node)', out.count('[label=') == 3)
cek('wyag status bersih', 'modified' not in wyag('status').stdout.decode())

print()
if gagal:
    print('GAGAL:', ', '.join(gagal))
    sys.exit(1)
print('SEMUA PASS — Irisan 5 terbukti: repo wyag sah di mata git asli.')
print('Folder uji:', tmp)
