"""
chart_12_gender_gap_by_cluster.py
-------------------------------------
Supplementary visual: Stage 5's free-exploration finding that the globally
widening obesity gender gap (Thread 5) is NOT universal - it's only
widening in 2 of the 5 typology clusters, and actually NARROWING in the
other 3.

DESIGN: a diverging bar chart of the CHANGE (2014 minus 1980) per cluster -
bars extending right (widening) in coral, left (narrowing) in indigo. This
is a direct visual rebuttal to a naive "the world's gender gap is
widening" headline - it shows clearly that direction depends entirely on
which cluster a country belongs to.
"""

import os
import sys
_SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

import pandas as pd
import altair as alt
from charts.chart_theme import INDIGO, CORAL, CHART_WIDTH, make_title


def build_gender_gap_by_cluster_chart(gender_gap_by_cluster: pd.DataFrame) -> alt.Chart:
    """
    Returns a diverging bar chart of the obesity gender-gap CHANGE
    (2014 - 1980) per typology cluster.
    """
    data = gender_gap_by_cluster.copy()
    data["Direction"] = data["Change"].apply(lambda x: "Widening" if x > 0 else "Narrowing")

    chart = (
        alt.Chart(data)
        .mark_bar(height=28)
        .encode(
            x=alt.X("Change:Q", title="Change in Obesity Gender Gap, 1980 to 2014 (pp)"),
            y=alt.Y("Cluster_Name:N", title=None, sort=alt.SortField("Change", order="descending"),
                    axis=alt.Axis(labelLimit=260)),
            color=alt.Color(
                "Direction:N", title=None,
                scale=alt.Scale(domain=["Widening", "Narrowing"], range=[CORAL, INDIGO]),
                legend=alt.Legend(orient="top"),
            ),
            tooltip=[
                alt.Tooltip("Cluster_Name:N"),
                alt.Tooltip("Gap_1980:Q", title="1980 gap", format="+.2f"),
                alt.Tooltip("Gap_2014:Q", title="2014 gap", format="+.2f"),
                alt.Tooltip("Change:Q", title="Change", format="+.2f"),
                alt.Tooltip("N_Countries:Q", title="Countries"),
            ],
        )
        .properties(
            width=CHART_WIDTH,
            height=260,
            title=make_title(
                "The Widening Gender Gap Is Real - But Only in 2 of 5 Clusters",
                eyebrow_number=7,
                subtitle_lines=[
                    "The global average widening (Thread 5) is driven by the two largest clusters; the other 3 are narrowing.",
                    "Direction of the gender gap depends on which kind of country you're looking at, not a single universal trend.",
                ],
            ),
        )
    )

    return chart
