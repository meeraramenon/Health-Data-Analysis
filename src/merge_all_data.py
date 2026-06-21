"""
merge_all_data.py
------------------
Merges the health panel (Country/Sex/Year + 3 disease metrics) with all
external data sources, using verified ISO3 country codes as the join key
(never free-text country names - see country_codes.py for why).

Every merge step below is a LEFT join from the health panel's perspective:
we keep every row of our 200-country health panel no matter what, and attach
external data where it's available. Rows that have no matching external data
simply get NaN for that column - nothing is dropped, nothing is invented.

A full audit log of which countries matched / did not match each external
source is written to logs/, so every step of this process can be checked.
"""

import pandas as pd

from country_codes import get_country_code_lookup, get_continent_lookup
from load_health_data import build_health_panel
from load_external_data import (
    load_gini_long, get_latest_gini_snapshot,
    load_uhc_long, get_who_region_lookup,
    load_income_group_historical, load_income_group_current,
    INCOME_GROUP_CODE_TO_LABEL,
)

LOG_DIR = "logs"


def _write_log(filename: str, lines: list[str]) -> None:
    with open(f"{LOG_DIR}/{filename}", "w") as f:
        f.write("\n".join(lines))


def attach_country_codes(panel: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a Country_Code column to the health panel based on the verified
    lookup in country_codes.py. Logs any country name that fails to match
    (there should be none for our known 200-country dataset - if any appear,
    this needs manual investigation before continuing, NOT a silent guess).
    """
    country_names = sorted(panel["Country"].unique())
    matched, unmatched = get_country_code_lookup(country_names)

    log_lines = [f"Total countries in health panel: {len(country_names)}"]
    log_lines.append(f"Matched to ISO3 code: {len(matched)}")
    log_lines.append(f"UNMATCHED (investigate before proceeding): {len(unmatched)}")
    for u in unmatched:
        log_lines.append(f"  - {u}")
    _write_log("01_country_code_matching.log", log_lines)

    if unmatched:
        raise ValueError(
            f"{len(unmatched)} country name(s) could not be matched to an ISO3 "
            f"code: {unmatched}. Resolve this in country_codes.py before "
            f"continuing - do not proceed with unmatched countries silently dropped."
        )

    panel = panel.copy()
    panel["Country_Code"] = panel["Country"].map(matched)
    return panel


def attach_continent(panel: pd.DataFrame) -> pd.DataFrame:
    """Adds Continent column based on Country_Code. Logs any code with no match."""
    codes = sorted(panel["Country_Code"].unique())
    continent_lookup = get_continent_lookup(codes)

    missing = [c for c in codes if c not in continent_lookup]
    log_lines = [f"Total country codes: {len(codes)}"]
    log_lines.append(f"Continent found for: {len(continent_lookup)}")
    log_lines.append(f"Missing continent (left as NaN, not guessed): {len(missing)}")
    for m in missing:
        log_lines.append(f"  - {m}")
    _write_log("02_continent_matching.log", log_lines)

    panel = panel.copy()
    panel["Continent"] = panel["Country_Code"].map(continent_lookup)
    return panel


def attach_who_region(panel: pd.DataFrame) -> pd.DataFrame:
    """
    Adds WHO_Region column using the lookup extracted directly from the UHC
    dataset (see load_external_data.get_who_region_lookup). Countries in our
    200-country panel that the WHO UHC file does not cover (it covers 195
    countries/territories, not all 200) are logged and left as NaN.
    """
    uhc_long = load_uhc_long()
    who_region_lookup = get_who_region_lookup(uhc_long)
    region_map = dict(zip(who_region_lookup["Country_Code"], who_region_lookup["WHO_Region"]))

    our_codes = set(panel["Country_Code"].unique())
    covered_codes = set(region_map.keys())
    missing = sorted(our_codes - covered_codes)

    log_lines = [f"Countries in our panel: {len(our_codes)}"]
    log_lines.append(f"Covered by WHO UHC source file: {len(our_codes & covered_codes)}")
    log_lines.append(f"NOT covered by WHO UHC source file (WHO_Region left as NaN): {len(missing)}")
    for m in missing:
        log_lines.append(f"  - {m}")
    _write_log("03_who_region_matching.log", log_lines)

    panel = panel.copy()
    panel["WHO_Region"] = panel["Country_Code"].map(region_map)
    return panel


def attach_uhc_index(panel: pd.DataFrame) -> pd.DataFrame:
    """
    Merges UHC_Index onto the panel by (Country_Code, Year).

    UHC data only exists from 2000 onward, but our health panel goes back to
    1975/1980. For years before 2000, each country's EARLIEST available UHC
    value is carried backward. This is an explicit, documented assumption
    (UHC reflects slow-moving health-system structure, not something that
    swings year to year) - it is applied transparently here, not hidden.
    A separate flag column records exactly which rows used this carried-back
    value vs. an actual reported value, so the report can be precise about it.
    """
    uhc_long = load_uhc_long()

    earliest_uhc = (
        uhc_long.sort_values("Year")
        .groupby("Country_Code", as_index=False)
        .first()
        .rename(columns={"Year": "UHC_Earliest_Year", "UHC_Index": "UHC_Index_Earliest"})
    )[["Country_Code", "UHC_Earliest_Year", "UHC_Index_Earliest"]]

    panel = panel.merge(uhc_long[["Country_Code", "Year", "UHC_Index"]],
                         on=["Country_Code", "Year"], how="left")
    panel = panel.merge(earliest_uhc, on="Country_Code", how="left")

    panel["UHC_Index_Is_Carried_Back"] = panel["UHC_Index"].isna() & panel["UHC_Index_Earliest"].notna()
    panel["UHC_Index_Final"] = panel["UHC_Index"].fillna(panel["UHC_Index_Earliest"])

    panel = panel.drop(columns=["UHC_Index", "UHC_Index_Earliest", "UHC_Earliest_Year"])
    panel = panel.rename(columns={"UHC_Index_Final": "UHC_Index"})

    return panel


def attach_gini_index(panel: pd.DataFrame) -> pd.DataFrame:
    """
    Attaches a single Gini_Index snapshot value (and the year it's from) per
    country - see load_external_data.get_latest_gini_snapshot for the
    sparse-data reasoning. This is the same value for every row of a given
    country regardless of Year, by design (structural/slow-moving variable).
    """
    gini_long = load_gini_long()
    gini_snapshot = get_latest_gini_snapshot(gini_long)

    our_codes = set(panel["Country_Code"].unique())
    covered_codes = set(gini_snapshot["Country_Code"].unique())
    missing = sorted(our_codes - covered_codes)

    log_lines = [f"Countries in our panel: {len(our_codes)}"]
    log_lines.append(f"Have at least one Gini value, any year: {len(our_codes & covered_codes)}")
    log_lines.append(f"No Gini value available at all (left as NaN): {len(missing)}")
    for m in missing:
        log_lines.append(f"  - {m}")
    _write_log("04_gini_matching.log", log_lines)

    panel = panel.merge(gini_snapshot, on="Country_Code", how="left")
    return panel


def attach_income_group(panel: pd.DataFrame) -> pd.DataFrame:
    """
    Attaches Income_Group as a year-varying field using the historical
    classification (OGHIST). For years before the historical file's coverage
    starts (1987), each country's EARLIEST available classification is
    carried backward - the same documented-assumption approach used for UHC,
    flagged with its own column.

    Countries entirely absent from the historical file fall back to the
    CURRENT (2025) classification instead, also flagged.
    """
    income_hist = load_income_group_historical()
    income_hist["Income_Group"] = income_hist["Income_Group_Code"].map(INCOME_GROUP_CODE_TO_LABEL)

    earliest_hist = (
        income_hist.dropna(subset=["Income_Group"])
        .sort_values("Year")
        .groupby("Country_Code", as_index=False)
        .first()
        .rename(columns={"Year": "Income_Earliest_Year", "Income_Group": "Income_Group_Earliest"})
    )[["Country_Code", "Income_Earliest_Year", "Income_Group_Earliest"]]

    panel = panel.merge(
        income_hist[["Country_Code", "Year", "Income_Group"]],
        on=["Country_Code", "Year"], how="left"
    )
    panel = panel.merge(earliest_hist, on="Country_Code", how="left")

    panel["Income_Group_Is_Carried_Back"] = panel["Income_Group"].isna() & panel["Income_Group_Earliest"].notna()
    panel["Income_Group"] = panel["Income_Group"].fillna(panel["Income_Group_Earliest"])
    panel = panel.drop(columns=["Income_Group_Earliest", "Income_Earliest_Year"])

    # Fallback to current classification only for countries with NO historical
    # data at all (not just missing in some years).
    income_current = load_income_group_current()
    current_map = dict(zip(income_current["Country_Code"], income_current["Income_Group_Current"]))

    codes_with_no_history = set(panel.loc[panel["Income_Group"].isna(), "Country_Code"].unique())
    log_lines = [f"Country codes with zero historical income data: {len(codes_with_no_history)}"]
    for c in sorted(codes_with_no_history):
        fallback_value = current_map.get(c, "NO DATA AVAILABLE AT ALL")
        log_lines.append(f"  - {c}: falling back to current classification -> {fallback_value}")
    _write_log("05_income_group_fallback.log", log_lines)

    panel["Income_Group_Used_Current_Fallback"] = panel["Income_Group"].isna() & panel["Country_Code"].map(current_map).notna()
    panel["Income_Group"] = panel["Income_Group"].fillna(panel["Country_Code"].map(current_map))

    return panel


def build_merged_master() -> pd.DataFrame:
    """
    Runs the full merge pipeline in order:
    health panel -> + country code -> + continent -> + WHO region
    -> + UHC index -> + Gini index -> + income group

    Returns the fully merged master DataFrame, ready for derived-column
    feature engineering (next module).
    """
    panel = build_health_panel()
    panel = attach_country_codes(panel)
    panel = attach_continent(panel)
    panel = attach_who_region(panel)
    panel = attach_uhc_index(panel)
    panel = attach_gini_index(panel)
    panel = attach_income_group(panel)
    return panel
