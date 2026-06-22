# Health Data Analysis Pipeline — README

This README is updated after every completed stage. It currently covers:
**Data Preparation → Typology (Thread 1) → Equality & Access Hypothesis
tests (Threads 3 & 4).**

---

## STAGE 1: Data Preparation (complete)

Loads the 3 original health sheets, cleans them, and merges in Continent,
WHO Region, UHC Index, Gini Index, and Income Group using verified ISO3
country codes (never free-text name matching).

**Outputs in `data/final/`:**

| File | Rows | Use |
|---|---|---|
| `master_panel_by_sex.csv` | 16,800 | Sex-disaggregated panel |
| `sex_gap_table.csv` | 8,400 | Female-minus-Male gap per disease (Thread 5 input) |
| `combined_panel_with_risk_index.csv` | 8,400 | Sex-averaged panel + Metabolic Risk Index — main file for everything else |

**Code:** `country_codes.py`, `load_health_data.py`, `load_external_data.py`,
`merge_all_data.py`, `feature_engineering.py`, `main.py`

**Key safeguard:** fuzzy country-name matching was tested and rejected — it
silently mapped "Niger" to Nigeria's code. Every merge uses verified ISO3
codes instead. Full audit trail in `logs/`.

---

## STAGE 2: Typology — Thread 1 (complete)

Converts each country's 1980-2014 trajectory into 12 numeric features
(Start level, End level, Slope, Curvature x 3 diseases), then clusters all
200 countries with k-means.

**k selection:** k=2 maximized the silhouette score (0.47) but only split
"27 extreme outliers" from "everyone else" - not a useful typology. k=5 was
chosen instead, sitting inside the k=3-8 plateau (silhouette ~0.25-0.28),
because its 5 clusters are each genuinely distinct in content, not just in
the score used to find them.

**The 5 clusters found:**

| Cluster | n | Defining pattern |
|---|---|---|
| Pacific Extreme Outliers | 13 | Obesity 30%->51%, the syndemic-trap group |
| Lean Hypertension / Low-Obesity Rising-BP | 64 | Obesity stays near 2-8%, but the *only* cluster where BP is still climbing |
| Wealthy Decouplers | 41 | Sharpest BP decline (-0.41/yr) despite rising obesity - Japan, Korea, US, UK all here |
| High-Starting-BP Recovery | 39 | Started highest on BP (37%), fell hard - Eastern Europe + Gulf states |
| Moderate Transition | 43 | The unremarkable middle ground |

**Outputs in `data/analysis/`:** `k_selection_diagnostics.csv`,
`country_typology.csv`, `cluster_profiles.csv`

**Code:** `typology_features.py`, `typology_clustering.py`, `typology_main.py`

**Worth keeping for the report:** Portugal lands in the "Lean Hypertension"
cluster despite being high-income - a geography-defying anomaly, because
clustering was done on trajectory shape, not wealth.

---

## STAGE 3: Equality & Access Hypothesis Tests — Threads 3 & 4 (complete)

Both tests follow the same two-step logic: regress one variable on another,
take the leftover residual (the part NOT explained), then check whether
that residual correlates with the hypothesised real driver.

### Thread 3 - Equality Hypothesis
*Does income equality (Gini), not income level, explain why some wealthy
countries stay thin and others don't?*

1. Regress `Obesity_End` on `Income_Group_Ordinal` -> income level alone
   explains 26.0% of obesity variation (R-squared=0.260, n=197).
2. Correlate the residual against `Gini_Index` -> **r = 0.019, p = 0.81 -
   not significant globally.**
3. Robustness check, restricted to the "Wealthy Decouplers" cluster only
   (where the actual Japan/Korea vs. USA/UK anomaly lives) -> **r = 0.143,
   p = 0.44 - still not significant, but directionally consistent.**

**Honest reading:** Gini does NOT explain this globally, and only weakly
even within the wealthy-country comparison. Looking at the actual numbers:
Japan (Gini 32.3) and the UK (Gini 32.4) have nearly identical income
equality, yet wildly different obesity (3.8% vs. 26.3%). The US (Gini 41.8,
the highest of the group) does have the highest obesity (34.6%) - so the
hypothesis holds for the US specifically, but the UK comparison breaks it.
**Conclusion: income equality is part of the picture but not sufficient on
its own** - something else (diet, food culture, urban design) separates
Japan/Korea from the UK, and this dataset cannot speak to what that is.
This is reported as a genuine, stated limitation, not papered over.

### Thread 4 - Access Hypothesis
*Does healthcare access (UHC), not spending, explain why some high-obesity
countries escape high BP?*

