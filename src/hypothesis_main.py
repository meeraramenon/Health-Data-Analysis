"""
hypothesis_main.py
---------------------
Orchestrates Threads 3 (Equality Hypothesis) and 4 (Access Hypothesis):
  1. Build the cross-sectional snapshot (one row per country)
  2. Run both hypothesis tests
  3. Save results + print a plain-language interpretation of what the
     correlation actually shows, including direction and strength - not
     just the raw numbers

Run with: python3 src/hypothesis_main.py   (from the project/ folder)
"""

import sys
sys.path.insert(0, "src")

import pandas as pd
from hypothesis_features import build_hypothesis_snapshot
from hypothesis_tests import run_equality_hypothesis, run_access_hypothesis

ANALYSIS_DIR = "data/analysis"


def _interpret_correlation(r: float, p: float, n: int, label: str) -> str:
    """Plain-language read of a correlation result - used in the printed summary."""
    direction = "negative" if r < 0 else "positive"
    strength = (
        "negligible" if abs(r) < 0.1 else
        "weak" if abs(r) < 0.3 else
        "moderate" if abs(r) < 0.5 else
        "strong"
    )
    significance = "statistically significant (p < 0.05)" if p < 0.05 else "NOT statistically significant (p >= 0.05)"
    return (
        f"{label}: r = {r:.3f} ({strength} {direction} relationship), "
        f"p = {p:.4f} -> {significance}, based on n = {n} countries."
    )


def main():
    print("Step 1: Loading country_typology.csv and combined_panel_with_risk_index.csv...")
    country_typology = pd.read_csv(f"{ANALYSIS_DIR}/country_typology.csv")
    combined_panel = pd.read_csv("data/final/combined_panel_with_risk_index.csv")

    print("Step 2: Building cross-sectional hypothesis snapshot...")
    snapshot = build_hypothesis_snapshot(country_typology, combined_panel)
    print(f"  -> {snapshot.shape[0]} countries in snapshot")
    print(f"  -> Have Gini_Index: {snapshot['Gini_Index'].notna().sum()}")
    print(f"  -> Have UHC_End: {snapshot['UHC_End'].notna().sum()}")
    print(f"  -> Have Income_Group_Ordinal: {snapshot['Income_Group_Ordinal'].notna().sum()}")

    print("\n" + "=" * 70)
    print("THREAD 3: EQUALITY HYPOTHESIS")
    print("=" * 70)
    equality_result, equality_summary = run_equality_hypothesis(snapshot)

    step1 = equality_summary["step1_income_to_obesity_regression"]
    print(f"\nStep 1 - Obesity_End predicted from Income_Group_Ordinal:")
    print(f"  Obesity = {step1['intercept']:.2f} + {step1['slope']:.2f} x Income_Level")
    print(f"  R-squared = {step1['r_squared']:.3f}  (n = {step1['n']})")
    print(f"  -> Income level alone explains {step1['r_squared']*100:.1f}% of obesity variation.")
    print(f"  -> The rest (Obesity_Residual) is what's left to explain.")

    step2 = equality_summary["step2_residual_vs_gini_correlation"]
    print(f"\nStep 2 - Does that leftover residual correlate with income EQUALITY (Gini)?")
    print(" ", _interpret_correlation(step2["pearson_r"], step2["p_value"], step2["n"], "Obesity_Residual vs Gini_Index"))

    if "step3_within_wealthy_cluster_robustness_check" in equality_summary:
        step3 = equality_summary["step3_within_wealthy_cluster_robustness_check"]
        print(f"\nStep 3 - Robustness check: same test, but ONLY within the 'Wealthy")
        print(f"  Decouplers' cluster (where the original Japan/Korea vs USA/UK")
        print(f"  anomaly actually lives, rather than diluted across all 200 countries):")
        print(" ", _interpret_correlation(step3["pearson_r"], step3["p_value"], step3["n"], "Obesity_End vs Gini_Index (within cluster)"))

    equality_result.to_csv(f"{ANALYSIS_DIR}/equality_hypothesis_results.csv", index=False)
    print(f"\nSaved: {ANALYSIS_DIR}/equality_hypothesis_results.csv")

    print("\n" + "=" * 70)
    print("THREAD 4: ACCESS HYPOTHESIS")
    print("=" * 70)
    access_result, access_summary = run_access_hypothesis(snapshot)

    step1 = access_summary["step1_obesity_to_bp_regression"]
    print(f"\nStep 1 - BP_End predicted from Obesity_End:")
    print(f"  BP = {step1['intercept']:.2f} + {step1['slope']:.2f} x Obesity")
    print(f"  R-squared = {step1['r_squared']:.3f}  (n = {step1['n']})")
    print(f"  -> Obesity level alone explains {step1['r_squared']*100:.1f}% of BP variation.")
    print(f"  -> The rest (BP_Residual) is what's left to explain.")

    step2 = access_summary["step2_residual_vs_uhc_correlation"]
    print(f"\nStep 2 - Does that leftover residual correlate with healthcare ACCESS (UHC)?")
    print(" ", _interpret_correlation(step2["pearson_r"], step2["p_value"], step2["n"], "BP_Residual vs UHC_End"))

    access_result.to_csv(f"{ANALYSIS_DIR}/access_hypothesis_results.csv", index=False)
    print(f"\nSaved: {ANALYSIS_DIR}/access_hypothesis_results.csv")

    return equality_result, access_result, equality_summary, access_summary


if __name__ == "__main__":
    main()
