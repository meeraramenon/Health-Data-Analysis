"""
load_health_data.py
--------------------
Loads the three original health sheets (Raised Blood Pressure, BMI, Diabetes)
from cw1_dataset.xlsx and combines them into a single, clean, long-format
panel: one row per Country / Sex / Year, with one column per health metric.

CLEANING DECISIONS MADE HERE (and why):
1. Sex labels "Men"/"Women" are renamed to "Male"/"Female" - this is a
   cosmetic standardisation only, no values are changed.
2. Prevalence values are stored as proportions (0-1) in the original file.
   They are converted to percentages (0-100) here, since percentages are
   the more interpretable unit for charts and commentary. This is a unit
   conversion, not a data change - multiplying by 100 does not alter what
   the number represents.
3. The three sheets have different year coverage (BP: 1975-2015, BMI:
   1975-2016, Diabetes: 1980-2014). They are NOT trimmed to a common window
   at this stage - that decision is left to the analysis step, because
   different analyses may want different windows (e.g. the typology
   clustering wants the longest run available per metric, while the
   cross-metric residual tests need the common 1980-2014 window). Trimming
   here would throw away real data future steps might need.
4. No missing values are filled in. If a country/sex/year combination is
   absent from a given sheet, the resulting column is left as NaN (missing),
   never zero, never an average, never invented.
"""

import pandas as pd

RAW_FILE_PATH = "data/raw/data.xlsx"

SEX_RENAME_MAP = {
    "Men": "Male",
    "Women": "Female",
}

# Each sheet's original column name -> the clean column name we want, and
# whether the value needs to be converted from proportion (0-1) to
# percentage (0-100).
SHEET_CONFIG = {
    "Raised Blood Pressure": {
        "value_col_raw": "Prevalence of raised blood pressure",
        "value_col_clean": "BP_Prevalence_pct",
    },
    "BMI": {
        "value_col_raw": "Prevalence of BMI>=30 kg/m\u2264 (obesity)",
        "value_col_clean": "Obesity_Prevalence_pct",
    },
    "Diabetes": {
        "value_col_raw": "Age-standardised diabetes prevalence",
        "value_col_clean": "Diabetes_Prevalence_pct",
    },
}

COUNTRY_COL_RAW = "Country/Region/World"
COUNTRY_COL_CLEAN = "Country"


def _load_and_clean_sheet(sheet_name: str) -> pd.DataFrame:
    """
    Loads one sheet, renames columns to clean names, standardises Sex labels,
    and converts the prevalence value from proportion to percentage.
    Returns a DataFrame with columns: Country, Sex, Year, <value_col_clean>
    """
    config = SHEET_CONFIG[sheet_name]
    df = pd.read_excel(RAW_FILE_PATH, sheet_name=sheet_name)

    df = df.rename(columns={
        COUNTRY_COL_RAW: COUNTRY_COL_CLEAN,
        config["value_col_raw"]: config["value_col_clean"],
    })

    df["Sex"] = df["Sex"].replace(SEX_RENAME_MAP)

    # Proportion -> percentage. This is a unit conversion only.
    df[config["value_col_clean"]] = df[config["value_col_clean"]] * 100

    # Explicit dtypes - guards against Year being read as float, etc.
    df["Year"] = df["Year"].astype(int)
    df["Country"] = df["Country"].astype(str)
    df["Sex"] = df["Sex"].astype(str)
    df[config["value_col_clean"]] = df[config["value_col_clean"]].astype(float)

    return df[["Country", "Sex", "Year", config["value_col_clean"]]]


def build_health_panel() -> pd.DataFrame:
    """
    Loads all three sheets and outer-joins them on (Country, Sex, Year).
    An OUTER join is used deliberately: if a country/sex/year combination
    exists in one sheet but not another (e.g. Diabetes data starts in 1980
    but BP data starts in 1975), we keep the row and leave the missing
    metric as NaN, rather than dropping the row (inner join) or inventing
    a value.

    Returns the combined long-format health panel:
    Country | Sex | Year | BP_Prevalence_pct | Obesity_Prevalence_pct | Diabetes_Prevalence_pct
    """
    bp = _load_and_clean_sheet("Raised Blood Pressure")
    bmi = _load_and_clean_sheet("BMI")
    diabetes = _load_and_clean_sheet("Diabetes")

    panel = bp.merge(bmi, on=["Country", "Sex", "Year"], how="outer")
    panel = panel.merge(diabetes, on=["Country", "Sex", "Year"], how="outer")

    panel = panel.sort_values(["Country", "Sex", "Year"]).reset_index(drop=True)

    return panel


def get_unique_country_names(panel: pd.DataFrame) -> list[str]:
    """Returns the sorted list of distinct country names in the panel."""
    return sorted(panel["Country"].unique())
