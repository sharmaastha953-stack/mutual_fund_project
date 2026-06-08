# Mutual Fund Analytics

## Capstone Project I - Mutual Fund Analytics

Project Start Date: 01 Jun 2026

Status: PLANNING
Priority: HIGH
Progress: 45%

## Project Structure

- `data/raw/` — raw CSV datasets and downloaded NAV JSON/CSV files
- `data/processed/` — processed outputs, summaries, and cleaned data
- `notebooks/` — Jupyter notebooks for exploration and modeling
- `sql/` — SQL scripts and queries
- `dashboard/` — dashboard code and visual assets
- `reports/` — analysis reports and presentation materials

## Deliverables

- `data_ingestion.py` — loads all CSV datasets from `data/raw/`, prints `.shape`, `.dtypes`, `.head()`, detects anomalies, explores `fund_master`, validates AMFI codes, and writes a summary.
- `live_nav_fetch.py` — fetches NAV JSON for HDFC Top 100 Direct and 5 additional schemes, parses responses, and saves raw CSV files.
- `requirements.txt` — dependency list for pandas, numpy, matplotlib, seaborn, plotly, sqlalchemy, requests, scipy, and jupyter.

## Usage

1. Place your 10 provided CSV datasets into `data/raw/`.
2. Install dependencies:
   ```powershell
   py -m pip install -r requirements.txt
   ```
3. Run data ingestion:
   ```powershell
   py data_ingestion.py
   ```
4. Fetch NAV history for selected schemes:
   ```powershell
   py live_nav_fetch.py
   ```

## Task 2: Cleaning and SQLite Load

1. Place the following files into `data/raw/`:
   - `nav_history.csv`
   - `investor_transactions.csv`
   - `scheme_performance.csv`
2. Run:
   ```powershell
   py data_pipeline.py
   ```
3. This will produce:
   - cleaned datasets in `data/processed/`
   - `bluestock_mf.db`
   - `schema.sql`
   - `queries.sql`
   - `data_dictionary.md`

## Notes

- The project is prepared for initial data ingestion and live NAV fetching.
- `data_ingestion.py` will report missing datasets or anomalies as it scans `data/raw/`.
- `live_nav_fetch.py` fetches scheme data from `https://api.mfapi.in/mf/{scheme_code}` and saves both JSON and CSV formats.
- Git is not available in the current environment, so repository initialization and pushing to GitHub must be done locally once Git is installed.
