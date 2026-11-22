# Implementasi QRIS Simulasi – Kuliner Bengkulu

Patch ini menambahkan alur pembayaran QRIS **khusus demonstrasi** untuk proyek Django 5.2 + MySQL. Tidak ada QRIS merchant sungguhan, transaksi uang, integrasi payment gateway, maupun callback provider.

## Perilaku

1. Pelanggan memilih metode QRIS.
2. Halaman pembayaran menampilkan ilustrasi QR yang diberi label DEMO dan nominal pesanan.
3. Pelanggan menekan **Simulasikan Pembayaran Berhasil**.
4. Django mengubah `Payment.status` menjadi `PAID`, mencatat `gateway_status=DEMO_SIMULATED`, dan mengubah status pesanan menjadi `WAITING_CONFIRMATION`.
5. Notifikasi DEMO dibuat untuk pelanggan dan akun admin/pegawai.

Endpoint hanya menerima POST, hanya dapat dipanggil pemilik pesanan yang login, hanya untuk metode QRIS, hanya ketika `PAYMENT_DEMO_MODE=True`, dan hanya selama pembayaran masih `WAITING` serta belum melewati batas waktu. Ilustrasi SVG bukan QR code yang bisa dipindai.

## Pemasangan

1. Ekstrak ZIP patch ke folder proyek (folder yang berisi `manage.py`).
2. Buka terminal VS Code di folder tersebut.
3. Jalankan:

   ```powershell
   python apply_demo_qris_patch.py
   ```

4. Tambahkan baris berikut ke `.env` proyek:

   ```env
   PAYMENT_DEMO_MODE=True
   ```

   Ini menyalakan simulasi. Tanpa pengaturan tersebut, mode default adalah OFF.

5. Periksa proyek:

   ```powershell
   python manage.py check
   ```

6. Jalankan server:

   ```powershell
   python manage.py runserver
   ```

7. Login sebagai pelanggan, buat pesanan baru, pilih QRIS, lalu tekan tombol simulasi pada halaman pembayaran.

## Tidak perlu migration

Patch hanya memakai field yang sudah ada pada model `Payment` (`status`, `gateway_status`, `gateway_transaction_id`, `verified_at`, `verified_by`, `staff_note`) dan `Order.status`. Tidak ada perubahan skema database.

## Backup dan pembatalan patch

Sebelum mengubah file, script membuat backup dengan akhiran `.before_demo_qris.bak`. Untuk membatalkan, pulihkan backup masing-masing file dan hapus `static/images/qris-demo.svg`.

## Peringatan hosting

Mode ini hanya untuk presentasi, demo, dan pengujian. Jangan mengaktifkan `PAYMENT_DEMO_MODE=True` pada website yang menerima pembayaran nyata. Jika website di-hosting untuk transaksi sungguhan, set `PAYMENT_DEMO_MODE=False` atau hapus baris tersebut, lalu integrasikan payment gateway/QRIS merchant resmi. Status `PAID` dengan `gateway_status=DEMO_SIMULATED` **bukan bukti bahwa uang telah diterima**.
