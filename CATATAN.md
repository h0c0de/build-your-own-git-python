# Catatan Build — Git dengan Python (wyag)

Satu irisan = satu halaman. Ditulis sesudah uji nyata, bukan sesudah membaca.

## Irisan 1 — init + model objek (15 Nov 2026, terverifikasi)

**Yang dibangun:** mengikuti *Write yourself a Git!* (Thibault Polge) bab 2–4 — `wyag` (executable) + `libwyag.py`: `GitRepository` (validasi `.git` + config `repositoryformatversion` 0), `repo_create`/`repo_find`, model objek (`object_read`/`object_write`/`object_hash`), `GitBlob`, dan perintah `init`, `hash-object`, `cat-file`. `object_find` masih penampung persis tahap panduan ini; kelas commit/tree/tag berupa penampung yang gagal dengan pesan jelas.

**Bukti jalan:** `uji_irisan1.py` — 21/21 PASS, semuanya interop melawan git asli 2.43.0:
- `wyag init` menghasilkan struktur `.git` yang **dikenali git asli** (`git status` dan `git rev-parse` jalan di repo buatan wyag).
- Hash wyag **identik** dengan hash git untuk berkas teks maupun biner 1 KB (semua nilai byte 0–255 ×4).
- Objek yang ditulis wyag (`hash-object -w`) dibaca balik sempurna oleh `git cat-file -p`, tipenya terbaca `blob`.
- Arah sebaliknya juga: objek tulisan `git hash-object -w` dibaca balik utuh oleh `wyag cat-file`.
- `repo_find` bekerja dari subdirektori dua tingkat di dalam repo.

**Konsep inti:**
- Git adalah *content-addressed filesystem*: nama sebuah objek adalah SHA-1 dari isinya sendiri (termasuk kepala `"<tipe> <ukuran>\0"`), disimpan terkompresi zlib di `.git/objects/xx/sisa-hash`. Karena nama = fungsi isi, isi yang sama selalu bernama sama di repo mana pun di dunia — itulah sebabnya hash kami dan hash git asli cocok tanpa koordinasi apa pun.
- Blob tidak punya format sama sekali: isinya data mentah pengguna. Seluruh "keajaiban" irisan ini hanya kepala + hash + zlib.
- Sebuah repo, pada dasarnya, hanyalah folder `.git` dengan beberapa direktori, satu berkas HEAD berisi penunjuk ref, dan config INI. `git status` menerima repo buatan wyag karena memang hanya itu yang ia periksa pada tahap ini.

**Kejutan:** tidak ada kegagalan — semua lulus pada jalan pertama. Satu-satunya penyesuaian sadar dari panduan: kelas GitCommit/GitTree/GitTag kami jadikan penampung yang melempar pesan "belum diimplementasikan (Irisan 2/3)", karena versi panduan membiarkan referensi kelas itu menggantung sampai babnya tiba (akan NameError bila disentuh lebih awal).

## Irisan 2 — Baca sejarah: log & ls-tree (15 Nov 2026, terverifikasi)

**Yang dibangun:** bab 5–6 panduan — parser KVLM (`kvlm_parse`/`kvlm_serialize`), `GitCommit`, `wyag log` (keluaran graphviz), `GitTree` (parse + serialize biner), `wyag ls-tree` (datar & `-r`), dan `wyag checkout` (realisasi tree ke folder kosong).

**Bukti jalan:** `uji_irisan2.py` — 14/14 PASS atas repo yang dibuat **seluruhnya oleh git asli** (3 commit, subdirektori dua tingkat), regresi Irisan 1 tetap hijau:
- Round-trip lewat parser wyag **identik byte**: `wyag cat-file commit` dan `cat-file tree` == keluaran git asli, termasuk byte biner tree.
- `wyag log` memuat 3 node dengan pesan yang benar dan 2 panah parent yang benar (c3→c2→c1).
- `wyag ls-tree` datar maupun `-r` **sama baris per baris** dengan `git ls-tree`.
- `wyag checkout` commit pertama menghasilkan pohon berkas persis keadaan saat itu (a.txt versi 1, tanpa d.txt); checkout HEAD menghasilkan versi 2 + d.txt.

**Temuan utama — bug panduan yang tertangkap uji byte:** panduan menormalkan mode direktori 5 byte (`40000`) menjadi 6 byte (`040000`) di dalam parser tree. Akibatnya serialisasi balik tree yang memuat direktori menghasilkan byte berbeda dari aslinya — dan karena nama objek adalah hash isinya, tree yang "sama" akan bernama beda: melanggar aturan identitas objek yang justru ditekankan panduan sendiri di bab 5. Git asli menyimpan mode direktori tanpa nol di depan (terbukti lewat `od -c`). **Perbaikan kami:** mode disimpan mentah apa adanya; normalisasi 6 byte hanya untuk tampilan di `ls_tree`. Sesudah perbaikan, round-trip tree identik byte.

