"""
convergence_analysis.py
-------------------------
Thread 2: Global Inequality / Convergence.

Question: is the GAP between the healthiest and sickest countries widening
or narrowing over 1980-2014, separately for each disease?

METHOD: for each year, compute the Coefficient of Variation (CV) across all
200 countries:

    CV = (standard deviation across countries) / (mean across countries)

CV is used rather than the raw standard deviation because the three
diseases are on different scales (Obesity ranges much wider than Diabetes,
for instance) - CV expresses spread relative to the average, so the three
resulting series are comparable to each other, and a rising/falling CV
means the relative inequality between countries is rising/falling,
independent of whether the global average itself is also rising or falling.

WINDOW: 1980-2014, the same common window used throughout this project
(the range where all three diseases have full data for every country).
"""

import pandas as pd

YEAR_MIN = 1980
YEAR_MAX = 2014
DISEASE_METRICS = ["BP_Prevalence_pct", "Obesity_Prevalence_pct", "Diabetes_Prevalence_pct"]


def compute_cv_by_year(combined_panel: pd.DataFrame) -> pd.DataFrame:
    """
    Returns one row per year (1980-2014), with columns:
      <metric>_Mean   - the simple cross-country average that year
      <metric>_StdDev - the cross-country standard deviation that year
      <metric>_CV     - StdDev / Mean (the dispersion measure itself)

    The Mean and StdDev are kept in the output (not just CV) so the report
    can show, alongside the inequality story, what the global average was
    doing at the same time - e.g. "the average is rising AND the gap is
    narrowing" is a different story to "the average is flat AND the gap is
    widening", and both numbers are needed to tell which one is happening.
    """
    window = combined_panel[
        (combined_panel["Year"] >= YEAR_MIN) & (combined_panel["Year"] <= YEAR_MAX)
    ]

    rows = []
    for year, group in window.groupby("Year"):
        row = {"Year": year}
        for metric in DISEASE_METRICS:
            values = group[metric].dropna()
            mean = values.mean()
            std = values.std()
            prefix = metric.replace("_Prevalence_pct", "")
            row[f"{prefix}_Mean"] = mean
            row[f"{prefix}_StdDev"] = std
            row[f"{prefix}_CV"] = std / mean if mean != 0 else float("nan")
        rows.append(row)

    return pd.DataFrame(rows).sort_values("Year").reset_index(drop=True)


def compute_population_weighted_note() -> str:
    """
    Documents why the population-weighted vs. unweighted comparison (the
    'bonus' chart from the original visual list) is NOT computed in this
    module: it requires a country population figure for every year, which
    is not present anywhere in this project's data so far (not in the
    original health sheets, not in Gini/UHC/Income Group files).

    Computing it would require either (a) downloading one more external
    file (World Bank Population, Total - indicator SP.POP.TOTL, same
    download pattern as the Gini file already used), or (b) skipping this
    bonus chart. This function exists so that decision is documented in
    code, not silently dropped.
    """
    return (
        "Population-weighted comparison NOT computed: no population data "
        "exists anywhere in this project yet. Requires either downloading "
        "World Bank Population Total (SP.POP.TOTL) as a 6th external file, "
        "or this bonus chart is dropped from the final visual set."
    )
