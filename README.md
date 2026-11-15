# Build-Your-Own Git — Python (wyag)

Build ketiga dari seri *build-your-own-x*: mengimplementasikan **Git dari nol**
dengan Python murni pustaka standar, mengikuti panduan Thibault Polge,
*Write yourself a Git!* — https://wyag.thb.lt/ (disebut dari
https://github.com/codecrafters-io/build-your-own-x).

Hasilnya adalah `wyag`: implementasi Git yang **saling kompatibel dengan
git asli** — repo yang lahir dan berkomit penuh oleh wyag lolos
`git fsck --strict`, dan tree yang dibangun wyag dari index ber-hash
identik dengan `git write-tree`.

## Cara menjalankan

```sh
./wyag init repo-baru
cd repo-baru
./../wyag add berkas.txt
./../wyag commit -m "pesan"
./../wyag log
./../wyag status
```

15 perintah: `init`, `hash-object`, `cat-file`, `log`, `ls-tree`,
`checkout`, `show-ref`, `tag`, `rev-parse`, `ls-files`, `check-ignore`,
`status`, `add`, `rm`, `commit`. Tanpa dependensi di luar pustaka standar
Python ≥ 3.10.

## Status verifikasi (15 Nov 2026)

Lima irisan, masing-masing terbukti oleh skrip uji melawan git asli 2.43.0:

| Irisan | Bukti |
|---|---|
| 1 — init + objek blob | `uji_irisan1.py` — 21/21: hash identik dua arah, repo wyag dikenali git |
| 2 — log & ls-tree | `uji_irisan2.py` — 14/14: round-trip commit/tree identik byte, checkout setia |
| 3 — refs & tag | `uji_irisan3.py` — 20/20: rev-parse/show-ref/tag sama dengan git |
| 4 — index & status | `uji_irisan4.py` — 8/8: status wyag == `git status --porcelain` |
| 5 — commit | `uji_irisan5.py` — 22/22: repo wyag-only, `git fsck --strict` bersih |

Jalankan semuanya: `python3 uji_irisan1.py` … `python3 uji_irisan5.py`.

## Penyimpangan sadar dari panduan

Didokumentasikan per irisan di `CATATAN.md`. Tiga yang terpenting, semuanya
tertangkap uji byte/hash, bukan selera:

1. Mode direktori disimpan mentah (`40000`, 5 byte) — normalisasi panduan
   (`040000`) merusak identitas hash tree (Irisan 2, berlaku juga di
   `tree_from_index` Irisan 5).
2. `index_write` mengurutkan entri dan menambahkan hash SHA-1 penutup
   berkas index — tanpa keduanya index tulisan tangan ditolak/dibaca
   salah oleh git asli (Irisan 5).
3. Cabang HEAD-lepas (detached) di `cmd_commit` panduan menulis hanya
   `"\n"`; diperbaiki menulis hash commit (Irisan 5).

Batas yang diwarisi dari panduan: hanya objek lepas (tanpa packfile),
aturan `.gitignore` berupa pendekatan fnmatch (pola direktori murni seperti
`build/` tanpa `/**` tidak bekerja), symlink belum didukung di checkout,
dan identitas tagger tag beranotasi masih bawaan panduan.

Rencana dan pagar penyelesaian: `RENCANA.md`. Catatan belajar per irisan:
`CATATAN.md`.

*Kode ditulis sebagai latihan belajar mengikuti struktur panduan;
panduan berlisensi CC BY-NC-SA 4.0 dan program aslinya GPL-3.0.*
