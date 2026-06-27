"""
chart_04_convergence_trend.py
--------------------------------
Visual #4: Thread 2's answer to "is the gap between countries widening or
narrowing?" - shown as three CV-over-time lines, with a clearly
distinguished extrapolated segment.

DESIGN INTENT: the headline finding is that Obesity's convergence is
extremely consistent (R-squared=0.999) while BP is weaker and Diabetes is
flat. To make that DIFFERENCE in reliability visible (not just the
direction), each line's solid (observed) portion is followed by a dashed
(extrapolated) portion - dashing is used here specifically because it's
the conventional visual signal for "projected, not measured", which a
reader can interpret without needing to consult the legend.

The coral accent is used deliberately on the Obesity line ONLY (the
strongest, most reliable finding), keeping BP and Diabetes in muted
indigo/olive tones - this directs the eye to the most important line
without needing an arrow or annotation.
"""

import pandas as pd
import altair as alt

import sys
sys.path.insert(0, "src")
from charts.chart_theme import INDIGO, CORAL, CHART_WIDTH, CHART_HEIGHT, make_title

DISEASE_COLOR_MAP = {
    "Obesity": CORAL,           # the headline finding - the one accent colour, used once
    "Blood Pressure": INDIGO,
    "Diabetes": "#8a8a3c",
}

DISEASE_LABELS = {"BP": "Blood Pressure", "Obesity": "Obesity", "Diabetes": "Diabetes"}


def _prepare_long_data(cv_by_year: pd.DataFrame, trend_extrapolation: pd.DataFrame) -> pd.DataFrame:
    """
    Combines the observed CV series with the extrapolated trend, into one
    long-format table: Year | Disease | CV | Is_Extrapolated
    """
    observed_long = cv_by_year.melt(
        id_vars=["Year"],
        value_vars=["BP_CV", "Obesity_CV", "Diabetes_CV"],
        var_name="Disease_Raw",
        value_name="CV",
    )
    observed_long["Disease"] = observed_long["Disease_Raw"].str.replace("_CV", "").map(DISEASE_LABELS)
    observed_long["Is_Extrapolated"] = False
    observed_long = observed_long.drop(columns="Disease_Raw")

    extrapolated = trend_extrapolation[trend_extrapolation["Is_Extrapolated"]].copy()
    extrapolated["Disease"] = extrapolated["Metric"].map(DISEASE_LABELS)

    # trend_extrapolation stores the CV value under a metric-specific column
    # name (e.g. "BP_CV", "Obesity_CV", "Diabetes_CV") depending on which
    # metric that row belongs to, with the other two columns NaN for that
    # row. This picks out whichever one is actually populated.
    def _get_cv_value(row):
        for col in ["BP_CV", "Obesity_CV", "Diabetes_CV"]:
            if col in row and pd.notna(row[col]):
                return row[col]
        return None

    extrapolated["CV"] = extrapolated.apply(_get_cv_value, axis=1)
    extrapolated = extrapolated[["Year", "Disease", "CV", "Is_Extrapolated"]]

    # Bridge point: repeat the last observed year as the first extrapolated
    # point too, so the dashed segment connects seamlessly to the solid line
    # rather than leaving a visual gap.
    bridge_rows = []
    for disease in observed_long["Disease"].unique():
        last_observed = observed_long[observed_long["Disease"] == disease].sort_values("Year").iloc[-1]
        bridge_rows.append({
            "Year": last_observed["Year"], "Disease": disease,
            "CV": last_observed["CV"], "Is_Extrapolated": True,
        })
    bridge_df = pd.DataFrame(bridge_rows)

    combined = pd.concat([observed_long, bridge_df, extrapolated], ignore_index=True)
    return combined.sort_values(["Disease", "Is_Extrapolated", "Year"]).reset_index(drop=True)


def build_convergence_trend_chart(cv_by_year: pd.DataFrame, trend_extrapolation: pd.DataFrame) -> alt.Chart:
    """
    Returns the convergence/divergence line chart: 3 diseases, solid
    observed lines (1980-2014) flowing into dashed extrapolated lines
    (2015-2024).
    """
    data = _prepare_long_data(cv_by_year, trend_extrapolation)

    color_scale = alt.Scale(domain=list(DISEASE_COLOR_MAP.keys()), range=list(DISEASE_COLOR_MAP.values()))

    observed_line = (
        alt.Chart(data[~data["Is_Extrapolated"]])
        .mark_line(strokeWidth=2.6)
        .encode(
            x=alt.X("Year:Q", title=None, axis=alt.Axis(format="d")),
            y=alt.Y("CV:Q", title="Coefficient of Variation (between-country dispersion)"),
            color=alt.Color("Disease:N", title="Disease", scale=color_scale),
        )
    )

    extrapolated_line = (
        alt.Chart(data[data["Is_Extrapolated"]])
        .mark_line(strokeWidth=2.6, strokeDash=[6, 4], opacity=0.75)
        .encode(
            x=alt.X("Year:Q", title=None),
            y=alt.Y("CV:Q"),
            color=alt.Color("Disease:N", scale=color_scale, title="Disease"),
        )
    )

    points = (
        alt.Chart(data)
        .mark_circle(size=28)
        .encode(
            x="Year:Q",
            y="CV:Q",
            color=alt.Color("Disease:N", scale=color_scale, title="Disease"),
            opacity=alt.condition(alt.datum.Is_Extrapolated, alt.value(0.4), alt.value(0.9)),
            tooltip=[
                alt.Tooltip("Disease:N"),
                alt.Tooltip("Year:Q", format="d"),
                alt.Tooltip("CV:Q", title="CV", format=".3f"),
                alt.Tooltip("Is_Extrapolated:N", title="Projected?"),
            ],
        )
    )

    divider = (
        alt.Chart(pd.DataFrame({"x": [2014]}))
        .mark_rule(strokeDash=[2, 2], color="#999990", strokeWidth=1)
        .encode(x="x:Q")
    )

    chart = (
        (observed_line + extrapolated_line + points + divider)
        .properties(
            width=CHART_WIDTH,
            height=CHART_HEIGHT,
            title=make_title(
                "Obesity Inequality Between Countries Is Closing - On an Almost Perfect Trend",
                eyebrow_number=4,
                subtitle_lines=[
                    "Dashed lines (2015-2024) are a simple straight-line projection, NOT a validated forecast.",
                    "Obesity's trend fits at R\u00b2=0.999; Blood Pressure is weaker (R\u00b2=0.27); Diabetes shows no real trend (R\u00b2=0.08).",
                ],
            ),
        )
    )

    return chart
