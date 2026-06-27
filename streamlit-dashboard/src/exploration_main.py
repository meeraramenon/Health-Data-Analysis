"""
exploration_main.py
----------------------
Orchestrates Stage 5: the Equality Hypothesis follow-up + the 3 free
exploration checks. Added so this stage runs the same consistent way as
every other stage (previously these were only run ad hoc).

Run with: python3 src/exploration_main.py   (from the project/ folder)
Depends on: typology_main.py and hypothesis_main.py having already run.
"""

import sys
sys.path.insert(0, "src")

import pandas as pd
from load_exploration_data import load_fao_consumption_long, load_physical_inactivity_long
from equality_followup_exploration import build_followup_snapshot, highlight_anomaly_countries
from typology_features import build_trajectory_feature_table
from typology_clustering import scale_features
from free_exploration import (
    check_cluster_robustness,
    compute_convergence_by_income_group,
    compute_gender_gap_by_cluster,
)

ANALYSIS_DIR = "data/analysis"


def main():
    combined = pd.read_csv("data/final/combined_panel_with_risk_index.csv")
    country_typology = pd.read_csv(f"{ANALYSIS_DIR}/country_typology.csv")
    sex_gap_table = pd.read_csv("data/final/sex_gap_table.csv")

    print("=" * 70)
    print("EQUALITY HYPOTHESIS FOLLOW-UP (sugar / alcohol / inactivity)")
    print("=" * 70)
    fao_long, fao_unmatched = load_fao_consumption_long()
    inactivity_long = load_physical_inactivity_long()
    print(f"FAO consumption rows: {fao_long.shape[0]}  (unmatched area names: {fao_unmatched})")

    snapshot = build_followup_snapshot(country_typology, fao_long, inactivity_long)
    snapshot.to_csv(f"{ANALYSIS_DIR}/equality_followup_wealthy_cluster.csv", index=False)
    print(f"Saved: {ANALYSIS_DIR}/equality_followup_wealthy_cluster.csv")

    print("\nThe original anomaly countries, side by side:")
    print(highlight_anomaly_countries(snapshot).to_string(index=False))

    print("\n" + "=" * 70)
    print("FREE EXPLORATION CHECK 1: Cluster robustness")
    print("=" * 70)
    features, _ = build_trajectory_feature_table(combined)
    scaled, _ = scale_features(features)
    robustness = check_cluster_robustness(scaled, country_typology["Cluster"], k=5)
    print(f"Adjusted Rand Index: {robustness['adjusted_rand_index']:.3f}")
    print(f"Interpretation: {robustness['interpretation']}")
    with open(f"{ANALYSIS_DIR}/cluster_robustness_check.txt", "w") as f:
        f.write(f"Adjusted Rand Index (k-means vs hierarchical, k=5): {robustness['adjusted_rand_index']:.3f}\n")
        f.write(f"Interpretation: {robustness['interpretation']}\n")

    print("\n" + "=" * 70)
    print("FREE EXPLORATION CHECK 2: Convergence by income group")
    print("=" * 70)
    by_income = compute_convergence_by_income_group(combined)
    by_income.to_csv(f"{ANALYSIS_DIR}/convergence_by_income_group.csv", index=False)
    for grp in by_income["Income_Group"].unique():
        sub = by_income[by_income["Income_Group"] == grp]
        first, last = sub.iloc[0], sub.iloc[-1]
        print(f"{grp:25s}: {first['Year']}: CV={first['Obesity_CV']:.3f}  ->  "
              f"{last['Year']}: CV={last['Obesity_CV']:.3f}")
    print(f"Saved: {ANALYSIS_DIR}/convergence_by_income_group.csv")

    print("\n" + "=" * 70)
    print("FREE EXPLORATION CHECK 3: Gender gap by cluster")
    print("=" * 70)
    by_cluster = compute_gender_gap_by_cluster(sex_gap_table, country_typology)
    by_cluster.to_csv(f"{ANALYSIS_DIR}/gender_gap_by_cluster.csv", index=False)
    print(by_cluster.to_string(index=False))
    print(f"Saved: {ANALYSIS_DIR}/gender_gap_by_cluster.csv")

    return snapshot, robustness, by_income, by_cluster


if __name__ == "__main__":
    main()
