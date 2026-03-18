"""
This script reads the cleaned dataset and creates EDA plots.

Example usage:

Run plots for all ZIP codes:
    python SCRIPTS/eda.py --zip

Run plot for a single ZIP code:
    python SCRIPTS/eda.py --zip XXXXX

Show rent data availability across ZIP codes and months:
    python SCRIPTS/eda.py --coverage

Plot distribution of monthly rent growth:
    python SCRIPTS/eda.py --rent-growth-dist

Plot distribution of business openings:
    python SCRIPTS/eda.py --business-dist

Scatter plot of business openings vs rent growth:
    python SCRIPTS/eda.py --scatter
"""

import argparse
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter
import pandas as pd


def plot_zip(zip_code, df, output_dir):
    sub = df[df["zip code"] == int(zip_code)]
    sub = sub.sort_values("month")

    plt.style.use("default")

    fig, ax1 = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor("white")

    ax1.set_facecolor("white")
    ax2 = ax1.twinx()
    ax2.set_facecolor("white")

    ax1.plot(
        sub["month"],
        sub["rent_price"],
        color="red",
        linewidth=2,
        label="Rent"
    )

    ax1.set_xlabel("Month")
    ax1.set_ylabel("Rent Price ($)", color="red")
    ax2.set_ylabel("Business Openings", color="blue")
    ax1.tick_params(axis="y", labelcolor="red")
    ax1.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))

    fig.autofmt_xdate(rotation=25)
    ax1.grid(True, color="black", linestyle="--", alpha=0.2)

    title = f"Rent and Business Openings per month in ZIP Code {zip_code}"
    ax1.set_title(title, fontweight="bold")

    ax2.bar(
        sub["month"],
        sub["business_openings"].fillna(0),
        width=18,
        color="#1f77b4",
        alpha=0.75
    )

    ax2.set_ylabel("Business openings", color="#1f77b4")
    ax2.tick_params(axis="y", labelcolor="#1f77b4")

    ax1.legend(loc="upper left", framealpha=0.8)

    fig.tight_layout()

    out_path = output_dir / f"rent_and_business_monthly_{zip_code}.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)

    print(f"Saved plot: {zip_code}")


def plot_rent_data_coverage(df, output_dir):
    coverage = df.copy()
    coverage["has_rent"] = coverage["rent_price"].notna().astype(int)

    pivot = coverage.pivot_table(
        index="zip code",
        columns="month",
        values="has_rent",
        fill_value=0
    )

    first_obs = coverage.groupby("zip code")["month"].min()
    pivot = pivot.loc[first_obs.sort_values().index]

    months = pivot.columns
    zips = pivot.index

    plt.figure(figsize=(16, 8))

    plt.imshow(
        pivot.values,
        aspect="auto",
        cmap="binary_r",
        interpolation="none"
    )

    plt.yticks(range(len(zips)), zips)

    year_positions = [i for i, m in enumerate(months) if m.month == 1]
    year_labels = [m.strftime("%Y") for m in months if m.month == 1]

    plt.xticks(year_positions, year_labels, rotation=45)

    plt.xlabel("Month")
    plt.ylabel("ZIP Code")
    plt.title("Rent Data Availability by ZIP Code")

    out_path = output_dir / "rent_data_availability.png"
    plt.savefig(out_path, dpi=150)
    plt.close()

    print("Saved plot: rent_data_availability")


def plot_rent_growth_distribution(df, output_dir):
    data = df["rent_growth"].dropna()

    plt.figure(figsize=(10, 6))
    plt.hist(data, bins=40)

    plt.xlabel("Monthly Rent Growth")
    plt.ylabel("Frequency")
    plt.title("Distribution of Monthly Rent Growth")
    plt.grid(alpha=0.3)

    out_path = output_dir / "rent_growth_distribution.png"
    plt.savefig(out_path, dpi=150)
    plt.close()

    print("Saved plot: rent_growth_distribution")


def plot_business_distribution(df, output_dir):
    data = df["business_openings"].dropna()

    plt.figure(figsize=(10, 6))
    plt.hist(data, bins=40)

    plt.xlabel("Business Openings per Month")
    plt.ylabel("Frequency")
    plt.title("Distribution of Business Openings")
    plt.grid(alpha=0.3)

    out_path = output_dir / "business_openings_distribution.png"
    plt.savefig(out_path, dpi=150)
    plt.close()

    print("Saved plot: business_openings_distribution")


def plot_business_vs_rent_growth(df, output_dir):
    sub = df.dropna(subset=["business_openings", "rent_growth"])

    plt.figure(figsize=(10, 6))
    plt.scatter(
        sub["business_openings"],
        sub["rent_growth"],
        alpha=0.4
    )

    plt.xlabel("Business Openings")
    plt.ylabel("Rent Growth")
    plt.title("Business Openings vs Rent Growth")
    plt.grid(alpha=0.3)

    out_path = output_dir / "business_vs_rent_growth.png"
    plt.savefig(out_path, dpi=150)
    plt.close()

    print("Saved plot: business_vs_rent_growth")


def main():
    parser = argparse.ArgumentParser(
        description="EDA plots for rent vs business openings."
    )

    parser.add_argument(
        "--zip",
        nargs="?",
        const=True,
        type=int,
        help="Run ZIP EDA plots. Use '--zip' for all ZIPs or '--zip XXXXX' for a single ZIP."
    )

    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Show rent data coverage for each ZIP code"
    )

    parser.add_argument(
        "--rent-growth-dist",
        action="store_true",
        help="Plot distribution of rent growth."
    )

    parser.add_argument(
        "--business-dist",
        action="store_true",
        help="Plot distribution of business openings."
    )

    parser.add_argument(
        "--scatter",
        action="store_true",
        help="Scatter plot: business openings vs rent growth."
    )

    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    data_path = project_root / "DATA" / "cleaned_chicago_dataset.csv"

    output_path = project_root / "OUTPUT"
    output_path.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(data_path)
    df.columns = df.columns.str.strip().str.lower()
    df["month"] = pd.to_datetime(df["month"], errors="coerce")

    if args.rent_growth_dist:
        plot_rent_growth_distribution(df, output_path)

    if args.business_dist:
        plot_business_distribution(df, output_path)

    if args.scatter:
        plot_business_vs_rent_growth(df, output_path)

    if args.coverage:
        plot_rent_data_coverage(df, output_path)

    if args.zip is not None:
        if args.zip is True:
            zip_codes = df["zip code"].dropna().unique().astype(int)
            for z in sorted(zip_codes):
                plot_zip(z, df, output_path)
        else:
            plot_zip(args.zip, df, output_path)



if __name__ == "__main__":
    main()