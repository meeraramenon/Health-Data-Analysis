"""
chart_11_convergence_by_income.py
-------------------------------------
Supplementary visual: Stage 5's free-exploration finding that the headline
Thread 2 result (obesity inequality between countries is shrinking,
R-squared=0.999) is NOT uniform - it's driven by the High and Low income
tiers, while Lower-middle income countries show almost no change at all
(0.674 -> 0.677).

DESIGN INTENT: 4 lines, one per income group, using a sequential-feeling
but still categorical colour progression (light to dark within the same
hue family) to visually suggest "income ladder" ordering even though the
underlying encoding is categorical (Income_Group is nominal in the data,
but reads naturally as ordinal here) - this is a deliberate exception to
the Dark2 categorical default, because an ordered concept (income tier)
benefits from a colour progression a reader can intuit without consulting
the legend every time.
"""

import os
import sys
_SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

import pandas as pd
import altair as alt
from charts.chart_theme import CHART_WIDTH, CHART_HEIGHT, make_title

INCOME_ORDER = ["Low income", "Lower middle income", "Upper middle income", "High income"]
# Light-to-dark within the coral/indigo family, deliberately suggesting an
# income "ladder" the reader can read without the legend.
INCOME_COLOR_RANGE = ["#f3b89a", "#e8623d", "#5b8a99", "#1B3A4B"]


def build_convergence_by_income_chart(convergence_by_income: pd.DataFrame) -> alt.Chart:
    """
    Returns the obesity-CV-over-time line chart, one line per income group.
    """
    data = convergence_by_income.copy()

    chart = (
        alt.Chart(data)
        .mark_line(strokeWidth=2.6, point=alt.OverlayMarkDef(size=22))
        .encode(
            x=alt.X("Year:Q", title=None, axis=alt.Axis(format="d", values=[1980, 1985, 1990, 1995, 2000, 2005, 2010, 2014])),
            y=alt.Y("Obesity_CV:Q", title="Coefficient of Variation (within-tier dispersion)"),
            color=alt.Color(
                "Income_Group:N", title="Income Group",
                scale=alt.Scale(domain=INCOME_ORDER, range=INCOME_COLOR_RANGE),
            ),
            tooltip=[
                alt.Tooltip("Income_Group:N"),
                alt.Tooltip("Year:Q", format="d"),
                alt.Tooltip("Obesity_CV:Q", format=".3f"),
                alt.Tooltip("N_Countries:Q", title="Countries that year"),
            ],
        )
        .properties(
            width=CHART_WIDTH,
            height=CHART_HEIGHT,
            title=make_title(
                "The Global Convergence Story Hides a Stuck Middle Tier",
                eyebrow_number=8,
                subtitle_lines=[
                    "High- and Low-income countries are both converging strongly on obesity; Lower-middle income is almost flat (0.674 -> 0.677).",
                    "The global Thread 2 headline finding is real, but driven by the top and bottom of the income ladder, not by every tier equally.",
                ],
            ),
        )
    )

    return chart
