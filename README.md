# Rent-a-Car and Fleet Management System

**Course:** Database Systems  
**Student:** Mehmethan Ünlü (202303001089)  
**Department:** Department of Computer Engineering, Doğuş University  

## Overview

This project is a relational database and web-based fleet management system developed using **PostgreSQL 19** and **Python 3 (Flask, psycopg2, Bootstrap 5)**. The database schema is normalized to Third Normal Form (3NF) and enforces core operational rules directly at the database layer using `CHECK` constraints, `UNIQUE` constraints, referential integrity rules (`ON DELETE RESTRICT` / `CASCADE`), a partial unique index (`uq_one_active_rental_per_vehicle`), an operational view (`active_rentals_view`), and two-stage triggers (`BEFORE` and `AFTER`).

## Repository Structure

- `schema.sql` - Physical DDL definitions for the 9 core tables, B-Tree and partial unique indexes, `active_rentals_view`, and trigger functions (`check_vehicle_available_for_rental`, `update_vehicle_status_on_rental`).
- `seed.sql` - Initial sample dataset containing 3 branches, 3 vehicle categories, 4 vehicles, 3 customers, 3 additional services, sample rentals, payments, and maintenance records.
- `setup_db.py` - Automated setup script that creates `rentacar_db` (if it does not exist) and executes `schema.sql` followed by `seed.sql`.
- `queries.sql` - 7 analytical and reporting SQL queries demonstrating joins, aggregations, `DISTINCT ON`, views, `HAVING`, and correlated subqueries.
- `app.py` - Flask web application providing vehicle listing, rental creation with row-level locking (`FOR UPDATE`), vehicle returns with automatic branch transfer, and rental cancellation with payment refund.
- `test_trigger.py` - Standalone database verification script testing trigger enforcement against double booking and renting vehicles under maintenance (uses `ROLLBACK` to leave the database unchanged).
- `baslat.bat` - Convenience startup script configured for the local Windows development environment.

## Prerequisites

- **PostgreSQL** (version 16 or higher, tested on PostgreSQL 19) running locally
- **Python** 3.10 or higher
- Required Python libraries:
  ```bash
  pip install flask psycopg2-binary
  ```

## Setup and Running Instructions

### 1. Configure Database Connection (Environment Variables)

By default, the scripts connect to `localhost:5432` using database `rentacar_db` and user `postgres`. Set your PostgreSQL password via the `DB_PASSWORD` environment variable before running the scripts:

- **Windows (Command Prompt):**
  ```cmd
  set DB_PASSWORD=your_postgres_password
  ```
- **Windows (PowerShell):**
  ```powershell
  $env:DB_PASSWORD="your_postgres_password"
  ```
- **Linux / macOS:**
  ```bash
  export DB_PASSWORD="your_postgres_password"
  ```

*(Optional variables: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `FLASK_SECRET_KEY`)*

### 2. Initialize the Database

Run `setup_db.py` to create `rentacar_db`, apply the schema, and load the initial dataset:

```bash
python setup_db.py
```

### 3. Start the Web Application

Launch the Flask server:

```bash
python app.py
```

Once running, open your browser and navigate to:
`http://127.0.0.1:5000`

## Running Analytical Queries and Trigger Tests

- **Execute the 7 analytical SQL queries via `psql`:**
  ```bash
  psql -U postgres -d rentacar_db -f queries.sql
  ```
- **Run the standalone database trigger test:**
  ```bash
  python test_trigger.py
  ```

## Note on `baslat.bat`

`baslat.bat` contains local file paths specific to the author's Windows environment (`C:\Users\Mehmethan\...`). When running the project on another machine, please follow the standard Python setup steps (`setup_db.py` and `app.py`) described above.