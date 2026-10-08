"""
exploratory_analysis.py
-----------------------
Step 3: Exploratory data analysis on Dataset/cleaned_dataset.csv.

Builds the summary tables used in the report: risk-category mix, city summary,
hot days vs Danger days, monthly/seasonal patterns, annual trends and the
wet-bulb cross-check. Functions are reused by data_visualization.py.

Run:  python exploratory_analysis.py   (after data_cleaning.py)
"""
import calendar

import pandas as pd
from scipy.stats import linregress

from data_loading import CITIES, RISK_LABELS, load_cleaned_dataset

DANGER = ["Danger", "Extreme Danger"]


def category_percentages(df):
    # % of days in each Heat Index risk category, per city
    return (pd.crosstab(df["city"], df["hi_category"], normalize="index")
            .reindex(columns=RISK_LABELS, fill_value=0) * 100).round(2)


def city_summary(df):
    # Mean/max Heat Index and Danger-day share, ranked by Danger-day share
    return (df.groupby("city", observed=True)
              .agg(mean_hi=("heat_index", "mean"),
                   max_hi=("heat_index", "max"),
                   danger_pct=("hi_category", lambda x: x.isin(DANGER).mean() * 100))
              .sort_values("danger_pct", ascending=False)
              .round(2))


def hot_day_vs_danger(df):
    # Temperature-only hot days vs humidity-adjusted Danger days, with ranks
    hot = (df.groupby("city")
             .agg(hot_days=("hot_day", "sum"), total_days=("hot_day", "size"))
             .reset_index())
    hot["hot_day_pct"] = (hot["hot_days"] / hot["total_days"] * 100).round(2)
    danger = (df.groupby("city", observed=True)["hi_category"]
                .apply(lambda x: x.isin(DANGER).mean() * 100)
                .rename("danger_days_pct").reset_index())
    out = hot[["city", "hot_days", "hot_day_pct"]].merge(danger, on="city", how="left")
    out["temperature_rank"] = out["hot_day_pct"].rank(method="min", ascending=False).astype(int)
    out["heat_index_rank"] = out["danger_days_pct"].rank(method="min", ascending=False).astype(int)
    return out.sort_values("heat_index_rank").reset_index(drop=True)


def monthly_heat_index(df):
    # Mean Heat Index by city (rows) and month (columns 1-12)
    return df.groupby(["city", "month"], observed=True)["heat_index"].mean().unstack().round(2)


def seasonal_heat_index(df):
    # Mean Heat Index by city (rows) and season (columns)
    return df.groupby(["city", "season"], observed=True)["heat_index"].mean().unstack()


def seasonal_risk(df):
    # % of days in each risk category, by city and season
    return (df.groupby(["city", "season"], observed=True)["hi_category"]
              .value_counts(normalize=True).mul(100).round(2).unstack())


def peak_months(monthly):
    # Peak month (name) and its mean Heat Index for each city
    out = pd.DataFrame({"Peak Month": monthly.idxmax(axis=1),
                        "Mean Heat Index (°C)": monthly.max(axis=1)}).round(2)
    out["Peak Month"] = out["Peak Month"].apply(lambda m: calendar.month_name[int(m)])
    return out


def annual_heat_index(df):
    # Mean Heat Index per city and year
    return (df.groupby(["city", "year"])["heat_index"].mean()
              .reset_index(name="mean_heat_index").round(2))


def annual_hot_days(df):
    # Number of hot days per city and year
    return df.groupby(["city", "year"])["hot_day"].sum().reset_index(name="hot_days")


def trend_table(annual, value_col, label):
    # Linear-regression trend (slope, p-value) for each city, alpha = 0.05
    rows = []
    for city in CITIES:
        d = annual[annual["city"] == city]
        r = linregress(d["year"], d[value_col])
        rows.append({"city": city, label: r.slope, "p_value": r.pvalue,
                     "r_squared": r.rvalue ** 2,
                     "significant": "Yes" if r.pvalue < 0.05 else "No"})
    return pd.DataFrame(rows)


def wet_bulb_check(df):
    # Mean Heat Index vs mean wet-bulb temperature per city, and their correlation
    summary = df.groupby("city").agg(mean_heat_index=("heat_index", "mean"),
                                     mean_wet_bulb=("wet_bulb_temperature", "mean"))
    return summary, df["heat_index"].corr(df["wet_bulb_temperature"])


def final_summary(df):
    # One table with the main result per city, ordered by Danger-day share
    cs, monthly, seasonal = city_summary(df), monthly_heat_index(df), seasonal_heat_index(df)
    pm = peak_months(monthly)
    return pd.DataFrame({
        "Mean HI (°C)": cs["mean_hi"], "Max HI (°C)": cs["max_hi"],
        "Danger Days (%)": cs["danger_pct"],
        "Peak Month": pm["Peak Month"], "Peak Month HI (°C)": pm["Mean Heat Index (°C)"],
        "Peak Season": seasonal.idxmax(axis=1), "Peak Season HI (°C)": seasonal.max(axis=1),
    }).loc[cs.index].round(2)


def main():
    df = load_cleaned_dataset()
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 20)

    print("=== Risk category mix (% of days) ===\n", category_percentages(df))
    print("\n=== City summary (ranked by Danger-day share) ===\n", city_summary(df))
    print("\n=== Hot days vs Danger days ===\n", hot_day_vs_danger(df))
    print("\n=== Monthly mean Heat Index ===\n", monthly_heat_index(df))
    print("\n=== Peak months ===\n", peak_months(monthly_heat_index(df)))
    print("\n=== Seasonal mean Heat Index ===\n", seasonal_heat_index(df).round(2))
    print("\n=== Seasonal risk (% of days) ===\n", seasonal_risk(df))
    print("\n=== Heat Index trend, 2010-2025 ===\n",
          trend_table(annual_heat_index(df), "mean_heat_index", "slope"))
    print("\n=== Hot-day trend, 2010-2025 ===\n",
          trend_table(annual_hot_days(df), "hot_days", "slope_hot_days_per_year"))
    summary, corr = wet_bulb_check(df)
    print("\n=== Wet-bulb cross-check ===\n", summary)
    print(f"Correlation between Heat Index and wet-bulb temperature: {corr:.3f}")
    print("\n=== Final city summary ===\n", final_summary(df))


if __name__ == "__main__":
    main()
