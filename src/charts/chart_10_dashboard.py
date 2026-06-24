"""
chart_10_dashboard.py
-------------------------
Visual #10 (final): the interactive linked dashboard - brings multiple
threads together into one explorable view, rather than introducing new
analysis. This is built LAST and reuses data already produced by Threads
1, 2, and 5.

DESIGN: two linked panels.
  LEFT  - a cluster scatter (Obesity vs. BP, end-of-period values), with a
          WHO Region dropdown filter (alt.binding_select) that narrows
          which countries are shown.
  RIGHT - a trajectory detail panel that is EMPTY until the reader clicks
          a point on the left - clicking a country draws its full
          1980-2014 BP/Obesity/Diabetes trajectory on the right. This is
          the "drill from overview to detail" pattern: the left panel
          answers "where does this country sit relative to everyone
          else", the right panel answers "what did getting there actually
          look like".

WHY CLICK-TO-REVEAL RATHER THAN ALWAYS SHOWING ALL TRAJECTORIES: with 200
countries, a trajectory chart showing everyone at once is unreadable (this
is exactly the problem the Thread 1 small-multiples chart solved by
aggregating to 5 clusters instead). The dashboard's job is different - it
lets the reader inspect ONE country at a time, on demand, which is only
possible with an interactive selection, not a static chart.

A WHO Region dropdown additionally filters the left panel, so the two
controls together (region filter + point click) cover both "show me a
slice of the world" and "show me one specific country" - directly
addressing the "filtering options"/"dashboard elements" marking criteria.
"""

import os
import sys
_SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

import pandas as pd
import altair as alt
from charts.chart_theme import INDIGO, CORAL, make_title

DISEASE_COLOR_MAP = {
    "Blood Pressure": INDIGO,
    "Obesity": CORAL,
    "Diabetes": "#8a8a3c",
}


def _prepare_overview_data(country_typology: pd.DataFrame, combined_panel: pd.DataFrame) -> pd.DataFrame:
    """
    One row per country: end-of-period BP/Obesity, cluster, region.
    WHO_Region isn't in country_typology.csv itself - it's pulled in here
    from the combined panel (most recent non-null value per country).
    """
    who_region_lookup = (
        combined_panel.sort_values("Year")
        .groupby("Country")["WHO_Region"]
        .last()
    )
    data = country_typology.copy()
    data["WHO_Region"] = data["Country"].map(who_region_lookup).fillna("Not classified")
    return data


def _prepare_trajectory_data(combined_panel: pd.DataFrame) -> pd.DataFrame:
    """Long-format full 1980-2014 trajectory data, one row per country/year/disease."""
    window = combined_panel[(combined_panel["Year"] >= 1980) & (combined_panel["Year"] <= 2014)]
    long_df = window.melt(
        id_vars=["Country", "Year"],
        value_vars=["BP_Prevalence_pct", "Obesity_Prevalence_pct", "Diabetes_Prevalence_pct"],
        var_name="Disease_Raw",
        value_name="Prevalence_pct",
    )
    long_df["Disease"] = long_df["Disease_Raw"].map({
        "BP_Prevalence_pct": "Blood Pressure",
        "Obesity_Prevalence_pct": "Obesity",
        "Diabetes_Prevalence_pct": "Diabetes",
    })
    return long_df[["Country", "Year", "Disease", "Prevalence_pct"]]


def build_dashboard(country_typology: pd.DataFrame, combined_panel: pd.DataFrame) -> alt.Chart:
    """
    Returns the full linked dashboard: overview scatter (left) + on-click
    trajectory detail (right), with a WHO Region dropdown filtering the
    overview panel.
    """
    overview_data = _prepare_overview_data(country_typology, combined_panel)
    trajectory_data = _prepare_trajectory_data(combined_panel)

    region_options = ["All regions"] + sorted(overview_data["WHO_Region"].unique().tolist())
    region_dropdown = alt.param(
        name="region_filter",
        value="All regions",
        bind=alt.binding_select(options=region_options, name="WHO Region: "),
    )

    click_selection = alt.selection_point(fields=["Country"], on="click", empty=False, name="country_click")

    overview = (
        alt.Chart(overview_data)
        .mark_circle(size=110, stroke="white", strokeWidth=0.5)
        .encode(
            x=alt.X("Obesity_End:Q", title="Obesity, 2010-14 avg (%)"),
            y=alt.Y("BP_End:Q", title="Blood Pressure, 2010-14 avg (%)"),
            color=alt.Color("Cluster_Name:N", title="Typology Cluster"),
            opacity=alt.condition(click_selection, alt.value(1.0), alt.value(0.55)),
            size=alt.condition(click_selection, alt.value(260), alt.value(110)),
            tooltip=[
                alt.Tooltip("Country:N"),
                alt.Tooltip("Cluster_Name:N"),
                alt.Tooltip("WHO_Region:N"),
                alt.Tooltip("Obesity_End:Q", format=".1f"),
                alt.Tooltip("BP_End:Q", format=".1f"),
            ],
        )
        .transform_filter(
            (alt.datum.WHO_Region == region_dropdown) | (region_dropdown == "All regions")
        )
        .add_params(region_dropdown, click_selection)
        .properties(width=380, height=420, title="Click a country to see its full trajectory")
    )

    detail = (
        alt.Chart(trajectory_data)
        .mark_line(strokeWidth=2.4)
        .encode(
            x=alt.X("Year:Q", title=None, axis=alt.Axis(format="d", values=[1980, 1990, 2000, 2010, 2014])),
            y=alt.Y("Prevalence_pct:Q", title="Prevalence (%)", scale=alt.Scale(domain=[0, 60])),
            color=alt.Color(
                "Disease:N", title="Disease",
                scale=alt.Scale(domain=list(DISEASE_COLOR_MAP.keys()), range=list(DISEASE_COLOR_MAP.values())),
            ),
            tooltip=[alt.Tooltip("Disease:N"), alt.Tooltip("Year:Q", format="d"), alt.Tooltip("Prevalence_pct:Q", format=".1f")],
        )
        .transform_filter(click_selection)
        .properties(width=380, height=420, title="Selected country's 1980-2014 trajectory")
    )

    dashboard = (
        alt.hconcat(overview, detail)
        .resolve_scale(color="independent")
        .properties(
            title=make_title(
                "Explore the Typology Yourself - Pick a Region, Click a Country",
                eyebrow_number=9,
                subtitle_lines=[
                    "Left: every country positioned by its 2010-14 Obesity/BP averages, coloured by cluster. Filter by WHO Region with the dropdown.",
                    "Right: click any point on the left to draw that country's full 35-year trajectory across all 3 diseases.",
                ],
            )
        )
    )

    return dashboard
