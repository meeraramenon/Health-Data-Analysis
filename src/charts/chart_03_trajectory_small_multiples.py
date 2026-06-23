"""
chart_03_trajectory_small_multiples.py
-----------------------------------------
Visual #3: trajectory small multiples - the intuitive storytelling partner
to the abstract PCA scatter in chart_02. Where chart_02 proves the 5
clusters are mathematically distinct, this chart shows WHAT that distinction
actually looks like as a lived trajectory: real percentages, real years,
three disease lines per cluster.

DESIGN: one small panel per cluster (5 panels, arranged in a grid via
Altair's facet/concat), each panel showing the cluster's AVERAGE BP,
Obesity, and Diabetes curve from 1980-2014. The three diseases use a fixed
colour assignment across every panel (indigo=BP, coral=Obesity,
a third muted tone=Diabetes) so the reader learns the colour code once
and can read all 5 panels with it - critical for small multiples to work
as a format.

WHY THIS PARTICULAR DESIGN CHOICE: a single combined chart with all 5
clusters x 3 diseases as 15 overlapping lines would be unreadable. Small
multiples trade a single "wow" chart for something actually legible -
each panel is simple, and the grid lets the reader compare shapes by eye
across panels (the core small-multiples principle: facet what's complex,
keep each facet trivially simple).
"""

import pandas as pd
import altair as alt

import sys
sys.path.insert(0, "src")
from charts.chart_theme import INDIGO, CORAL, make_title

YEAR_MIN = 1980
YEAR_MAX = 2014

DISEASE_COLOR_MAP = {
    "Blood Pressure": INDIGO,
    "Obesity": CORAL,
    "Diabetes": "#8a8a3c",  # muted olive - distinct from both indigo and coral, low-key third tone
}

CLUSTER_ORDER = [
    "Pacific Extreme Outliers",
    "Lean Hypertension / Low-Obesity Rising-BP",
    "Wealthy Decouplers",
    "High-Starting-BP Recovery",
    "Moderate Transition",
]


def _build_cluster_year_averages(combined_panel: pd.DataFrame, country_typology: pd.DataFrame) -> pd.DataFrame:
    """
    For each cluster and year (1980-2014), computes the average BP, Obesity,
    and Diabetes value across all countries in that cluster, then reshapes
    to long format (one row per cluster/year/disease) for faceted plotting.
    """
    merged = combined_panel.merge(
        country_typology[["Country", "Cluster_Name"]], on="Country", how="inner"
    )
    window = merged[(merged["Year"] >= YEAR_MIN) & (merged["Year"] <= YEAR_MAX)]

    cluster_avg = (
        window.groupby(["Cluster_Name", "Year"])[
            ["BP_Prevalence_pct", "Obesity_Prevalence_pct", "Diabetes_Prevalence_pct"]
        ]
        .mean()
        .reset_index()
    )

    long_df = cluster_avg.melt(
        id_vars=["Cluster_Name", "Year"],
        value_vars=["BP_Prevalence_pct", "Obesity_Prevalence_pct", "Diabetes_Prevalence_pct"],
        var_name="Disease",
        value_name="Prevalence_pct",
    )
    long_df["Disease"] = long_df["Disease"].map({
        "BP_Prevalence_pct": "Blood Pressure",
        "Obesity_Prevalence_pct": "Obesity",
        "Diabetes_Prevalence_pct": "Diabetes",
    })

    return long_df


def build_trajectory_small_multiples(combined_panel: pd.DataFrame, country_typology: pd.DataFrame) -> alt.Chart:
    """
    Returns the 5-panel small-multiples chart, one panel per cluster.
    """
    data = _build_cluster_year_averages(combined_panel, country_typology)

    base = (
        alt.Chart(data)
        .mark_line(strokeWidth=2.4)
        .encode(
            x=alt.X("Year:Q", title=None, axis=alt.Axis(format="d", values=[1980, 1990, 2000, 2010, 2014])),
            y=alt.Y("Prevalence_pct:Q", title="Prevalence (%)", scale=alt.Scale(domain=[0, 55])),
            color=alt.Color(
                "Disease:N",
                title="Disease",
                scale=alt.Scale(domain=list(DISEASE_COLOR_MAP.keys()), range=list(DISEASE_COLOR_MAP.values())),
            ),
            tooltip=[
                alt.Tooltip("Cluster_Name:N", title="Cluster"),
                alt.Tooltip("Disease:N", title="Disease"),
                alt.Tooltip("Year:Q", title="Year", format="d"),
                alt.Tooltip("Prevalence_pct:Q", title="Avg. Prevalence (%)", format=".1f"),
            ],
        )
        .properties(width=260, height=190)
    )

    chart = (
        base.facet(
            facet=alt.Facet("Cluster_Name:N", title=None, sort=CLUSTER_ORDER),
            columns=3,
        )
        .resolve_scale(y="shared")
        .properties(
            title=make_title(
                "The Same Three Diseases, Five Completely Different Stories",
                eyebrow_number=3,
                subtitle_lines=[
                    "Average trajectory per cluster, 1980-2014. Same y-axis scale across all panels for fair comparison.",
                ],
            )
        )
    )

    return chart
