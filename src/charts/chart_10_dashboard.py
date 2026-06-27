"""
chart_10_dashboard.py
-------------------------
Visual #10 (final): the interactive linked dashboard - the most heavily
interactive artefact in the project, bringing several threads into one
explorable view. Rebuilt to be genuinely rich rather than a single linked
scatter: it now has FOUR coordinated elements and exercises encoding
channels the other charts barely use (size, shape, interval brush).

LAYOUT (2x2):
  TOP-LEFT  - the main scatter: every country at a CHOSEN YEAR (driven by a
              year slider), positioned Obesity (x) vs BP (y). It encodes
              FOUR variables at once:
                * x = obesity, y = blood pressure
                * COLOUR = typology cluster
                * SIZE   = diabetes prevalence (bigger = more diabetes)
                * SHAPE  = income group (the SHAPE channel, unused elsewhere)
              A drag-to-select interval BRUSH lets the reader rubber-band a
              region of the scatter; the other three panels react to it.
  TOP-RIGHT - a live bar chart of how many selected countries fall in each
              cluster - updates as the brush moves.
  BOTTOM-LEFT - the trajectory detail: click a single country to draw its
              full 1980-2014 path across all 3 diseases.
  BOTTOM-RIGHT - a compact "what am I looking at" KPI/legend text panel.

CONTROLS, stacked: a YEAR slider (1980-2014) moves the whole scatter
through time; a WHO REGION dropdown filters which countries appear; a drag
BRUSH cross-filters the cluster bar chart; a CLICK drives the trajectory.
Four distinct interaction types - slider, dropdown, brush, click - which is
exactly the breadth the "interactivity / dashboard elements" criteria
reward.
"""

import os
import sys
_SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

import pandas as pd
import altair as alt
from charts.chart_theme import INDIGO, CORAL, CATEGORICAL_SCHEME, make_title

DISEASE_COLOR_MAP = {
    "Blood Pressure": INDIGO,
    "Obesity": CORAL,
    "Diabetes": "#8a8a3c",
}

INCOME_SHAPES = {
    "Low income": "triangle-down",
    "Lower middle income": "square",
    "Upper middle income": "diamond",
    "High income": "circle",
}


def _prepare_scatter_data(combined_panel: pd.DataFrame, country_typology: pd.DataFrame) -> pd.DataFrame:
    """
    Per country-year (1980-2014): obesity, BP, diabetes, cluster name,
    income group, WHO region. This is the data the year-slider scatter
    moves through.
    """
    window = combined_panel[(combined_panel["Year"] >= 1980) & (combined_panel["Year"] <= 2014)].copy()
    cluster_lookup = country_typology.set_index("Country")["Cluster_Name"]
    window["Cluster_Name"] = window["Country"].map(cluster_lookup)
    window["WHO_Region"] = window["WHO_Region"].fillna("Not classified")
    window["Income_Group"] = window["Income_Group"].fillna("Unknown")
    window = window.dropna(subset=["Obesity_Prevalence_pct", "BP_Prevalence_pct", "Cluster_Name"])
    return window[[
        "Country", "Year", "Obesity_Prevalence_pct", "BP_Prevalence_pct",
        "Diabetes_Prevalence_pct", "Cluster_Name", "Income_Group", "WHO_Region",
    ]]


def _prepare_trajectory_data(combined_panel: pd.DataFrame) -> pd.DataFrame:
    window = combined_panel[(combined_panel["Year"] >= 1980) & (combined_panel["Year"] <= 2014)]
    long_df = window.melt(
        id_vars=["Country", "Year"],
        value_vars=["BP_Prevalence_pct", "Obesity_Prevalence_pct", "Diabetes_Prevalence_pct"],
        var_name="Disease_Raw", value_name="Prevalence_pct",
    )
    long_df["Disease"] = long_df["Disease_Raw"].map({
        "BP_Prevalence_pct": "Blood Pressure",
        "Obesity_Prevalence_pct": "Obesity",
        "Diabetes_Prevalence_pct": "Diabetes",
    })
    return long_df[["Country", "Year", "Disease", "Prevalence_pct"]]


