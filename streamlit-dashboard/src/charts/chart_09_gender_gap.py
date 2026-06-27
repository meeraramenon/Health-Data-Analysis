"""
chart_09_gender_gap.py
-------------------------
Visual #9: Thread 5's answer to "is the male/female gap widening or
narrowing?" - shown two ways side by side: a diverging bar snapshot
(1980 vs 2014) for immediate comparison, and the full trend line for the
complete 35-year picture (including the sign-flip in Diabetes, which a
two-point snapshot alone would hide).

DESIGN INTENT: a diverging bar chart is the natural form for a SIGNED
quantity like a gender gap - bars extend right (coral, higher in women) or
left (indigo, higher in men) from a zero baseline, making the direction of
the disparity immediately legible without reading the sign in a tooltip.
Paired with the trend line (same disease colour mapping as charts 3/4),
the two panels together show both "where are we now vs. then" and "how did
we get there" - including Diabetes's sign flip, a genuinely unusual result
that a single before/after bar would visually flatten into "no big change"
when the real story is two different groups swapping places.
"""

import pandas as pd
import altair as alt

import sys
sys.path.insert(0, "src")
from charts.chart_theme import INDIGO, CORAL, make_title

DISEASE_LABELS = {"BP": "Blood Pressure", "Obesity": "Obesity", "Diabetes": "Diabetes"}
LINE_COLOR_MAP = {"Blood Pressure": INDIGO, "Obesity": CORAL, "Diabetes": "#8a8a3c"}


def _prepare_snapshot_data(gender_gap_by_year: pd.DataFrame) -> pd.DataFrame:
    """Builds the 1980-vs-2014 long-format snapshot for the diverging bars."""
    rows = []
    for prefix, label in DISEASE_LABELS.items():
        col = f"{prefix}_Sex_Gap_pct"
        for year in [1980, 2014]:
            value = gender_gap_by_year[gender_gap_by_year["Year"] == year][col].values[0]
            rows.append({
                "Disease": label,
                "Year": str(year),
                "Gap": value,
                "Category": f"{label} - {year}",
                "Direction": "Higher in women" if value > 0 else "Higher in men",
            })
    return pd.DataFrame(rows)


def _prepare_trend_data(gender_gap_by_year: pd.DataFrame) -> pd.DataFrame:
    """Builds the full-period long-format trend data for the line chart."""
    long_df = gender_gap_by_year.melt(
        id_vars=["Year"],
        value_vars=[f"{p}_Sex_Gap_pct" for p in DISEASE_LABELS],
        var_name="Disease_Raw",
        value_name="Gap",
    )
    long_df["Disease"] = long_df["Disease_Raw"].str.replace("_Sex_Gap_pct", "").map(DISEASE_LABELS)
    return long_df


def build_gender_gap_chart(gender_gap_by_year: pd.DataFrame) -> alt.Chart:
    """
    Returns a side-by-side chart: diverging 1980-vs-2014 bars (left) +
    full trend line 1980-2014 (right).
    """
    snapshot_data = _prepare_snapshot_data(gender_gap_by_year)
    trend_data = _prepare_trend_data(gender_gap_by_year)

    bars = (
        alt.Chart(snapshot_data)
        .mark_bar(height=16)
        .encode(
            x=alt.X("Gap:Q", title="Gender Gap (pp) - negative = higher in men"),
            y=alt.Y("Category:N", title=None, sort=alt.SortField("Disease")),
            color=alt.Color(
                "Direction:N", title=None,
                scale=alt.Scale(domain=["Higher in women", "Higher in men"], range=[CORAL, INDIGO]),
                legend=alt.Legend(orient="top"),
            ),
            tooltip=[alt.Tooltip("Category:N"), alt.Tooltip("Gap:Q", format="+.2f")],
        )
        .properties(width=320, height=260, title="1980 vs. 2014 Snapshot")
    )

    zero_rule = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color="#999990").encode(x="x:Q")

    trend_lines = (
        alt.Chart(trend_data)
        .mark_line(strokeWidth=2.4)
        .encode(
            x=alt.X("Year:Q", title=None, axis=alt.Axis(format="d", values=[1980, 1990, 2000, 2010, 2014])),
            y=alt.Y("Gap:Q", title="Gender Gap (pp)"),
            color=alt.Color(
                "Disease:N", title="Disease",
                scale=alt.Scale(domain=list(LINE_COLOR_MAP.keys()), range=list(LINE_COLOR_MAP.values())),
            ),
            tooltip=[alt.Tooltip("Disease:N"), alt.Tooltip("Year:Q", format="d"), alt.Tooltip("Gap:Q", format="+.2f")],
        )
    )
    trend_zero_rule = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color="#999990").encode(y="y:Q")

    trend_chart = (trend_lines + trend_zero_rule).properties(width=320, height=260, title="Full 1980-2014 Trend")

    chart = (
        alt.hconcat(bars + zero_rule, trend_chart)
        .resolve_scale(color="independent")
        .properties(
            title=make_title(
                "Three Diseases, Three Different Gender Stories",
                eyebrow_number=7,
                subtitle_lines=[
                    "BP and Obesity gaps are WIDENING (in opposite directions); Diabetes is narrowing AND flips which sex is more affected.",
                    "Obesity's gender gap moves in near-lockstep with the between-country convergence in Thread 2 (r=-0.969).",
                ],
            )
        )
    )

    return chart
