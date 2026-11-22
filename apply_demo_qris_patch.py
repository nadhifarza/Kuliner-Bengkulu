from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
BASE = Path.cwd()

REQUIRED = [
    BASE / 'manage.py',
    BASE / 'store' / 'views.py',
    BASE / 'store' / 'urls.py',
    BASE / 'kuliner' / 'settings.py',
    BASE / 'templates' / 'store' / 'payment_detail.html',
    BASE / 'templates' / 'store' / 'payment_select.html',
    BASE / 'static' / 'css' / 'style.css',
]
missing = [str(p.relative_to(BASE)) for p in REQUIRED if not p.exists()]
if missing:
    print('GAGAL: Jalankan script dari folder proyek yang berisi manage.py.')
    print('File yang tidak ditemukan:')
    for item in missing:
        print(' -', item)
    sys.exit(1)

views_path = BASE / 'store' / 'views.py'
urls_path = BASE / 'store' / 'urls.py'
settings_path = BASE / 'kuliner' / 'settings.py'
payment_detail_path = BASE / 'templates' / 'store' / 'payment_detail.html'
payment_select_path = BASE / 'templates' / 'store' / 'payment_select.html'
css_path = BASE / 'static' / 'css' / 'style.css'
svg_target = BASE / 'static' / 'images' / 'qris-demo.svg'

views = views_path.read_text(encoding='utf-8')
urls = urls_path.read_text(encoding='utf-8')
settings = settings_path.read_text(encoding='utf-8')

# Back up each file before changing it. Existing backups are preserved.
files_to_backup = [views_path, urls_path, settings_path, payment_detail_path, payment_select_path, css_path]
for path in files_to_backup:
    backup = path.with_suffix(path.suffix + '.before_demo_qris.bak')
    if not backup.exists():
        shutil.copy2(path, backup)

# 1) Add an explicit opt-in switch. It is OFF unless .env enables it.
setting_line = "PAYMENT_WEBHOOK_SECRET = os.getenv('PAYMENT_WEBHOOK_SECRET', '')"
setting_addition = setting_line + "\nPAYMENT_DEMO_MODE = os.getenv('PAYMENT_DEMO_MODE', 'False').strip().lower() == 'true'"
if 'PAYMENT_DEMO_MODE' not in settings:
    if setting_line not in settings:
        raise SystemExit('Tidak menemukan konfigurasi PAYMENT_WEBHOOK_SECRET di kuliner/settings.py. Tidak ada file yang selesai diubah.')
    settings = settings.replace(setting_line, setting_addition, 1)

# 2) Pass demo-mode status into payment method selection screen.
old_select_render = "return render(request,'store/payment_select.html',{'order':order,'payment':payment})"
new_select_render = "return render(request,'store/payment_select.html',{'order':order,'payment':payment,'demo_mode':settings.PAYMENT_DEMO_MODE})"
if new_select_render not in views:
    if old_select_render not in views:
        raise SystemExit('Tidak menemukan return render payment_select yang dikenali di store/views.py.')
    views = views.replace(old_select_render, new_select_render, 1)

