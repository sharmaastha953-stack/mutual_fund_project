import re
from pathlib import Path
from typing import Optional, Union

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / 'data' / 'raw'
PROCESSED_DIR = ROOT / 'data' / 'processed'
SQL_DIR = ROOT / 'sql'
DB_PATH = ROOT / 'bluestock_mf.db'
SCHEMA_PATH = ROOT / 'schema.sql'

VALID_TRANSACTION_TYPES = {
    'sip': 'SIP',
    'systematic investment plan': 'SIP',
    'systematic investment': 'SIP',
    's i p': 'SIP',
    'lumpsum': 'LUMPSUM',
    'lump sum': 'LUMPSUM',
    'lump-sum': 'LUMPSUM',
    'one time': 'LUMPSUM',
    'redemption': 'REDEMPTION',
    'sell': 'REDEMPTION',
    'withdrawal': 'REDEMPTION',
}

VALID_KYC_STATUSES = {
    'pending',
    'approved',
    'verified',
    'rejected',
    'registered',
    'disabled',
}


def ensure_directories() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    SQL_DIR.mkdir(parents=True, exist_ok=True)


def choose_column(df: pd.DataFrame, keywords: list[str]) -> Optional[str]:
    lower = {col.lower(): col for col in df.columns}
    for keyword in keywords:
        for col_name, original in lower.items():
            if keyword in col_name:
                return original
    return None


def normalize_expense_ratio(value: Union[float, str, int]) -> float:
    try:
        ratio = float(str(value).replace('%', '').strip())
    except (TypeError, ValueError):
        return float('nan')

    if ratio > 2.5 and ratio <= 100:
        ratio = ratio / 100.0
    if 0.001 <= ratio <= 2.5:
        return ratio
    return np.nan


def clean_nav_history() -> pd.DataFrame | None:
    path = RAW_DIR / 'nav_history.csv'
    if not path.exists():
        print('nav_history.csv not found in data/raw/. Skipping NAV cleaning.')
        return None

    df = pd.read_csv(path)
    code_col = choose_column(df, ['amfi', 'scheme code', 'scheme_code', 'code'])
    date_col = choose_column(df, ['date'])
    nav_col = choose_column(df, ['nav', 'nav_value', 'net asset value'])

    if code_col is None or date_col is None or nav_col is None:
        raise ValueError('nav_history.csv must contain AMFI code, date, and NAV columns.')

    df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
    df = df.dropna(subset=[code_col, date_col])
    df[code_col] = df[code_col].astype(str).str.strip()
    df[nav_col] = pd.to_numeric(df[nav_col], errors='coerce')
    df = df[df[nav_col] > 0]

    cleaned = []
    for amfi_code, group in df.groupby(code_col, sort=True):
        group = group.drop_duplicates(subset=[date_col], keep='last').set_index(date_col).sort_index()
        all_days = pd.date_range(group.index.min(), group.index.max(), freq='D')
        group = group.reindex(all_days)
        group[code_col] = amfi_code
        group[nav_col] = group[nav_col].ffill()
        group = group.reset_index().rename(columns={'index': date_col})
        cleaned.append(group)

    result = pd.concat(cleaned, ignore_index=True)
    result = result.drop_duplicates(subset=[code_col, date_col], keep='last')
    result = result.sort_values([code_col, date_col])
    result = result.rename(columns={code_col: 'amfi_code', date_col: 'date', nav_col: 'nav'})
    result['date'] = pd.to_datetime(result['date'], errors='coerce')
    result = result[result['nav'] > 0]
    result.to_csv(PROCESSED_DIR / 'nav_history_cleaned.csv', index=False)
    print(f'Wrote cleaned NAV history to {PROCESSED_DIR / "nav_history_cleaned.csv"}')
    return result


def standardize_transaction_type(value: str) -> str:
    if not isinstance(value, str):
        return 'UNKNOWN'
    cleaned = value.strip().lower()
    return VALID_TRANSACTION_TYPES.get(cleaned, VALID_TRANSACTION_TYPES.get(re.sub(r'[^a-z0-9]+', ' ', cleaned).strip(), 'UNKNOWN'))


def standardize_kyc_status(value: str) -> str:
    if not isinstance(value, str):
        return 'Unknown'
    normalized = value.strip().lower()
    if normalized in VALID_KYC_STATUSES:
        return normalized.title()
    return 'Unknown'


