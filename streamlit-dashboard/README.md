# Project Notes, Bugs Found, and Explanations

This file records explanations and fixes that came up during development,
specifically the ones worth remembering rather than re-discovering later.

---

## Fix 1: `ModuleNotFoundError: No module named 'geo_lookup'` (and similar)

**The bug:** every chart module in `src/charts/` started with:
```python
import sys
sys.path.insert(0, "src")
```
`"src"` here is a RELATIVE path. It only resolves correctly if the Python
process's current working directory happens to be `project/` at the moment
the import runs. If a chart module is imported from anywhere else - a
different folder, a script that does its own `cd`, or even just running
`python3 chart_01_choropleth.py` directly from inside `src/charts/` -
`"src"` no longer points at the right place, and any import of a sibling
top-level module (`geo_lookup`, `typology_features`, etc.) fails with
`ModuleNotFoundError`.

**The fix:** every chart module (and `build_all_charts.py`) now computes an
ABSOLUTE path using `__file__`, which always points to that file's real
location on disk regardless of the current working directory:
```python
import os
import sys
_SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)
```
`build_all_charts.py` additionally calls `os.chdir(_PROJECT_DIR)` at import
time, since its `pd.read_csv("data/final/...")` calls assume the working
directory is `project/` too - fixing only the import path would have left
the data-loading calls just as fragile.

**Verified by:** running `build_all_charts.py` via its absolute path from
`/tmp` (a directory with no relationship to the project at all), and by
importing `chart_01_choropleth` after adding only `src/charts` (not `src`)
to `sys.path` - both now succeed.

---

## Explanation: how years/data coverage actually work in this project

There was confusion about three different things that look similar but are
NOT the same mechanism. Writing them out clearly:

### 1. The core merged panel covers 1975-2016, not just 1980-2014
`combined_panel_with_risk_index.csv` deliberately keeps the FULL available
range from the original 3 health sheets (BP: 1975-2015, Obesity: 1975-2016,
Diabetes: 1980-2014) rather than trimming everything down to the
1980-2014 overlap immediately. This is intentional - trimming early would
throw away real data that some future analysis might want.

**The 1980-2014 window is applied LATER, inside specific analyses that
need all 3 diseases at once** (typology features, convergence CV,
hypothesis-test snapshots) - because that's the only window where all
three diseases have data for every country. Outside those specific
calculations, rows for 1975-1979 and 2015-2016 still exist in the main
panel, with real BP/Obesity values and a NaN for Diabetes (since Diabetes
genuinely has no data those years) - **nothing is calculated or guessed
for those NaN cells.**

### 2. UHC_Index and Income_Group: a real "carry-back" assumption, explicitly flagged
UHC data only exists from 2000 onward; historical Income Group only goes
back to 1987. For years BEFORE each source's real coverage starts, this
project carries each country's EARLIEST available real value backward as
a stated, simplifying assumption (e.g. a country's 1990 UHC value = its
year-2000 value, because UHC reflects slow-moving health-system structure,
not something that swings year to year).

**This is the ONE place in the project where a value is extended beyond
what was actually measured** - and it is never silent: every such row is
flagged `True` in `UHC_Index_Is_Carried_Back` or
`Income_Group_Is_Carried_Back`. Anyone using this data can filter out
carried-back rows entirely if they want only directly-observed values.

### 3. The equality follow-up (sugar/alcohol/inactivity): NO carry-back at all
This is the one that caused the confusion. To be precise about what
actually happens in `equality_followup_exploration.py`:

