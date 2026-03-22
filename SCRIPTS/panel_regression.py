"""
panel_regression.py

Runs a set of panel regression models for the Chicago rent analysis project. 

Models:
1. ZIP + month fixed effects model using total business openings (use with --fe-time)
2. Lagged model using current openings to predict next-month rent growth (use with --lag)
3. Sector-level model using categorized business openings (use with --sector)
4. Cumulative model using a 3-month rolling sum of business openings (use with --cumulative)

The script can print full regression tables with no further flags, or it can print 
summaries of what each model tracks and what the evidence suggests (use with --all --interpret).
"""


import argparse
from pathlib import Path
import pandas as pd
import statsmodels.api as sm


# Load data
# ------------------------

def load_data(data_path):
    df = pd.read_csv(data_path)
    df["month"] = pd.to_datetime(df["month"], errors="coerce")
    df = df.sort_values(["ZIP CODE", "month"]).copy()
    return df



def add_rolling_openings(df):
    df = df.copy()
    df = df.sort_values(["ZIP CODE", "month"])

    if "business_openings" in df.columns:
        df["3_month_rolling_sum"] = (
            df.groupby("ZIP CODE")["business_openings"]
            .transform(lambda s: s.rolling(window=3, min_periods=3).sum())
        )

    return df


# Helpers
# ---------

def build_fixed_effect_dummies(df, include_month_fe=False):
    zip_dummies = pd.get_dummies(
        df["ZIP CODE"],
        prefix="zip",
        drop_first=True,
        dtype=float
    )

    X_parts = [zip_dummies]

    if include_month_fe:
        month_dummies = pd.get_dummies(
            df["month"],
            prefix="month",
            drop_first=True,
            dtype=float
        )
        X_parts.append(month_dummies)

    return X_parts


def fit_clustered_ols(y, X, groups):
    X = sm.add_constant(X, has_constant="add").astype(float)
    y = y.astype(float)

    model = sm.OLS(y, X).fit(
        cov_type="cluster",
        cov_kwds={"groups": groups}
    )
    return model


# nterpretation generators
# ------------------------

def interpret_single_predictor_model(model, predictor_name, outcome_name, context_label, what_it_tracks):
    coef = model.params.get(predictor_name, float("nan"))
    pval = model.pvalues.get(predictor_name, float("nan"))

    if predictor_name in model.params.index:
        ci_low, ci_high = model.conf_int().loc[predictor_name]
    else:
        ci_low, ci_high = float("nan"), float("nan")

    significance = get_significance(pval)

    if coef > 0:
        direction = "positive"
    elif coef < 0:
        direction = "negative"
    else:
        direction = "near zero"

    lines = [
        f"This model tracks {what_it_tracks}.",
        f"For the {context_label}, the coefficient on {predictor_name} is {coef:.6g}, which is {significance}.",
        f"The estimated relationship is {direction}, with a 95% confidence interval from {ci_low:.6g} to {ci_high:.6g}.",
        f"The model R-squared is {model.rsquared:.3f}, so the model explains about {model.rsquared * 100:.1f}% of the variation in {outcome_name}.",
    ]

    if pval >= 0.10:
        lines.append(
            f"This means the model does not provide strong evidence that {predictor_name} is associated with {outcome_name} after accounting for the included fixed effects and clustered standard errors."
        )
    else:
        lines.append(
            f"This suggests evidence of an association between {predictor_name} and {outcome_name}, though the size and practical importance of the effect should still be interpreted carefully."
        )

    return lines


