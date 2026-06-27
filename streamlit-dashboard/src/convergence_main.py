"""
convergence_main.py
----------------------
Orchestrates Thread 2: Global Inequality / Convergence.

Run with: python3 src/convergence_main.py   (from the project/ folder)
"""

import sys
sys.path.insert(0, "src")

import pandas as pd
from convergence_analysis import compute_cv_by_year, compute_population_weighted_note
from trend_extrapolation import extrapolate_linear_trend

ANALYSIS_DIR = "data/analysis"
DISEASE_PREFIXES = ["BP", "Obesity", "Diabetes"]


def main():
    combined_panel = pd.read_csv("data/final/combined_panel_with_risk_index.csv")

    print("Step 1: Computing Coefficient of Variation by year (1980-2014)...")
    cv_by_year = compute_cv_by_year(combined_panel)
    cv_by_year.to_csv(f"{ANALYSIS_DIR}/convergence_cv_by_year.csv", index=False)
    print(f"  -> Saved: {ANALYSIS_DIR}/convergence_cv_by_year.csv  (shape: {cv_by_year.shape})")

    print("\nStep 2: Fitting + extrapolating linear trend for each disease's CV series...")
    extrapolation_results = []
    for prefix in DISEASE_PREFIXES:
        cv_col = f"{prefix}_CV"
        extrapolated, fit = extrapolate_linear_trend(cv_by_year, "Year", cv_col, years_forward=10)
        extrapolated["Metric"] = prefix
        extrapolation_results.append(extrapolated)

        direction = "WIDENING (divergence)" if fit.slope > 0 else "NARROWING (convergence)"
        last_observed = cv_by_year[cv_col].iloc[-1]
        projected_2024 = extrapolated[extrapolated["Year"] == 2024][cv_col].values[0]

        r_squared = fit.rvalue ** 2
        fit_quality = (
            "a very tight, consistent linear trend" if r_squared > 0.7 else
            "a moderate trend with some year-to-year noise" if r_squared > 0.3 else
            "a noisy series where the straight-line trend explains only a small part of the year-to-year movement"
        )
        print(f"\n  {prefix}: CV slope = {fit.slope:+.5f} per year -> {direction}")
        print(f"    2014 CV = {last_observed:.3f}  ->  simple linear projection for 2024 = {projected_2024:.3f}")
        print(f"    R-squared of trend fit = {r_squared:.3f} ({fit_quality})")

    all_extrapolations = pd.concat(extrapolation_results, ignore_index=True)
    all_extrapolations.to_csv(f"{ANALYSIS_DIR}/convergence_trend_extrapolation.csv", index=False)
    print(f"\nSaved: {ANALYSIS_DIR}/convergence_trend_extrapolation.csv")

    print("\nStep 3: Population-weighted comparison check...")
    print(" ", compute_population_weighted_note())

    return cv_by_year, all_extrapolations


if __name__ == "__main__":
    main()
