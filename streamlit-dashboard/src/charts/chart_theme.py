"""
chart_theme.py
----------------
The shared design system for every visual in this report. Registered once,
applied everywhere, so all 9 charts read as one coherent piece of work
rather than 9 separately-styled exports.

DESIGN DECISIONS (stated explicitly, not left implicit):

Palette - deep indigo (#1B3A4B) is the grounding neutral used for most
marks and text. Warm coral (#E8623D) is reserved as a SINGLE accent colour
used only to draw the eye to "this is the finding" - a specific cluster, a
specific country, a specific bar - never used decoratively. This follows
the principle of spending boldness in one place rather than scattering
bright colours everywhere (which is what makes most dashboards look busy
without actually directing attention).

Sequential/continuous data uses Viridis - chosen deliberately over a
custom gradient because it is perceptually uniform AND colourblind-safe;
for choropleth/heat-style data, correctness beats house-colour purity.

Diverging data (the two hypothesis-test scatter plots, where a residual
can be positive or negative) uses a purple-orange scheme - this is also
colourblind-safe, AND it echoes the indigo/coral identity above rather
than defaulting to a generic red-blue diverging scale.

Categorical data (clusters, regions) uses the muted "dark2" palette
instead of Vega's bright default "category10" - dark2 is colourblind-safe
and reads as considered/editorial rather than a default BI tool.

Typography pairs a serif title face (editorial weight, like a journal
infographic) with a clean sans body face for axis labels and data -
two distinct roles, not one font used everywhere.

Signature device: every chart title states the FINDING in plain language
("Five Distinct Health Journeys, Not One Global Story"), not the chart
type ("Cluster Scatter Plot"). A small eyebrow label above the title ties
each chart to its analytical thread (e.g. "THREAD 1 - TYPOLOGY"). This
numbering is earned here because the 9 visuals genuinely are a sequential
argument, not an arbitrary list.
"""

import altair as alt

TITLE_FONT = "Georgia, 'Times New Roman', serif"
BODY_FONT = "Helvetica Neue, Arial, sans-serif"

INDIGO = "#1B3A4B"
CORAL = "#E8623D"
BODY_TEXT = "#33404a"
GRID_COLOR = "#e4e4e0"
BACKGROUND = "#FAF9F6"  # warm off-white, not stark white - reads as considered, prints cleanly

SEQUENTIAL_SCHEME = "viridis"
DIVERGING_SCHEME = "puor"        # purple-orange: colourblind-safe, echoes indigo/coral identity
CATEGORICAL_SCHEME = "dark2"     # muted, editorial - not the bright default category10

CHART_WIDTH = 650
CHART_HEIGHT = 420

EYEBROW_LABELS = {
    1: "THREAD 1 \u00b7 TYPOLOGY",
    2: "THREAD 1 \u00b7 TYPOLOGY",
    3: "THREAD 1 \u00b7 TYPOLOGY",
    4: "THREAD 2 \u00b7 CONVERGENCE",
    5: "THREAD 3 \u00b7 EQUALITY HYPOTHESIS",
    6: "THREAD 4 \u00b7 ACCESS HYPOTHESIS",
    7: "THREAD 5 \u00b7 GENDER",
    8: "METHODOLOGY CHECK",
    9: "ALL THREADS \u00b7 INTERACTIVE DASHBOARD",
}


def make_title(main_text: str, eyebrow_number: int, subtitle_lines: list[str] = None) -> alt.TitleParams:
    """
    Builds a consistent title block: small eyebrow thread-label, then the
    FINDING stated in plain language as the main title, then optional
    subtitle lines for methodology caveats/disclosures.
    """
    eyebrow = EYEBROW_LABELS.get(eyebrow_number, "")
    full_subtitle = [eyebrow, ""] + (subtitle_lines or [])
    return alt.TitleParams(
        text=main_text,
        subtitle=full_subtitle,
        font=TITLE_FONT,
        fontSize=19,
        fontWeight="bold",
        subtitleFont=BODY_FONT,
        subtitleFontSize=11,
        subtitleColor="#6b6b66",
        anchor="start",
        offset=14,
    )


def health_report_theme():
    """Altair theme definition - registered via register_theme() below."""
    return {
        "config": {
            "title": {
                "font": TITLE_FONT,
                "fontSize": 19,
                "fontWeight": "bold",
                "anchor": "start",
                "color": INDIGO,
            },
            "axis": {
                "labelFont": BODY_FONT,
                "titleFont": BODY_FONT,
                "labelColor": BODY_TEXT,
                "titleColor": BODY_TEXT,
                "gridColor": GRID_COLOR,
                "domainColor": "#999990",
                "labelFontSize": 11,
                "titleFontSize": 12.5,
                "titleFontWeight": "normal",
            },
            "legend": {
                "labelFont": BODY_FONT,
                "titleFont": BODY_FONT,
                "labelColor": BODY_TEXT,
                "titleColor": BODY_TEXT,
                "labelFontSize": 11,
                "titleFontSize": 12,
            },
            "view": {"stroke": "transparent"},
            "background": BACKGROUND,
            "range": {
                "category": {"scheme": CATEGORICAL_SCHEME},
                "diverging": {"scheme": DIVERGING_SCHEME},
                "heatmap": {"scheme": SEQUENTIAL_SCHEME},
            },
        }
    }


def register_theme():
    """Call once at the start of any script that builds charts."""
    alt.themes.register("health_report_theme", health_report_theme)
    alt.themes.enable("health_report_theme")
