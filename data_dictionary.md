# Data Dictionary

## dim_fund

- `fund_id` (INTEGER): Surrogate primary key for the fund dimension.
- `amfi_code` (TEXT): Unique AMFI scheme code for each fund.
- `fund_name` (TEXT): Name of the mutual fund scheme.
- `fund_house` (TEXT): Asset management company.
- `category` (TEXT): Fund category, such as Large Cap, Hybrid, or Debt.
- `subcategory` (TEXT): More specific classification within the category.
- `risk_grade` (TEXT): Risk grade label assigned to the scheme.
- `expense_ratio` (REAL): Annual expense ratio as a decimal percent.
- `aum` (REAL): Latest assets under management value.

## dim_date

- `date_id` (INTEGER): Numeric surrogate key in YYYYMMDD format.
- `date` (TEXT): Calendar date string.
- `year` (INTEGER): Year component.
- `quarter` (TEXT): Fiscal quarter label, e.g. Q1, Q2.
- `month` (INTEGER): Month number.
- `month_name` (TEXT): Month name.
- `day` (INTEGER): Day of month.
- `weekday` (INTEGER): Numeric weekday value.
- `weekday_name` (TEXT): Weekday name.
- `week_of_year` (INTEGER): ISO week number.

## fact_nav

- `nav_id` (INTEGER): Surrogate primary key.
- `amfi_code` (TEXT): Fund identifier.
- `date_id` (INTEGER): Date dimension foreign key.
- `nav` (REAL): Net asset value for the fund on that date.
- `source` (TEXT): Optional source label for NAV data.

## fact_transactions

- `transaction_id` (INTEGER): Surrogate primary key.
- `amfi_code` (TEXT): Fund identifier for the transaction.
- `date_id` (INTEGER): Transaction date foreign key.
- `transaction_type` (TEXT): Normalized transaction type: `SIP`, `LUMPSUM`, or `REDEMPTION`.
- `amount` (REAL): Transaction amount.
- `units` (REAL): Number of units purchased or redeemed.
- `price` (REAL): Transaction price per unit.
- `state` (TEXT): Investor state or region from the transaction record.
- `kyc_status` (TEXT): Standardized KYC status.
- `investor_id` (TEXT): Investor identifier.

## fact_performance

- `performance_id` (INTEGER): Surrogate primary key.
- `amfi_code` (TEXT): Fund identifier.
- `date_id` (INTEGER): Performance observation date.
- `return_1m` (REAL): One-month return.
- `return_3m` (REAL): Three-month return.
- `return_6m` (REAL): Six-month return.
- `return_1y` (REAL): One-year return.
- `return_3y` (REAL): Three-year return.
- `return_5y` (REAL): Five-year return.
- `expense_ratio` (REAL): Normalized expense ratio.
- `aum` (REAL): AUM value reported with performance data.
- `anomaly_flag` (INTEGER): 1 if performance values are outside expected bounds or non-numeric.

## fact_aum

- `aum_id` (INTEGER): Surrogate primary key.
- `amfi_code` (TEXT): Fund identifier.
- `date_id` (INTEGER): Date foreign key.
- `aum_value` (REAL): AUM value for the fund on that date.

## Cleaning rules

- `nav_history.csv`: parse dates to `datetime`, sort by `amfi_code` and date, forward-fill missing NAV values across calendar days, remove duplicate records, and validate NAV > 0.
- `investor_transactions.csv`: normalize transaction types to `SIP`, `LUMPSUM`, or `REDEMPTION`; validate amounts are positive; parse and standardize transaction dates; and normalize KYC status values.
- `scheme_performance.csv`: coerce return columns to numeric, flag non-numeric anomalies, normalize expense ratios into decimal percent units, and validate values within the 0.1%–2.5% range.
