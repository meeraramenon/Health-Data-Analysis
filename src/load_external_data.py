"""
load_external_data.py
----------------------
Loads and cleans the three external datasets that get merged into the health
panel. Each loader returns a tidy long-format table keyed by ISO3 country
code (and Year, where the data varies by year), ready to be merged.

No values are invented anywhere in this file. Where source data is missing
for a country/year, it stays missing (NaN) - it is never filled, averaged,
or guessed.
"""

import pandas as pd

GINI_RAW_PATH = "data/external/gini_worldbank_raw.csv"
UHC_RAW_PATH = "data/external/uhc_who_raw.csv"
INCOME_HISTORICAL_RAW_PATH = "data/external/income_group_historical_raw.xlsx"
INCOME_CURRENT_RAW_PATH = "data/external/income_group_current_raw.xlsx"


# ---------------------------------------------------------------------------
# GINI INDEX (World Bank) - Equality Hypothesis variable
# ---------------------------------------------------------------------------

def load_gini_long() -> pd.DataFrame:
    """
    Loads the World Bank Gini CSV (wide format: one column per year) and
    reshapes it to long format: Country_Code | Year | Gini_Index

    The raw file has 4 metadata rows before the real header, hence skiprows=4.
    Rows are kept exactly as published - no interpolation, no filling gaps.
    """
    df = pd.read_csv(GINI_RAW_PATH, skiprows=4)

    year_cols = [c for c in df.columns if c.strip().isdigit()]

    long_df = df.melt(
        id_vars=["Country Code"],
        value_vars=year_cols,
        var_name="Year",
        value_name="Gini_Index",
    )
    long_df = long_df.rename(columns={"Country Code": "Country_Code"})
    long_df["Year"] = long_df["Year"].astype(int)
    long_df = long_df.dropna(subset=["Gini_Index"])

    return long_df.reset_index(drop=True)


def get_latest_gini_snapshot(gini_long: pd.DataFrame) -> pd.DataFrame:
    """
    For each country, keeps only its most recent available Gini value.

    WHY A SNAPSHOT: Gini is reported very sparsely (most countries are only
    surveyed every few years), so it cannot be treated as a full year-by-year
    time series. It is used here as a relatively stable, slow-moving
    structural characteristic of each country rather than an annual metric.

    Returns: Country_Code | Gini_Index | Gini_Year (the year the snapshot is from,
    kept so the assumption is traceable / auditable in the final report)
    """
    latest = (
        gini_long.sort_values("Year")
        .groupby("Country_Code", as_index=False)
        .tail(1)
        .rename(columns={"Year": "Gini_Year"})
    )
    return latest[["Country_Code", "Gini_Index", "Gini_Year"]]


# ---------------------------------------------------------------------------
# UHC SERVICE COVERAGE INDEX (WHO) - Access Hypothesis variable
# Also the source of WHO Region, used directly instead of building a
# separate region lookup.
# ---------------------------------------------------------------------------

def load_uhc_long() -> pd.DataFrame:
    """
    Loads the WHO UHC Service Coverage Index file and keeps only the columns
    we need: country ISO3 code, WHO region, year, and the index value.

    Returns: Country_Code | WHO_Region | Year | UHC_Index
    """
    df = pd.read_csv(UHC_RAW_PATH)

    clean = df.rename(columns={
        "SpatialDimValueCode": "Country_Code",
        "ParentLocation": "WHO_Region",
        "Period": "Year",
        "Value": "UHC_Index",
    })

    clean = clean[["Country_Code", "WHO_Region", "Year", "UHC_Index"]].copy()
    clean["Year"] = clean["Year"].astype(int)
    clean["UHC_Index"] = pd.to_numeric(clean["UHC_Index"], errors="coerce")
    clean = clean.dropna(subset=["UHC_Index"])

    return clean.reset_index(drop=True)


def get_who_region_lookup(uhc_long: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts a clean Country_Code -> WHO_Region lookup (one row per country).
    Since WHO Region doesn't change year to year, we just take the first
    occurrence per country.
    """
    return (
        uhc_long[["Country_Code", "WHO_Region"]]
        .drop_duplicates(subset="Country_Code")
        .reset_index(drop=True)
    )


# ---------------------------------------------------------------------------
# INCOME GROUP - historical (year-varying) and current (fallback only)
# ---------------------------------------------------------------------------

def load_income_group_historical() -> pd.DataFrame:
    """
    Loads the OGHIST "Country Analytical History" sheet, which records each
    country's income classification (L / LM / UM / H) for every fiscal year
    back to FY89 (calendar year 1987).

    The sheet is laid out awkwardly (header rows mixed with data, codes for
    fiscal year and calendar year on separate rows). This function locates
    the calendar-year header row and the country rows programmatically rather
    than hard-coding row numbers, so it doesn't silently break if the file's
    layout shifts slightly between World Bank releases.

    Returns long format: Country_Code | Year | Income_Group_Code
    where Income_Group_Code is one of: L, LM, UM, H (or ".." which the source
    file uses for "not yet classified" - kept as NaN, not invented).
    """
    raw = pd.read_excel(
        INCOME_HISTORICAL_RAW_PATH,
        sheet_name="Country Analytical History",
        header=None,
    )

    # Row 5 (0-indexed) holds the calendar year for each column, e.g. 1987, 1988, ...
    calendar_year_row = raw.iloc[5]

    # Identify which columns actually contain a 4-digit calendar year.
    year_columns = {}
    for col_idx, val in calendar_year_row.items():
        try:
            year = int(val)
            if 1900 < year < 2100:
                year_columns[col_idx] = year
        except (ValueError, TypeError):
            continue

    # Country rows: column 0 holds the ISO/World Bank country code, column 1
    # holds the country name. Real country rows have a non-null code.
    country_rows = raw[raw[0].notna()].copy()

    records = []
    for _, row in country_rows.iterrows():
        code = row[0]
        for col_idx, year in year_columns.items():
            value = row[col_idx]
            records.append({
                "Country_Code": code,
                "Year": year,
                "Income_Group_Code": value,
            })

    long_df = pd.DataFrame(records)

    # The source file uses ".." for "not classified that year" - treat as missing.
    long_df["Income_Group_Code"] = long_df["Income_Group_Code"].replace("..", pd.NA)

    # A small number of cells carry a footnote marker ("LM*" instead of "LM"),
    # found here on Yemen's 1987-88 rows only. The asterisk denotes a footnote
    # in the source file, not a different income category, so it is stripped.
    long_df["Income_Group_Code"] = long_df["Income_Group_Code"].astype(str).str.replace("*", "", regex=False)
    long_df["Income_Group_Code"] = long_df["Income_Group_Code"].replace("nan", pd.NA)

    return long_df


INCOME_GROUP_CODE_TO_LABEL = {
    "L": "Low income",
    "LM": "Lower middle income",
    "UM": "Upper middle income",
    "H": "High income",
}


def load_income_group_current() -> pd.DataFrame:
    """
    Loads the current (2025) CLASS.xlsx 'List of economies' sheet, used only
    as a fallback for countries that are entirely missing from the historical
    file (e.g. very small territories that weren't tracked back in 1987).

    Returns: Country_Code | Income_Group_Current (full text label already,
    e.g. "High income" - no code translation needed for this file)
    """
    df = pd.read_excel(INCOME_CURRENT_RAW_PATH, sheet_name="List of economies")
    df = df.rename(columns={"Code": "Country_Code", "Income group": "Income_Group_Current"})
    return df[["Country_Code", "Income_Group_Current"]].dropna(subset=["Income_Group_Current"])
