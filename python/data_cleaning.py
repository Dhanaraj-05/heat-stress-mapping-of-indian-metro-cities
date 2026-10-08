"""
data_cleaning.py
----------------
Step 2: Clean and transform the raw dataset.

  * rename columns and drop the ones not used in the analysis
  * validate the data (-999 codes, duplicates, daily date coverage)
  * build date, month and season columns
  * compute the NWS Heat Index, its risk category and the hot-day flag
  * save Dataset/cleaned_dataset.csv

Run:  python data_cleaning.py   (after data_loading.py)
"""
import numpy as np
import pandas as pd

from data_loading import CLEANED_FILE, RISK_LABELS, load_raw_dataset

# Heat Index risk bands in deg C (NWS categories), lower bound inclusive
HI_BINS = [-np.inf, 26.7, 32.2, 39.4, 51.7, np.inf]
HOT_DAY_THRESHOLD = 40  # deg C, based on maximum daily temperature


def set_season(month):
    # Season definition used in the project (a simplification)
    if month in [3, 4, 5, 6]:
        return "Summer"
    if month in [7, 8, 9]:
        return "Monsoon"
    if month in [10, 11]:
        return "Post-Monsoon"
    return "Winter"


def heat_index_c(temperature, humidity):
    # NWS Heat Index. Inputs: temperature (deg C), relative humidity (%). Output: deg C
    t = np.asarray(temperature, dtype=float) * 9 / 5 + 32
    rh = np.asarray(humidity, dtype=float)

    simple = 0.5 * (t + 61.0 + (t - 68.0) * 1.2 + rh * 0.094)

    rothfusz = (-42.379 + 2.04901523 * t + 10.14333127 * rh
                - 0.22475541 * t * rh - 0.00683783 * t ** 2 - 0.05481717 * rh ** 2
                + 0.00122874 * t ** 2 * rh + 0.00085282 * t * rh ** 2
                - 0.00000199 * t ** 2 * rh ** 2)

    # Adjustments apply only to the Rothfusz result, in their valid ranges
    low = (rh < 13) & (t >= 80) & (t <= 112)
    rothfusz = np.where(low, rothfusz - ((13 - rh) / 4)
                        * np.sqrt(np.clip((17 - np.abs(t - 95)) / 17, 0, None)), rothfusz)
    high = (rh > 85) & (t >= 80) & (t <= 87)
    rothfusz = np.where(high, rothfusz + ((rh - 85) / 10) * ((87 - t) / 5), rothfusz)

    # NWS rule: use Rothfusz only if the average of simple and T is >= 80 F
    hi_f = np.where((simple + t) / 2 >= 80, rothfusz, simple)
    return (hi_f - 32) * 5 / 9


def clean_data(df):
    # Rename/drop columns, validate and add all derived columns
    df = df.rename(columns={
        "YEAR": "year",
        "DOY": "day_of_year",
        "T2M": "temperature",
        "T2M_MAX": "max_temperature",
        "RH2M": "humidity",
        "T2MWET": "wet_bulb_temperature",
    })
    df = df.drop(columns=["T2M_MIN", "T2MDEW", "WS2M", "PRECTOTCORR"], errors="ignore")

    # NASA POWER uses -999 for missing values (none are present in this dataset)
    df = df.replace(-999, np.nan)

    # Date, month and season
    df["date"] = pd.to_datetime(
        df["year"].astype(str) + df["day_of_year"].astype(str).str.zfill(3), format="%Y%j")
    df["month"] = df["date"].dt.month
    df["season"] = df["month"].apply(set_season)

    # Heat Index, risk category and hot-day flag
    # Categories use the unrounded value; the stored column is rounded to 2 decimals
    hi = heat_index_c(df["temperature"], df["humidity"])
    df["heat_index"] = hi.round(2)
    df["hi_category"] = pd.cut(hi, bins=HI_BINS, labels=RISK_LABELS, right=False)
    df["hot_day"] = df["max_temperature"] >= HOT_DAY_THRESHOLD
    return df


def validate_data(df):
    # Print basic data-quality checks
    print("Missing values per column:\n", df.isna().sum().to_string())
    print("\nCity/year/day duplicates:", df.duplicated(subset=["city", "year", "day_of_year"]).sum())
    gaps = df.groupby("city")["date"].apply(lambda s: (s.diff().dt.days.dropna() == 1).all())
    print("Continuous daily dates per city:\n", gaps.to_string())
    print("\nDate coverage:\n", df.groupby("city")["date"].agg(first="min", last="max", records="count"))


def main():
    raw = load_raw_dataset()
    print("Total -999 values in raw data:", (raw == -999).sum().sum(), "\n")
    df = clean_data(raw)
    validate_data(df)
    print("\nHeat Index summary:\n", df["heat_index"].describe())
    print("\nRisk categories:\n", df["hi_category"].value_counts().reindex(RISK_LABELS))
    df.to_csv(CLEANED_FILE, index=False)
    print(f"\nSaved cleaned dataset {df.shape} to {CLEANED_FILE}")


if __name__ == "__main__":
    main()