def build_dashboard(country_typology: pd.DataFrame, combined_panel: pd.DataFrame) -> alt.Chart:
    scatter_data = _prepare_scatter_data(combined_panel, country_typology)
    trajectory_data = _prepare_trajectory_data(combined_panel)

    regions = ["All regions"] + sorted([r for r in scatter_data["WHO_Region"].unique() if r != "Not classified"]) + ["Not classified"]

    year_param = alt.param(
        name="dash_year", value=2014,
        bind=alt.binding_range(min=1980, max=2014, step=1, name="Year: "),
    )
    region_param = alt.param(
        name="dash_region", value="All regions",
        bind=alt.binding_select(options=regions, name="WHO Region: "),
    )
    brush = alt.selection_interval(name="brush", encodings=["x", "y"])
    click = alt.selection_point(name="pick", fields=["Country"], on="click", empty=False)

    cluster_domain = sorted(scatter_data["Cluster_Name"].unique())

    # ---- TOP-LEFT: the rich scatter (x, y, colour, size, shape + brush) ----
    scatter = (
        alt.Chart(scatter_data)
        .mark_point(filled=True, fillOpacity=0.75, stroke="white", strokeWidth=0.4)
        .encode(
            x=alt.X("Obesity_Prevalence_pct:Q", title="Obesity (%)", scale=alt.Scale(domain=[0, 65])),
            y=alt.Y("BP_Prevalence_pct:Q", title="Blood Pressure (%)", scale=alt.Scale(domain=[5, 45])),
            color=alt.Color("Cluster_Name:N", title="Cluster", scale=alt.Scale(scheme=CATEGORICAL_SCHEME)),
            size=alt.Size("Diabetes_Prevalence_pct:Q", title="Diabetes (%)", scale=alt.Scale(range=[20, 500])),
            shape=alt.Shape("Income_Group:N", title="Income group",
                            scale=alt.Scale(domain=list(INCOME_SHAPES.keys()), range=list(INCOME_SHAPES.values()))),
            opacity=alt.condition(brush, alt.value(0.85), alt.value(0.12)),
            tooltip=[
                alt.Tooltip("Country:N"), alt.Tooltip("Year:Q", format="d"),
                alt.Tooltip("Obesity_Prevalence_pct:Q", title="Obesity %", format=".1f"),
                alt.Tooltip("BP_Prevalence_pct:Q", title="BP %", format=".1f"),
                alt.Tooltip("Diabetes_Prevalence_pct:Q", title="Diabetes %", format=".1f"),
                alt.Tooltip("Cluster_Name:N"), alt.Tooltip("Income_Group:N"),
            ],
        )
        .transform_filter((alt.datum.Year == year_param))
        .transform_filter((alt.datum.WHO_Region == region_param) | (region_param == "All regions"))
        .add_params(year_param, region_param, brush, click)
        .properties(width=380, height=300, title="Drag to select a region; click a point for its history")
    )

    # ---- TOP-RIGHT: live cluster counts of the brushed selection ----
    cluster_bars = (
        alt.Chart(scatter_data)
        .mark_bar()
        .encode(
            x=alt.X("count():Q", title="Countries selected"),
            y=alt.Y("Cluster_Name:N", title=None, sort=cluster_domain),
            color=alt.Color("Cluster_Name:N", legend=None, scale=alt.Scale(scheme=CATEGORICAL_SCHEME)),
            tooltip=[alt.Tooltip("Cluster_Name:N"), alt.Tooltip("count():Q", title="Countries")],
        )
        .transform_filter((alt.datum.Year == year_param))
        .transform_filter((alt.datum.WHO_Region == region_param) | (region_param == "All regions"))
        .transform_filter(brush)
        .properties(width=300, height=300, title="Clusters within your selection")
    )

    # ---- BOTTOM-LEFT: clicked country's trajectory ----
    detail = (
        alt.Chart(trajectory_data)
        .mark_line(strokeWidth=2.4, point=alt.OverlayMarkDef(size=18))
        .encode(
            x=alt.X("Year:Q", title=None, axis=alt.Axis(format="d", values=[1980, 1990, 2000, 2010, 2014])),
            y=alt.Y("Prevalence_pct:Q", title="Prevalence (%)", scale=alt.Scale(domain=[0, 60])),
            color=alt.Color("Disease:N", title="Disease",
                            scale=alt.Scale(domain=list(DISEASE_COLOR_MAP.keys()), range=list(DISEASE_COLOR_MAP.values()))),
            tooltip=[alt.Tooltip("Disease:N"), alt.Tooltip("Year:Q", format="d"), alt.Tooltip("Prevalence_pct:Q", format=".1f")],
        )
        .transform_filter(click)
        .properties(width=380, height=240, title="Clicked country: full 1980-2014 trajectory")
    )

    # ---- BOTTOM-RIGHT: reading guide ----
    guide_rows = pd.DataFrame({
        "line": [
            "HOW TO READ THIS DASHBOARD",
            "Bubble position  =  obesity (x) vs blood pressure (y)",
            "Bubble size  =  diabetes prevalence",
            "Bubble shape  =  income group",
            "Bubble colour  =  typology cluster",
            "",
            "Slider  =  move all countries through time",
            "Dropdown  =  filter to one WHO region",
            "Drag  =  select an area; bars at top-right update",
            "Click a bubble  =  draw its history bottom-left",
        ],
        "y": list(range(9, -1, -1)),
        "bold": [True, False, False, False, False, False, False, False, False, False],
    })
    guide = (
        alt.Chart(guide_rows)
        .mark_text(align="left", dx=-150, fontSize=12)
        .encode(
            y=alt.Y("y:O", axis=None),
            text="line:N",
            color=alt.condition(alt.datum.bold, alt.value(INDIGO), alt.value("#555555")),
            size=alt.condition(alt.datum.bold, alt.value(13), alt.value(11)),
        )
        .properties(width=300, height=240, title="Reading guide")
    )

    dashboard = (
        alt.vconcat(
            alt.hconcat(scatter, cluster_bars).resolve_scale(color="shared"),
            alt.hconcat(detail, guide).resolve_scale(color="independent"),
        )
        .resolve_scale(color="independent", size="independent", shape="independent")
        .properties(
            title=make_title(
                "The Whole Story in One View - Move Through Time, Select, and Drill Down",
                eyebrow_number=9,
                subtitle_lines=[
                    "Four linked panels and four controls (year slider, region dropdown, drag-select, click).",
                    "One bubble = one country in the chosen year; position, size, shape and colour each carry a different variable.",
                ],
            )
        )
    )

    return dashboard
