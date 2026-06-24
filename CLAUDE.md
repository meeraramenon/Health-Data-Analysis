# CLAUDE.md — Project Notes, Bugs Found, and Explanations

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
