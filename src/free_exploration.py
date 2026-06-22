"""
free_exploration.py
----------------------
Three additional checks that need NO new external data - they just ask
more questions of data already merged. Each is a genuine robustness/depth
check, not decoration:

1. CLUSTER ROBUSTNESS: does a completely different clustering algorithm
   (hierarchical/agglomerative) agree with the k-means typology from
   Thread 1? If two different methods land on similar groups, that's real
   evidence the typology reflects something genuine in the data, not an
   artifact of k-means specifically.

2. CONVERGENCE BY INCOME GROUP: Thread 2 found between-country obesity
   inequality is shrinking globally. Does that hold within each income
   tier too, or is the global trend actually driven by one tier (e.g. is
   it really "everyone converging", or "only middle-income countries
   converging, masked by an unrelated global average")?

3. GENDER GAP BY CLUSTER: Thread 5 found the obesity gender gap moves with
   country-level convergence globally (r=-0.969). Is that relationship
   uniform across all 5 typology clusters, or concentrated in specific ones?
"""

import pandas as pd
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import adjusted_rand_score


def check_cluster_robustness(feature_table_scaled, kmeans_labels: pd.Series, k: int = 5) -> dict:
    """
    Re-clusters the same scaled features with hierarchical (agglomerative)
    clustering instead of k-means, then measures agreement with the
    Adjusted Rand Index (ARI): 1.0 = identical groupings, 0.0 = no better
    than random agreement, negative = worse than random.
    """
    hierarchical = AgglomerativeClustering(n_clusters=k, linkage="ward")
    hierarchical_labels = hierarchical.fit_predict(feature_table_scaled)

    ari = adjusted_rand_score(kmeans_labels, hierarchical_labels)

    agreement_quality = (
        "strong agreement - the typology is robust to choice of algorithm" if ari > 0.5 else
        "moderate agreement - the broad shape is consistent, some boundary differences" if ari > 0.2 else
        "weak agreement - the two methods see different structure"
    )

    return {
        "adjusted_rand_index": ari,
        "interpretation": agreement_quality,
        "hierarchical_labels": hierarchical_labels,
    }


def compute_convergence_by_income_group(combined_panel: pd.DataFrame,
                                          year_min: int = 1980, year_max: int = 2014) -> pd.DataFrame:
    """
    Computes the same Coefficient of Variation as Thread 2, but separately
    for each Income_Group, for Obesity specifically (the metric with the
    strongest global convergence signal).

    Returns one row per (Year, Income_Group): Year | Income_Group | Obesity_CV | N_Countries
    Income groups with very few countries in a given year produce a noisy
    CV - N_Countries is included so that can be judged directly rather than
    hidden.
    """
    window = combined_panel[
        (combined_panel["Year"] >= year_min) & (combined_panel["Year"] <= year_max)
    ]

    rows = []
    for (year, income_group), group in window.groupby(["Year", "Income_Group"], dropna=True):
        values = group["Obesity_Prevalence_pct"].dropna()
        if len(values) < 3:
            continue  # too few countries that year/group for a meaningful CV
        mean = values.mean()
        std = values.std()
        rows.append({
            "Year": year,
            "Income_Group": income_group,
            "Obesity_CV": std / mean if mean != 0 else float("nan"),
            "N_Countries": len(values),
        })

    return pd.DataFrame(rows).sort_values(["Income_Group", "Year"]).reset_index(drop=True)


def compute_gender_gap_by_cluster(sex_gap_table: pd.DataFrame, country_typology: pd.DataFrame,
                                    year_min: int = 1980, year_max: int = 2014) -> pd.DataFrame:
    """
    For each typology cluster, computes the 1980 and 2014 average Obesity
    gender gap, and the change between them - to see whether the widening
    gender gap found globally in Thread 5 is uniform across clusters or
    concentrated in specific ones.

    Returns one row per cluster: Cluster_Name | Gap_1980 | Gap_2014 | Change | N_Countries
    """
    merged = sex_gap_table.merge(
        country_typology[["Country", "Cluster_Name"]], on="Country", how="inner"
    )
    window = merged[(merged["Year"] >= year_min) & (merged["Year"] <= year_max)]

    rows = []
    for cluster_name, group in window.groupby("Cluster_Name"):
        gap_1980 = group[group["Year"] == year_min]["Obesity_Sex_Gap_pct"].mean()
        gap_2014 = group[group["Year"] == year_max]["Obesity_Sex_Gap_pct"].mean()
        n_countries = group["Country"].nunique()
        rows.append({
            "Cluster_Name": cluster_name,
            "Gap_1980": gap_1980,
            "Gap_2014": gap_2014,
            "Change": gap_2014 - gap_1980,
            "N_Countries": n_countries,
        })

    return pd.DataFrame(rows).sort_values("Change", ascending=False).reset_index(drop=True)
