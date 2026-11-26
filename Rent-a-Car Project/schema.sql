SET client_encoding = 'UTF8';

DROP VIEW IF EXISTS active_rentals_view CASCADE;
DROP TABLE IF EXISTS maintenance_records CASCADE;
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS rental_services CASCADE;
DROP TABLE IF EXISTS additional_services CASCADE;
DROP TABLE IF EXISTS rentals CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS vehicles CASCADE;
DROP TABLE IF EXISTS vehicle_categories CASCADE;
DROP TABLE IF EXISTS branches CASCADE;
DROP FUNCTION IF EXISTS update_vehicle_status_on_rental() CASCADE;
DROP FUNCTION IF EXISTS check_vehicle_available_for_rental() CASCADE;

-- 1. Şubeler
CREATE TABLE branches (
    branch_id SERIAL PRIMARY KEY,
    branch_name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    address TEXT NOT NULL,
    phone VARCHAR(20) NOT NULL
);

-- 2. Araç Kategorileri
CREATE TABLE vehicle_categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(50) UNIQUE NOT NULL,
    daily_rate NUMERIC(10, 2) NOT NULL CHECK (daily_rate > 0),
    deposit_amount NUMERIC(10, 2) NOT NULL CHECK (deposit_amount >= 0)
);

-- 3. Araçlar
CREATE TABLE vehicles (
    vehicle_id SERIAL PRIMARY KEY,
    plate_number VARCHAR(15) UNIQUE NOT NULL,
    brand VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    model_year INT NOT NULL CHECK (model_year >= 2015),
    status VARCHAR(20) NOT NULL DEFAULT 'Available'
        CHECK (status IN ('Available', 'Rented', 'Maintenance')),
    mileage INT NOT NULL DEFAULT 0 CHECK (mileage >= 0),
    category_id INT NOT NULL REFERENCES vehicle_categories(category_id) ON DELETE RESTRICT,
    branch_id INT NOT NULL REFERENCES branches(branch_id) ON DELETE RESTRICT
);

-- 4. Müşteriler
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    national_id CHAR(11) UNIQUE NOT NULL CHECK (national_id ~ '^[0-9]{11}$'),
    driver_license_no VARCHAR(20) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL CHECK (email LIKE '%_@_%._%')
);

-- 5. Kiralama İşlemleri
-- end_date: planlanan teslim tarihi, actual_return_date: gerçek teslim tarihi
CREATE TABLE rentals (
    rental_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT,
    vehicle_id INT NOT NULL REFERENCES vehicles(vehicle_id) ON DELETE RESTRICT,
    pickup_branch_id INT NOT NULL REFERENCES branches(branch_id) ON DELETE RESTRICT,
    return_branch_id INT NOT NULL REFERENCES branches(branch_id) ON DELETE RESTRICT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    actual_return_date DATE,
    total_amount NUMERIC(10, 2) NOT NULL CHECK (total_amount >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'Active'
        CHECK (status IN ('Active', 'Completed', 'Cancelled')),
    CONSTRAINT chk_rental_dates CHECK (end_date >= start_date),
    CONSTRAINT chk_actual_return CHECK (actual_return_date IS NULL OR actual_return_date >= start_date)
);

-- 6. Ek Hizmetler
CREATE TABLE additional_services (
    service_id SERIAL PRIMARY KEY,
    service_name VARCHAR(80) UNIQUE NOT NULL,
    daily_price NUMERIC(10, 2) NOT NULL CHECK (daily_price >= 0)
);

-- 7. Kiralama - Ek Hizmet Ara Tablosu (M:N)
CREATE TABLE rental_services (
    rental_id INT NOT NULL REFERENCES rentals(rental_id) ON DELETE CASCADE,
    service_id INT NOT NULL REFERENCES additional_services(service_id) ON DELETE RESTRICT,
    quantity INT NOT NULL DEFAULT 1 CHECK (quantity > 0),
    PRIMARY KEY (rental_id, service_id)
);

-- 8. Ödemeler (mali kayıt olduğu için kiralama silinse bile sessizce silinmesin: RESTRICT)
CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    rental_id INT NOT NULL REFERENCES rentals(rental_id) ON DELETE RESTRICT,
    payment_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    amount NUMERIC(10, 2) NOT NULL CHECK (amount > 0),
    payment_method VARCHAR(30) NOT NULL
        CHECK (payment_method IN ('Credit Card', 'Debit Card', 'Cash', 'Bank Transfer')),
    payment_status VARCHAR(20) NOT NULL DEFAULT 'Paid'
        CHECK (payment_status IN ('Paid', 'Pending', 'Refunded'))
);

