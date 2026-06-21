"""
feature_engineering.py
-----------------------
Builds the derived columns and tables needed for the analysis stage. This
file produces THREE outputs from the merged master panel:

1. combined_panel: one row per Country/Year (sexes combined), with the three
   disease metrics averaged across Male and Female, plus all external
   variables. This is the unit most of the planned analyses operate on
   (typology clustering, convergence/dispersion, equality/access hypothesis
   tests) - those questions are about countries, not male/female subgroups.

2. sex_gap_table: one row per Country/Year, with the Female-minus-Male gap
   for each of the three disease metrics. This is what feeds the gender
   thread specifically.

3. combined_panel_with_risk_index: combined_panel plus the new
   Metabolic_Risk_Index column - a single composite score per country/year
   combining all three diseases.

WHY AVERAGE MALE/FEMALE FOR THE "COMBINED" VIEW (rather than use a
pre-existing "Both sexes" category): our source data does not include a
"Both" category at all (only Male/Female), so combining is done explicitly
here as a simple, equally-weighted mean - this is a stated, visible
assumption, not a hidden one.
"""

import pandas as pd

EXTERNAL_COLUMNS = [
    "Country_Code", "Continent", "WHO_Region",
    "UHC_Index", "UHC_Index_Is_Carried_Back",
    "Gini_Index", "Gini_Year",
    "Income_Group", "Income_Group_Is_Carried_Back", "Income_Group_Used_Current_Fallback",
]

DISEASE_METRICS = ["BP_Prevalence_pct", "Obesity_Prevalence_pct", "Diabetes_Prevalence_pct"]


def build_combined_sex_panel(master_long: pd.DataFrame) -> pd.DataFrame:
    """
    Averages Male and Female values for each disease metric, per Country/Year.
    External variables (Continent, UHC, Gini, etc.) are identical across the
    Male/Female rows for a given Country/Year, so they are simply carried
    over (first value) rather than averaged.

    Uses skipna averaging: if only one sex has a value for a given
    country/year/metric, that single value is used as the average rather
    than producing NaN - but if BOTH are missing, the result is correctly
    left as NaN (never invented).
    """
    metric_avg = (
        master_long.groupby(["Country", "Year"], as_index=False)[DISEASE_METRICS]
        .mean()  # pandas .mean() skips NaN by default; all-NaN groups correctly stay NaN
    )

    external = (
        master_long.groupby(["Country", "Year"], as_index=False)[EXTERNAL_COLUMNS]
        .first()
    )

    combined = metric_avg.merge(external, on=["Country", "Year"], how="left")
    return combined.sort_values(["Country", "Year"]).reset_index(drop=True)


def build_sex_gap_table(master_long: pd.DataFrame) -> pd.DataFrame:
    """
    Computes Female-minus-Male gap for each disease metric, per Country/Year.
    Positive value = prevalence is higher among women; negative = higher among men.

    Implemented by pivoting Sex into columns first, so the subtraction is
    guaranteed to compare the correct matching Country/Year/metric pair.
    Country/Year combinations missing either sex produce NaN for that gap,
    not zero - a missing comparison is not the same as "no gap".
    """
    pivoted = master_long.pivot_table(
        index=["Country", "Year"],
        columns="Sex",
        values=DISEASE_METRICS,
        aggfunc="first",
    )

    gap_table = pd.DataFrame(index=pivoted.index)
    for metric in DISEASE_METRICS:
        gap_col_name = metric.replace("_Prevalence_pct", "_Sex_Gap_pct")
        gap_table[gap_col_name] = pivoted[(metric, "Female")] - pivoted[(metric, "Male")]

    gap_table = gap_table.reset_index()
    return gap_table.sort_values(["Country", "Year"]).reset_index(drop=True)


def _min_max_normalize(series: pd.Series) -> pd.Series:
    """
    Scales a series to 0-100 using min-max normalisation, based on the
    observed minimum and maximum in THIS dataset (not an assumed theoretical
    range) - documented clearly since this choice affects interpretation of
    the composite index.
    """
    min_val = series.min()
    max_val = series.max()
    return (series - min_val) / (max_val - min_val) * 100


def add_metabolic_risk_index(combined_panel: pd.DataFrame) -> pd.DataFrame:
    """
    Adds Metabolic_Risk_Index: an equal-weighted composite of the three
    disease metrics, each independently min-max normalised to 0-100 first
    (so that, e.g., diabetes - which has a smaller numeric range than obesity
    - is not automatically given less influence simply because its raw
    percentages are smaller).

    EQUAL WEIGHTING IS A STATED SIMPLIFYING ASSUMPTION, not a finding - this
    is flagged explicitly here and should be repeated in the report. Rows
    missing any one of the three underlying metrics produce a NaN index
    rather than a score based on incomplete information.
    """
    df = combined_panel.copy()

    normalized_cols = []
    for metric in DISEASE_METRICS:
        norm_col = metric.replace("_Prevalence_pct", "_Normalized")
        df[norm_col] = _min_max_normalize(df[metric])
        normalized_cols.append(norm_col)

    # If any one of the three normalized metrics is missing, the row-mean
    # would silently average over fewer values. We require all three present.
    has_all_three = df[normalized_cols].notna().all(axis=1)
    df["Metabolic_Risk_Index"] = df[normalized_cols].mean(axis=1)
    df.loc[~has_all_three, "Metabolic_Risk_Index"] = pd.NA

    df = df.drop(columns=normalized_cols)
    return df
