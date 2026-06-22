"""
typology_main.py
------------------
Orchestrates the full typology (Thread 1) pipeline:
  1. Build trajectory features for all 200 countries
  2. Evaluate k=2 through k=8 (statistical diagnostics)
  3. Fit the final model at the chosen k
  4. Profile each cluster and assign a descriptive NAME based on its actual
     content (not decided in advance - see CLUSTER_NAMES below, which was
     written only after inspecting the profile table printed by this script)
  5. Save everything needed for the Altair visuals (cluster scatter,
     trajectory small multiples) to data/analysis/

Run with: python3 src/typology_main.py   (from the project/ folder)
"""

import sys
sys.path.insert(0, "src")

import pandas as pd
from typology_features import build_trajectory_feature_table
from typology_clustering import (
    scale_features, evaluate_k_range, fit_final_clustering,
    summarize_clusters, list_countries_per_cluster,
)

CHOSEN_K = 5
RANDOM_STATE = 42
ANALYSIS_DIR = "data/analysis"

# ---------------------------------------------------------------------------
# Cluster names - assigned AFTER inspecting the k=5 profile table (printed
# by this script), based on what each cluster actually contains. These are
# tied to the specific cluster index KMeans happens to assign with
# random_state=42 / n_init=10 on this feature set - if the upstream features
# or random_state ever change, re-run, re-inspect the profile table, and
# update this mapping accordingly (it is NOT guaranteed to stay index 0-4
# in this order if anything upstream changes).
# ---------------------------------------------------------------------------
CLUSTER_NAMES = {
    0: "Moderate Transition",
    1: "Pacific Extreme Outliers",
    2: "Wealthy Decouplers",
    3: "High-Starting-BP Recovery",
    4: "Lean Hypertension / Low-Obesity Rising-BP",
}


def main():
    combined = pd.read_csv("data/final/combined_panel_with_risk_index.csv")

    print("Step 1: Building trajectory features...")
    features, incomplete = build_trajectory_feature_table(combined)
    print(f"  -> {features.shape[0]} countries with complete features, {len(incomplete)} excluded")
    if incomplete:
        print(f"  -> Excluded: {incomplete}")

    print("\nStep 2: Evaluating k=2 through k=8...")
    scaled, scaler = scale_features(features)
    k_diagnostics = evaluate_k_range(scaled, k_values=list(range(2, 9)), random_state=RANDOM_STATE)
    k_diagnostics.to_csv(f"{ANALYSIS_DIR}/k_selection_diagnostics.csv", index=False)
    print(k_diagnostics.to_string(index=False))
    print(f"\n  NOTE: k=2 maximizes silhouette score but only separates extreme")
    print(f"  outliers from everyone else (not a useful typology). k={CHOSEN_K} is")
    print(f"  chosen instead - within the k=3-8 plateau, and validated below by")
    print(f"  checking cluster content is genuinely distinct.")

    print(f"\nStep 3: Fitting final model at k={CHOSEN_K}...")
    clustered = fit_final_clustering(features, scaled, k=CHOSEN_K, random_state=RANDOM_STATE)

    print("\nStep 4: Cluster profiles (inspect before trusting CLUSTER_NAMES above):")
    profile = summarize_clusters(clustered)
    print(profile.to_string())

    clustered["Cluster_Name"] = clustered["Cluster"].map(CLUSTER_NAMES)

    # Attach Country_Code/Continent/Income_Group back on for downstream
    # visuals (the choropleth and cluster scatter need these), pulling the
    # most recent non-null value per country from the combined panel.
    country_metadata = (
        combined.sort_values("Year")
        .groupby("Country")[["Country_Code", "Continent", "Income_Group"]]
        .last()
    )
    final_typology = clustered.join(country_metadata)
    final_typology.to_csv(f"{ANALYSIS_DIR}/country_typology.csv")
    profile.to_csv(f"{ANALYSIS_DIR}/cluster_profiles.csv")

    print(f"\nSaved: {ANALYSIS_DIR}/country_typology.csv (per-country cluster assignment + features)")
    print(f"Saved: {ANALYSIS_DIR}/cluster_profiles.csv (per-cluster average profile)")

    print("\nStep 5: Country lists per cluster (sanity-check geography/economics):")
    country_lists = list_countries_per_cluster(clustered)
    for cid, countries in country_lists.items():
        name = CLUSTER_NAMES.get(cid, "UNNAMED")
        print(f"\nCluster {cid} - '{name}' (n={len(countries)}):")
        print(countries)

    return final_typology, profile


if __name__ == "__main__":
    main()