-- 9. Bakım Kayıtları
CREATE TABLE maintenance_records (
    maintenance_id SERIAL PRIMARY KEY,
    vehicle_id INT NOT NULL REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
    maintenance_date DATE NOT NULL,
    description TEXT NOT NULL,
    cost NUMERIC(10, 2) NOT NULL CHECK (cost >= 0)
);

-- Performans İndeksleri
CREATE INDEX idx_vehicles_status ON vehicles(status);
CREATE INDEX idx_rentals_status ON rentals(status);
-- PostgreSQL yabancı anahtar sütunlarına otomatik indeks oluşturmaz
CREATE INDEX idx_rentals_vehicle ON rentals(vehicle_id);
CREATE INDEX idx_rentals_customer ON rentals(customer_id);
CREATE INDEX idx_payments_rental ON payments(rental_id);
CREATE INDEX idx_maintenance_vehicle ON maintenance_records(vehicle_id);

-- Bir araç için aynı anda yalnızca BİR aktif kiralama olabilir (çift kiralamaya karşı ikinci güvence)
CREATE UNIQUE INDEX uq_one_active_rental_per_vehicle
    ON rentals(vehicle_id) WHERE status = 'Active';

-- Aktif Kiralamalar Görünümü (VIEW)
CREATE VIEW active_rentals_view AS
SELECT
    r.rental_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.phone AS customer_phone,
    v.plate_number,
    v.brand || ' ' || v.model AS vehicle_model,
    vc.category_name,
    b.branch_name AS pickup_branch,
    rb.branch_name AS return_branch,
    r.start_date,
    r.end_date,
    r.total_amount
FROM rentals r
JOIN customers c ON r.customer_id = c.customer_id
JOIN vehicles v ON r.vehicle_id = v.vehicle_id
JOIN vehicle_categories vc ON v.category_id = vc.category_id
JOIN branches b ON r.pickup_branch_id = b.branch_id
JOIN branches rb ON r.return_branch_id = rb.branch_id
WHERE r.status = 'Active';

-- TETİKLEYİCİ 1 (BEFORE): Yalnızca 'Available' araç aktif kiralamaya alınabilir.
-- FOR UPDATE ile araç satırı kilitlenir; eşzamanlı iki kiralama isteği sıraya girer.
CREATE OR REPLACE FUNCTION check_vehicle_available_for_rental()
RETURNS TRIGGER AS $$
DECLARE
    v_status TEXT;
BEGIN
    IF NEW.status = 'Active' AND (TG_OP = 'INSERT' OR OLD.status <> 'Active') THEN
        SELECT status INTO v_status FROM vehicles WHERE vehicle_id = NEW.vehicle_id FOR UPDATE;
        IF v_status IS DISTINCT FROM 'Available' THEN
            RAISE EXCEPTION 'Araç (id=%) kiralanamaz: mevcut durum = %', NEW.vehicle_id, COALESCE(v_status, 'bulunamadı');
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_rental_check_available
BEFORE INSERT OR UPDATE OF status ON rentals
FOR EACH ROW
EXECUTE FUNCTION check_vehicle_available_for_rental();

-- TETİKLEYİCİ 2 (AFTER): Araç durumunu ve konumunu otomatik günceller.
--  * Yeni Active kayıt          -> araç 'Rented'
--  * Active -> Completed        -> araç 'Available' + araç teslim şubesine taşınır
--  * Active -> Cancelled        -> araç 'Available'
-- Geçmişe dönük (Completed/Cancelled) kayıt eklemek aracın güncel durumunu değiştirmez.
CREATE OR REPLACE FUNCTION update_vehicle_status_on_rental()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'Active' AND (TG_OP = 'INSERT' OR OLD.status <> 'Active') THEN
        UPDATE vehicles SET status = 'Rented' WHERE vehicle_id = NEW.vehicle_id;
    ELSIF TG_OP = 'UPDATE' AND OLD.status = 'Active' AND NEW.status = 'Completed' THEN
        UPDATE vehicles
           SET status = 'Available', branch_id = NEW.return_branch_id
         WHERE vehicle_id = NEW.vehicle_id;
    ELSIF TG_OP = 'UPDATE' AND OLD.status = 'Active' AND NEW.status = 'Cancelled' THEN
        UPDATE vehicles SET status = 'Available' WHERE vehicle_id = NEW.vehicle_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_rental_status_change
AFTER INSERT OR UPDATE OF status ON rentals
FOR EACH ROW
EXECUTE FUNCTION update_vehicle_status_on_rental();