- **Sugar & Alcohol (FAO):** a single fixed real year, **2013** (the last
  year FAO's file covers) - the SAME real, directly-observed 2013 value
  for every country. Nothing before or after 2013 is used, estimated, or
  filled in for this comparison.
- **Physical Inactivity (WHO):** each country's own most recent REAL
  observed year - which, when checked, turned out to be **2022 for every
  single country that has any data at all** (38 of 41 countries in the
  Wealthy Decouplers cluster; 3 have no inactivity data and are correctly
  left blank, not estimated).

**So: no value in this specific exploration is calculated, interpolated,
or carried back from a different year.** Every number is a real,
directly-reported figure. The potential issue was not fabricated data -
it was that the actual year used per country was not being SHOWN in the
output table, which made this impossible to verify at a glance.

**Fix applied:** `build_followup_snapshot()` now returns two additional
columns, `Sugar_Alcohol_Year` and `Inactivity_Year`, so the exact year
behind every number is visible directly in
`data/analysis/equality_followup_wealthy_cluster.csv`, not just asserted
in documentation.

### Summary table

| Data | Real coverage | What happens outside that range | Flagged how |
|---|---|---|---|
| BP / Obesity / Diabetes (core panel) | 1975/1975/1980 to 2015/2016/2014 | Left as NaN, nothing calculated | Implicit (NaN) |
| UHC_Index | 2000-2023 | Carried back from earliest real value | `UHC_Index_Is_Carried_Back` column |
| Income_Group | 1987-present | Carried back from earliest real value, or current-year fallback | `Income_Group_Is_Carried_Back` / `Income_Group_Used_Current_Fallback` |
| Gini_Index | sparse, varies by country | Used as single most-recent snapshot, never extended | `Gini_Year` column shows which year |
| Sugar/Alcohol (FAO, follow-up only) | 1970-2013 | Not extended - fixed real 2013 value only | `Sugar_Alcohol_Year` column |
| Physical Inactivity (WHO, follow-up only) | 2000-2022 | Not extended - each country's own real latest year | `Inactivity_Year` column |

---

## Stage 7: Streamlit Dashboard (app.py)

**What was built:** A single-file Streamlit application (`app.py`, ~900 lines) at the
project root bringing together all 5 analytical threads, 12 Altair charts, hypothesis
verdicts, data sources, and methodology notes into a modern interactive dashboard.

**Run with:**
```bash
streamlit run app.py
```
(Must be run from the project root — chart modules use relative `data/` paths.)

**Requires:** `pip install streamlit scikit-learn` (in addition to the existing
`altair pandas numpy scipy scikit-learn pycountry` stack).

### Structure (9 sidebar pages)

| Page | Contents |
|---|---|
| 🏠 Overview | KPI metric cards, expandable findings table for all 5 threads, verdict badges, cluster summary |
| 🗺️ Thread 1 · Country Typology | 5 tabs: choropleth map, PCA cluster scatter, trajectory small multiples, cluster profiles + member-country browser, k-selection chart |
| 📉 Thread 2 · Global Convergence | CV trend chart (observed + projected), convergence by income tier, 1980 vs 2014 summary table |
| ⚖️ Thread 3 · Equality Hypothesis | Equality scatter (null result), self-correction chart (sugar/alcohol/inactivity), full data table, open-question callout |
| 🏥 Thread 4 · Access Hypothesis | Access scatter (confirmed result), full data table |
| 👥 Thread 5 · Gender Gaps | Diverging bars + trend line, gender gap by cluster chart |
| 🔍 Supplementary Exploration | Risk leaderboard with live year slider, cluster robustness (ARI=0.684), **new** country deep-dive tool (searchable dropdown → trajectory + risk index) |
| 🎛️ Interactive Dashboard | Full linked click-to-reveal dashboard (Chart 10) |
| 📋 Data & Methodology | 8-source data table, 6-stage pipeline, integrity caveats |

### Design decisions

- All data loading uses `@st.cache_data` to avoid re-reading CSVs on every interaction.
- PCA + feature scaling (needed for Chart 2 cluster scatter) uses `@st.cache_resource`
  so the sklearn computation only runs once per session.
- Path setup at the top of `app.py` ensures chart modules resolve correctly:
  ```python
  _ROOT = os.path.dirname(os.path.abspath(__file__))
  _SRC  = os.path.join(_ROOT, "src")
  sys.path.insert(0, _SRC)
  os.chdir(_ROOT)   # needed for data/ relative paths inside chart modules
  ```
- `.streamlit/config.toml` sets theme colours to match the project design system
  (coral `#E8623D`, deep indigo `#1B3A4B`, warm off-white background `#FAF9F6`).

---

## Fix 2: Choropleth Arrow serialization error in Streamlit

**The bug:** Rendering the choropleth with `st.altair_chart(chart)` produced:
```
pyarrow.lib.ArrowTypeError: ("Expected bytes, got a 'dict' object",
'Conversion failed for column value with type object')
```

**Why it happened:** `st.altair_chart()` internally serialises chart data through
Apache Arrow before passing it to Vega-Embed. The choropleth uses
`alt.Data(values=topo, format=alt.DataFormat(type="topojson", feature="countries"))`
where `topo` is the full TopoJSON dict (~1 MB) loaded from `data/geo/world-110m.json`.
This is a deeply nested dict/list structure. PyArrow expects flat scalar columns and
cannot convert nested dicts — hence the `ArrowTypeError`.

**Why only the choropleth:** every other chart uses plain pandas DataFrames (flat
tabular data) for its inline data, which Arrow handles fine. The TopoJSON dict is the
only non-tabular inline data source in the project.

**The fix:** replaced `st.altair_chart(chart)` with:
```python
components.html(chart.to_html(), height=700, scrolling=False)
```
`chart.to_html()` serialises the full Vega-Lite spec (including the TopoJSON) into a
self-contained HTML/JS string — the same path used by `chart.save("file.html")`, which
already worked fine. `components.html()` injects it as an iframe, so Apache Arrow is
never involved. All Vega-Embed interactivity (year slider, metric dropdown) continues
to work client-side inside the iframe.

**Also added:** `import streamlit.components.v1 as components` at the top of `app.py`.

---

## Fix 3: Choropleth interactive controls not visible in iframe

**The bug:** After Fix 2, the choropleth rendered but the year slider and metric
dropdown were invisible. Only the map and colour bar appeared.

**Why it happened:** Vega-Embed places the `vega-bindings` div (which contains the
HTML input elements for the slider and dropdown) **below** the chart canvas in a
flex-column layout. The full content stack for this chart is:

| Element | Height |
|---|---|
| Title + subtitle block | ~90 px |
| Map canvas (`CHART_HEIGHT = 420`) | ~420 px |
| Colour-bar legend | ~50 px |
| Bindings (year slider + metric dropdown) | ~60 px |
| **Total** | **~620 px** |

The original `components.html(..., height=550)` clipped everything below ~550 px,
cutting off the bindings div entirely. The controls were rendered in the DOM but
outside the iframe's visible viewport.

**Diagnosis note:** `vega-bindings` does NOT appear as a literal string in the
static HTML that `chart.to_html()` produces — Vega-Embed injects that div
dynamically via JavaScript at render time. Searching the HTML for `vega-bindings`
to check if controls are "missing from the spec" is a red herring; their presence
must be inferred from the `params` → `bind` entries in the Vega-Lite spec, which
are present (confirmed at char 143071 in the generated HTML).

**The fix:** increased the iframe height from `550` to `700`:
```python
# Before
components.html(chart.to_html(), height=550)
# After
components.html(chart.to_html(), height=700, scrolling=False)
```
700 px gives ~80 px of headroom above the ~620 px content total. `scrolling=False`
keeps the iframe flush without an inner scrollbar.

**Verified by:** year slider and metric dropdown now visible below the map in the
Streamlit app.
