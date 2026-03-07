"""
This script reads in data from Business_Licenses_Chicago.csv and 
Zillow_Rent_Prices.csv and performs cleaning and merging to create 
a single dataset with monthly rent prices and business openings by ZIP code.
"""


import pandas as pd
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "DATA"
DATA_PATH.mkdir(parents=True, exist_ok=True)


# Converts ZIP codes to valid 5-digit strings
def normalize_zip(zip_series):
    zip_str = zip_series.astype(str).str.strip()
    zip_digits = zip_str.str.extract(r"(\d{5})")[0]
    return zip_digits

# Load and process Zillow rent data to a monthly time series.
def load_rent_data(data_path):
    rent_df = pd.read_csv(data_path / "Zillow_Rent_Prices.csv")

    rent_df = rent_df[rent_df["Metro"] == "Chicago-Naperville-Elgin, IL-IN-WI"]
    rent_df = rent_df[rent_df["RegionType"] == "zip"]

    rent_df["ZIP CODE"] = normalize_zip(rent_df["RegionName"])
    rent_df = rent_df.dropna(subset=["ZIP CODE"])

    rent_long = (
        rent_df
        .melt(id_vars=["ZIP CODE"], var_name="month", value_name="rent_price")
        .query("month.str.contains('-')")
    )

    rent_long["month"] = pd.to_datetime(rent_long["month"], errors="coerce")
    rent_long = rent_long.dropna(subset=["month"])

    # Align to month start so merging matches business opening months
    rent_long["month"] = rent_long["month"].dt.to_period("M").dt.to_timestamp()

    # Keep only Chicago ZIPs (606__, 607__, & 608__)
    rent_long = rent_long[rent_long["ZIP CODE"].str.match(r"^60[6-8]", na=False)]

    return rent_long

# Load and process business license data, count openings per month in each ZIP code.
def load_business_data(data_path):
    licenses_df = pd.read_csv(data_path / "Business_Licenses_Chicago.csv")

    # Drop invalid and non-Chicago ZIPs
    licenses_df["ZIP CODE"] = normalize_zip(licenses_df["ZIP CODE"])
    licenses_df = licenses_df.dropna(subset=["ZIP CODE"])
    licenses_df = licenses_df[licenses_df["ZIP CODE"].str.match(r"^60[6-8]", na=False)]

    # Use the license term start date to represent the opening month.
    licenses_df["LICENSE TERM START DATE"] = pd.to_datetime(
        licenses_df["LICENSE TERM START DATE"], errors="coerce"
    )
    licenses_df = licenses_df.dropna(subset=["LICENSE TERM START DATE"])

    # For each license (by LICENSE NUMBER), keep only the earliest start date as the "opening".
    if "LICENSE NUMBER" in licenses_df.columns:
        licenses_df = (
            licenses_df
            .sort_values(["LICENSE NUMBER", "LICENSE TERM START DATE"])
            .drop_duplicates(subset=["LICENSE NUMBER"], keep="first")
        )

    licenses_df["month"] = (
        licenses_df["LICENSE TERM START DATE"].dt.to_period("M").dt.to_timestamp()
    )

    # Count unique licenses opening per ZIP/month
    count_col = "LICENSE NUMBER" if "LICENSE NUMBER" in licenses_df.columns else "LICENSE ID"
    business_monthly = (
        licenses_df
        .groupby(["ZIP CODE", "month"], dropna=False)
        [count_col]
        .nunique()
        .reset_index(name="business_openings")
    )

    return business_monthly


# Combine rent and business openings into a single monthly time series. Join using (ZIP CODE, month) pairs.
def build_combined_dataset(rent_long, business_monthly):
    # Create a set of (ZIP CODE, month) keys
    keys = (
        pd.concat(
            [rent_long[['ZIP CODE', 'month']], business_monthly[['ZIP CODE', 'month']]],
            ignore_index=True,
        )
        .drop_duplicates()
    )

    combined = (
        keys
        .merge(rent_long, on=['ZIP CODE', 'month'], how='left')
        .merge(business_monthly, on=['ZIP CODE', 'month'], how='left')
    )

    combined = combined.sort_values(['ZIP CODE', 'month']).reset_index(drop=True)

    return combined



def main():
    rent_long = load_rent_data(DATA_PATH)
    business_monthly = load_business_data(DATA_PATH)

    combined_df = build_combined_dataset(rent_long, business_monthly)

    # Only keep ZIP codes that actually have rent data (drop ZIPs present only in business filings).
    rent_zips = set(rent_long["ZIP CODE"].unique())
    combined_df = combined_df[combined_df["ZIP CODE"].isin(rent_zips)]

    # Find the timespan where every ZIP has data for both rent and recorded openings.
    valid = combined_df[combined_df["rent_price"].notna() & combined_df["business_openings"].notna()]
    zip_ranges = (
        valid.groupby("ZIP CODE")["month"].agg(["min", "max"]).reset_index()
    )
    common_start = zip_ranges["min"].max()
    common_end = zip_ranges["max"].min()

    combined_df = combined_df[combined_df["month"].between(common_start, common_end)]

    # Save cleaned dataset in DATA folder.
    out_path = DATA_PATH / "cleaned_chicago_dataset.csv"
    combined_df.to_csv(out_path, index=False)


    print("Time span:", common_start.date(), "->", common_end.date())


if __name__ == "__main__":
    main()
