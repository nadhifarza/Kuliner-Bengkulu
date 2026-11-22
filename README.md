# Website Kuliner Bengkulu

Website berbasis **Python 3.13 + Django 5.2 + MySQL** dengan opsi SQLite untuk uji jalan pertama. Tampilan mengikuti paket SVG yang diberikan: logo resmi, Poppins, cream `#FFF6E6`, maroon `#7A0E15`, merah `#C0392B`, dan gold `#F4C542`. Desktop dan mobile memakai satu sistem desain responsif.

## Fitur yang sudah dibuat
- Login, registrasi pelanggan, verifikasi email (tautan tampil di terminal dalam mode lokal), lupa/reset password.
- Katalog 23 menu, pencarian nama, filter kategori, detail produk.
- Keranjang, perubahan jumlah dan catatan, checkout pengiriman/pickup, snapshot harga transaksi, validasi stok dan pengurangan stok.
- Pembayaran transfer bank/QRIS dengan status terpisah dari status pesanan, tenggat 30 menit, webhook HMAC scaffold, review pegawai.
- Riwayat pesanan, detail, pembatalan sebelum diproses, notifikasi internal.
- Dashboard admin, manajemen produk/kategori/pegawai, profil usaha, laporan transaksi/penjualan/stok, ekspor PDF dan Excel.
- Dashboard pegawai, antrean pemeriksaan pembayaran, pengelolaan proses pesanan.

## Catatan data menu
Menu awal dibuat lewat `seed_kuliner` sesuai daftar yang diberikan. Harga dikosongkan dan stok awal 0 karena harga/stok belum diberikan. Produk baru bisa dibeli setelah admin mengisi harga dan stok. Foto tersedia untuk 22 menu; Pendap memakai placeholder karena fotonya tidak ditemukan di ZIP foto. `download.jpg` dipetakan sementara ke Santan Palak Ikan berdasarkan tampilannya; mohon koreksi jika itu bukan foto Santan Palak Ikan.

Deskripsi, komposisi, dan sejarah menu belum disediakan sehingga diisi teks placeholder agar admin dapat melengkapinya. Foto yang disediakan pengguna disalin ke `static/images/products/`.

## Menjalankan di Windows (VS Code)
1. Ekstrak ZIP project, buka folder `Kuliner_Bengkulu_Website` di VS Code.
2. Buka Terminal PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

3. Jalankan migrasi dan isi 23 produk awal:

```powershell
python manage.py makemigrations store
python manage.py migrate
python manage.py seed_kuliner
python manage.py createsuperuser
```

Saat membuat superuser, gunakan alamat email yang sama untuk kolom Username dan Email, lalu masukkan password. Superuser otomatis mendapat akses Admin meskipun field role default berbeda.

4. Jalankan server:

```powershell
python manage.py runserver
```

Buka `http://127.0.0.1:8000/`.

5. Untuk verifikasi registrasi lokal, setelah klik daftar lihat URL verifikasi yang tercetak di terminal. Buka URL tersebut di browser, lalu login.

## Menggunakan MySQL
SQLite dipakai sebagai default agar proyek bisa langsung diuji tanpa menunggu konfigurasi MySQL. Untuk menggunakan MySQL yang sudah dipasang, salin `.env.example` menjadi `.env`, lalu ubah `DB_ENGINE=mysql`, `DB_NAME`, `DB_USER`, dan `DB_PASSWORD`. File `.env` dibaca otomatis oleh settings:

```powershell
$env:DB_ENGINE='mysql'
$env:DB_NAME='kuliner_bengkulu'
$env:DB_USER='root'
$env:DB_PASSWORD='PASSWORD_MYSQL_KAMU'
$env:DB_HOST='127.0.0.1'
$env:DB_PORT='3306'
python manage.py migrate
```

Buat database melalui MySQL Workbench atau jalankan SQL berikut:

```sql
CREATE DATABASE kuliner_bengkulu CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Setelah database dibuat, jalankan migrasi lagi menggunakan konfigurasi MySQL tersebut.

## Script praktis Windows
- Jalankan `setup_awal_windows.ps1` di PowerShell untuk menyiapkan virtual environment, menginstal dependensi, migrasi, dan data menu. Jika PowerShell memblokir script, jalankan `Set-ExecutionPolicy -Scope Process Bypass` pada terminal tersebut.
- Setelah membuat akun admin dengan `python manage.py createsuperuser`, jalankan `jalankan_website.bat` atau `python manage.py runserver`.

## Mengisi harga dan stok
Login sebagai admin, buka Pengelola → Produk → Ubah. Masukkan harga dan stok sebenarnya. Jangan isi angka contoh dari file desain sebagai harga aktual.

## Payment gateway
Provider transfer/QRIS belum ditentukan. Halaman pembayaran secara jujur menampilkan bahwa gateway belum dikonfigurasi. Endpoint callback `/webhook/payment/` sudah disediakan dengan HMAC-SHA256, tetapi perlu disesuaikan dengan format signature dan payload provider yang dipilih. Jangan mengaktifkan transaksi nyata sebelum menguji callback dan settlement.

## Hal yang masih perlu dilengkapi
- Harga dan stok 23 produk.
- Deskripsi, komposisi, sejarah/asal-usul produk.
- Foto Pendap.
- Pemilihan payment gateway dan detail rekening/QRIS dari provider.
- Rumus biaya pengiriman, penyedia kurir, serta mekanisme refund. Sampai aturan ongkir ditentukan, total checkout hanya menjumlahkan produk dan belum menghitung ongkir.
- Konten final syarat dan ketentuan serta kebijakan privasi.
- Jadwalkan `python manage.py expire_kuliner_orders` setiap menit (Task Scheduler/cron) agar tenggat pembayaran diproses tepat waktu di luar aktivitas pengguna.

## Role / akun
- Pelanggan: daftar sendiri dan verifikasi email.
- Admin: buat dengan `createsuperuser` atau set `role='ADMIN'` pada akun yang ditunjuk.
- Pegawai: dibuat melalui halaman Admin → Akun Pegawai.
- Django Admin teknis: `/django-admin/`.

## Struktur
- `store/`: model, form, view, URL, seed data, expiry command.
- `templates/`: halaman pelanggan/admin/pegawai/authentication.
- `static/`: CSS, JS, logo, foto menu.
- `docs/uiux_reference/`: SVG sumber desktop dan mobile yang diunggah.
