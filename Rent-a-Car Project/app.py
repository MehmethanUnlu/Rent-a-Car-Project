import os
import secrets
from datetime import datetime, date
from decimal import Decimal

from flask import (Flask, render_template_string, request, redirect,
                   url_for, flash, session, abort)
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
# Gizli bilgiler koda gömülmez; ortam değişkenlerinden okunur.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "database": os.environ.get("DB_NAME", "rentacar_db"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "port": os.environ.get("DB_PORT", "5432"),
}


def get_db_connection():
    return psycopg2.connect(
        **DB_CONFIG,
        cursor_factory=RealDictCursor,
        options="-c client_encoding=UTF8"
    )


# --- Basit CSRF koruması: her POST isteği oturumdaki token'ı taşımak zorunda ---
@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.get("csrf_token")
        if not token or token != request.form.get("csrf_token"):
            abort(400, "Geçersiz veya eksik CSRF belirteci.")


def _csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return session["csrf_token"]


app.jinja_env.globals["csrf_token"] = _csrf_token


def db_error_message(e):
    """Kullanıcıya ham SQL hatası yerine tetikleyicinin/kısıtın mesajını göster."""
    diag = getattr(e, "diag", None)
    return (diag.message_primary if diag and diag.message_primary else "İşlem veritabanı kuralları nedeniyle reddedildi.")


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rent-a-Car Filo Yönetim Sistemi</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">

<nav class="navbar navbar-dark bg-dark mb-4">
    <div class="container">
        <span class="navbar-brand mb-0 h1">Rent-a-Car & Filo Yönetim Sistemi</span>
    </div>
</nav>

