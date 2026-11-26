SET client_encoding = 'UTF8';

-- Sorgu 1: Müsait Durumdaki Araçların Kategori ve Şube Bilgileriyle Listelenmesi
SELECT v.plate_number, v.brand, v.model, v.model_year,
       vc.category_name, vc.daily_rate, b.branch_name, b.city
FROM vehicles v
JOIN vehicle_categories vc ON v.category_id = vc.category_id
JOIN branches b ON v.branch_id = b.branch_id
WHERE v.status = 'Available'
ORDER BY vc.daily_rate ASC;

-- Sorgu 2: Şube Bazlı Toplam Kiralama Sayısı ve Gelir Analizi
-- LEFT JOIN: hiç kiralaması olmayan şubeler de 0 ile listelenir.
-- Durum filtresi WHERE yerine ON içinde olmalı; aksi halde LEFT JOIN INNER JOIN'e dönüşür.
SELECT b.branch_name,
       COUNT(r.rental_id) AS total_rentals,
       COALESCE(SUM(r.total_amount), 0) AS total_revenue
FROM branches b
LEFT JOIN rentals r ON b.branch_id = r.pickup_branch_id
                   AND r.status IN ('Active', 'Completed')
GROUP BY b.branch_id, b.branch_name
ORDER BY total_revenue DESC;

-- Sorgu 3: Kiralamalarda Seçilen Ek Hizmetler ve Günlük Ek Maliyetleri (M:N İlişki Sorgusu)
SELECT r.rental_id,
       c.first_name || ' ' || c.last_name AS customer,
       STRING_AGG(s.service_name, ', ' ORDER BY s.service_id) AS selected_services,
       SUM(s.daily_price * rs.quantity) AS daily_extra_cost
FROM rentals r
JOIN customers c ON r.customer_id = c.customer_id
JOIN rental_services rs ON r.rental_id = rs.rental_id
JOIN additional_services s ON rs.service_id = s.service_id
GROUP BY r.rental_id, c.first_name, c.last_name
ORDER BY r.rental_id;

-- Sorgu 4: Bakımda Olan Araçların SON Bakım Kaydı
-- (DISTINCT ON: her araç için yalnızca en yeni bakım kaydı)
SELECT DISTINCT ON (v.vehicle_id)
       v.plate_number, v.brand, v.model,
       m.maintenance_date, m.description, m.cost
FROM vehicles v
JOIN maintenance_records m ON v.vehicle_id = m.vehicle_id
WHERE v.status = 'Maintenance'
ORDER BY v.vehicle_id, m.maintenance_date DESC;

-- Sorgu 5: Aktif Kiralamalar Görünümü (VIEW) Sorgusu
SELECT * FROM active_rentals_view;

-- Sorgu 6: Müşteri Bazlı Toplam Ödeme (GROUP BY + HAVING)
SELECT c.first_name || ' ' || c.last_name AS customer,
       COUNT(DISTINCT r.rental_id) AS rental_count,
       SUM(p.amount) AS total_paid
FROM customers c
JOIN rentals r ON c.customer_id = r.customer_id
JOIN payments p ON r.rental_id = p.rental_id
WHERE p.payment_status = 'Paid'
GROUP BY c.customer_id, c.first_name, c.last_name
HAVING SUM(p.amount) > 4000
ORDER BY total_paid DESC;

-- Sorgu 7: Hiç Kiralanmamış Araçlar (Alt Sorgu / NOT EXISTS)
SELECT v.plate_number, v.brand, v.model, v.status
FROM vehicles v
WHERE NOT EXISTS (SELECT 1 FROM rentals r WHERE r.vehicle_id = v.vehicle_id);
