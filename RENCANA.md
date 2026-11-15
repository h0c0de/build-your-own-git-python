# Build Ketiga BYOX — Git dengan Python (wyag)

Dipilih Vero 15 Nov 2026 sebagai build ketiga (sesudah Web Server & Mini Redis),
atas rekomendasi Muse: alat yang dipakai Vero tiap hari, panduan Python murni,
dan uji interopnya paling tegas — Git buatan sendiri harus dibaca Git asli.
Sumber induk: fork https://github.com/h0c0de/build-your-own-x → *Build your own Git*.

## Panduan yang diikuti

Thibault Polge — *Write yourself a Git!* (wyag.thb.lt, terverifikasi 15 Nov 2026):
https://wyag.thb.lt/

Satu panduan utuh ±983 baris Python murni pustaka standar, dua berkas
(`wyag` executable + `libwyag.py`), 15 perintah: init, hash-object, cat-file,
log, ls-tree, checkout, show-ref, tag, rev-parse, ls-files, check-ignore,
status, add, rm, commit. Tanpa packfile (objek lepas saja) — batas panduan
yang dinyatakan sendiri oleh penulisnya.

## Irisan

1. **init + model objek** (panduan §2–§4): repo, hash-object, cat-file (blob).
   Bukti: interop dua arah dengan git asli — objek tulisan wyag dibaca
   `git cat-file`, objek tulisan git dibaca wyag, hash identik.
2. **Baca sejarah** (§5–§6): commit (parser KVLM), log, tree, ls-tree.
   Bukti: wyag log/ls-tree atas repo git asli menyamai keluaran git asli.
3. **Refs & tag** (§7): show-ref, tag, rev-parse, object_find sungguhan.
4. **Index I** (§8): ls-files, check-ignore, status atas repo git asli.
5. **Index II + tutup** (§9): add, rm, commit — repo lahir & berkomit penuh
   oleh wyag, diverifikasi `git fsck` + `git log`; terbitkan repo GitHub.

## Pagar selesai

- [x] Kode tiap irisan jalan dan terbukti interop dengan git asli, bukan sekadar tertulis.
- [x] `CATATAN.md` terisi satu halaman per irisan: konsep inti + kejutan/kegagalan.
- [ ] Repo GitHub publik diterbitkan dan terverifikasi (seperti build sebelumnya).

## Status

- [x] Irisan 1 — selesai & terverifikasi 15 Nov 2026 (lihat CATATAN.md)
- [x] Irisan 2 — selesai & terverifikasi 15 Nov 2026 (lihat CATATAN.md)
- [x] Irisan 3 — selesai & terverifikasi 15 Nov 2026 (lihat CATATAN.md)
- [x] Irisan 4 — selesai & terverifikasi 15 Nov 2026 (lihat CATATAN.md)
- [x] Irisan 5 — selesai & terverifikasi 15 Nov 2026 (lihat CATATAN.md); repo lahir & berkomit penuh oleh wyag, `git fsck --strict` bersih

## Cara menjalankan Irisan 1

```sh
./wyag init /tmp/repo-uji
./wyag hash-object -w berkas.txt     # dari dalam repo
./wyag cat-file blob <sha>
python3 uji_irisan1.py               # bukti interop dua arah dengan git asli
```
