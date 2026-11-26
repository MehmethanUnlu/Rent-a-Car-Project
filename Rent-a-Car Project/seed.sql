SET client_encoding = 'UTF8';

-- 1. Şubeler
INSERT INTO branches (branch_name, city, address, phone) VALUES
('Sabiha Gökçen Havalimanı', 'İstanbul', 'Sanayi Mah. Havaalanı İç Hatlar Terminali, Pendik', '02165550101'),
('Kadıköy Merkez', 'İstanbul', 'Söğütlüçeşme Cad. No:42, Kadıköy', '02165550202'),
('Dalaman Havalimanı', 'Muğla', 'Ege Mah. Havalimanı Yolu No:10, Dalaman', '02525550303');

-- 2. Araç Kategorileri
INSERT INTO vehicle_categories (category_name, daily_rate, deposit_amount) VALUES
('Ekonomik', 1400.00, 3000.00),
('Sedan', 1950.00, 4500.00),
('SUV', 3200.00, 7500.00);

-- 3. Araçlar (34DEF202 aktif kiralama eklendiğinde trigger ile otomatik 'Rented' olur;
--    34ABC101 geçmiş kiralamada Kadıköy'e (şube 2) bırakıldığı için konumu şube 2'dir)
INSERT INTO vehicles (plate_number, brand, model, model_year, status, mileage, category_id, branch_id) VALUES
('34ABC101', 'Renault', 'Clio', 2023, 'Available', 24500, 1, 2),
('34DEF202', 'Toyota', 'Corolla', 2024, 'Available', 15200, 2, 1),
('34GHI303', 'Peugeot', '3008', 2023, 'Available', 31800, 3, 2),
('48JKL404', 'Nissan', 'Qashqai', 2022, 'Maintenance', 54100, 3, 3);

-- 4. Müşteriler
INSERT INTO customers (first_name, last_name, national_id, driver_license_no, phone, email) VALUES
('Ahmet', 'Yılmaz', '12345678901', 'B-987654', '05321112233', 'ahmet.yilmaz@example.com'),
('Zeynep', 'Kaya', '23456789012', 'B-876543', '05332223344', 'zeynep.kaya@example.com'),
('Mehmet', 'Demir', '34567890123', 'B-765432', '05343334455', 'mehmet.demir@example.com');

-- 5. Ek Hizmetler
INSERT INTO additional_services (service_name, daily_price) VALUES
('Tam Kasko Paketi', 350.00),
('Bebek Koltuğu', 150.00),
('GPS Navigasyon', 100.00);

-- 6. Kiralama Kayıtları
INSERT INTO rentals (customer_id, vehicle_id, pickup_branch_id, return_branch_id, start_date, end_date, actual_return_date, total_amount, status) VALUES
(1, 2, 1, 1, '2026-11-25', '2026-11-28', NULL, 7350.00, 'Active'),
(2, 1, 1, 2, '2026-11-10', '2026-11-13', '2026-11-13', 4200.00, 'Completed');

-- 7. Kiralama Ek Hizmetleri
INSERT INTO rental_services (rental_id, service_id, quantity) VALUES
(1, 1, 1),
(1, 2, 1);

-- 8. Ödemeler
INSERT INTO payments (rental_id, payment_date, amount, payment_method, payment_status) VALUES
(1, '2026-11-25 10:15:00', 7350.00, 'Credit Card', 'Paid'),
(2, '2026-11-10 14:30:00', 4200.00, 'Debit Card', 'Paid');

-- 9. Bakım Kayıtları
INSERT INTO maintenance_records (vehicle_id, maintenance_date, description, cost) VALUES
(3, '2026-10-15', '30.000 km periyodik bakım ve fren balatası değişimi', 8500.00),
(4, '2026-11-20', 'Şanzıman sensör kontrolü ve yağ değişimi', 12400.00);