def interpret_sector_model(model, sector_cols, outcome_name):
    significant = []
    marginal = []

    for col in sector_cols:
        if col not in model.params.index:
            continue

        coef = model.params[col]
        pval = model.pvalues[col]

        if pval < 0.05:
            significant.append((col, coef, pval))
        elif pval < 0.10:
            marginal.append((col, coef, pval))

    lines = [
        "This model tracks whether specific categories of business openings are linked to rent growth, rather than looking only at total openings.",
        f"The model R-squared is {model.rsquared:.3f}, so the model explains about {model.rsquared * 100:.1f}% of the variation in {outcome_name}.",
    ]

    if len(significant) == 0 and len(marginal) == 0:
        lines.append(
            "None of the sector-specific opening variables are statistically significant at conventional levels."
        )
        lines.append(
            "That means there is no strong evidence that any particular category of openings has a distinct relationship with rent growth in this specification."
        )
    else:
        if significant:
            sig_text = "; ".join(
                [f"{name} (coef={coef:.6g}, p={pval:.3g})" for name, coef, pval in significant]
            )
            lines.append(f"Statistically significant sector predictors: {sig_text}.")

        if marginal:
            marg_text = "; ".join(
                [f"{name} (coef={coef:.6g}, p={pval:.3g})" for name, coef, pval in marginal]
            )
            lines.append(f"Marginally significant sector predictors: {marg_text}.")

        lines.append(
            "These results suggest that at least some business categories may differ in their association with rent growth, but the evidence should be interpreted cautiously."
        )

    return lines

def get_significance(p_value):
    if pd.isna(p_value):
        return "could not be evaluated"
    if p_value < 0.05:
        return "statistically significant at the 5% level"
    return "not statistically significant"


def print_output(title, model, interpretation_lines, interpret=False):
    print(f"\n=== {title} ===\n")

    if not interpret:
        print(model.summary())

    print("\nInterpretation:")
    for line in interpretation_lines:
        print(f"- {line}")
    print()


# Model 1: ZIP + Month Fixed Effects
# ----------------------------------

def run_fe_time_model(df, interpret=False):
    df_model = df.copy()
    predictor = "business_openings"

    df_model = df_model.dropna(subset=["rent_growth", predictor, "ZIP CODE", "month"])

    X_parts = [df_model[[predictor]].astype(float)]
    X_parts.extend(build_fixed_effect_dummies(df_model, include_month_fe=True))
    X = pd.concat(X_parts, axis=1)

    y = df_model["rent_growth"]
    model = fit_clustered_ols(y, X, df_model["ZIP CODE"])

    interpretation = interpret_single_predictor_model(
        model=model,
        predictor_name=predictor,
        outcome_name="rent_growth",
        context_label="ZIP + month fixed effects model",
        what_it_tracks="whether changes in total business openings within a ZIP code over time are associated with changes in rent growth, while controlling for ZIP-specific and month-specific effects"
    )

    print_output(
        title="ZIP + Month Fixed Effects Regression",
        model=model,
        interpretation_lines=interpretation,
        interpret=interpret
    )


# Model 2: Lagged Model + Fixed Effects
# --------------------------------------

def run_lagged_model(df, interpret=False):
    df_model = df.copy()
    predictor = "business_openings"

    df_model = df_model.sort_values(["ZIP CODE", "month"])
    df_model["next_rent_growth"] = df_model.groupby("ZIP CODE")["rent_growth"].shift(-1)

    df_model = df_model.dropna(subset=["next_rent_growth", predictor, "ZIP CODE", "month"])

    X_parts = [df_model[[predictor]].astype(float)]
    X_parts.extend(build_fixed_effect_dummies(df_model, include_month_fe=True))
    X = pd.concat(X_parts, axis=1)

    y = df_model["next_rent_growth"]
    model = fit_clustered_ols(y, X, df_model["ZIP CODE"])

    interpretation = interpret_single_predictor_model(
        model=model,
        predictor_name=predictor,
        outcome_name="next_rent_growth",
        context_label="lagged model",
        what_it_tracks="whether business openings in one month are associated with rent growth in the following month"
    )

    print_output(
        title="Lagged Regression Business Openings Predicting Next Month's Rent Growth (+ ZIP + month fixed effects)",
        model=model,
        interpretation_lines=interpretation,
        interpret=interpret
    )


# Model 3: Sector Model
# ------------------------

