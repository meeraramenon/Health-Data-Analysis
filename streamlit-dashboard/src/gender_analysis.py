"""
gender_analysis.py
---------------------
Thread 5: Gender as a thread (not a footnote).

Two questions:
  1. Is the Female-minus-Male gap in each disease widening, narrowing, or
     flat over 1980-2014, averaged across all 200 countries?
  2. Does that gender-gap trend move WITH the between-country convergence
     found in Thread 2, or INDEPENDENTLY of it? (i.e. as countries become
     more alike on average, are men and women within those countries also
     becoming more alike, or is that a separate story?)

Uses sex_gap_table.csv (already built in the data preparation stage:
Female value minus Male value, per country per year per disease).
"""

import pandas as pd
from scipy.stats import linregress, pearsonr

YEAR_MIN = 1980
YEAR_MAX = 2014
DISEASE_PREFIXES = ["BP", "Obesity", "Diabetes"]


def compute_global_average_gender_gap_by_year(sex_gap_table: pd.DataFrame) -> pd.DataFrame:
    """
    Averages the Female-minus-Male gap ACROSS all 200 countries, for each
    year. A positive value means, on average across the world that year,
    prevalence is higher in women; negative means higher in men.

    Restricted to 1980-2014, the same common window used throughout, so
    this is directly comparable year-for-year with the Thread 2 CV series.
    """
    window = sex_gap_table[
        (sex_gap_table["Year"] >= YEAR_MIN) & (sex_gap_table["Year"] <= YEAR_MAX)
    ]

    gap_cols = [f"{prefix}_Sex_Gap_pct" for prefix in DISEASE_PREFIXES]
    yearly_avg = window.groupby("Year")[gap_cols].mean().reset_index()

    return yearly_avg


def compute_gender_gap_trend(yearly_avg_gap: pd.DataFrame) -> dict:
    """
    Fits a linear trend to each disease's global-average gender gap over
    time, and labels the direction in plain terms.

    IMPORTANT: "widening" vs "narrowing" is judged on the trend of the
    ABSOLUTE gap (|Female - Male|), not the raw signed slope. A gap that
    starts at -3.74 and moves to -4.16 has grown in MAGNITUDE (the
    difference between men and women got bigger) even though the raw
    slope is negative - judging only the sign of the raw slope would
    incorrectly call that "narrowing" when it is actually widening.

    Returns {prefix: {"slope": ..., "r_squared": ..., "direction": ...}}
    """
    results = {}
    for prefix in DISEASE_PREFIXES:
        col = f"{prefix}_Sex_Gap_pct"

        # Trend of the absolute gap - this is what determines widening/narrowing.
        abs_series = yearly_avg_gap[col].abs()
        abs_fit = linregress(yearly_avg_gap["Year"], abs_series)

        # Trend of the raw (signed) gap - kept for reference, to see if the
        # sign itself is changing (e.g. a gap that crosses from positive to
        # negative, meaning which sex is more affected has flipped).
        raw_fit = linregress(yearly_avg_gap["Year"], yearly_avg_gap[col])

        gap_1980 = yearly_avg_gap[yearly_avg_gap["Year"] == YEAR_MIN][col].values[0]
        gap_2014 = yearly_avg_gap[yearly_avg_gap["Year"] == YEAR_MAX][col].values[0]
        sign_flipped = (gap_1980 > 0) != (gap_2014 > 0) and abs(gap_1980) > 0.01 and abs(gap_2014) > 0.01

        if abs(abs_fit.slope) < 0.001:
            direction = "essentially flat (magnitude of the gap is not changing)"
        elif abs_fit.slope > 0:
            direction = "WIDENING (the size of the gap between men and women is growing)"
        else:
            direction = "NARROWING (the size of the gap between men and women is shrinking)"

        if sign_flipped:
            who_1980 = "women" if gap_1980 > 0 else "men"
            who_2014 = "women" if gap_2014 > 0 else "men"
            direction += f" -- AND the sign flipped: higher in {who_1980} in 1980, higher in {who_2014} by 2014"

        results[prefix] = {
            "slope_of_raw_gap_per_year": raw_fit.slope,
            "slope_of_abs_gap_per_year": abs_fit.slope,
            "r_squared": abs_fit.rvalue ** 2,
            "direction": direction,
            "gap_1980": gap_1980,
            "gap_2014": gap_2014,
            "sign_flipped": sign_flipped,
        }
    return results


def compute_gender_vs_convergence_correlation(yearly_avg_gap: pd.DataFrame, cv_by_year: pd.DataFrame) -> dict:
    """
    For each disease, correlates the year-by-year gender gap series against
    the year-by-year between-country CV series (from Thread 2), across the
    same 35 years. This is the direct test of "does the gender gap move
    WITH or INDEPENDENTLY OF the between-country gap".

    A high |r| means the two move together (gender equality and country
    equality rise/fall in step); a low |r| means they are unrelated
    phenomena moving on their own separate paths.
    """
    merged = yearly_avg_gap.merge(cv_by_year, on="Year")

    results = {}
    for prefix in DISEASE_PREFIXES:
        gap_col = f"{prefix}_Sex_Gap_pct"
        cv_col = f"{prefix}_CV"
        r, p = pearsonr(merged[gap_col], merged[cv_col])
        results[prefix] = {"pearson_r": r, "p_value": p, "n_years": len(merged)}

    return results