<div class="container mb-5">

    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                    {{ message }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Kapat"></button>
                </div>
            {% endfor %}
        {% endif %}
    {% endwith %}

    <!-- Yeni Kiralama Oluşturma Formu -->
    <div class="card shadow-sm mb-4">
        <div class="card-header bg-primary text-white fw-semibold">
            Yeni Kiralama Oluştur
        </div>
        <div class="card-body">
            <form method="POST" action="{{ url_for('create_rental') }}">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                <div class="row g-3">
                    <div class="col-md-4">
                        <label class="form-label">Müşteri</label>
                        <select name="customer_id" class="form-select" required>
                            {% for c in customers %}
                                <option value="{{ c.customer_id }}">{{ c.first_name }} {{ c.last_name }} ({{ c.phone }})</option>
                            {% endfor %}
                        </select>
                    </div>

                    <div class="col-md-4">
                        <label class="form-label">Müsait Araç (alış şubesi = aracın bulunduğu şube)</label>
                        <select name="vehicle_id" class="form-select" required>
                            {% if available_vehicles %}
                                {% for v in available_vehicles %}
                                    <option value="{{ v.vehicle_id }}">
                                        {{ v.plate_number }} - {{ v.brand }} {{ v.model }} ({{ v.category_name }} | {{ v.daily_rate }} ₺/gün | Alış: {{ v.branch_name }})
                                    </option>
                                {% endfor %}
                            {% else %}
                                <option value="" disabled selected>Müsait araç bulunmuyor</option>
                            {% endif %}
                        </select>
                    </div>

                    <div class="col-md-4">
                        <label class="form-label">Ödeme Yöntemi</label>
                        <select name="payment_method" class="form-select" required>
                            <option value="Credit Card">Kredi Kartı (Credit Card)</option>
                            <option value="Debit Card">Banka Kartı (Debit Card)</option>
                            <option value="Cash">Nakit (Cash)</option>
                            <option value="Bank Transfer">Havale / EFT (Bank Transfer)</option>
                        </select>
                    </div>

                    <div class="col-md-4">
                        <label class="form-label">Teslim Şubesi</label>
                        <select name="return_branch_id" class="form-select" required>
                            {% for b in branches %}
                                <option value="{{ b.branch_id }}">{{ b.branch_name }} ({{ b.city }})</option>
                            {% endfor %}
                        </select>
                    </div>

                    <div class="col-md-4">
                        <label class="form-label">Alış Tarihi</label>
                        <input type="date" id="start_date" name="start_date" class="form-control" required>
                    </div>

                    <div class="col-md-4">
                        <label class="form-label">Teslim Tarihi</label>
                        <input type="date" id="end_date" name="end_date" class="form-control" required>
                    </div>

                    <div class="col-12">
                        <label class="form-label d-block">Ek Hizmetler (Opsiyonel)</label>
                        {% for s in services %}
                            <div class="form-check form-check-inline">
                                <input class="form-check-input" type="checkbox" name="service_ids"
                                       id="srv_{{ s.service_id }}" value="{{ s.service_id }}">
                                <label class="form-check-label" for="srv_{{ s.service_id }}">
                                    {{ s.service_name }} (+{{ s.daily_price }} ₺/gün)
                                </label>
                            </div>
                        {% endfor %}
                    </div>

                    <div class="col-12">
                        <button type="submit" class="btn btn-primary" {% if not available_vehicles %}disabled{% endif %}>
                            Kirala
                        </button>
                    </div>
                </div>
            </form>
        </div>
    </div>

    <!-- Aktif Kiralamalar Tablosu -->
    <div class="card shadow-sm mb-4">
        <div class="card-header bg-dark text-white fw-semibold">
            Aktif Kiralamalar (active_rentals_view)
        </div>
        <div class="card-body p-0">
            <div class="table-responsive">
                <table class="table table-striped table-hover mb-0 align-middle">
                    <thead class="table-light">
                        <tr>
                            <th>ID</th>
                            <th>Müşteri</th>
                            <th>Telefon</th>
                            <th>Plaka</th>
                            <th>Araç</th>
                            <th>Alış Şubesi</th>
                            <th>Teslim Şubesi</th>
                            <th>Alış Tarihi</th>
                            <th>Teslim Tarihi</th>
                            <th>Toplam Tutar</th>
                            <th>İşlem</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for r in active_rentals %}
                            <tr>
                                <td>{{ r.rental_id }}</td>
                                <td>{{ r.customer_name }}</td>
                                <td>{{ r.customer_phone }}</td>
                                <td><span class="badge bg-secondary">{{ r.plate_number }}</span></td>
                                <td>{{ r.vehicle_model }} ({{ r.category_name }})</td>
                                <td>{{ r.pickup_branch }}</td>
                                <td>{{ r.return_branch }}</td>
                                <td>{{ r.start_date }}</td>
                                <td>{{ r.end_date }}</td>
                                <td class="fw-semibold">{{ r.total_amount }} ₺</td>
                                <td>
                                    <form method="POST" action="{{ url_for('return_rental', rental_id=r.rental_id) }}" class="d-inline">
                                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                                        <button type="submit" class="btn btn-sm btn-success">Teslim Al</button>
                                    </form>
                                    <form method="POST" action="{{ url_for('cancel_rental', rental_id=r.rental_id) }}" class="d-inline"
                                          onsubmit="return confirm('Kiralama iptal edilsin mi?');">
                                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                                        <button type="submit" class="btn btn-sm btn-outline-danger">İptal</button>
                                    </form>
                                </td>
                            </tr>
                        {% else %}
                            <tr>
                                <td colspan="11" class="text-center text-muted py-3">Aktif kiralama kaydı bulunmuyor.</td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Filo Durumu Tablosu -->
    <div class="card shadow-sm">
        <div class="card-header bg-secondary text-white fw-semibold">
            Filo Durumu (Tüm Araçlar)
        </div>
        <div class="card-body p-0">
            <div class="table-responsive">
                <table class="table table-bordered table-hover mb-0 align-middle">
                    <thead class="table-light">
                        <tr>
                            <th>Plaka</th>
                            <th>Marka / Model</th>
                            <th>Yıl</th>
                            <th>Kategori</th>
                            <th>Günlük Ücret</th>
                            <th>Bulunduğu Şube</th>
                            <th>Kilometre</th>
                            <th>Durum</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for v in all_vehicles %}
                            <tr>
                                <td class="fw-semibold">{{ v.plate_number }}</td>
                                <td>{{ v.brand }} {{ v.model }}</td>
                                <td>{{ v.model_year }}</td>
                                <td>{{ v.category_name }}</td>
                                <td>{{ v.daily_rate }} ₺</td>
                                <td>{{ v.branch_name }}</td>
                                <td>{{ v.mileage }} km</td>
                                <td>
                                    {% if v.status == 'Available' %}
                                        <span class="badge bg-success">Available</span>
                                    {% elif v.status == 'Rented' %}
                                        <span class="badge bg-warning text-dark">Rented</span>
                                    {% else %}
                                        <span class="badge bg-danger">Maintenance</span>
                                    {% endif %}
                                </td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script>
    const startInput = document.getElementById('start_date');
    const endInput = document.getElementById('end_date');
    const today = new Date().toISOString().split('T')[0];
    startInput.min = today;
    endInput.min = today;

    startInput.addEventListener('change', function () {
        endInput.min = this.value;
        if (endInput.value && endInput.value < this.value) {
            endInput.value = this.value;
        }
    });
