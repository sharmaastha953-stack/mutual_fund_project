import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / 'data' / 'raw'
PROCESSED_DIR = ROOT / 'data' / 'processed'
SUMMARY_PATH = PROCESSED_DIR / 'data_quality_summary.txt'


def ensure_directories():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def list_csv_files():
    return sorted(RAW_DIR.glob('*.csv'))


def summarize_dataframe(name: str, df: pd.DataFrame) -> list[str]:
    anomalies = []
    print(f"\n=== {name} ===")
    print(f"Location: {RAW_DIR / (name + '.csv')}")
    print(f"Shape: {df.shape}")
    print("Data types:")
    print(df.dtypes)
    print("Head:")
    print(df.head(5).to_string(index=False))

    if df.empty:
        anomalies.append('Empty dataset')
    if df.columns.duplicated().any():
        anomalies.append('Duplicate column names detected')
    na_counts = df.isna().sum()
    missing_columns = na_counts[na_counts > 0]
    if not missing_columns.empty:
        anomalies.append(f"Missing values present in {len(missing_columns)} column(s): {', '.join(missing_columns.index.astype(str))}")
    dup_rows = df.duplicated().sum()
    if dup_rows > 0:
        anomalies.append(f"{dup_rows} duplicate row(s)")

    return anomalies


def choose_column(df: pd.DataFrame, keywords: list[str]) -> str | None:
    lower = {col.lower(): col for col in df.columns}
    for keyword in keywords:
        for col_name, original in lower.items():
            if keyword in col_name:
                return original
    return None


def analyze_fund_master(fund_master: pd.DataFrame, nav_history: pd.DataFrame | None) -> list[str]:
    notes = []
    print("\n--- Fund Master Exploration ---")
    fund_house_col = choose_column(fund_master, ['fund house', 'asset management company', 'amc'])
    category_col = choose_column(fund_master, ['category'])
    subcategory_col = choose_column(fund_master, ['sub category', 'subcategory', 'sub-category'])
    risk_col = choose_column(fund_master, ['risk grade', 'risk'])
    amfi_col = choose_column(fund_master, ['amfi', 'scheme code', 'scheme_code', 'code'])

    if fund_house_col:
        print(f"Unique fund houses ({fund_house_col}): {fund_master[fund_house_col].dropna().unique()[:20].tolist()}")
    else:
        notes.append('Fund house column not detected in fund_master.')
    if category_col:
        print(f"Unique categories ({category_col}): {fund_master[category_col].dropna().unique().tolist()}")
    if subcategory_col:
        print(f"Unique sub-categories ({subcategory_col}): {fund_master[subcategory_col].dropna().unique().tolist()}")
    if risk_col:
        print(f"Unique risk grades ({risk_col}): {fund_master[risk_col].dropna().unique().tolist()}")

    if amfi_col:
        codes = fund_master[amfi_col].dropna().astype(str).str.strip()
        lengths = codes.str.len().value_counts().to_dict()
        prefix_summary = codes.str.slice(0, 2).value_counts().to_dict()
        print(f"AMFI/scheme code column: {amfi_col}")
        print(f"AMFI code lengths: {lengths}")
        print(f"First-two-digit prefix counts: {prefix_summary}")
        notes.append(f"Detected {codes.nunique()} unique AMFI/scheme codes in fund_master.")
        if nav_history is not None:
            nav_key = choose_column(nav_history, ['amfi', 'scheme code', 'scheme_code', 'code'])
            if nav_key:
                nav_codes = nav_history[nav_key].dropna().astype(str).str.strip()
                missing_codes = sorted(set(codes) - set(nav_codes))
                if missing_codes:
                    notes.append(f"{len(missing_codes)} AMFI codes from fund_master are missing in nav_history.")
                    print(f"Missing AMFI codes in nav_history: {missing_codes[:20]}")
                else:
                    notes.append('All AMFI codes in fund_master exist in nav_history.')
            else:
                notes.append('Could not detect a scheme code column in nav_history for validation.')
    else:
        notes.append('Could not detect an AMFI/scheme code column in fund_master.')

    return notes


def main() -> None:
    ensure_directories()
    csv_paths = list_csv_files()
    summary_lines: list[str] = []

    if not csv_paths:
        message = f'No CSV datasets found in {RAW_DIR}. Place your 10 datasets there and rerun.'
        print(message)
        summary_lines.append(message)
    else:
        print(f"Found {len(csv_paths)} CSV file(s) in {RAW_DIR}")
        fund_master = None
        nav_history = None

        for path in csv_paths:
            name = path.stem
            try:
                df = pd.read_csv(path)
            except Exception as exc:
                error = f"Failed to read {path.name}: {exc}"
                print(error)
                summary_lines.append(error)
                continue

            anomalies = summarize_dataframe(name, df)
            if anomalies:
                summary_lines.append(f"{name}: {', '.join(anomalies)}")
            else:
                summary_lines.append(f"{name}: no obvious anomalies detected.")

            if name.lower() in {'fund_master', 'fund master', 'fundmaster'}:
                fund_master = df
            if name.lower() in {'nav_history', 'nav history', 'navhistory'}:
                nav_history = df

        if fund_master is not None:
            notes = analyze_fund_master(fund_master, nav_history)
            summary_lines.extend(notes)
        else:
            summary_lines.append('fund_master dataset not found; expected file name like fund_master.csv.')

        if nav_history is not None and fund_master is None:
            summary_lines.append('nav_history found, but fund_master was not available for code validation.')

    summary_text = '\n'.join(summary_lines)
    SUMMARY_PATH.write_text(summary_text, encoding='utf-8')
    print(f"\nData quality summary saved to {SUMMARY_PATH}")


if __name__ == '__main__':
    main()
