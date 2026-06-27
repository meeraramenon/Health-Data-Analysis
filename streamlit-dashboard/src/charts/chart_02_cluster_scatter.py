"""
chart_02_cluster_scatter.py
------------------------------
Visual #2: the data-driven typology, shown as a 2D scatter.

DESIGN INTENT: the 12-dimensional feature space (4 features x 3 diseases)
can't be shown directly, so PCA compresses it to 2 dimensions for plotting.
This is disclosed honestly in the subtitle (PCA always loses some
information - the chart shows how much is retained via the variance-
explained note), rather than presenting 2D coordinates as if they were the
whole story.

INTERACTIVITY: clicking a cluster name in the legend isolates that cluster
(everything else fades to low opacity) - this lets the reader test the
typology themselves: "is the Pacific cluster really separate from
everyone else?" becomes something they can check by clicking, not just
something they're told.

COLOUR: the muted Dark2 categorical scheme (set in chart_theme.py) keeps
all 5 clusters distinguishable without looking like a bright default
dashboard legend.
"""

import pandas as pd
import altair as alt
from sklearn.decomposition import PCA

import sys
sys.path.insert(0, "src")
from charts.chart_theme import CHART_WIDTH, CHART_HEIGHT, make_title


def _add_pca_coordinates(country_typology: pd.DataFrame, scaled_features) -> pd.DataFrame:
    """
    Runs PCA on the same scaled feature matrix used for clustering, and
    attaches the first 2 principal components plus the % variance they
    explain (so the chart can disclose how much of the original 12-feature
    structure these 2 dimensions actually represent).
    """
    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(scaled_features)

    result = country_typology.copy()
    result["PC1"] = coords[:, 0]
    result["PC2"] = coords[:, 1]

    variance_explained = pca.explained_variance_ratio_
    return result, variance_explained


def build_cluster_scatter(country_typology: pd.DataFrame, scaled_features) -> alt.Chart:
    """
    Returns the interactive PCA cluster scatter chart.
    """
    data, variance_explained = _add_pca_coordinates(country_typology, scaled_features)
    total_variance = variance_explained.sum() * 100

    legend_selection = alt.selection_point(fields=["Cluster_Name"], bind="legend")

    chart = (
        alt.Chart(data)
        .mark_circle(size=110, stroke="white", strokeWidth=0.6)
        .encode(
            x=alt.X("PC1:Q", title=f"Principal Component 1", axis=alt.Axis(grid=True)),
            y=alt.Y("PC2:Q", title=f"Principal Component 2"),
            color=alt.Color(
                "Cluster_Name:N",
                title="Typology Cluster",
                legend=alt.Legend(orient="right", labelLimit=240, symbolSize=140),
            ),
            opacity=alt.condition(legend_selection, alt.value(0.9), alt.value(0.12)),
            tooltip=[
                alt.Tooltip("Country:N", title="Country"),
                alt.Tooltip("Cluster_Name:N", title="Cluster"),
                alt.Tooltip("BP_End:Q", title="BP 2010-14 avg (%)", format=".1f"),
                alt.Tooltip("Obesity_End:Q", title="Obesity 2010-14 avg (%)", format=".1f"),
                alt.Tooltip("Diabetes_End:Q", title="Diabetes 2010-14 avg (%)", format=".1f"),
            ],
        )
        .add_params(legend_selection)
        .properties(
            width=CHART_WIDTH,
            height=CHART_HEIGHT,
            title=make_title(
                "Five Distinct Health Journeys, Not One Global Story",
                eyebrow_number=2,
                subtitle_lines=[
                    f"Each point is a country, positioned by the shape of its 1980-2014 trajectory across all 3 diseases.",
                    f"Click a cluster in the legend to isolate it. These 2 axes capture {total_variance:.0f}% of the original 12-feature variation.",
                ],
            ),
        )
    )

    return chart
