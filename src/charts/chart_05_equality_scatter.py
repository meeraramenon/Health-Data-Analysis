"""
chart_05_equality_scatter.py
-------------------------------
Visual #5: Thread 3's answer to "does income EQUALITY explain who stays
thin?" - and the honest answer is no, so this chart needs to show a weak/
absent relationship clearly, not dress it up.

DESIGN INTENT: a flat scatter with a near-zero trend line IS the finding.
Rather than hide that, the chart leans into it: the regression line is
shown, its near-zero slope is stated in the subtitle, and the 4 anomaly
countries that motivated this whole question (Japan, South Korea, UK, USA)
are individually labelled directly on the plot - so the reader can see
with their own eyes that Japan and the UK sit at almost the same Gini value
while being worlds apart on the y-axis.

COLOUR: Income_Group (the variable already "removed" via the residual) is
shown via colour anyway, specifically to demonstrate that even controlling
for income level, no clear equality-driven pattern emerges within or across
income tiers.
"""

import pandas as pd
import altair as alt

import sys
sys.path.insert(0, "src")
from charts.chart_theme import CHART_WIDTH, CHART_HEIGHT, make_title, INDIGO, CORAL

ANOMALY_COUNTRIES = ["Japan", "South Korea", "United Kingdom", "United States of America"]

INCOME_ORDER = ["Low income", "Lower middle income", "Upper middle income", "High income"]


def build_equality_scatter(equality_results: pd.DataFrame) -> alt.Chart:
    """
    Returns the Obesity_Residual vs. Gini_Index scatter, coloured by
    Income_Group, with a regression line and the 4 anomaly countries
    individually labelled.
    """
    data = equality_results.dropna(subset=["Obesity_Residual", "Gini_Index"])

    points = (
        alt.Chart(data)
        .mark_circle(size=90, stroke="white", strokeWidth=0.5, opacity=0.85)
        .encode(
            x=alt.X("Gini_Index:Q", title="Gini Index (income inequality, higher = less equal)"),
            y=alt.Y("Obesity_Residual:Q", title="Obesity Residual (actual minus income-predicted obesity)"),
            color=alt.Color(
                "Income_Group:N", title="Income Group",
                scale=alt.Scale(domain=INCOME_ORDER, scheme="dark2"),
            ),
            tooltip=[
                alt.Tooltip("Country:N"),
                alt.Tooltip("Income_Group:N"),
                alt.Tooltip("Gini_Index:Q", format=".1f"),
                alt.Tooltip("Obesity_Residual:Q", title="Obesity Residual", format=".1f"),
            ],
        )
    )

    # NOTE: transform_regression() inherits the base chart's encodings,
    # including the Income_Group colour channel - color must be explicitly
    # overridden here or the line silently renders in an inherited colour
    # instead of the intended neutral grey.
    regression_line = (
        points.transform_regression("Gini_Index", "Obesity_Residual")
        .mark_line(strokeDash=[4, 3], strokeWidth=2)
        .encode(color=alt.value("#999990"))
    )

    zero_line = (
        alt.Chart(pd.DataFrame({"y": [0]}))
        .mark_rule(strokeDash=[2, 2], color="#bbbbb0")
        .encode(y="y:Q")
    )

    anomaly_data = data[data["Country"].isin(ANOMALY_COUNTRIES)]
    anomaly_labels = (
        alt.Chart(anomaly_data)
        .mark_text(dy=-14, fontSize=11, fontWeight="bold", color=CORAL)
        .encode(x="Gini_Index:Q", y="Obesity_Residual:Q", text="Country:N")
    )
    anomaly_points = (
        alt.Chart(anomaly_data)
        .mark_circle(size=140, stroke=CORAL, strokeWidth=2.5, fillOpacity=0)
        .encode(x="Gini_Index:Q", y="Obesity_Residual:Q")
    )

    chart = (
        (points + regression_line + zero_line + anomaly_points + anomaly_labels)
        .properties(
            width=CHART_WIDTH,
            height=CHART_HEIGHT,
            title=make_title(
                "Income Equality Does Not Explain Who Stays Thin",
                eyebrow_number=5,
                subtitle_lines=[
                    "r=0.019, p=0.81 (not significant) - the dashed trend line is essentially flat.",
                    "Japan and the UK have nearly identical Gini scores (32.3 vs 32.4) yet wildly different obesity outcomes.",
                ],
            ),
        )
    )

    return chart
