"""
country_codes.py
-----------------
Builds a single, verified lookup table mapping every country name used in our
original health dataset (cw1_dataset.xlsx) to its ISO 3166-1 alpha-3 code
(e.g. "Afghanistan" -> "AFG").

WHY THIS EXISTS:
Every external dataset we bring in (Gini, UHC, Income Group) spells country
names slightly differently ("Russia" vs "Russian Federation" vs "Russian Fed.").
Merging on free-text country names is exactly how silent, wrong merges happen.
Merging on ISO3 codes instead removes that risk almost entirely, because codes
are standardised and unambiguous.

HOW IT WORKS:
1. Try an EXACT (case-insensitive) match against pycountry's official name,
   common name, and official name fields. No fuzzy/approximate matching is
   used anywhere in this file, because fuzzy matching was tested and found to
   silently produce wrong results (e.g. it matched "Niger" to Nigeria's code).
2. The handful of names that don't exact-match (because our dataset uses an
   older/alternate name, e.g. "Swaziland" instead of "Eswatini") are mapped
   manually below. Every single one of these manual mappings was individually
   verified against pycountry's official record before being added (see the
   verification step run during development - each line below states what
   pycountry's official name for that code actually is, as a permanent
   comment, so the mapping can be audited later).

OUTPUT:
get_country_code_lookup() returns a dict: {our_country_name: iso3_code}
covering all 200 countries in the original dataset. Nothing is invented -
any name that cannot be matched or verified is left out and will show up
as a logged warning rather than a silent guess.
"""

import pandas as pd
import pycountry


# Manually verified mappings for names that don't exact-match pycountry's
# name / common_name / official_name fields.
# Format: "name as it appears in our dataset": "ISO3 code"
# Each comment shows pycountry's official name for that code, confirmed
# individually before being added here.
MANUAL_COUNTRY_CODE_OVERRIDES = {
    "China (Hong Kong SAR)": "HKG",              # pycountry: Hong Kong
    "Cote d'Ivoire": "CIV",                       # pycountry: Côte d'Ivoire
    "DR Congo": "COD",                            # pycountry: Congo, The Democratic Republic of the
    "Guinea Bissau": "GNB",                       # pycountry: Guinea-Bissau
    "Lao PDR": "LAO",                             # pycountry: Lao People's Democratic Republic
    "Macedonia (TFYR)": "MKD",                    # pycountry: North Macedonia
    "Micronesia (Federated States of)": "FSM",    # pycountry: Micronesia, Federated States of
    "Occupied Palestinian Territory": "PSE",       # pycountry: Palestine, State of
    "Swaziland": "SWZ",                            # pycountry: Eswatini
    "Turkey": "TUR",                               # pycountry: Türkiye
    # Added while processing the FAO consumption file (load_exploration_data.py):
    "Bolivia (Plurinational State of)": "BOL",     # pycountry: Bolivia, Plurinational State of
    "Iran (Islamic Republic of)": "IRN",           # pycountry: Iran, Islamic Republic of
    "Netherlands (Kingdom of the)": "NLD",         # pycountry: Netherlands
    "Republic of Korea": "KOR",                    # pycountry: Korea, Republic of
    "Venezuela (Bolivarian Republic of)": "VEN",   # pycountry: Venezuela, Bolivarian Republic of
}


def _build_exact_match_lookup() -> dict:
    """
    Builds a lowercase-name -> ISO3 lookup using ONLY exact string matches
    against pycountry's name, common_name, and official_name fields.
    No fuzzy/approximate matching - this is intentional (see module docstring).
    """
    lookup = {}
    for c in pycountry.countries:
        lookup[c.name.lower()] = c.alpha_3
        if hasattr(c, "common_name"):
            lookup[c.common_name.lower()] = c.alpha_3
        if hasattr(c, "official_name"):
            lookup[c.official_name.lower()] = c.alpha_3
    return lookup


def get_country_code_lookup(country_names: list[str]) -> tuple[dict, list[str]]:
    """
    Given a list of country names (as they appear in our raw dataset),
    returns:
        - a dict {country_name: iso3_code} for every name successfully matched
        - a list of names that could NOT be matched (should be empty for our
          known 200-country dataset; if not empty, this must be investigated
          before proceeding - it means a new/unrecognised country name appeared)

    No invented codes are ever returned. A name either matches exactly or
    via the verified manual override list above, or it is reported as
    unmatched.
    """
    exact_lookup = _build_exact_match_lookup()

    matched = {}
    unmatched = []

    for name in country_names:
        key = name.lower()
        if key in exact_lookup:
            matched[name] = exact_lookup[key]
        elif name in MANUAL_COUNTRY_CODE_OVERRIDES:
            matched[name] = MANUAL_COUNTRY_CODE_OVERRIDES[name]
        else:
            unmatched.append(name)

    return matched, unmatched


# pycountry_convert's continent table is missing a small number of countries
# (confirmed by testing against our actual 200-country list - only this one
# came up missing). Mapped manually here, citing the UN geoscheme as the
# basis, rather than left blank.
MANUAL_CONTINENT_OVERRIDES = {
    "TLS": "Asia",  # Timor-Leste - UN geoscheme: South-Eastern Asia
}


def get_continent_lookup(iso3_codes: list[str]) -> dict:
    """
    Maps ISO3 codes to continent names using pycountry_convert, topped up with
    MANUAL_CONTINENT_OVERRIDES above for the few codes pycountry_convert's
    table does not cover. Any code still missing after both steps is left out
    of the result rather than guessed - the merge step logs these explicitly.
    """
    import pycountry_convert as pcc

    continent_name_map = {
        "AF": "Africa",
        "AS": "Asia",
        "EU": "Europe",
        "NA": "North America",
        "SA": "South America",
        "OC": "Oceania",
        "AN": "Antarctica",
    }

    lookup = {}
    for code in iso3_codes:
        if code in MANUAL_CONTINENT_OVERRIDES:
            lookup[code] = MANUAL_CONTINENT_OVERRIDES[code]
            continue
        try:
            alpha_2 = pcc.country_alpha3_to_country_alpha2(code)
            continent_code = pcc.country_alpha2_to_continent_code(alpha_2)
            lookup[code] = continent_name_map.get(continent_code)
        except KeyError:
            # Not in pycountry_convert's table and no manual override exists -
            # leave unmapped rather than guess.
            continue
    return lookup