</script>
</body>
</html>
"""


@app.route("/")
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM customers ORDER BY customer_id;")
        customers = cur.fetchall()

        cur.execute("SELECT * FROM branches ORDER BY branch_id;")
        branches = cur.fetchall()

        cur.execute("SELECT * FROM additional_services ORDER BY service_id;")
        services = cur.fetchall()

        cur.execute("""
            SELECT v.vehicle_id, v.plate_number, v.brand, v.model,
                   vc.category_name, vc.daily_rate, b.branch_name
            FROM vehicles v
            JOIN vehicle_categories vc ON v.category_id = vc.category_id
            JOIN branches b ON v.branch_id = b.branch_id
            WHERE v.status = 'Available'
            ORDER BY v.vehicle_id;
        """)
        available_vehicles = cur.fetchall()

        cur.execute("SELECT * FROM active_rentals_view ORDER BY rental_id;")
        active_rentals = cur.fetchall()

        cur.execute("""
            SELECT v.vehicle_id, v.plate_number, v.brand, v.model, v.model_year,
                   v.mileage, v.status, vc.category_name, vc.daily_rate, b.branch_name
            FROM vehicles v
            JOIN vehicle_categories vc ON v.category_id = vc.category_id
            JOIN branches b ON v.branch_id = b.branch_id
            ORDER BY v.vehicle_id;
        """)
        all_vehicles = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    return render_template_string(
        HTML_TEMPLATE,
        customers=customers,
        branches=branches,
        services=services,
        available_vehicles=available_vehicles,
        active_rentals=active_rentals,
        all_vehicles=all_vehicles
    )


@app.route("/rent", methods=["POST"])
def create_rental():
    try:
        customer_id = int(request.form.get("customer_id", ""))
        vehicle_id = int(request.form.get("vehicle_id", ""))
        return_branch_id = int(request.form.get("return_branch_id", ""))
        service_ids = sorted({int(s) for s in request.form.getlist("service_ids")})
    except ValueError:
        flash("Hata: Formda geçersiz seçim var.", "danger")
        return redirect(url_for("index"))

    payment_method = request.form.get("payment_method", "Credit Card")
    start_date_str = request.form.get("start_date")
    end_date_str = request.form.get("end_date")

    try:
        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        flash("Hata: Lütfen geçerli bir alış ve teslim tarihi seçin.", "danger")
        return redirect(url_for("index"))

    if end_dt < start_dt:
        flash("Hata: Teslim tarihi, alış tarihinden önce olamaz!", "danger")
        return redirect(url_for("index"))
    if start_dt < date.today():
        flash("Hata: Alış tarihi geçmişte olamaz.", "danger")
        return redirect(url_for("index"))

    # Aynı gün teslim de en az 1 günlük ücrete tabidir.
    rental_days = max((end_dt - start_dt).days, 1)

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Aracı kilitle: aynı anda gelen ikinci istek bu satırda bekler (yarış durumu önlenir).
        cur.execute("""
            SELECT vc.daily_rate, v.status, v.branch_id
            FROM vehicles v
            JOIN vehicle_categories vc ON v.category_id = vc.category_id
            WHERE v.vehicle_id = %s
            FOR UPDATE OF v;
        """, (vehicle_id,))
        vehicle = cur.fetchone()

        if not vehicle or vehicle["status"] != "Available":
            conn.rollback()
            flash("Hata: Seçilen araç şu anda müsait değil.", "danger")
            return redirect(url_for("index"))

        # Alış şubesi her zaman aracın fiilen bulunduğu şubedir.
        pickup_branch_id = vehicle["branch_id"]
        daily_rate = Decimal(vehicle["daily_rate"])
        extra_daily_cost = Decimal("0")

        if service_ids:
            cur.execute(
                "SELECT service_id, daily_price FROM additional_services WHERE service_id = ANY(%s);",
                (service_ids,)
            )
            selected_services = cur.fetchall()
            if len(selected_services) != len(service_ids):
                conn.rollback()
                flash("Hata: Geçersiz ek hizmet seçimi.", "danger")
                return redirect(url_for("index"))
            extra_daily_cost = sum((Decimal(s["daily_price"]) for s in selected_services), Decimal("0"))

        total_amount = (daily_rate + extra_daily_cost) * rental_days

        cur.execute("""
            INSERT INTO rentals (
                customer_id, vehicle_id, pickup_branch_id, return_branch_id,
                start_date, end_date, total_amount, status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Active')
            RETURNING rental_id;
        """, (customer_id, vehicle_id, pickup_branch_id, return_branch_id,
              start_dt, end_dt, total_amount))
        new_rental_id = cur.fetchone()["rental_id"]

        for sid in service_ids:
            cur.execute(
                "INSERT INTO rental_services (rental_id, service_id, quantity) VALUES (%s, %s, 1);",
                (new_rental_id, sid)
            )

        cur.execute("""
            INSERT INTO payments (rental_id, amount, payment_method, payment_status)
            VALUES (%s, %s, %s, 'Paid');
        """, (new_rental_id, total_amount, payment_method))

        conn.commit()
        flash(f"Kiralama kaydı (#{new_rental_id}) oluşturuldu. Toplam tutar: {total_amount:.2f} ₺", "success")

    except psycopg2.Error as e:
        conn.rollback()
        flash(f"Veritabanı hatası: {db_error_message(e)}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("index"))


@app.route("/return/<int:rental_id>", methods=["POST"])
def return_rental(rental_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE rentals
               SET status = 'Completed',
                   actual_return_date = GREATEST(CURRENT_DATE, start_date)
             WHERE rental_id = %s AND status = 'Active';
        """, (rental_id,))
        updated = cur.rowcount
        conn.commit()
        if updated:
            flash(f"#{rental_id} numaralı kiralama teslim alındı; araç Available oldu ve teslim şubesine taşındı.", "info")
        else:
            flash(f"#{rental_id} numaralı kiralama aktif değil; işlem yapılmadı.", "warning")
    except psycopg2.Error as e:
        conn.rollback()
        flash(f"Teslim alma sırasında veritabanı hatası: {db_error_message(e)}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("index"))


@app.route("/cancel/<int:rental_id>", methods=["POST"])
def cancel_rental(rental_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE rentals SET status = 'Cancelled' WHERE rental_id = %s AND status = 'Active';",
                    (rental_id,))
        updated = cur.rowcount
        if updated:
            cur.execute("UPDATE payments SET payment_status = 'Refunded' WHERE rental_id = %s AND payment_status = 'Paid';",
                        (rental_id,))
        conn.commit()
        if updated:
            flash(f"#{rental_id} numaralı kiralama iptal edildi, ödeme iade olarak işaretlendi.", "info")
        else:
            flash(f"#{rental_id} numaralı kiralama aktif değil; işlem yapılmadı.", "warning")
    except psycopg2.Error as e:
        conn.rollback()
        flash(f"İptal sırasında veritabanı hatası: {db_error_message(e)}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("index"))


if __name__ == "__main__":
    # debug=True yalnızca geliştirme içindir; ortam değişkeniyle açılır.
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")