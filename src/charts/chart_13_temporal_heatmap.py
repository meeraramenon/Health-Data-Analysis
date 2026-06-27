"""
chart_13_temporal_heatmap.py
-------------------------------
EARLY-UNDERSTANDING visual: a temporal heatmap, the kind of "first look at
the whole dataset at once" chart used near the start of an analysis to spot
where and when the crisis heated up, before any modelling.

This intentionally uses two encoding channels that the other charts barely
touch:
  - ROW facet (continent) x  X (year)  - a dense grid
  - COLOR intensity            - the metric value

DESIGN: one horizontal band per continent, time running left to right, with
colour deepening as prevalence rises. A dropdown switches the metric
(Metabolic Risk Index / BP / Obesity / Diabetes). This is the "global
warming of disease" style overview - it shows the reader the entire 35-year
story for every continent in a single glance, which is exactly what an
opening orientation chart should do.

WHY A HEATMAP HERE AND NOT A LINE CHART: with continents x years x metric,
a line chart would need many overlapping lines; a heatmap reads the same
data as a temperature map, where the eye picks up "deepening colour over
time" instantly without tracing individual lines. Heatmaps trade precise
value-reading (recoverable via tooltip) for immediate pattern-spotting,
which is the right trade for an orientation chart.
"""

import os
import sys
_SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

import pandas as pd
import altair as alt
from charts.chart_theme import SEQUENTIAL_SCHEME, make_title

METRIC_OPTIONS = {
    "Metabolic Risk Index": "Metabolic_Risk_Index",
    "Blood Pressure (%)": "BP_Prevalence_pct",
    "Obesity (%)": "Obesity_Prevalence_pct",
    "Diabetes (%)": "Diabetes_Prevalence_pct",
}


def _prepare_continent_year_data(combined_panel: pd.DataFrame) -> pd.DataFrame:
    """
    Averages each metric across all countries within a continent, per year,
    1980-2014. Returns one row per continent/year with all 4 metrics.
    """
    window = combined_panel[(combined_panel["Year"] >= 1980) & (combined_panel["Year"] <= 2014)]
    window = window.dropna(subset=["Continent"])

    agg = (
        window.groupby(["Continent", "Year"])[list(METRIC_OPTIONS.values())]
        .mean()
        .reset_index()
    )
    return agg


def build_temporal_heatmap(combined_panel: pd.DataFrame) -> alt.Chart:
    """
    Returns the continent x year temporal heatmap, with a metric-selector
    dropdown.
    """
    data = _prepare_continent_year_data(combined_panel)

    metric_param = alt.param(
        name="heat_metric",
        value="Metabolic Risk Index",
        bind=alt.binding_select(options=list(METRIC_OPTIONS.keys()), name="Metric: "),
    )

    # Build a calculate expression that picks the selected metric's column.
    calc_expr = "datum['" + METRIC_OPTIONS["Diabetes (%)"] + "']"
    for label in ["Obesity (%)", "Blood Pressure (%)", "Metabolic Risk Index"]:
        field = METRIC_OPTIONS[label]
        calc_expr = f"heat_metric == '{label}' ? datum['{field}'] : ({calc_expr})"

    chart = (
        alt.Chart(data)
        .transform_calculate(value_to_show=calc_expr)
        .mark_rect()
        .encode(
            x=alt.X("Year:O", title=None, axis=alt.Axis(values=[1980, 1985, 1990, 1995, 2000, 2005, 2010, 2014], labelAngle=0)),
            y=alt.Y("Continent:N", title=None, sort="-color"),
            color=alt.Color(
                "value_to_show:Q", title=None,
                scale=alt.Scale(scheme=SEQUENTIAL_SCHEME),
                legend=alt.Legend(orient="right", gradientLength=200),
            ),
            tooltip=[
                alt.Tooltip("Continent:N"),
                alt.Tooltip("Year:O"),
                alt.Tooltip("value_to_show:Q", title="Value", format=".1f"),
            ],
        )
        .add_params(metric_param)
        .properties(
            width=620,
            height=240,
            title=make_title(
                "The Global Warming of Disease: Where and When It Heated Up",
                eyebrow_number=1,
                subtitle_lines=[
                    "Each band is a continent; colour deepens as average prevalence rises. Use the dropdown to switch metric.",
                    "An orientation view of all 35 years at once, before any modelling - read it like a temperature map.",
                ],
            ),
        )
    )

    return chart
