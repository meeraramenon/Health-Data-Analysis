"""
chart_07_risk_leaderboard.py
-------------------------------
SUPPLEMENTARY chart (not tied to one specific hypothesis test) - a
Top 10 / Bottom 10 leaderboard for the composite Metabolic Risk Index in
2014. This exists to give the reader concrete, nameable countries to
anchor on early, before the more abstract statistical charts (PCA scatter,
residual plots) - a common, effective pattern in data journalism: ground
the abstract analysis in specific, checkable real-world examples.

DESIGN: a single diverging horizontal bar chart - highest 10 countries in
coral (the "this is concerning" accent), lowest 10 in indigo (the calm,
"baseline" colour), sorted so the two groups read top-to-bottom as a
continuous ranking rather than two disconnected charts. This is a more
information-dense alternative to the reference report's separate
Obesity/BP/Diabetes leaderboards - one chart for the composite measure
instead of three for the individual ones.
"""

import pandas as pd
import altair as alt

import sys
sys.path.insert(0, "src")
from charts.chart_theme import INDIGO, CORAL, CHART_WIDTH, make_title


def build_risk_leaderboard(combined_panel: pd.DataFrame, year: int = 2014, n: int = 10) -> alt.Chart:
    """
    Returns a diverging Top-N/Bottom-N leaderboard for Metabolic_Risk_Index
    in the given year.
    """
    snapshot = combined_panel[combined_panel["Year"] == year].dropna(subset=["Metabolic_Risk_Index"])

    top = snapshot.nlargest(n, "Metabolic_Risk_Index").copy()
    top["Group"] = "Highest risk"

    bottom = snapshot.nsmallest(n, "Metabolic_Risk_Index").copy()
    bottom["Group"] = "Lowest risk"

    data = pd.concat([top, bottom])

    chart = (
        alt.Chart(data)
        .mark_bar(height=14)
        .encode(
            x=alt.X("Metabolic_Risk_Index:Q", title="Metabolic Risk Index (composite, 0-100 scale)"),
            y=alt.Y("Country:N", title=None, sort=alt.SortField("Metabolic_Risk_Index", order="descending")),
            color=alt.Color(
                "Group:N", title=None,
                scale=alt.Scale(domain=["Highest risk", "Lowest risk"], range=[CORAL, INDIGO]),
                legend=alt.Legend(orient="top"),
            ),
            tooltip=[
                alt.Tooltip("Country:N"),
                alt.Tooltip("Metabolic_Risk_Index:Q", format=".1f"),
                alt.Tooltip("BP_Prevalence_pct:Q", title="BP (%)", format=".1f"),
                alt.Tooltip("Obesity_Prevalence_pct:Q", title="Obesity (%)", format=".1f"),
                alt.Tooltip("Diabetes_Prevalence_pct:Q", title="Diabetes (%)", format=".1f"),
            ],
        )
        .properties(
            width=CHART_WIDTH,
            height=420,
            title=make_title(
                f"The {n} Highest- and {n} Lowest-Risk Countries, {year}",
                eyebrow_number=1,
                subtitle_lines=[
                    "Composite Metabolic Risk Index: BP, Obesity, and Diabetes combined into one equally-weighted, normalised score.",
                ],
            ),
        )
    )

    return chart
