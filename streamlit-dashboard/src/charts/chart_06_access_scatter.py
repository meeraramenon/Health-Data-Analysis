"""
chart_06_access_scatter.py
-----------------------------
Visual #6: Thread 4's answer to "does healthcare ACCESS explain who
escapes high BP?" - and this one IS confirmed strongly (r=-0.479,
p<0.0001), so the design goal here is the opposite of chart 5: make the
real, significant negative relationship unmistakable.

DESIGN INTENT: the regression line actually has a meaningful slope here,
so it's drawn solid (not dashed like chart 5's near-null line) and in the
coral accent colour - this is the headline confirmed result, so it earns
the one "this matters" colour. Points are coloured by WHO_Region instead
of Income_Group, to show the relationship holds across regions, not just
within the wealthy world (a stronger, more general claim than chart 5
could make).
"""

import pandas as pd
import altair as alt

import sys
sys.path.insert(0, "src")
from charts.chart_theme import CHART_WIDTH, CHART_HEIGHT, make_title, CORAL


def build_access_scatter(access_results: pd.DataFrame) -> alt.Chart:
    """
    Returns the BP_Residual vs. UHC_End scatter, coloured by WHO_Region,
    with a solid coral regression line marking the confirmed relationship.
    """
    data = access_results.dropna(subset=["BP_Residual", "UHC_End"]).copy()
    data["WHO_Region"] = data["WHO_Region"].fillna("Not classified")

    points = (
        alt.Chart(data)
        .mark_circle(size=90, stroke="white", strokeWidth=0.5, opacity=0.85)
        .encode(
            x=alt.X("UHC_End:Q", title="UHC Service Coverage Index (healthcare access, 0-100)"),
            y=alt.Y("BP_Residual:Q", title="BP Residual (actual minus obesity-predicted BP)"),
            color=alt.Color("WHO_Region:N", title="WHO Region", scale=alt.Scale(scheme="dark2")),
            tooltip=[
                alt.Tooltip("Country:N"),
                alt.Tooltip("WHO_Region:N"),
                alt.Tooltip("UHC_End:Q", title="UHC Index", format=".1f"),
                alt.Tooltip("BP_Residual:Q", title="BP Residual", format=".1f"),
            ],
        )
    )

    # NOTE: transform_regression() inherits its base chart's encodings,
    # including the WHO_Region colour channel - without overriding colour
    # explicitly here, the regression line silently renders in whatever
    # colour that channel assigns rather than the intended fixed coral.
    regression_line = (
        points.transform_regression("UHC_End", "BP_Residual")
        .mark_line(strokeWidth=3)
        .encode(color=alt.value(CORAL))
    )

    zero_line = (
        alt.Chart(pd.DataFrame({"y": [0]}))
        .mark_rule(strokeDash=[2, 2], color="#bbbbb0")
        .encode(y="y:Q")
    )

    chart = (
        (points + regression_line + zero_line)
        .properties(
            width=CHART_WIDTH,
            height=CHART_HEIGHT,
            title=make_title(
                "Healthcare Access Really Does Explain Who Escapes High Blood Pressure",
                eyebrow_number=6,
                subtitle_lines=[
                    "r=-0.479, p<0.0001, n=192 countries - one of the strongest results in this entire analysis.",
                    "Higher UHC access -> blood pressure meaningfully lower than obesity level alone would predict.",
                ],
            ),
        )
    )

    return chart
