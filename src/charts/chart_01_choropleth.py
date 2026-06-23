"""
chart_01_choropleth.py
-------------------------
Visual #1: World choropleth map, year slider, Metabolic Risk Index with
drill-down to the 3 individual diseases.

DESIGN:
- A dropdown lets the reader pick which metric to colour the map by:
  the composite Metabolic Risk Index (default), or any one of the 3
  individual diseases - this is the "drill-down" from the original visual
  spec, implemented as a single chart with a selectable field rather than
  4 separate maps.
- A year slider (1980-2014) lets the reader scrub through time.
- Both controls are Altair params bound to native HTML input widgets
  (a dropdown and a range slider), and the map's colour encoding reacts to
  both via a calculated field.

DATA: uses combined_panel_with_risk_index.csv joined to the local world map
geometry (data/geo/world-110m.json) via the numeric ID lookup in
geo_lookup.py. 32 small countries are not present in this simplified map
file's geometry and will not render (see geo_lookup.py docstring) - this is
disclosed in the chart's caption/subtitle, not hidden.
"""

import json
import pandas as pd
import altair as alt

# This chart embeds all 1980-2014 years (so the year slider can filter
# client-side, with no server/recompute step). That's 200 countries x 35
# years = 7000 rows, just over Altair's default 5000-row safety cap. The
# cap exists to warn against accidentally embedding genuinely huge
# datasets; 7000 simple rows is not that, so it's safely disabled here.
alt.data_transformers.disable_max_rows()

import sys
sys.path.insert(0, "src")
from geo_lookup import get_alpha3_to_numeric_id_lookup
from charts.chart_theme import SEQUENTIAL_SCHEME, CHART_WIDTH, CHART_HEIGHT, make_title, CORAL

GEO_FILE_PATH = "data/geo/world-110m.json"

METRIC_OPTIONS = {
    "Metabolic Risk Index": "Metabolic_Risk_Index",
    "Blood Pressure (%)": "BP_Prevalence_pct",
    "Obesity (%)": "Obesity_Prevalence_pct",
    "Diabetes (%)": "Diabetes_Prevalence_pct",
}


def _load_geo_data() -> alt.Data:
    """
    Loads the local topojson file as inline Altair Data.

    IMPORTANT: the full topology object (with its "arcs" array) must be
    passed through, with format type "topojson" and feature="countries" -
    this tells Vega to decode the delta-encoded arcs into real coordinates
    itself. Passing just the "geometries" list with format type "json"
    (an earlier version of this function did this) does NOT work - those
    geometries only contain arc INDEX references, not actual coordinates,
    and rendering them as plain GeoJSON silently produces broken shapes.
    """
    with open(GEO_FILE_PATH) as f:
        topo = json.load(f)
    return alt.Data(values=topo, format=alt.DataFormat(type="topojson", feature="countries"))


def _prepare_data(combined_panel: pd.DataFrame) -> pd.DataFrame:
    """
    Adds the numeric map ID to a copy of the combined panel, restricted to
    1980-2014 (the common window) and only the 4 columns the map actually
    needs, to keep the embedded chart data small.
    """
    df = combined_panel[(combined_panel["Year"] >= 1980) & (combined_panel["Year"] <= 2014)].copy()

    id_lookup = get_alpha3_to_numeric_id_lookup(sorted(df["Country_Code"].unique()))
    df["map_id"] = df["Country_Code"].map(id_lookup)
    df = df.dropna(subset=["map_id"])
    df["map_id"] = df["map_id"].astype(int)

    needed_cols = ["map_id", "Country", "Year"] + list(METRIC_OPTIONS.values())
    return df[needed_cols]