# 3) Replace the payment detail view and add the guarded POST-only demo action.
start_marker = '@active_customer\ndef payment_detail(request,code):'
end_marker = '@active_customer\ndef order_history(request):'
if 'def simulate_qris_payment(request,code):' not in views:
    if start_marker not in views or end_marker not in views:
        raise SystemExit('Tidak menemukan blok payment_detail/order_history yang dikenali di store/views.py.')
    start = views.index(start_marker)
    end = views.index(end_marker, start)
    replacement = '''@active_customer
def payment_detail(request,code):
    order=get_object_or_404(Order,code=code,customer=request.user)
    return render(request,'store/payment_detail.html',money_context({
        'order':order,
        'payment':order.payment,
        'gateway_ready':bool(settings.PAYMENT_GATEWAY_NAME),
        'demo_mode':settings.PAYMENT_DEMO_MODE,
    }))


@active_customer
@require_POST
def simulate_qris_payment(request,code):
    """Demo-only QRIS action. Never represents or confirms a real money transfer."""
    if not settings.PAYMENT_DEMO_MODE:
        return HttpResponseForbidden('Mode simulasi pembayaran sedang dinonaktifkan.')

    # Run the normal expiry routine before accepting a demo payment.
    expire_pending_orders()

    with transaction.atomic():
        order=get_object_or_404(
            Order.objects.select_for_update(),
            code=code,
            customer=request.user,
        )
        payment=get_object_or_404(Payment.objects.select_for_update(),order=order)

        if payment.method != 'QRIS':
            messages.error(request,'Simulasi ini hanya tersedia untuk metode QRIS.')
            return redirect('payment_detail',code=code)

        if payment.status == 'PAID' and payment.gateway_status == 'DEMO_SIMULATED':
            messages.info(request,'Pembayaran pesanan ini sudah disimulasikan berhasil.')
            return redirect('payment_detail',code=code)

        if payment.status != 'WAITING':
            messages.error(request,'Pesanan ini tidak lagi berada pada status menunggu pembayaran.')
            return redirect('payment_detail',code=code)

        if payment.deadline and payment.deadline <= timezone.now():
            messages.error(request,'Batas pembayaran sudah berakhir. Silakan buat pesanan baru atau hubungi pengelola.')
            return redirect('payment_detail',code=code)

        now=timezone.now()
        payment.status='PAID'
        payment.gateway_status='DEMO_SIMULATED'
        payment.gateway_transaction_id='DEMO-'+uuid.uuid4().hex[:12].upper()
        payment.verified_by=None
        payment.verified_at=now
        payment.staff_note='SIMULASI DEMO: tidak ada transaksi atau perpindahan uang sungguhan.'
        payment.save(update_fields=[
            'status','gateway_status','gateway_transaction_id',
            'verified_by','verified_at','staff_note'
        ])

        order.status='WAITING_CONFIRMATION'
        order.save(update_fields=['status','updated_at'])

        notify(
            order.customer,
            'Pembayaran simulasi berhasil',
            f'Pembayaran DEMO untuk pesanan {order.code} berhasil disimulasikan. Tidak ada uang sungguhan yang ditransfer.',
            'PAYMENT',
            order,
        )
        staff_users=User.objects.filter(
            Q(role__in=['ADMIN','EMPLOYEE']) | Q(is_superuser=True)
        ).distinct()
        for staff_user in staff_users:
            notify(
                staff_user,
                'Pembayaran DEMO baru',
                f'Pesanan {order.code} telah melewati simulasi pembayaran QRIS. Bukan transaksi nyata.',
                'PAYMENT',
                order,
            )

    messages.success(request,'Simulasi pembayaran QRIS berhasil. Ini hanya transaksi DEMO, bukan pembayaran sungguhan.')
    return redirect('payment_detail',code=code)


'''
    views = views[:start] + replacement + views[end:]

# 4) Add the simulation route once.
route = "path('pembayaran/<str:code>/simulasi-berhasil/',views.simulate_qris_payment,name='simulate_qris_payment'),"
if route not in urls:
    anchor = "path('pembayaran/<str:code>/detail/',views.payment_detail,name='payment_detail'),"
    if anchor not in urls:
        raise SystemExit('Tidak menemukan route payment_detail di store/urls.py.')
    urls = urls.replace(anchor, anchor + route, 1)

# Write Python files only after the transformations above have succeeded.
settings_path.write_text(settings, encoding='utf-8')
views_path.write_text(views, encoding='utf-8')
urls_path.write_text(urls, encoding='utf-8')

