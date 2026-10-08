"""
data_visualization.py
---------------------
Step 4: Create the four analysis figures and save them to Visualizations/.

  distribution_analysis.png  - temperature, Heat Index and Heat Index by city
  trend_analysis.png         - annual / monthly trends and the city x month heatmap
  category_analysis.png      - risk-category mix and hot days vs Danger days
  correlation_analysis.png   - temperature vs humidity, Heat Index vs wet-bulb

Run:  python data_visualization.py   (after data_cleaning.py)
"""
import calendar

import matplotlib
matplotlib.use("Agg")  # save figures to files (no pop-up windows)
import matplotlib.pyplot as plt

from data_loading import CITIES, ROOT, load_cleaned_dataset
from exploratory_analysis import (annual_heat_index, annual_hot_days, category_percentages,
                                  hot_day_vs_danger, monthly_heat_index, wet_bulb_check)

OUT_DIR = ROOT / "Visualizations"
MONTHS = [calendar.month_abbr[i] for i in range(1, 13)]


def save(fig, name):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_DIR / name, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Saved", OUT_DIR / name)


def distribution_analysis(df):
    fig, ax = plt.subplots(1, 3, figsize=(20, 5.5))

    ax[0].hist(df["temperature"].dropna(), bins=30)
    ax[0].set(title="Distribution of Daily Mean Temperature",
              xlabel="Mean Temperature (°C)", ylabel="Number of Days")

    ax[1].hist(df["heat_index"].dropna(), bins=30)
    ax[1].set(title="Distribution of Daily Heat Index",
              xlabel="Heat Index (°C)", ylabel="Number of Days")

    order = df.groupby("city", observed=True)["heat_index"].median().sort_values().index
    ax[2].boxplot([df.loc[df["city"] == c, "heat_index"].dropna() for c in order],
                  tick_labels=order)
    ax[2].set(title="Heat Index Distribution by City", ylabel="Heat Index (°C)")
    ax[2].tick_params(axis="x", rotation=30)

    fig.suptitle("Distribution Analysis", fontsize=16, fontweight="bold")
    fig.tight_layout()
    save(fig, "distribution_analysis.png")


def trend_analysis(df):
    fig, ax = plt.subplots(2, 2, figsize=(18, 11))

    ai, ah = annual_heat_index(df), annual_hot_days(df)
    for city in CITIES:
        d = ai[ai["city"] == city]
        ax[0, 0].plot(d["year"], d["mean_heat_index"], marker="o", label=city)
        d = ah[ah["city"] == city]
        ax[0, 1].plot(d["year"], d["hot_days"], marker="o", label=city)
    ax[0, 0].set(title="Annual Mean Heat Index Trends by City", xlabel="Year",
                 ylabel="Mean Annual Heat Index (°C)")
    ax[0, 1].set(title="Annual Hot-Day Frequency by City", xlabel="Year",
                 ylabel="Number of Hot Days (max temp ≥ 40°C)")
    ax[0, 0].legend()
    ax[0, 1].legend()

    monthly = monthly_heat_index(df)
    monthly.T.plot(ax=ax[1, 0], marker="o")
    ax[1, 0].set(title="Monthly Mean Heat Index by City (2010-2025)", xlabel="Month",
                 ylabel="Mean Heat Index (°C)")
    ax[1, 0].set_xticks(range(1, 13), MONTHS)
    ax[1, 0].grid(True, alpha=0.3)
    ax[1, 0].legend(title="City")

    im = ax[1, 1].imshow(monthly, aspect="auto", cmap="YlOrRd")
    fig.colorbar(im, ax=ax[1, 1], label="Mean Heat Index (°C)")
    ax[1, 1].set_xticks(range(12), MONTHS)
    ax[1, 1].set_yticks(range(len(monthly.index)), monthly.index)
    ax[1, 1].set(title="City x Month Mean Heat Index", xlabel="Month", ylabel="City")

    fig.suptitle("Trend Analysis", fontsize=16, fontweight="bold")
    fig.tight_layout()
    save(fig, "trend_analysis.png")


def category_analysis(df):
    fig, ax = plt.subplots(1, 2, figsize=(18, 6))

    category_percentages(df).plot(kind="bar", stacked=True, ax=ax[0])
    ax[0].set(title="Heat Index Risk Category Distribution by City (2010-2025)",
              xlabel="City", ylabel="Percentage of Days (%)")
    ax[0].legend(title="Heat Index Category", loc="upper left", bbox_to_anchor=(1.01, 1))
    ax[0].tick_params(axis="x", rotation=0)

    comp = hot_day_vs_danger(df).set_index("city")[["hot_day_pct", "danger_days_pct"]]
    comp.columns = ["Hot days (max temp ≥ 40°C)", "Danger days (Heat Index)"]
    comp.plot(kind="bar", ax=ax[1], color=["#4C72B0", "#DD5144"])
    ax[1].set(title="Temperature-only Hot Days vs Humidity-adjusted Danger Days",
              xlabel="City", ylabel="Percentage of Days (%)")
    ax[1].tick_params(axis="x", rotation=0)

    fig.suptitle("Category Analysis", fontsize=16, fontweight="bold")
    fig.tight_layout()
    save(fig, "category_analysis.png")


def correlation_analysis(df):
    fig, ax = plt.subplots(1, 2, figsize=(16, 6))

    ax[0].scatter(df["temperature"], df["humidity"], alpha=0.25, s=8)
    ax[0].set(title="Temperature vs Relative Humidity", xlabel="Mean Temperature (°C)",
              ylabel="Relative Humidity (%)")

    _, corr = wet_bulb_check(df)
    ax[1].scatter(df["wet_bulb_temperature"], df["heat_index"], alpha=0.25, s=8)
    ax[1].set(title=f"Heat Index vs Wet-Bulb Temperature (r = {corr:.2f})",
              xlabel="Wet-Bulb Temperature (°C)", ylabel="Heat Index (°C)")

    fig.suptitle("Correlation Analysis", fontsize=16, fontweight="bold")
    fig.tight_layout()
    save(fig, "correlation_analysis.png")


def main():
    df = load_cleaned_dataset()
    distribution_analysis(df)
    trend_analysis(df)
    category_analysis(df)
    correlation_analysis(df)


if __name__ == "__main__":
    main()
