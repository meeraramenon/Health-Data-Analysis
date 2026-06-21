# Data Preparation Pipeline — README

## What this pipeline produces

Three final files in `data/final/`:

1. **`master_panel_by_sex.csv`** (16,800 rows)
   One row per Country × Sex × Year. The full panel with Male and Female
   kept separate. Use this for anything sex-specific.

2. **`sex_gap_table.csv`** (8,400 rows)
   One row per Country × Year. Female-minus-Male gap for each disease.
   Positive = higher in women, negative = higher in men. This is the input
   for the gender thread.

3. **`combined_panel_with_risk_index.csv`** (8,400 rows)
   One row per Country × Year. Male/Female averaged together, plus the new
   `Metabolic_Risk_Index` column. **This is the main file for the typology
   clustering, convergence/dispersion analysis, and the Equality/Access
   hypothesis tests** — those questions are about countries, not sex
   subgroups.

## Folder structure

```
project/
├── data/
│   ├── raw/                  the original cw1_dataset.xlsx, untouched
│   ├── external/             the 3 downloaded external files, untouched
│   ├── processed/            (reserved for the next analysis stage)
│   └── final/                the 3 output files described above
├── src/
│   ├── country_codes.py      builds the verified ISO3 country code lookup
│   ├── load_health_data.py   loads + cleans the 3 original health sheets
│   ├── load_external_data.py loads + cleans Gini, UHC, Income Group
│   ├── merge_all_data.py     merges everything together, with audit logging
│   ├── feature_engineering.py builds Sex Gap, combined panel, Risk Index
│   └── main.py                runs the whole pipeline end to end
└── logs/                      audit logs from every merge step (see below)
```

## How country matching works (the most important step)

External files spell country names differently ("Russia" vs. "Russian
Federation"). Merging on free-text names is how silent wrong merges happen.
So every merge in this pipeline uses **ISO3 country codes** instead
(e.g. `RUS`, `USA`, `AFG`), built once in `country_codes.py`:

- 190 of our 200 countries matched **exactly** against pycountry's official
  name fields — no guessing involved.
- The remaining 10 (e.g. "DR Congo", "Swaziland", "Turkey") were mapped
  **manually**, and each mapping was individually checked against
  pycountry's official record before being added — see the comments next to
  each entry in `country_codes.py`.
- **Fuzzy/approximate name matching was tested and rejected** — it silently
  mapped "Niger" to Nigeria's country code. Nothing in this pipeline uses
  fuzzy matching anywhere.

## Audit logs (`logs/` folder) — read these to verify nothing was invented

| Log file | What it shows |
|---|---|
| `01_country_code_matching.log` | All 200/200 countries matched to a code. |
| `02_continent_matching.log` | All 200/200 matched to a continent (1 manual fix: Timor-Leste). |
| `03_who_region_matching.log` | 192/200 matched; 8 small territories (e.g. Hong Kong, Puerto Rico, Greenland) aren't separately tracked by WHO and are left blank. |
| `04_gini_matching.log` | 169/200 have at least one Gini value; 31 countries (mostly Gulf states, small islands, a few unsurveyed nations) have none, left blank. |
| `05_income_group_fallback.log` | Only 3 countries (Cook Islands, Niue, Tokelau) have no income classification at all, anywhere. |

**Nothing in this pipeline fills a gap with a guessed, averaged, or invented
value.** Where data doesn't exist, the cell is `NaN`.

## Explicit, flagged assumptions (the only places this pipeline "extends" data)

These are the only two simplifications made, and both are flagged with their
own boolean column so they're fully traceable in any later analysis:

1. **UHC Index only exists from 2000 onward**, but health data goes back to
   1975. For years before 2000, each country's *earliest available* UHC
   value is carried backward. Flagged in `UHC_Index_Is_Carried_Back`.
2. **Historical Income Group only goes back to 1987.** For 1975-1986, each
   country's earliest available classification is carried backward. Flagged
   in `Income_Group_Is_Carried_Back`. (A handful of countries have no
   historical data at all and fall back to the *current*, 2025
   classification instead — flagged separately in
   `Income_Group_Used_Current_Fallback`.)

**Gini Index is deliberately NOT extended this way** — it's used as a single
snapshot (each country's most recent available value, recorded in
`Gini_Year`), exactly as planned, because it's reported too sparsely to
treat as a time-varying field at all.

## Column dictionary

| Column | Type | Meaning |
|---|---|---|
| `Country` | text | Country name as it appears in the original dataset |
| `Country_Code` | text | ISO3 code, used as the join key for all merges |
| `Sex` | text | Male / Female (only in `master_panel_by_sex.csv`) |
| `Year` | integer | Calendar year |
| `BP_Prevalence_pct` | float | % of population with raised blood pressure |
| `Obesity_Prevalence_pct` | float | % of population with BMI ≥ 30 |
| `Diabetes_Prevalence_pct` | float | Age-standardised diabetes prevalence, % |
| `Continent` | text | From pycountry_convert (+1 manual fix) |
| `WHO_Region` | text | From the WHO UHC source file directly |
| `UHC_Index` | float | WHO Universal Health Coverage service coverage score, 0-100 |
| `Gini_Index` | float | World Bank income inequality score (0=perfectly equal, 100=perfectly unequal); single snapshot per country |
| `Gini_Year` | integer | The year that country's Gini snapshot is from |
| `Income_Group` | text | Low / Lower-middle / Upper-middle / High income, year-aware where possible |
| `*_Sex_Gap_pct` | float | Female value minus Male value (sex_gap_table.csv only) |
| `Metabolic_Risk_Index` | float | Equal-weighted composite of all 3 diseases, each min-max normalised to 0-100 first; NaN if any of the 3 underlying metrics is missing |

## What's intentionally NOT done yet (next stage, not this one)

This pipeline stops at clean, merged, feature-ready data. It does **not**
yet compute: the trajectory clustering/typology, the BP/Obesity regression
residuals for the Equality and Access hypothesis tests, the
convergence/dispersion (coefficient of variation) series, or the trend
extrapolation. Those belong to the analysis stage, which uses these three
output files as its starting point.