def build_choropleth(combined_panel: pd.DataFrame) -> alt.Chart:
    """
    Returns the complete, interactive choropleth chart. Save with
    chart.save("path.html") for an interactive version, or
    chart.save("path.png") for a static snapshot (PNG only captures
    whatever the sliders are set to at save time, since PNG has no
    interactivity).
    """
    data = _prepare_data(combined_panel)
    world_shapes = _load_geo_data()

    year_param = alt.param(
        name="selected_year",
        value=2014,
        bind=alt.binding_range(min=1980, max=2014, step=1, name="Year: "),
    )

    # Vega-Lite dropdown binding for metric selection. The field name itself
    # is swapped via a calculate transform below, driven by this parameter.
    metric_param = alt.param(
        name="selected_metric_label",
        value="Metabolic Risk Index",
        bind=alt.binding_select(options=list(METRIC_OPTIONS.keys()), name="Colour by: "),
    )

    # Lookup transform pulls the matching row's data onto each map shape by map_id.
    lookup_fields = ["Country", "Year"] + list(METRIC_OPTIONS.values())

    base = (
        alt.Chart(world_shapes)
        .mark_geoshape(stroke="white", strokeWidth=0.5)
        .transform_lookup(
            lookup="id",
            from_=alt.LookupData(data=data, key="map_id", fields=lookup_fields),
        )
        .transform_filter(alt.datum.Year == year_param)
        .add_params(year_param, metric_param)
    )

    # Build one calculate expression per metric option, chained via nested
    # if/else on the metric_param value, so a single colour channel can
    # represent whichever metric the dropdown currently selects.
    calc_expr = "datum['" + METRIC_OPTIONS["Diabetes (%)"] + "']"
    for label in ["Obesity (%)", "Blood Pressure (%)", "Metabolic Risk Index"]:
        field = METRIC_OPTIONS[label]
        calc_expr = f"selected_metric_label == '{label}' ? datum['{field}'] : ({calc_expr})"

    chart = (
        base
        .transform_calculate(value_to_show=calc_expr)
        .encode(
            color=alt.Color(
                "value_to_show:Q",
                title=None,
                scale=alt.Scale(scheme=SEQUENTIAL_SCHEME),
                legend=alt.Legend(orient="bottom", gradientLength=300),
            ),
            tooltip=[
                alt.Tooltip("Country:N", title="Country"),
                alt.Tooltip("value_to_show:Q", title="Value", format=".1f"),
            ],
        )
        .project("equalEarth")
        .properties(
            width=CHART_WIDTH,
            height=CHART_HEIGHT,
            title=make_title(
                "Where Metabolic Risk Concentrates, and How It Has Moved",
                eyebrow_number=1,
                subtitle_lines=[
                    "Drag the slider to change year; use the dropdown to switch metric.",
                    "32 small island/micro-states are not shown due to map resolution (still included in every other chart).",
                ],
            ),
        )
    )

    return chart


def build_choropleth_static(combined_panel: pd.DataFrame, year: int = 2014,
                             metric_label: str = "Metabolic Risk Index") -> alt.Chart:
    """
    A non-interactive version of the same map, fixed to one year and one
    metric, with the filtering done in pandas BEFORE the chart is built
    (rather than via Altair params). This exists because the fully
    interactive version (build_choropleth) cannot currently be exported to
    a static PNG - vl-convert's static renderer does not resolve the
    parameter-driven calculate/filter transforms used for the slider and
    dropdown. This function is what produces the PNG used in the written
    report; the HTML from build_choropleth() is the interactive deliverable.
    """
    field = METRIC_OPTIONS[metric_label]

    df = combined_panel[combined_panel["Year"] == year].copy()
    id_lookup = get_alpha3_to_numeric_id_lookup(sorted(df["Country_Code"].unique()))
    df["map_id"] = df["Country_Code"].map(id_lookup)
    df = df.dropna(subset=["map_id"])
    df["map_id"] = df["map_id"].astype(int)
    df = df[["map_id", "Country", field]].rename(columns={field: "value_to_show"})

    world_shapes = _load_geo_data()

    chart = (
        alt.Chart(world_shapes)
        .mark_geoshape(stroke="white", strokeWidth=0.5)
        .transform_lookup(
            lookup="id",
            from_=alt.LookupData(data=df, key="map_id", fields=["Country", "value_to_show"]),
        )
        .encode(
            color=alt.Color(
                "value_to_show:Q",
                title=metric_label,
                scale=alt.Scale(scheme=SEQUENTIAL_SCHEME),
                legend=alt.Legend(orient="bottom", gradientLength=300),
            ),
            tooltip=[
                alt.Tooltip("Country:N", title="Country"),
                alt.Tooltip("value_to_show:Q", title="Value", format=".1f"),
            ],
        )
        .project("equalEarth")
        .properties(
            width=CHART_WIDTH,
            height=CHART_HEIGHT,
            title=make_title(
                f"Global {metric_label}, {year}",
                eyebrow_number=1,
                subtitle_lines=["32 small island/micro-states are not shown due to map resolution."],
            ),
        )
    )
    return chart