**Konsep inti:**
- Commit adalah objek KVLM: pasangan kunci-nilai (tree, parent, author, committer) + pesan; kunci yang berulang (parent pada merge) menjadi list, dan *urutan* field ikut menentukan hash.
- Sejarah git adalah Merkle DAG: nama commit mengikat seluruh leluhurnya — mengubah satu byte di masa lalu mengganti nama semua commit sesudahnya.
- Tree adalah format biner ringkas `[mode] spasi [path]\0 [sha 20 byte]`, dan direktori diurutkan seolah namanya berakhiran `/` — kekhasan kecil yang menjaga satu struktur direktori hanya punya satu nama.
- `wyag log` belum bisa dipanggil tanpa SHA penuh (`wyag log` polos gagal) karena `object_find` masih penampung — resolusi nama seperti `HEAD` adalah materi Irisan 3, sesuai urutan panduan.

## Irisan 3 — Refs & tag (15 Nov 2026, terverifikasi)

**Yang dibangun:** bab 7 panduan — `ref_resolve` (mengikuti rantai ref tak langsung), `ref_list`/`show_ref`, `GitTag` (mewarisi GitCommit, hanya ganti `fmt`), `wyag tag` (daftar, ringan, dan objek beranotasi), `object_resolve` + `object_find` sungguhan (HEAD, hash penuh/pendek, tag, branch, branch remote; mengikuti tag → commit → tree bila tipe diminta), dan `wyag rev-parse`.

**Bukti jalan:** `uji_irisan3.py` — 20/20 PASS atas repo git asli (3 commit, branch `fitur`, tag ringan & beranotasi buatan git), regresi Irisan 1+2 hijau:
- `wyag show-ref` == `git show-ref` sebagai himpunan baris.
- `wyag rev-parse` menyamai git untuk HEAD, nama branch, hash pendek 7 char, dan kedua tag; `--wyag-type commit` mengikuti objek tag sampai commit-nya, `--wyag-type tree HEAD` memberi tree HEAD, `--wyag-type tag HEAD` menjawab `None` dengan jujur.
- **`wyag log` polos akhirnya bekerja** (resolusi HEAD), begitu pula `ls-tree HEAD` dan `ls-tree fitur` — keduanya sama dengan git.
- Arah sebaliknya: tag ringan dan tag objek **buatan wyag** dibaca balik benar oleh git asli (`cat-file -t` = tag; `^{commit}` menunjuk commit yang dimaksud).

**Konsep inti:**
- Ref ternyata hal paling sederhana di git: berkas teks di `.git/refs/...` berisi satu hash — atau berisi `ref: <ref lain>` (HEAD adalah ref tak langsung ke branch aktif). Branch pun bukan struktur khusus: hanya ref di `refs/heads/` yang digeser tiap commit. Tag = ref di `refs/tags/` yang tidak digeser.
- Tag beranotasi adalah *objek* (KVLM seperti commit: object, type, tag, tagger, pesan), sedangkan tag ringan murni ref — perbedaan yang terlihat langsung di `rev-parse`: yang satu mengembalikan SHA objek tag, yang lain SHA commit.
- Resolusi nama mengumpulkan *semua* kandidat lalu menolak bila ambigu — nama pendek yang menunjuk dua objek adalah kesalahan, bukan tebakan.

**Batas yang dinyatakan panduan (kami ikuti sadar):** identitas tagger dan pesan tag objek buatan wyag masih tetap ("Wyag <wyag@example.com>", pesan bawaan panduan) — panduan sendiri menandainya sebagai hal yang baru bisa diganti sesudah bab commit; kami biarkan terlihat apa adanya di kode, bukan disembunyikan.

## Irisan 4 — Index I: status (15 Nov 2026, terverifikasi)

**Yang dibangun:** bab 8 panduan — parser index biner (`GitIndexEntry`, `GitIndex`, `index_read`: kepala `DIRC`, entri 62 byte + nama + padding kelipatan 8), `wyag ls-files` (+ `--verbose` khas wyag), aturan abaikan (`gitignore_read`, `check_ignore` tiga-nilai, `wyag check-ignore`), dan `wyag status` tiga bagian (branch aktif; HEAD vs index; index vs worktree + untracked).

**Bukti jalan:** `uji_irisan4.py` — 8/8 PASS atas repo git asli berkeadaan campur (staged baru/ubah/hapus, unstaged ubah/hapus, untracked, ignored termasuk negasi `!penting.log` dan `.gitignore` subdirektori), regresi Irisan 1–3 hijau:
- `wyag ls-files` == `git ls-files` persis; kepala `--verbose` cocok dengan hitungan git.
- `wyag check-ignore` == `git check-ignore`: `sampah.log` dan `sub/x.tmp` terabaikan; `penting.log` (negasi) dan `x.tmp` di root (aturan hanya berlaku di `sub/`) tidak.
- Tiga himpunan `wyag status` (staged/unstaged/untracked) **sama persis** dengan terjemahan `git status --porcelain`.