def run_sector_model(df, interpret=False):
    df_model = df.copy()

    sector_cols = sorted(
        [
            c for c in df_model.columns
            if c.startswith("openings_")
            and c != "3_month_rolling_sum"
        ]
    )

    if not sector_cols:
        print("\n=== Sector-Level Regression ===\n")
        print("No sector columns found that start with 'openings_'.\n")
        return

    needed_cols = ["rent_growth", "ZIP CODE", "month"] + sector_cols
    df_model = df_model.dropna(subset=needed_cols)

    X_parts = [df_model[sector_cols].astype(float)]
    X_parts.extend(build_fixed_effect_dummies(df_model, include_month_fe=True))
    X = pd.concat(X_parts, axis=1)

    y = df_model["rent_growth"]
    model = fit_clustered_ols(y, X, df_model["ZIP CODE"])

    interpretation = interpret_sector_model(
        model=model,
        sector_cols=sector_cols,
        outcome_name="rent_growth"
    )

    print_output(
        title="Sector-Level Regression (Category-Specific Openings + ZIP + month fixed effects)",
        model=model,
        interpretation_lines=interpretation,
        interpret=interpret
    )


# Model 4: Rolling Model
# ------------------------

def run_cumulative_model(df, interpret=False):
    df_model = df.copy()
    predictor = "3_month_rolling_sum"

    if predictor not in df_model.columns:
        print("\n=== Cumulative / Rolling Regression ===\n")
        print("Column '3_month_rolling_sum' could not be created.\n")
        return

    df_model = df_model.dropna(subset=["rent_growth", predictor, "ZIP CODE", "month"])

    X_parts = [df_model[[predictor]].astype(float)]
    X_parts.extend(build_fixed_effect_dummies(df_model, include_month_fe=True))
    X = pd.concat(X_parts, axis=1)

    y = df_model["rent_growth"]
    model = fit_clustered_ols(y, X, df_model["ZIP CODE"])

    interpretation = interpret_single_predictor_model(
        model=model,
        predictor_name=predictor,
        outcome_name="rent_growth",
        context_label="cumulative / rolling activity model",
        what_it_tracks="whether the cumulative number of business openings over the current month and previous two months is associated with rent growth"
    )

    print_output(
        title="Cumulative Business Activity Regression (3-Month Rolling Sum + ZIP + month fixed effects)",
        model=model,
        interpretation_lines=interpretation,
        interpret=interpret
    )


# ------------------------
# Main
# ------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Panel regression models for Chicago rent analysis."
    )

    parser.add_argument(
        "--fe-time",
        action="store_true",
        help="Run ZIP + month fixed effects model with total business openings."
    )
    parser.add_argument(
        "--lag",
        action="store_true",
        help="Run lagged model using current business openings to predict next month's rent growth."
    )
    parser.add_argument(
        "--sector",
        action="store_true",
        help="Run sector-level model using category-specific openings."
    )
    parser.add_argument(
        "--cumulative",
        action="store_true",
        help="Run cumulative / rolling activity model using a 3-month rolling sum of openings."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all four models."
    )
    parser.add_argument(
        "--interpret",
        action="store_true",
        help="Print interpretations only, without the full regression tables."
    )

    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    data_path = project_root / "DATA" / "cleaned_chicago_dataset.csv"

    df = load_data(data_path)
    df = add_rolling_openings(df)

    ran_any = False

    if args.all:
        run_fe_time_model(df, interpret=args.interpret)
        run_lagged_model(df, interpret=args.interpret)
        run_sector_model(df, interpret=args.interpret)
        run_cumulative_model(df, interpret=args.interpret)
        return

    if args.fe_time:
        run_fe_time_model(df, interpret=args.interpret)
        ran_any = True

    if args.lag:
        run_lagged_model(df, interpret=args.interpret)
        ran_any = True

    if args.sector:
        run_sector_model(df, interpret=args.interpret)
        ran_any = True

    if args.cumulative:
        run_cumulative_model(df, interpret=args.interpret)
        ran_any = True

    if not ran_any:
        print("No model selected. Use --help to see options.")


if __name__ == "__main__":
    main()
