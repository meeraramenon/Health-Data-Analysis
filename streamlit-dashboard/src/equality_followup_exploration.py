"""
equality_followup_exploration.py
-----------------------------------
A SMALL, TARGETED follow-up - not a new full-scale hypothesis test.

The Equality Hypothesis (Gini explains who stays thin) did not hold up.
This module checks the next most obvious candidates - sugar/sweetener
supply, alcohol supply, and physical inactivity - but ONLY for the
"Wealthy Decouplers" cluster (the ~41 countries where the original
Japan/Korea vs USA/UK anomaly actually lives).

WHY THIS IS A COMPARISON TABLE, NOT A CORRELATION TEST: with roughly 30-40
countries (and fewer once missing data is accounted for), a correlation
coefficient is not reliable - small samples produce noisy, unstable r
values that can look meaningful by chance. The honest approach for a
sample this size is a direct, transparent comparison of the actual
countries in question, not a statistic dressed up to look more rigorous
than the sample size can support.
"""

import pandas as pd

YEAR_FOR_SNAPSHOT = 2013  # last year FAO consumption data covers


def build_followup_snapshot(country_typology: pd.DataFrame,
                             fao_consumption_long: pd.DataFrame,
                             inactivity_long: pd.DataFrame) -> pd.DataFrame:
    """
    Builds a small snapshot table for ONLY the Wealthy Decouplers cluster:
    Country, Obesity_End (already known), Sugar_Sweeteners_kg_per_capita,
    Alcohol_kg_per_capita (FAO, fixed 2013 snapshot - the last year FAO's
    file covers), Physical_Inactivity_pct (WHO, each country's own most
    recent available year - NOT a fixed year across countries).

    IMPORTANT - NO VALUE HERE IS CALCULATED, ESTIMATED, OR CARRIED BACK.
    Every number is a real, directly observed value for the year shown.
    The actual year used is exposed explicitly in Inactivity_Year for this
    reason: FAO's snapshot is a single fixed year (2013) for every country,
    but the inactivity snapshot takes each country's own latest available
    year, which is NOT necessarily the same year for every country (e.g.
    one country's latest reported year might be 2019, another's 2022) -
    exposing the actual year lets this be checked rather than assumed.
    """
    wealthy = country_typology[country_typology["Cluster_Name"] == "Wealthy Decouplers"].copy()

    fao_snapshot = fao_consumption_long[fao_consumption_long["Year"] == YEAR_FOR_SNAPSHOT]
    fao_snapshot = fao_snapshot.drop(columns="Year")

    inactivity_snapshot = (
        inactivity_long.sort_values("Year")
        .groupby("Country_Code", as_index=False)
        .last()
        .rename(columns={"Year": "Inactivity_Year"})
    )

    result = wealthy.merge(fao_snapshot, on="Country_Code", how="left")
    result = result.merge(inactivity_snapshot, on="Country_Code", how="left")
    result["Sugar_Alcohol_Year"] = YEAR_FOR_SNAPSHOT

    return result[[
        "Country", "Country_Code", "Obesity_End",
        "Sugar_Sweeteners_kg_per_capita", "Alcohol_kg_per_capita", "Sugar_Alcohol_Year",
        "Physical_Inactivity_pct", "Inactivity_Year",
    ]].sort_values("Obesity_End")


def highlight_anomaly_countries(snapshot: pd.DataFrame) -> pd.DataFrame:
    """
    Pulls out just the original anomaly countries (Japan, South Korea vs.
    USA, UK) for the most direct possible side-by-side comparison.
    """
    anomaly_countries = ["Japan", "South Korea", "Republic of Korea",
                          "United States of America", "United Kingdom"]
    return snapshot[snapshot["Country"].isin(anomaly_countries)]
