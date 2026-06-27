"""
load_exploration_data.py
---------------------------
Loads and cleans the two ADDITIONAL datasets sourced for the targeted
follow-up exploration (NOT part of the core 5-thread analysis - these exist
specifically to dig into the unresolved Equality Hypothesis anomaly, and as
free bonus material for the Lean Hypertension story).

Two sources:

1. FAO Food Balance Sheets (consumption.xlsx) - gives Sugar & Sweeteners
   and Alcoholic Beverages supply, in kg/capita/year, 1970-2013. Covers
   217 "Area" entries, which include CONTINENT AGGREGATES (e.g. "Africa",
   "Asia") mixed in with real countries - these are filtered out.

2. WHO physical inactivity (physical_inactivity.csv) - % of adults with
   insufficient physical activity, 2000-2022, already in the same WHO GHO
   format as the UHC file (ISO3 codes built in - no name matching needed
   for this one at all).

BOTH are merged using the same ISO3-code-only discipline as every other
external source in this project - the FAO file needs fresh name-to-code
matching (its "Area" column uses FAO's own country names, not ours), done
the same verified, no-fuzzy-matching way as country_codes.py.
"""

import pandas as pd
import sys
sys.path.insert(0, "src")
from country_codes import get_country_code_lookup

CONSUMPTION_RAW_PATH = "data/external/consumption.xlsx"
INACTIVITY_RAW_PATH = "data/external/physical_inactivity.csv"

FAO_ITEMS_OF_INTEREST = {
    "Sugar & Sweeteners": "Sugar_Sweeteners_kg_per_capita",
    "Alcoholic Beverages": "Alcohol_kg_per_capita",
}


def _is_continent_aggregate(area_name: str) -> bool:
    """
    FAO's Area column mixes real countries with regional aggregates (e.g.
    "Africa", "Asia", "Australia and New Zealand", "Belgium-Luxembourg" -
    a defunct combined entry). These are identified and excluded by name,
    using a fixed list of known FAO aggregate labels rather than trying to
    algorithmically detect them - this is more transparent and auditable
    than a heuristic guess.
    """
    KNOWN_AGGREGATES = {
        "Africa", "Americas", "Asia", "Europe", "Oceania",
        "Australia and New Zealand", "Belgium-Luxembourg",
        "Eastern Africa", "Western Africa", "Middle Africa", "Northern Africa",
        "Southern Africa", "Eastern Asia", "Southern Asia", "South-eastern Asia",
        "Central Asia", "Western Asia", "Eastern Europe", "Northern Europe",
        "Southern Europe", "Western Europe", "Caribbean", "Central America",
        "South America", "Northern America", "Melanesia", "Micronesia",
        "Polynesia", "Low Income Food Deficit Countries",
        "Land Locked Developing Countries", "Small Island Developing States",
        "Least Developed Countries", "Net Food Importing Developing Countries",
        "World", "European Union (27)", "European Union (28)",
        "USSR", "Czechoslovakia", "Yugoslav SFR", "Sudan (former)",
        "Serbia and Montenegro", "Ethiopia PDR", "China, mainland",
        "China, Hong Kong SAR", "China, Macao SAR", "China, Taiwan Province of",
    }
    return area_name in KNOWN_AGGREGATES


def load_fao_consumption_long() -> tuple[pd.DataFrame, list[str]]:
    """
    Loads consumption.xlsx, keeps only the 2 food items of interest, melts
    the wide year columns (Y1970, Y1971, ...) into long format, excludes
    continent aggregates, and maps each remaining Area name to an ISO3 code.

    Returns:
      - long DataFrame: Country_Code | Year | Sugar_Sweeteners_kg_per_capita | Alcohol_kg_per_capita
      - list of Area names that could not be matched to an ISO3 code (for
        manual review - NOT silently dropped without being reported)
    """
    df = pd.read_excel(CONSUMPTION_RAW_PATH, sheet_name="FoodBalanceSheetsHistoric_E_All")

    df = df[df["Item"].isin(FAO_ITEMS_OF_INTEREST.keys())]
    df = df[~df["Area"].apply(_is_continent_aggregate)]

    year_value_cols = [c for c in df.columns if c.startswith("Y") and c[1:].isdigit()]

    long_df = df.melt(
        id_vars=["Area", "Item"],
        value_vars=year_value_cols,
        var_name="Year",
        value_name="Value",
    )
    long_df["Year"] = long_df["Year"].str.replace("Y", "").astype(int)
    long_df = long_df.dropna(subset=["Value"])

    # Pivot the two Items into their own columns.
    wide = long_df.pivot_table(index=["Area", "Year"], columns="Item", values="Value").reset_index()
    wide = wide.rename(columns=FAO_ITEMS_OF_INTEREST)

    # Map Area names to ISO3 codes - exact matching only, same verified
    # approach as country_codes.py, applied fresh here since FAO's naming
    # doesn't necessarily match our project's original 200 country names.
    area_names = sorted(wide["Area"].unique())
    matched, unmatched = get_country_code_lookup(area_names)

    wide["Country_Code"] = wide["Area"].map(matched)
    wide = wide.dropna(subset=["Country_Code"])

    result = wide[["Country_Code", "Year"] + list(FAO_ITEMS_OF_INTEREST.values())]
    return result.reset_index(drop=True), unmatched


def load_physical_inactivity_long() -> pd.DataFrame:
    """
    Loads physical_inactivity.csv, keeps only "Both sexes" rows (this
    dataset also includes Male/Female breakdowns, not needed for this
    exploration), and renames to clean column names.

    Already has ISO3 codes built in (SpatialDimValueCode) - no name
    matching needed, same as the UHC file.

    Returns: Country_Code | Year | Physical_Inactivity_pct
    """
    df = pd.read_csv(INACTIVITY_RAW_PATH)
    df = df[df["Dim1"] == "Both sexes"]

    clean = df.rename(columns={
        "SpatialDimValueCode": "Country_Code",
        "Period": "Year",
        "FactValueNumeric": "Physical_Inactivity_pct",
    })

    return clean[["Country_Code", "Year", "Physical_Inactivity_pct"]].reset_index(drop=True)
