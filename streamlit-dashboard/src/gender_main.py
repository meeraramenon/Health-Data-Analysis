"""
gender_main.py
-----------------
Orchestrates Thread 5: Gender.

Run with: python3 src/gender_main.py   (from the project/ folder)
NOTE: depends on Thread 2 already having been run (reads
data/analysis/convergence_cv_by_year.csv).
"""

import sys
sys.path.insert(0, "src")

import pandas as pd
from gender_analysis import (
    compute_global_average_gender_gap_by_year,
    compute_gender_gap_trend,
    compute_gender_vs_convergence_correlation,
)

ANALYSIS_DIR = "data/analysis"


def main():
    sex_gap_table = pd.read_csv("data/final/sex_gap_table.csv")
    cv_by_year = pd.read_csv(f"{ANALYSIS_DIR}/convergence_cv_by_year.csv")

    print("Step 1: Computing global average gender gap by year (1980-2014)...")
    yearly_avg_gap = compute_global_average_gender_gap_by_year(sex_gap_table)
    yearly_avg_gap.to_csv(f"{ANALYSIS_DIR}/gender_gap_by_year.csv", index=False)
    print(f"  -> Saved: {ANALYSIS_DIR}/gender_gap_by_year.csv  (shape: {yearly_avg_gap.shape})")

    print("\nStep 2: Is the gender gap widening or narrowing, per disease?")
    trends = compute_gender_gap_trend(yearly_avg_gap)
    for prefix, stats in trends.items():
        print(f"\n  {prefix}:")
        print(f"    1980 gap = {stats['gap_1980']:+.2f} pp  ->  2014 gap = {stats['gap_2014']:+.2f} pp")
        print(f"    {stats['direction']}")
        print(f"    (slope of |gap| = {stats['slope_of_abs_gap_per_year']:+.4f} pp/year, R-squared = {stats['r_squared']:.3f})")

    print("\nStep 3: Does the gender gap move WITH or INDEPENDENTLY of the")
    print("        between-country convergence found in Thread 2?")
    correlations = compute_gender_vs_convergence_correlation(yearly_avg_gap, cv_by_year)
    for prefix, stats in correlations.items():
        relationship = "MOVES TOGETHER WITH" if abs(stats["pearson_r"]) > 0.5 else "LARGELY INDEPENDENT OF"
        significance = "significant" if stats["p_value"] < 0.05 else "not significant"
        print(f"\n  {prefix}: gender gap vs. between-country CV -> r = {stats['pearson_r']:+.3f} "
              f"(p = {stats['p_value']:.4f}, {significance}, n = {stats['n_years']} years)")
        print(f"    -> The gender gap appears to be {relationship} the between-country gap.")

    return yearly_avg_gap, trends, correlations


if __name__ == "__main__":
    main()
