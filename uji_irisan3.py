# uji_irisan3.py — Bukti Irisan 3: refs, tag, resolusi nama.
# Repo uji oleh git asli: 3 commit, branch fitur, tag ringan & beranotasi.
# 1. wyag show-ref == git show-ref (himpunan baris).
# 2. wyag rev-parse untuk HEAD/nama branch/hash pendek/tag == git asli,
#    termasuk --wyag-type commit/tree mengikuti objek tag.
# 3. wyag log & ls-tree kini menerima NAMA (HEAD, branch) bukan hanya SHA.
# 4. Tag buatan wyag (ringan & objek) dibaca balik benar oleh git asli.

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


def rp_git(repo, *args):
    return jalan(['git', '-C', repo, 'rev-parse'] + list(args)).stdout.decode().strip()


def rp_wyag(repo, *args):
    return jalan([WYAG, 'rev-parse'] + list(args), cwd=repo).stdout.decode().strip()


tmp = tempfile.mkdtemp(prefix='wyag-uji3-')
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
    return rp_git(repo, 'HEAD')


tulis('a.txt', 'versi 1\n')
c1 = commit('commit pertama')
tulis('a.txt', 'versi 2\n')
c2 = commit('commit kedua')
jalan(['git', '-C', repo, 'branch', 'fitur'], env=ENV)
tulis('b.txt', 'berkas b\n')
c3 = commit('commit ketiga')
jalan(['git', '-C', repo, 'tag', 'v-ringan', c1], env=ENV)
jalan(['git', '-C', repo, 'tag', '-a', 'v-beranotasi', '-m', 'tag resmi', c3], env=ENV)
cek('repo uji terbangun (3 commit, branch, 2 tag)', len(c3) == 40)

# 1. show-ref
w = jalan([WYAG, 'show-ref'], cwd=repo).stdout.decode().strip().splitlines()
g = jalan(['git', '-C', repo, 'show-ref']).stdout.decode().strip().splitlines()
cek('show-ref wyag == git (himpunan)', sorted(w) == sorted(g),
    '' if sorted(w) == sorted(g) else '\nwyag: %s\ngit: %s' % (w, g))

# 2. rev-parse berbagai nama
cek('rev-parse HEAD', rp_wyag(repo, 'HEAD') == rp_git(repo, 'HEAD') == c3)
cek('rev-parse branch master', rp_wyag(repo, 'master') == c3)
cek('rev-parse branch fitur', rp_wyag(repo, 'fitur') == rp_git(repo, 'fitur') == c2)
cek('rev-parse hash pendek', rp_wyag(repo, c2[:7]) == c2)
cek('rev-parse tag ringan', rp_wyag(repo, 'v-ringan') == rp_git(repo, 'v-ringan') == c1)
cek('rev-parse tag beranotasi = objek tag',
    rp_wyag(repo, 'v-beranotasi') == rp_git(repo, 'v-beranotasi') != c3)
cek('rev-parse --wyag-type commit mengikuti tag',
    rp_wyag(repo, '--wyag-type', 'commit', 'v-beranotasi') == c3)
cek('rev-parse --wyag-type tree HEAD',
    rp_wyag(repo, '--wyag-type', 'tree', 'HEAD') == rp_git(repo, 'HEAD^{tree}'))
cek('rev-parse --wyag-type tag HEAD = None',
    rp_wyag(repo, '--wyag-type', 'tag', 'HEAD') == 'None')

# 3. nama kini bisa dipakai di log & ls-tree
out = jalan([WYAG, 'log'], cwd=repo).stdout.decode()
cek('wyag log polos (HEAD) 3 node', out.count('[label=') == 3)
w = jalan([WYAG, 'ls-tree', 'HEAD'], cwd=repo).stdout.decode()
g = jalan(['git', '-C', repo, 'ls-tree', 'HEAD']).stdout.decode()
cek('wyag ls-tree HEAD == git', w == g)
w = jalan([WYAG, 'ls-tree', 'fitur'], cwd=repo).stdout.decode()
g = jalan(['git', '-C', repo, 'ls-tree', 'fitur']).stdout.decode()
cek('wyag ls-tree fitur == git', w == g)

# daftar tag
w = jalan([WYAG, 'tag'], cwd=repo).stdout.decode().strip().splitlines()
cek('wyag tag (daftar) == git tag', sorted(w) == sorted(['v-beranotasi', 'v-ringan']))

# 4. tag buatan wyag dibaca git asli
r = jalan([WYAG, 'tag', 'wyag-ringan', 'fitur'], cwd=repo)
cek('wyag tag ringan dibuat', r.returncode == 0, r.stderr.decode()[:100])
cek('git membaca tag ringan wyag', rp_git(repo, 'wyag-ringan') == c2)
r = jalan([WYAG, 'tag', '-a', 'wyag-beranotasi', c1], cwd=repo)
cek('wyag tag -a dibuat', r.returncode == 0, r.stderr.decode()[:100])
t = jalan(['git', '-C', repo, 'cat-file', '-t', 'wyag-beranotasi']).stdout.decode().strip()
cek('git: objek wyag-beranotasi bertipe tag', t == 'tag')
cek('git: tag wyag menunjuk c1', rp_git(repo, 'wyag-beranotasi^{commit}') == c1)

print()
if gagal:
    print('GAGAL:', ', '.join(gagal))
    sys.exit(1)
print('SEMUA PASS — Irisan 3 terbukti.')
print('Folder uji:', tmp)