**Temuan — perbaikan Irisan 2 punya radius ledak:** uji pertama gagal: `status` melaporkan `sub/jaga.txt` dan `sub/.gitignore` sebagai "added" dan `sub` sebagai "deleted". Akarnya: `tree_to_dict` dari panduan memeriksa subtree dengan awalan mode `b'04'` — benar untuk parser panduan yang menormalkan mode, tapi salah untuk mode mentah `40000` hasil perbaikan Irisan 2 kami. Kode panduan konsisten internal dengan normalisasinya sendiri yang cacat; memperbaikinya di satu tempat berarti menyesuaikan semua pemakai asumsi itu. **Perbaikan:** pemeriksaan subtree memakai awalan `b'4'` (mencakup kedua bentuk, tak bertabrakan dengan mode berkas 10/12/16). Pelajarannya dicatat apa adanya: uji irisan ini hanya menangkapnya karena repo uji sengaja punya subdirektori.

**Konsep inti:**
- Index bukan delta dari HEAD — ia *salinan* HEAD dalam format lain, ditambah metadata filesystem (ctime/mtime/inode/ukuran) supaya status bisa memutuskan "tidak berubah" tanpa membaca isi berkas; hash ulang hanya terjadi bila metadata bergeser.
- Status sebenarnya dua perbandingan terpisah: HEAD↔index (yang akan di-commit) dan index↔worktree (yang belum di-stage). Kebingungan pemula soal "modified dua kali" hilang begitu dua sumbu ini dipisah.
- Aturan abaikan dibaca dari `.gitignore` **yang ada di index**, bukan dari worktree — hanya yang sudah ter-stage yang berlaku; dan pencocokan aturan bersifat tiga-nilai (cocok-abaikan / cocok-negasi / tidak cocok) karena berkas yang lebih spesifik harus bisa membatalkan yang lebih umum, dan sebaliknya ketiadaan kecocokan harus diteruskan ke berkas yang lebih umum.

## Irisan 5 — Index II: commit (15 Nov 2026, terverifikasi — build tuntas)

**Yang dibangun:** bab 9 panduan — `index_write` (serialisasi index), `rm`, `add` (hash berkas → blob + entri index dari `stat()`), `tree_from_index` (index datar → tree rekursif dari direktori terdalam ke akar), `commit_create` + `wyag commit` (identitas dari `~/.gitconfig`, induk dari HEAD, lalu geser ref branch aktif).

**Bukti jalan:** `uji_irisan5.py` — 22/22 PASS pada jalan pertama, regresi Irisan 1–4 hijau. Kali ini seluruh siklus hidup digerakkan **wyag saja** (`init` → `add` → `commit` ×3 → `rm`), dan git asli murni menjadi juri:
- Index tulisan wyag dibaca git tanpa keluhan dan **terurut** (`git ls-files`), walau `add` dipanggil tidak menurut abjad.
- Tree commit pertama wyag ber-hash **identik** dengan `git write-tree` atas index yang sama — pembangunan tree kami dan git menghasilkan objek yang sama persis.
- `git log` membaca 3 commit dengan urutan pesan dan rantai induk yang benar; `git show HEAD:a.txt` / `HEAD~1:a.txt` memberi versi yang tepat; sesudah `wyag rm`, `git status` melaporkan penghapusan staged dengan benar.
- **`git fsck --strict` bersih total**, dan `git status` akhir bersih — repo buatan wyag adalah repo git yang sah sepenuhnya.

**Tiga perbaikan sadar atas panduan di irisan ini** (dua tertangkap desain uji, satu terbaca dari teks):
1. **Hash penutup index.** Panduan tidak menulis hash SHA-1 di ekor berkas index; git asli selalu menulisnya dan memverifikasinya. Kami tambahkan — status git yang bersih di atas adalah buktinya diterima.
2. **Entri index terurut.** `add` panduan menambahkan entri di ekor; index git wajib terurut nama. Kami urutkan di `index_write`, satu-satunya pintu keluar index.
3. **Bug HEAD lepas di teks panduan.** Cabang detached-HEAD `cmd_commit` di artikel menulis hanya `"\n"` ke `.git/HEAD` (akan menghancurkan HEAD); kami tulis hash commit-nya. Dan mode subtree di `tree_from_index` memakai `40000` mentah, meneruskan perbaikan Irisan 2 — kesetaraan hash dengan `git write-tree` di atas membuktikan pilihan ini, karena satu byte nol ekstra saja akan mengganti seluruh hash tree.

**Konsep inti penutup:**
- Commit sesungguhnya rangkaian sederhana: index → (tree_from_index) → tree → commit object berisi tree+parent+identitas+waktu+pesan → geser satu berkas ref. Tidak ada sihir lain; "branch berpindah" hanyalah berkas teks berisi hash yang ditulis ulang.
- Identitas penulis diambil dari config pengguna (`~/.gitconfig`), dan stempel waktu commit adalah bagian dari objek — mengubahnya berarti mengubah hash, seperti semua hal lain di git.
- Pelajaran lintas-build: tiga build berturut-turut (web server, Redis, Git) menunjukkan pola yang sama — implementasi "mainan" dari protokol nyata menjadi sungguhan tepat pada titik ia diuji melawan implementasi aslinya, byte per byte.
