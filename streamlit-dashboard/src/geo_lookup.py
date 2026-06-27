"""
geo_lookup.py
---------------
The world map geometry file (data/geo/world-110m.json) identifies each
country by an ISO 3166-1 NUMERIC code (e.g. 4 = Afghanistan), not the
alpha-3 code (AFG) used everywhere else in this project. This module
builds the bridge between the two, using pycountry - the same trusted
library already used for the alpha-3 lookup in country_codes.py.

WHERE THE MAP FILE CAME FROM: fetched once from
https://raw.githubusercontent.com/vega/vega-datasets/main/data/world-110m.json
(the standard Vega/Altair example world map dataset) and saved locally to
data/geo/world-110m.json, so chart rendering never depends on a live
network call.

WHAT THIS MEANS FOR COVERAGE: the map file contains 177 country shapes.
Our dataset has 200 countries. Small territories (e.g. Pacific islands,
Caribbean micro-states) that exist in our health data but not on this
simplified world map will simply not have a shape to colour in - they are
NOT dropped from the underlying data, they just won't appear on the map
visual specifically (they still appear in every other chart). This gap is
logged explicitly, not silently absorbed.
"""

import pandas as pd
import pycountry

GEO_FILE_PATH = "data/geo/world-110m.json"


def get_alpha3_to_numeric_id_lookup(alpha3_codes: list[str]) -> dict:
    """
    Returns {alpha3_code: numeric_id (int)} for every code pycountry can
    resolve. Codes pycountry has no numeric ID for are simply absent from
    the result (not guessed).
    """
    lookup = {}
    for code in alpha3_codes:
        country = pycountry.countries.get(alpha_3=code)
        if country is not None and hasattr(country, "numeric"):
            lookup[code] = int(country.numeric)
    return lookup


def check_map_coverage(alpha3_codes: list[str]) -> tuple[list[str], list[str]]:
    """
    Compares our country codes against the IDs actually present in the map
    geometry file. Returns (covered, not_covered) lists of alpha3 codes.
    Use this before building the choropleth to know exactly which countries
    will and won't render on the map.
    """
    import json

    with open(GEO_FILE_PATH) as f:
        topo = json.load(f)
    map_ids = {g["id"] for g in topo["objects"]["countries"]["geometries"]}

    id_lookup = get_alpha3_to_numeric_id_lookup(alpha3_codes)

    covered = [code for code, num_id in id_lookup.items() if num_id in map_ids]
    not_covered = [code for code in alpha3_codes if code not in covered]

    return covered, not_covered