payment_detail_template = r'''{% extends 'store/base.html' %}
{% load kb_filters %}
{% load static %}

{% block title %}Status Pembayaran | Kuliner Bengkulu{% endblock %}

{% block content %}
<div class="narrow">
    <div class="status-banner">
        <span class="status-icon">◷</span>
        <p class="eyebrow">PEMBAYARAN PESANAN</p>
        <h1>{{ payment.get_status_display }}</h1>
        <p>Pesanan {{ order.code }}</p>
        {% if payment.gateway_status == 'DEMO_SIMULATED' %}
            <span class="demo-status-pill">PEMBAYARAN SIMULASI</span>
        {% endif %}
    </div>

    <section class="panel">
        <div class="summary-line">
            <span>Total yang harus dibayar</span>
            <b class="detail-price">{{ order.total|rupiah }}</b>
        </div>
        <div class="summary-line">
            <span>Metode</span>
            <b>{{ payment.get_method_display }}</b>
        </div>
        <div class="summary-line">
            <span>Batas pembayaran</span>
            <b>{{ payment.deadline|date:'d M Y, H:i' }} WIB</b>
        </div>

        {% if payment.method == 'QRIS' %}
            {% if payment.gateway_status == 'DEMO_SIMULATED' and payment.status == 'PAID' %}
                <section class="demo-qris-card demo-qris-success">
                    <span class="demo-label">MODE DEMO</span>
                    <h2>Simulasi pembayaran berhasil!</h2>
                    <p>Status pembayaran telah berubah menjadi <strong>Berhasil</strong> dan pesanan diteruskan ke tahap konfirmasi.</p>
                    <p class="demo-disclaimer"><strong>Perhatian:</strong> ini hanya simulasi untuk demonstrasi website. Tidak ada uang sungguhan yang ditransfer atau diterima.</p>
                </section>
            {% elif demo_mode and payment.status == 'WAITING' %}
                <section class="demo-qris-card">
                    <div class="demo-label">MODE DEMO · BUKAN TRANSAKSI NYATA</div>
                    <h2>Simulasi Pembayaran QRIS</h2>
                    <p>Halaman ini menampilkan alur pembayaran untuk keperluan demonstrasi. QR di bawah bukan QRIS merchant dan tidak dapat dipindai untuk membayar.</p>
                    <div class="demo-qr-wrap">
                        <img src="{% static 'images/qris-demo.svg' %}" alt="Ilustrasi QRIS simulasi, tidak dapat digunakan untuk pembayaran">
                    </div>
                    <div class="demo-amount">
                        <span>Nominal simulasi</span>
                        <strong>{{ order.total|rupiah }}</strong>
                    </div>
                    <form method="post" action="{% url 'simulate_qris_payment' order.code %}">
                        {% csrf_token %}
                        <button type="submit" class="btn btn-primary full" onclick="return confirm('Jalankan simulasi pembayaran berhasil? Tidak ada uang sungguhan yang ditransfer.')">
                            Simulasikan Pembayaran Berhasil
                        </button>
                    </form>
                    <p class="demo-disclaimer">Tombol ini hanya mengubah status transaksi untuk demo. Jangan gunakan untuk menyatakan pembayaran pelanggan sungguhan telah diterima.</p>
                </section>
            {% elif payment.status == 'WAITING' %}
                <div class="gateway-note">
                    <b>Pembayaran QRIS belum dikonfigurasi</b>
                    <p>Mode demo sedang nonaktif dan payment gateway belum terhubung. Pembayaran QRIS nyata belum dapat diproses melalui website ini.</p>
                </div>
            {% else %}
                <div class="gateway-note">
                    <b>Status pembayaran: {{ payment.get_status_display }}</b>
                    <p>Silakan lihat detail pesanan atau hubungi pengelola jika memerlukan bantuan.</p>
                </div>
            {% endif %}
        {% else %}
            <div class="gateway-note">
                <b>Instruksi transfer bank</b>
                <p>Transfer bank belum diintegrasikan dengan payment gateway. Untuk demonstrasi pembayaran, pilih metode QRIS dan aktifkan MODE DEMO.</p>
            </div>
        {% endif %}

        {% if payment.staff_note and payment.status == 'REJECTED' %}
            <p class="message error">Catatan pengelola: {{ payment.staff_note }}</p>
        {% endif %}

        <a href="{% url 'order_detail' order.code %}" class="btn btn-primary full">Lihat Detail Pesanan</a>
    </section>
</div>
{% endblock %}
'''
payment_detail_path.write_text(payment_detail_template, encoding='utf-8')

