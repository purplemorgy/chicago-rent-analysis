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

# Load and process Zillow rent data to a monthly time series
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

    # Remove months where Zillow has no rent value
    rent_long = rent_long.dropna(subset=["rent_price"])

    rent_long["month"] = pd.to_datetime(rent_long["month"], errors="coerce")
    rent_long = rent_long.dropna(subset=["month"])

    # Align to month start so merging matches business opening months
    rent_long["month"] = rent_long["month"].dt.to_period("M").dt.to_timestamp()

    # Keep only Chicago ZIPs (606__, 607__, & 608__)
    rent_long = rent_long[rent_long["ZIP CODE"].str.match(r"^60[6-8]", na=False)]

    return rent_long

# Group license descriptions by business type
def categorize_business_group(description):
    nightlife = {
        "Caterer's Liquor License",
        "Caterer's Registration (Liquor)",
        "Outdoor Patio",
        "Late Hour",
        "Music and Dance",
        "Riverwalk Venue Liquor License",
    }

    retail = {
        "Pop-Up Retail User",
        "Secondhand Dealer",
        "Retail Food Establishment",
        "Produce Merchant",
    }

    lifestyle = {
        "Body Piercing",
        "Grooming Facility",
        "Massage Establishment",
        "Massage Therapist",
    }

    food_hospitality = {
        "Bed-And-Breakfast Establishment",
        "Food - Shared Kitchen",
        "Food - Shared Kitchen - Supplemental",
        "Hotel",
        "Shared Kitchen User (Long Term)",
        "Shared Kitchen User (Short Term)",
        "Retail Food Establishment",
        "Retail Food Est.-Supplemental License for Dog-Friendly Areas",
        "Retail Food - Seasonal Lakefront Food Establishment",
    }

    if description in nightlife:
        return "Nightlife"
    if description in retail:
        return "Retail"
    if description in lifestyle:
        return "Lifestyle services"
    if description in food_hospitality:
        return "Food and hospitality"

    return "Other"


# Load and process business license data, count openings per month in each ZIP code
def load_business_data(data_path):
    licenses_df = pd.read_csv(data_path / "Business_Licenses_Chicago.csv")

    # Drop invalid and non-Chicago ZIPs
    licenses_df["ZIP CODE"] = normalize_zip(licenses_df["ZIP CODE"])
    licenses_df = licenses_df.dropna(subset=["ZIP CODE"])
    licenses_df = licenses_df[licenses_df["ZIP CODE"].str.match(r"^60[6-8]", na=False)]

    # Use the license term start date to represent the opening month
    licenses_df["LICENSE TERM START DATE"] = pd.to_datetime(
        licenses_df["LICENSE TERM START DATE"], errors="coerce"
    )
    licenses_df = licenses_df.dropna(subset=["LICENSE TERM START DATE"])

    # For each license (by LICENSE NUMBER), keep only the earliest start date as the opening
    if "LICENSE NUMBER" in licenses_df.columns:
        licenses_df = (
            licenses_df
            .sort_values(["LICENSE NUMBER", "LICENSE TERM START DATE"])
            .drop_duplicates(subset=["LICENSE NUMBER"], keep="first")
        )

    licenses_df["month"] = (
        licenses_df["LICENSE TERM START DATE"].dt.to_period("M").dt.to_timestamp()
    )

    # Compute the requested business-type group for each license record
    licenses_df["business_group"] = licenses_df["LICENSE DESCRIPTION"].apply(categorize_business_group)

    # Count unique licenses opening per ZIP/month
    count_col = "LICENSE NUMBER" if "LICENSE NUMBER" in licenses_df.columns else "LICENSE ID"
    business_monthly = (
        licenses_df
        .groupby(["ZIP CODE", "month"], dropna=False)
        [count_col]
        .nunique()
        .reset_index(name="business_openings")
    )

    # Also count by group categories and merge into the same frame
    group_counts = (
        licenses_df
        .groupby(["ZIP CODE", "month", "business_group"], dropna=False)
        [count_col]
        .nunique()
        .reset_index(name="group_openings")
    )

    group_pivot = (
        group_counts
        .pivot_table(
            index=["ZIP CODE", "month"],
            columns="business_group",
            values="group_openings",
            fill_value=0,
        )
        .reset_index()
    )

    group_pivot.columns = [
        "ZIP CODE" if c == "ZIP CODE" else "month" if c == "month" else f"openings_{str(c).strip().replace(' ', '_')}"
        for c in group_pivot.columns
    ]

    business_monthly = business_monthly.merge(group_pivot, on=["ZIP CODE", "month"], how="left")
    business_monthly.fillna(0, inplace=True)

    return business_monthly


# Combine rent and business openings into a single monthly time series
def build_combined_dataset(rent_long, business_monthly):

    # Start with rent data so only months with rent exist
    combined = (
        rent_long
        .merge(business_monthly, on=["ZIP CODE", "month"], how="left")
    )

    # Business openings should be 0 if none occurred
    business_cols = [c for c in combined.columns if c.startswith("openings_") or c == "business_openings"]
    combined[business_cols] = combined[business_cols].fillna(0)

    combined = combined.sort_values(["ZIP CODE", "month"]).reset_index(drop=True)

    return combined



def main():
    rent_long = load_rent_data(DATA_PATH)
    business_monthly = load_business_data(DATA_PATH)

    combined_df = build_combined_dataset(rent_long, business_monthly)

    combined_df = build_combined_dataset(rent_long, business_monthly)

    # Count number of rent observations per ZIP
    zip_counts = combined_df.groupby("ZIP CODE")["rent_price"].count()

    # Keep ZIPs with at least 24 months of data
    valid_zips = zip_counts[zip_counts >= 24].index

    combined_df = combined_df[combined_df["ZIP CODE"].isin(valid_zips)]

    # Compute monthly rent growth per ZIP code
    combined_df = combined_df.sort_values(["ZIP CODE", "month"])
    combined_df["rent_growth"] = combined_df.groupby("ZIP CODE")["rent_price"].pct_change()

    # Save cleaned dataset in DATA folder.
    out_path = DATA_PATH / "cleaned_chicago_dataset.csv"
    combined_df.to_csv(out_path, index=False)


if __name__ == "__main__":
    main()
