"""
data_loading.py
---------------
Step 1: Load the raw NASA POWER (MERRA-2) daily files for the six cities,
combine them into one table and save it as Dataset/raw_dataset.csv.

Also provides helper functions used by the other scripts.
Run:  python data_loading.py
"""
from pathlib import Path

import pandas as pd

# Paths (relative to the project root)
ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT / "Dataset"
RAW_CITY_DIR = DATASET_DIR / "raw_datasets"      # one NASA POWER file per city
RAW_FILE = DATASET_DIR / "raw_dataset.csv"       # combined raw data
CLEANED_FILE = DATASET_DIR / "cleaned_dataset.csv"

# Project settings
CITIES = ["Chennai", "Delhi", "Mumbai", "Kolkata", "Bengaluru", "Ahmedabad"]
HEADER_LINES = 16                                # NASA POWER metadata lines to skip
RISK_LABELS = ["Safe", "Caution", "Extreme Caution", "Danger", "Extreme Danger"]


def load_city_file(city):
    # Read one city's NASA POWER CSV (skipping the metadata header)
    df = pd.read_csv(RAW_CITY_DIR / f"{city}.csv", skiprows=HEADER_LINES)
    df["city"] = city
    return df


def load_raw_data(cities=CITIES):
    # Load every city file and stack them into a single DataFrame
    return pd.concat([load_city_file(c) for c in cities], ignore_index=True)


def save_raw_dataset(df, path=RAW_FILE):
    # Save the combined raw data
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def load_raw_dataset(path=RAW_FILE):
    # Read the combined raw dataset created by this script
    return pd.read_csv(path)


def load_cleaned_dataset(path=CLEANED_FILE):
    # Read the cleaned dataset with proper types (date, ordered risk category)
    df = pd.read_csv(path, parse_dates=["date"])
    df["hi_category"] = pd.Categorical(df["hi_category"], categories=RISK_LABELS, ordered=True)
    return df


def main():
    df = load_raw_data()
    df.info()
    print("\nDataset shape:", df.shape)
    print("Cities:", ", ".join(df["city"].unique()))
    print(df.head())
    save_raw_dataset(df)
    print(f"\nSaved raw dataset to {RAW_FILE}")


if __name__ == "__main__":
    main()
