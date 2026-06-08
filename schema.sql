BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS dim_fund (
    fund_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code TEXT NOT NULL UNIQUE,
    fund_name TEXT,
    fund_house TEXT,
    category TEXT,
    subcategory TEXT,
    risk_grade TEXT,
    expense_ratio REAL,
    aum REAL
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_id INTEGER PRIMARY KEY,
    date TEXT NOT NULL UNIQUE,
    year INTEGER,
    quarter TEXT,
    month INTEGER,
    month_name TEXT,
    day INTEGER,
    weekday INTEGER,
    weekday_name TEXT,
    week_of_year INTEGER
);

CREATE TABLE IF NOT EXISTS fact_nav (
    nav_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code TEXT NOT NULL,
    date_id INTEGER NOT NULL,
    nav REAL,
    source TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
);

CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code TEXT,
    date_id INTEGER,
    transaction_type TEXT,
    amount REAL,
    units REAL,
    price REAL,
    state TEXT,
    kyc_status TEXT,
    investor_id TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
);

CREATE TABLE IF NOT EXISTS fact_performance (
    performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code TEXT,
    date_id INTEGER,
    return_1m REAL,
    return_3m REAL,
    return_6m REAL,
    return_1y REAL,
    return_3y REAL,
    return_5y REAL,
    expense_ratio REAL,
    aum REAL,
    anomaly_flag INTEGER,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
);

CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code TEXT,
    date_id INTEGER,
    aum_value REAL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
);

COMMIT;