def clean_investor_transactions() -> pd.DataFrame | None:
    path = RAW_DIR / 'investor_transactions.csv'
    if not path.exists():
        print('investor_transactions.csv not found in data/raw/. Skipping transactions cleaning.')
        return None

    df = pd.read_csv(path)
    date_col = choose_column(df, ['date', 'transaction_date', 'trade_date'])
    amount_col = choose_column(df, ['amount', 'transaction amount', 'folio value'])
    type_col = choose_column(df, ['transaction_type', 'transaction type', 'type'])
    kyc_col = choose_column(df, ['kyc', 'kyc_status', 'kyc status'])
    state_col = choose_column(df, ['state', 'region'])
    fund_col = choose_column(df, ['amfi', 'fund code', 'scheme code', 'scheme_code', 'code'])
    investor_col = choose_column(df, ['investor', 'investor_id', 'client_id'])

    if date_col is None or amount_col is None or type_col is None:
        raise ValueError('investor_transactions.csv must contain date, amount, and transaction_type columns.')

    df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
    df = df.dropna(subset=[date_col, amount_col, type_col])
    df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce')
    df = df[df[amount_col] > 0]
    df[type_col] = df[type_col].apply(standardize_transaction_type)
    df[kyc_col] = df[kyc_col].apply(standardize_kyc_status) if kyc_col else 'Unknown'

    cleaned = pd.DataFrame({
        'transaction_date': df[date_col],
        'amount': df[amount_col],
        'transaction_type': df[type_col],
        'kyc_status': df[kyc_col] if kyc_col else 'Unknown',
        'state': df[state_col] if state_col else None,
        'amfi_code': df[fund_col] if fund_col else None,
        'investor_id': df[investor_col] if investor_col else None,
    })

    if 'units' in df.columns:
        cleaned['units'] = pd.to_numeric(df['units'], errors='coerce')
    if 'price' in df.columns:
        cleaned['price'] = pd.to_numeric(df['price'], errors='coerce')

    cleaned = cleaned.sort_values(['amfi_code', 'transaction_date'])
    cleaned.to_csv(PROCESSED_DIR / 'investor_transactions_cleaned.csv', index=False)
    print(f'Wrote cleaned transactions to {PROCESSED_DIR / "investor_transactions_cleaned.csv"}')
    return cleaned


def clean_scheme_performance() -> pd.DataFrame | None:
    path = RAW_DIR / 'scheme_performance.csv'
    if not path.exists():
        print('scheme_performance.csv not found in data/raw/. Skipping performance cleaning.')
        return None

    df = pd.read_csv(path)
    expense_col = choose_column(df, ['expense_ratio', 'expense ratio', 'expense'])
    if expense_col is None:
        raise ValueError('scheme_performance.csv must contain an expense ratio column.')

    return_cols = [col for col in df.columns if 'return' in col.lower() or '%' in col]
    for col in return_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df['expense_ratio'] = df[expense_col].apply(normalize_expense_ratio)
    df['expense_ratio_flag'] = df['expense_ratio'].apply(lambda x: x < 0.001 or x > 2.5)
    df['performance_note'] = np.where(df[return_cols].isna().any(axis=1), 'non-numeric return values present', 'ok')

    renamed = {
        expense_col: 'expense_ratio'
    }
    df = df.rename(columns=renamed)
    output_cols = ['amfi_code', 'expense_ratio', 'expense_ratio_flag', 'performance_note'] + return_cols
    output_cols = [col for col in output_cols if col in df.columns]
    cleaned = df[output_cols].copy()
    cleaned.to_csv(PROCESSED_DIR / 'scheme_performance_cleaned.csv', index=False)
    print(f'Wrote cleaned performance to {PROCESSED_DIR / "scheme_performance_cleaned.csv"}')
    return cleaned


def load_cleaned_datasets(engine):
    cleaned_files = {
        'dim_nav_history': 'nav_history_cleaned.csv',
        'fact_transactions': 'investor_transactions_cleaned.csv',
        'fact_performance': 'scheme_performance_cleaned.csv',
    }
    counts = {}
    for table, filename in cleaned_files.items():
        path = PROCESSED_DIR / filename
        if path.exists():
            df = pd.read_csv(path)
            df.to_sql(table, engine, if_exists='replace', index=False)
            counts[table] = len(df)
            print(f'Loaded {len(df)} rows into {table}')
        else:
            print(f'{filename} not found in data/processed/. Skipping load for {table}.')
    return counts


def create_database_schema(engine):
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f'{SCHEMA_PATH} is missing. Create schema.sql before loading the database.')
    with SCHEMA_PATH.open('r', encoding='utf-8') as handle:
        ddl = handle.read()
    with engine.begin() as conn:
        for statement in ddl.split(';'):
            statement = statement.strip()
            if statement:
                conn.exec_driver_sql(statement)
    print(f'Initialized database schema in {DB_PATH}')


def main() -> None:
    ensure_directories()
    nav_history = clean_nav_history()
    investor_transactions = clean_investor_transactions()
    scheme_performance = clean_scheme_performance()

    engine = create_engine(f'sqlite:///{DB_PATH}')
    if SCHEMA_PATH.exists():
        create_database_schema(engine)
    else:
        print(f'{SCHEMA_PATH} does not exist. Skipping database schema creation.')

    counts = load_cleaned_datasets(engine)
    print('Row counts loaded into SQLite:')
    for table, count in counts.items():
        print(f'  {table}: {count}')


if __name__ == '__main__':
    main()