payment_select_template = r'''{% extends 'store/base.html' %}
{% load kb_filters %}
{% block title %}Metode Pembayaran | Kuliner Bengkulu{% endblock %}
{% block content %}
<div class="breadcrumb">Checkout / Metode Pembayaran</div>
<div class="narrow">
    <h1>Pilih Pembayaran</h1>
    <p class="muted">Pesanan {{ order.code }} · Total {{ order.total|rupiah }}</p>
    <form method="post" class="panel">
        {% csrf_token %}
        <label class="payment-option">
            <input type="radio" name="method" value="BANK_TRANSFER" {% if payment.method == 'BANK_TRANSFER' %}checked{% endif %}>
            <span><b>Transfer Bank</b><small>Instruksi transfer belum tersedia pada mode demo.</small></span>
            <strong>⇢</strong>
        </label>
        <label class="payment-option">
            <input type="radio" name="method" value="QRIS" {% if payment.method == 'QRIS' %}checked{% endif %}>
            <span>
                <b>QRIS {% if demo_mode %}<em class="demo-inline-label">SIMULASI</em>{% endif %}</b>
                <small>{% if demo_mode %}Simulasikan pembayaran untuk demonstrasi website; bukan transaksi nyata.{% else %}Pembayaran QRIS belum dikonfigurasi.{% endif %}</small>
            </span>
            <strong>▦</strong>
        </label>
        {% if demo_mode %}<p class="demo-disclaimer">Mode demo aktif. Pembayaran simulasi tidak memindahkan uang dan tidak boleh dianggap sebagai transaksi sungguhan.</p>{% endif %}
        <button class="btn btn-primary full" type="submit">Lanjutkan</button>
    </form>
</div>
{% endblock %}
'''
payment_select_path.write_text(payment_select_template, encoding='utf-8')

css = css_path.read_text(encoding='utf-8')
css_addition = '''\n/* QRIS demo-only payment UI */\n.demo-qris-card{margin:20px 0;padding:20px;border:1px solid #f0d99e;border-radius:15px;background:#fffaf0;text-align:center}\n.demo-qris-card h2{color:var(--maroon);font-size:20px;margin:10px 0}\n.demo-qris-card p{font-size:12px;color:var(--muted);line-height:1.7}\n.demo-label,.demo-status-pill,.demo-inline-label{display:inline-flex;align-items:center;border-radius:30px;padding:5px 10px;background:#fff0c4;color:#875a00;font-size:10px;font-weight:800;letter-spacing:.7px}\n.demo-inline-label{font-size:9px;padding:3px 7px;margin-left:5px}\n.demo-status-pill{background:#e8f2e3;color:#4f713d;margin-top:8px}\n.demo-qr-wrap{display:flex;justify-content:center;margin:16px auto;max-width:245px}\n.demo-qr-wrap img{display:block;width:100%;height:auto;border:1px solid var(--line);border-radius:12px;background:white;padding:8px}\n.demo-amount{display:flex;flex-direction:column;gap:4px;padding:13px;margin:12px 0;background:#fff1d4;border-radius:10px}\n.demo-amount span{font-size:11px;color:var(--muted)}\n.demo-amount strong{font-size:24px;color:var(--maroon)}\n.demo-disclaimer{margin:12px 0 0;padding:10px;border-radius:9px;background:#fff1d4;color:#765323!important;font-size:11px!important}\n.demo-qris-success{background:#f2f8ee;border-color:#c9ddbf}\n.demo-qris-success .demo-label{background:#e2f0d9;color:#476c35}\n@media(max-width:640px){.demo-qris-card{padding:14px}.demo-qr-wrap{max-width:210px}}\n'''
if '/* QRIS demo-only payment UI */' not in css:
    css += css_addition
css_path.write_text(css, encoding='utf-8')

# Copy the clearly non-functional QR illustration.
source_svg = ROOT / 'static' / 'images' / 'qris-demo.svg'

if source_svg.resolve() != svg_target.resolve():
    svg_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_svg, svg_target)
elif not svg_target.exists():
    raise FileNotFoundError(f'File QRIS demo tidak ditemukan: {svg_target}')

print('Berhasil memasang patch QRIS SIMULASI.')
print('File asli telah dibuatkan backup dengan akhiran .before_demo_qris.bak')
print('Langkah selanjutnya: tambahkan PAYMENT_DEMO_MODE=True ke .env, lalu jalankan:')
print('  python manage.py check')
print('  python manage.py runserver')
