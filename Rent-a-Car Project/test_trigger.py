import getpass
import os
import sys
from datetime import date, timedelta

import psycopg2

DB = dict(
    host=os.environ.get("DB_HOST", "localhost"),
    dbname=os.environ.get("DB_NAME", "rentacar_db"),
    user=os.environ.get("DB_USER", "postgres"),
    password=os.environ.get("DB_PASSWORD") or getpass.getpass("PostgreSQL parolası: "),
    port=os.environ.get("DB_PORT", "5432"),
)

INSERT_SQL = """
    INSERT INTO rentals (customer_id, vehicle_id, pickup_branch_id, return_branch_id,
                         start_date, end_date, total_amount, status)
    VALUES (1, %s, %s, %s, %s, %s, 1000, 'Active')
"""


def try_insert(cur, vehicle):
    """Kiralama eklemeyi dener; (başarılı_mı, mesaj) döndürür. Hata olursa savepoint'e döner."""
    vid, _, branch = vehicle
    start = date.today()
    cur.execute("SAVEPOINT deneme")
    try:
        cur.execute(INSERT_SQL, (vid, branch, branch, start, start + timedelta(days=1)))
        return True, "kayıt eklendi"
    except psycopg2.Error as e:
        cur.execute("ROLLBACK TO SAVEPOINT deneme")
        msg = e.diag.message_primary or str(e)
        return False, msg


def vehicle_status(cur, vid):
    cur.execute("SELECT status FROM vehicles WHERE vehicle_id = %s", (vid,))
    return cur.fetchone()[0]


def main():
    try:
        conn = psycopg2.connect(**DB, options="-c client_encoding=UTF8")
    except psycopg2.OperationalError as e:
        sys.exit("Bağlantı hatası: %s" % e)

    try:
        cur = conn.cursor()
        cur.execute("SELECT vehicle_id, plate_number, branch_id FROM vehicles "
                    "WHERE status = 'Available' ORDER BY vehicle_id LIMIT 1")
        avail = cur.fetchone()
        cur.execute("SELECT vehicle_id, plate_number, branch_id FROM vehicles "
                    "WHERE status = 'Maintenance' ORDER BY vehicle_id LIMIT 1")
        maint = cur.fetchone()
        if not avail:
            sys.exit("Müsait araç yok. Önce bir kiralamayı teslim al/iptal et ya da setup_db.py çalıştır.")

        print("=" * 70)
        print("TETİKLEYİCİ TESTİ (trg_rental_check_available)")
        print("=" * 70)

        print(f"\nTest A: Müsait araç ({avail[1]}) için aktif kiralama ekleniyor...")
        ok, msg = try_insert(cur, avail)
        print(f"  Sonuç : {'BAŞARILI' if ok else 'REDDEDİLDİ'} - {msg}")
        print(f"  Araç durumu: {vehicle_status(cur, avail[0])}")

        print(f"\nTest B: Aynı araç ({avail[1]}) için İKİNCİ aktif kiralama deneniyor...")
        ok, msg = try_insert(cur, avail)
        print(f"  Sonuç : {'BAŞARILI (BEKLENMEYEN!)' if ok else 'REDDEDİLDİ'} - {msg}")

        if maint:
            print(f"\nTest C: Bakımdaki araç ({maint[1]}) için kiralama deneniyor...")
            ok, msg = try_insert(cur, maint)
            print(f"  Sonuç : {'BAŞARILI (BEKLENMEYEN!)' if ok else 'REDDEDİLDİ'} - {msg}")
        else:
            print("\nTest C atlandı: bakımda araç yok.")

        print("\nTüm deneme kayıtları geri alınıyor (ROLLBACK)...")
    finally:
        conn.rollback()
        conn.close()
    print("Tamam. Veritabanında hiçbir değişiklik kalmadı.")


if __name__ == "__main__":
    main()
