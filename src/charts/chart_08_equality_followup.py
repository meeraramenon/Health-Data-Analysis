"""
chart_08_equality_followup.py
---------------------------------
Visual #8: the SELF-CORRECTION chart - this is a genuine storytelling
element, not just another result. It documents the moment the analysis
asked "if not income equality, then what?" and shows, honestly, that the
next three obvious candidates (sugar, alcohol, physical inactivity) don't
explain the Japan/Korea vs UK/USA gap either.

DESIGN INTENT: small multiples again (one panel per candidate variable),
but this time the point of the chart is an ABSENCE of a clean pattern -
the 4 countries should NOT line up neatly with their obesity outcomes in
any panel. The physical inactivity panel is the most interesting because
it runs backwards from intuition (Japan/Korea show MORE inactivity than
UK/USA despite far lower obesity) - this panel is the one to lead with in
the report's narrative.

WHY A SMALL SAMPLE GETS A COMPARISON CHART, NOT A SCATTER WITH A TREND
LINE: with only ~30-40 countries in the Wealthy Decouplers cluster (and
fewer once missing data is accounted for), a correlation/regression line
would be statistically unreliable. Showing the 4 specific countries
directly, side by side, is the honest way to present a sample this small -
no false precision.
"""

import pandas as pd
import altair as alt

import sys
sys.path.insert(0, "src")
from charts.chart_theme import INDIGO, CORAL, CHART_WIDTH, make_title

VARIABLE_CONFIG = {
    "Sugar_Sweeteners_kg_per_capita": "Sugar & Sweeteners (kg/capita/yr)",
    "Alcohol_kg_per_capita": "Alcohol (kg/capita/yr)",
    "Physical_Inactivity_pct": "Physical Inactivity (% adults)",
}

ANOMALY_ORDER = ["Japan", "South Korea", "United Kingdom", "United States of America"]


def build_equality_followup_chart(followup_snapshot: pd.DataFrame) -> alt.Chart:
    """
    Returns a 3-panel small-multiples bar chart (one per candidate
    variable: sugar, alcohol, inactivity), restricted to the 4 specific
    anomaly countries, coloured by whether that country is low-obesity
    (Japan/Korea) or high-obesity (UK/USA) within this comparison.
    """
    anomaly = followup_snapshot[followup_snapshot["Country"].isin(ANOMALY_ORDER)].copy()
    anomaly["Obesity_Group"] = anomaly["Obesity_End"].apply(
        lambda x: "Low obesity (Japan/Korea)" if x < 15 else "High obesity (UK/USA)"
    )

    long_data = anomaly.melt(
        id_vars=["Country", "Obesity_Group"],
        value_vars=list(VARIABLE_CONFIG.keys()),
        var_name="Variable",
        value_name="Value",
    )
    long_data["Variable_Label"] = long_data["Variable"].map(VARIABLE_CONFIG)

    chart = (
        alt.Chart(long_data)
        .mark_bar(size=32)
        .encode(
            x=alt.X("Country:N", title=None, sort=ANOMALY_ORDER, axis=alt.Axis(labelAngle=-25)),
            y=alt.Y("Value:Q", title=None),
            color=alt.Color(
                "Obesity_Group:N", title="Obesity outcome",
                scale=alt.Scale(domain=["Low obesity (Japan/Korea)", "High obesity (UK/USA)"], range=[INDIGO, CORAL]),
            ),
            column=alt.Column("Variable_Label:N", title=None, sort=list(VARIABLE_CONFIG.values())),
            tooltip=[
                alt.Tooltip("Country:N"),
                alt.Tooltip("Variable_Label:N", title="Measure"),
                alt.Tooltip("Value:Q", format=".1f"),
            ],
        )
        .properties(width=180, height=320)
        .properties(
            title=make_title(
                "Sugar, Alcohol, and Inactivity Don't Explain It Either",
                eyebrow_number=5,
                subtitle_lines=[
                    "Follow-up test after the Equality Hypothesis failed: none of these 3 candidates cleanly separate the pairs.",
                    "Inactivity runs BACKWARDS from intuition - Japan (50.6%) and Korea (60.7%) report MORE inactivity than the UK (21.9%) and US (36.4%).",
                ],
            )
        )
    )

    return chart
