import os
import sys
import psycopg2

DB = dict(
    host=os.environ.get("DB_HOST", "localhost"),
    dbname=os.environ.get("DB_NAME", "rentacar_db"),
    user=os.environ.get("DB_USER", "postgres"),
    password=os.environ.get("DB_PASSWORD", ""),
    port=os.environ.get("DB_PORT", "5432"),
)
HERE = os.path.dirname(os.path.abspath(__file__))

try:
    conn = psycopg2.connect(**DB, options="-c client_encoding=UTF8")
except psycopg2.OperationalError as e:
    # rentacar_db yoksa oluşturmayı dene
    if "does not exist" in str(e):
        admin = psycopg2.connect(**{**DB, "dbname": "postgres"})
        admin.autocommit = True
        admin.cursor().execute("CREATE DATABASE %s ENCODING 'UTF8' TEMPLATE template0" % DB["dbname"])
        admin.close()
        conn = psycopg2.connect(**DB, options="-c client_encoding=UTF8")
    else:
        sys.exit("Bağlantı hatası: %s" % e)

try:
    with conn, conn.cursor() as cur:
        for name in ("schema.sql", "seed.sql"):
            with open(os.path.join(HERE, name), encoding="utf-8") as f:
                cur.execute(f.read())
            print(name, "yüklendi.")
        cur.execute("SELECT plate_number, status FROM vehicles ORDER BY vehicle_id")
        for row in cur.fetchall():
            print(" ", row)
    print("Tamam. Şimdi: python app.py")
except Exception as e:
    sys.exit("Hata: %s" % e)
finally:
    conn.close()