1. Regress `BP_End` on `Obesity_End` -> obesity alone explains 10.6% of BP
   variation (R-squared=0.106, n=200).
2. Correlate the residual against `UHC_End` -> **r = -0.479, p < 0.0001 -
   statistically significant, n=192.**

**Honest reading: this one holds up.** Countries with stronger healthcare
access have blood pressure meaningfully lower than their obesity level
alone would predict. This is real, tested evidence for the "shield"
mechanism the reference report only asserted.

**Outputs in `data/analysis/`:** `equality_hypothesis_results.csv`,
`access_hypothesis_results.csv` (each: full per-country snapshot +
residuals + regression predictions, ready to feed straight into the Altair
scatter plots)

**Code:** `hypothesis_features.py`, `hypothesis_tests.py`, `hypothesis_main.py`

---

## STAGE 4: Convergence & Gender — Threads 2 & 5 (complete)

### Thread 2 — Global Inequality / Convergence
*Is the gap between the healthiest and sickest countries widening or narrowing?*

Computed the Coefficient of Variation (CV = std dev / mean across all 200
countries) for each year, 1980-2014, per disease:

| Disease | Direction | Trend strength (R²) | 2014 CV → 2024 projection |
|---|---|---|---|
| **Obesity** | NARROWING (converging) | 0.999 - extremely tight, consistent trend | 0.603 → 0.507 |
| BP | NARROWING (converging) | 0.268 - noisy | 0.180 → 0.137 |
| Diabetes | Essentially flat | 0.075 - basically noise | 0.507 → 0.510 |

**Headline finding: Obesity inequality between countries is converging on
an almost mechanically consistent trend (R²=0.999)** — poorer countries are
not being left behind on obesity, they are catching up to richer ones at a
steady, predictable rate. This directly complicates the "rich countries
have an obesity problem, poor countries don't" framing.

The 2024 projection is a simple straight-line continuation of the existing
trend, explicitly NOT a validated forecast - labeled as such throughout.

**Not computed: population-weighted comparison.** This bonus chart needs a
country population figure for every year, which doesn't exist anywhere in
this project's data yet. Documented as an open decision in
`convergence_analysis.py` - either source one more file (World Bank
Population Total, SP.POP.TOTL) or drop this bonus chart.

**Outputs in `data/analysis/`:** `convergence_cv_by_year.csv`,
`convergence_trend_extrapolation.csv`

**Code:** `convergence_analysis.py`, `trend_extrapolation.py`, `convergence_main.py`

### Thread 5 — Gender
*Is the male/female gap widening or narrowing, and does it track the
between-country story or move independently?*

| Disease | 1980 gap | 2014 gap | Direction | vs. country-level convergence |
|---|---|---|---|---|
| BP | -3.74pp (higher in men) | -4.16pp | WIDENING | independent (r=0.270, not significant) |
| Obesity | +5.69pp (higher in women) | +7.25pp | WIDENING | **moves together** (r=-0.969, p<0.0001) |
| Diabetes | +0.68pp (higher in women) | -0.12pp (higher in men) | NARROWING, **sign flips** | independent (r=0.176, not significant) |

**Headline finding: as countries converge on obesity (Thread 2), the
gender gap within countries widens in near-lockstep (r=-0.969).** The
country-level and sex-level stories for obesity are tightly linked; for BP
and Diabetes they are not - meaning obesity is uniquely a story where both
"between nations" and "between sexes" inequality are moving together,
while the other two diseases tell two unrelated stories at the national vs.
gender level.

A bug was caught and fixed while building this: widening/narrowing must be
judged on the trend of the ABSOLUTE gap, not the raw signed slope - a gap
moving from -3.74 to -4.16 is WIDENING in magnitude even though the raw
slope is negative. Judging only the sign would have wrongly called that
narrowing.

**Outputs in `data/analysis/`:** `gender_gap_by_year.csv`

**Code:** `gender_analysis.py`, `gender_main.py`


## STAGE 5: Targeted Follow-Up + Free Exploration (complete)

### Equality Hypothesis follow-up (new data, narrowly scoped)
Since Gini didn't explain the Japan/Korea vs. USA/UK obesity gap, three
more candidates were tested - but ONLY as a direct comparison table for
the ~41 "Wealthy Decouplers" cluster countries, not a full correlation test
(with this few countries, a correlation coefficient isn't reliable, so this
is presented honestly as a comparison, not a statistic dressed up to look
more rigorous than the sample supports).

