"""
typology_features.py
----------------------
Converts each country's raw year-by-year disease values into a small set of
NUMERIC features describing the *shape* of its 1980-2014 trajectory - not
just where it ends up, but how it got there. This is what the k-means
clustering in typology_clustering.py actually groups countries on.

WHY THESE SPECIFIC FEATURES:
A single number like "obesity in 2014" only tells you the destination.
Two countries can arrive at the same 2014 value via completely different
journeys (one rising steadily, one rising fast and then plateauing) - and
those are different stories worth distinguishing. So for each disease we
compute four numbers that, together, describe the journey:

  - <metric>_Start   : average value over the first 5 years (1980-1984),
                        smoothed over 5 years rather than a single year to
                        reduce noise from any one unusual data point.
  - <metric>_End     : average value over the last 5 years (2010-2014),
                        same smoothing logic.
  - <metric>_Slope   : overall linear trend across the full 1980-2014 window
                        (a linear regression slope, in percentage points per
                        year) - the average speed of change.
  - <metric>_Curvature : late-period slope minus early-period slope (the
                        window is split into 1980-1997 and 1997-2014).
                        Positive = accelerating (getting worse faster over
                        time); negative = decelerating (the rise is slowing,
                        flattening, or reversing). This is what lets the
                        clustering distinguish "still climbing fast" from
                        "rose hard early then leveled off", which a single
                        slope value can't tell apart.

WHY THE 1980-2014 WINDOW SPECIFICALLY: this is the only window where all
three diseases (BP, Obesity, Diabetes) have data for every country in this
dataset (Diabetes is the limiting factor - it only covers 1980-2014). Using
a common window means the three diseases' features are directly comparable
within a country, rather than measuring BP's trajectory over one period and
Diabetes's over a different one.

NO IMPUTATION: if a country is missing any year inside 1980-2014 for any
metric (it shouldn't be, based on the original source data, but this is
checked rather than assumed), that country is excluded from clustering and
reported explicitly, not filled in.
"""

import pandas as pd
import numpy as np
from scipy.stats import linregress

YEAR_MIN = 1980
YEAR_MAX = 2014
EARLY_PERIOD_END = 1997   # midpoint-ish split of 1980-2014 into two 17/18-year halves
DISEASE_METRICS = ["BP_Prevalence_pct", "Obesity_Prevalence_pct", "Diabetes_Prevalence_pct"]


def _check_complete_coverage(panel: pd.DataFrame) -> tuple[list[str], list[str]]:
    """
    Checks which countries have a complete, gap-free 1980-2014 record for
    all three disease metrics. Returns (complete_countries, incomplete_countries).
    This is checked explicitly rather than assumed, even though the original
    source sheets had no internal gaps.
    """
    expected_years = set(range(YEAR_MIN, YEAR_MAX + 1))
    complete, incomplete = [], []

    for country, group in panel.groupby("Country"):
        window = group[(group["Year"] >= YEAR_MIN) & (group["Year"] <= YEAR_MAX)]
        years_present = set(window["Year"])
        has_all_years = years_present == expected_years
        has_all_metrics = window[DISEASE_METRICS].notna().all().all()

        if has_all_years and has_all_metrics:
            complete.append(country)
        else:
            incomplete.append(country)

    return complete, incomplete


def _trajectory_features_for_one_metric(window: pd.DataFrame, metric: str) -> dict:
    """
    Computes Start / End / Slope / Curvature for a single metric, for a
    single country's 1980-2014 window (already filtered and sorted by Year).
    """
    early = window[window["Year"] <= EARLY_PERIOD_END]
    late = window[window["Year"] >= EARLY_PERIOD_END]

    start_level = window[window["Year"] <= YEAR_MIN + 4][metric].mean()
    end_level = window[window["Year"] >= YEAR_MAX - 4][metric].mean()

    overall_slope = linregress(window["Year"], window[metric]).slope
    early_slope = linregress(early["Year"], early[metric]).slope
    late_slope = linregress(late["Year"], late[metric]).slope
    curvature = late_slope - early_slope

    prefix = metric.replace("_Prevalence_pct", "")
    return {
        f"{prefix}_Start": start_level,
        f"{prefix}_End": end_level,
        f"{prefix}_Slope": overall_slope,
        f"{prefix}_Curvature": curvature,
    }


def build_trajectory_feature_table(combined_panel: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Main entry point. Takes the combined (sex-averaged) country/year panel
    and returns:
      - a DataFrame indexed by Country, one row per country, with 4 features
        x 3 diseases = 12 numeric columns
      - a list of countries excluded due to incomplete 1980-2014 coverage

    This DataFrame is the direct input to the clustering step.
    """
    complete_countries, incomplete_countries = _check_complete_coverage(combined_panel)

    rows = []
    for country in complete_countries:
        country_data = combined_panel[
            (combined_panel["Country"] == country)
            & (combined_panel["Year"] >= YEAR_MIN)
            & (combined_panel["Year"] <= YEAR_MAX)
        ].sort_values("Year")

        feature_row = {"Country": country}
        for metric in DISEASE_METRICS:
            feature_row.update(_trajectory_features_for_one_metric(country_data, metric))
        rows.append(feature_row)

    feature_table = pd.DataFrame(rows).set_index("Country")
    return feature_table, incomplete_countries
