"""
typology_clustering.py
------------------------
Runs k-means on the trajectory feature table built in typology_features.py,
following the decision rule already agreed:

  Do NOT just take the silhouette-maximizing k (which turned out to be k=2 -
  a near-useless split of "27 extreme outlier countries vs everyone else").
  Instead, evaluate k=4 through k=7, look at silhouette score AND inertia
  (elbow) AND the actual content of each cluster, and pick the smallest k
  that produces clusters which are genuinely distinct from each other.

WHY FEATURES ARE SCALED FIRST: k-means measures similarity as literal
numeric distance. Our 12 features are on very different scales (e.g. a
"Start" level might be 0-60, while a "Curvature" value might be -1 to 1).
Without scaling, the larger-scale features would dominate the clustering
just because their numbers are bigger, not because they're more important.
StandardScaler (z-score: mean 0, std 1) puts every feature on equal footing.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


def scale_features(feature_table: pd.DataFrame) -> tuple[np.ndarray, StandardScaler]:
    """
    Standardizes all feature columns to mean 0, std 1.
    Returns the scaled array plus the fitted scaler (kept in case we need to
    transform new data the same way later, e.g. for a forecast/extrapolation step).
    """
    scaler = StandardScaler()
    scaled = scaler.fit_transform(feature_table.values)
    return scaled, scaler


def evaluate_k_range(scaled_features: np.ndarray, k_values: list[int], random_state: int = 42) -> pd.DataFrame:
    """
    Fits k-means for each k in k_values and records:
      - inertia (within-cluster sum of squares - the "elbow" metric; lower is
        tighter clusters, but always decreases as k increases, so it's read
        for where the rate of decrease slows down, not for an absolute minimum)
      - silhouette score (-1 to 1; higher means better-separated clusters)

    Returns a small DataFrame, one row per k, meant to be plotted (elbow plot
    and silhouette plot) so the choice of k can be justified visually as well
    as numerically.
    """
    results = []
    for k in k_values:
        model = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        labels = model.fit_predict(scaled_features)
        sil_score = silhouette_score(scaled_features, labels)
        results.append({"k": k, "inertia": model.inertia_, "silhouette_score": sil_score})

    return pd.DataFrame(results)


def fit_final_clustering(feature_table: pd.DataFrame, scaled_features: np.ndarray,
                          k: int, random_state: int = 42) -> pd.DataFrame:
    """
    Fits the final k-means model with the chosen k and attaches the resulting
    cluster label back onto the original (unscaled) feature table, so cluster
    profiles can be read in real, interpretable units (percentage points),
    not z-scores.

    Returns the feature table with one new column: Cluster (integer label).
    """
    model = KMeans(n_clusters=k, random_state=random_state, n_init=10)
    labels = model.fit_predict(scaled_features)

    result = feature_table.copy()
    result["Cluster"] = labels
    return result


def summarize_clusters(feature_table_with_clusters: pd.DataFrame) -> pd.DataFrame:
    """
    Produces one row per cluster: how many countries it contains, and the
    average value of every feature within that cluster. This is the table
    to read BEFORE naming the clusters - it tells you what each cluster
    actually looks like in real terms (e.g. "this cluster starts high on
    obesity and keeps climbing" vs "this cluster starts low and stays flat").
    """
    feature_cols = [c for c in feature_table_with_clusters.columns if c != "Cluster"]

    profile = feature_table_with_clusters.groupby("Cluster")[feature_cols].mean()
    profile["N_Countries"] = feature_table_with_clusters.groupby("Cluster").size()

    return profile.round(2)


def list_countries_per_cluster(feature_table_with_clusters: pd.DataFrame) -> dict:
    """
    Returns {cluster_id: [list of country names]} - read this alongside
    summarize_clusters() to sanity-check that the clusters make geographic/
    economic sense, not just numeric sense.
    """
    return {
        cluster_id: sorted(group.index.tolist())
        for cluster_id, group in feature_table_with_clusters.groupby("Cluster")
    }