**New data used:**
- FAO Food Balance Sheets (`consumption.xlsx`) -> Sugar & Sweeteners and
  Alcoholic Beverages supply, kg/capita/year, 1970-2013
- WHO physical inactivity (`physical_inactivity.csv`) -> % adults
  insufficiently active, 2000-2022

**Result: none of the three explain it either.** Sugar and alcohol don't
cleanly separate Japan/Korea from UK/US. Physical inactivity runs
**opposite** to the naive assumption - Japan (50.6%) and Korea (60.7%)
report *more* inactivity than the UK (21.9%) and US (36.4%).

**Conclusion for the report:** income level, income equality, sugar,
alcohol, and physical inactivity have now all been tested and ruled out as
explanations for this specific anomaly. This is reported as a genuine open
question, not papered over with a forced explanation.

**Outputs:** `data/analysis/equality_followup_wealthy_cluster.csv`
**Code:** `load_exploration_data.py`, `equality_followup_exploration.py`

**Note:** 5 more country-name overrides were found and verified while
processing the FAO file (incl. "Republic of Korea" -> KOR, critical for
this exact comparison) - added to the shared override list in
`country_codes.py`.

### Free exploration (no new data - just asking more of what exists)

| Check | Finding |
|---|---|
| Cluster robustness (hierarchical vs. k-means) | Adjusted Rand Index = 0.684 - strong agreement, the typology is not a k-means artifact |
| Obesity convergence by income group | NOT uniform - High and Low income are converging strongly; Lower-middle income is completely flat (0.674 to 0.677) |
| Obesity gender gap by cluster | NOT uniform either - widening in 2 of 5 clusters (Lean Hypertension, Moderate Transition), narrowing in the other 3 |

**Outputs:** `data/analysis/convergence_by_income_group.csv`,
`data/analysis/gender_gap_by_cluster.csv`, `data/analysis/cluster_robustness_check.txt`
**Code:** `free_exploration.py`

---

## Folder structure (current)

```
project/
├── data/
│   ├── raw/                  original cw1_dataset.xlsx, untouched
│   ├── external/              6 downloaded external files, untouched
│   ├── processed/             still reserved, unused
│   ├── geo/                   world-110m.json (map geometry, Stage 6)
│   └── final/                 Stage 1 outputs (3 files)
│   └── analysis/              Stage 2-5 outputs (12 files)
│       ├── k_selection_diagnostics.csv
│       ├── country_typology.csv
│       ├── cluster_profiles.csv
│       ├── equality_hypothesis_results.csv
│       ├── access_hypothesis_results.csv
│       ├── convergence_cv_by_year.csv
│       ├── convergence_trend_extrapolation.csv
│       ├── gender_gap_by_year.csv
│       ├── equality_followup_wealthy_cluster.csv
│       ├── convergence_by_income_group.csv
│       ├── gender_gap_by_cluster.csv
│       └── cluster_robustness_check.txt
├── src/
│   ├── country_codes.py
│   ├── load_health_data.py
│   ├── load_external_data.py
│   ├── merge_all_data.py
│   ├── feature_engineering.py
│   ├── main.py
│   ├── typology_features.py
│   ├── typology_clustering.py
│   ├── typology_main.py
│   ├── hypothesis_features.py

**To re-run everything so far, in order:**
```bash
python3 src/main.py                  # Stage 1
python3 src/typology_main.py         # Stage 2
python3 src/hypothesis_main.py       # Stage 3
python3 src/convergence_main.py      # Stage 4a
python3 src/gender_main.py           # Stage 4b
# Stage 5 (equality follow-up + free exploration) - see equality_followup_exploration.py
# and free_exploration.py for the functions; no single orchestrator script yet.
```

---

## NEXT STEP: Continue building the remaining Altair visuals

Population-weighted comparison chart: dropped for now (parked, no
population data sourced yet) - can revisit later if needed.

Visual #1 (choropleth) is complete (`visuals/01_choropleth.html` +
static PNG). Remaining visuals to build, in order:
- Cluster scatter + trajectory small multiples (Thread 1)
- Convergence line chart with trend extrapolation (Thread 2)
- Equality/Access hypothesis scatters (Threads 3/4)
- Sex-gap diverging bar + trend line (Thread 5)
- Interactive linked dashboard (built last)

The Stage 5 findings (equality follow-up, cluster robustness, income-group
convergence breakdown, cluster-level gender gap) are additional depth for
the written report's discussion sections - they don't need their own
dedicated Altair visual, but the convergence-by-income-group and
gender-gap-by-cluster tables are good candidates for a small supplementary
chart if there's room.
