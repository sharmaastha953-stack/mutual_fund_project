import csv
import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / 'data' / 'raw'
RAW_DIR.mkdir(parents=True, exist_ok=True)
BASE_URL = 'https://api.mfapi.in/mf/{scheme_code}'

SCHEMES = {
    'HDFC Top 100 Direct': '125497',
    'SBI Bluechip': '119551',
    'ICICI Bluechip': '120503',
    'Nippon Large Cap': '118632',
    'Axis Bluechip': '119092',
    'Kotak Bluechip': '120841',
}


def safe_filename(name: str) -> str:
    return ''.join(ch if ch.isalnum() or ch in ('_', '-') else '_' for ch in name).strip('_')


def fetch_nav_json(scheme_code: str) -> dict:
    url = BASE_URL.format(scheme_code=scheme_code)
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    payload = response.json()
    if 'data' not in payload or 'meta' not in payload:
        raise ValueError('API returned unexpected structure')
    return payload


def save_json(payload: dict, path: Path) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding='utf-8')


def save_csv(payload: dict, path: Path) -> None:
    rows = payload.get('data', [])
    if not rows:
        raise ValueError('No NAV history data found to save.')
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fetch_and_save(name: str, scheme_code: str) -> None:
    print(f"Fetching {name} ({scheme_code})...")
    payload = fetch_nav_json(scheme_code)
    json_path = RAW_DIR / f"nav_{scheme_code}.json"
    csv_path = RAW_DIR / f"nav_{scheme_code}_{safe_filename(name)}.csv"
    save_json(payload, json_path)
    save_csv(payload, csv_path)
    latest = payload['data'][-1] if payload['data'] else None
    if latest:
        print(f"Latest NAV for {name}: {latest.get('nav')} on {latest.get('date')}")
    print(f"Saved JSON: {json_path}")
    print(f"Saved CSV: {csv_path}\n")


def main() -> None:
    for name, code in SCHEMES.items():
        try:
            fetch_and_save(name, code)
        except Exception as exc:
            print(f"Failed to fetch {name} ({code}): {exc}")


if __name__ == '__main__':
    main()
