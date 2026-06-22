"""
hypothesis_features.py
------------------------
Builds the single cross-sectional (one row per country) table that both the
Equality Hypothesis and Access Hypothesis tests run on.

WHY CROSS-SECTIONAL, NOT THE FULL YEAR-BY-YEAR PANEL:
Gini_Index is a snapshot by design (see load_external_data.py - it's too
sparsely reported to treat as a time series). To compare it fairly against
Obesity and BP, those also need to be reduced to one representative number
per country - using the SAME "recent average" logic already established in
typology_features.py (mean of the last 5 available years, 2010-2014), so
every variable in this table reflects "where the country actually is now",
not a single noisy year.

WHAT THIS BUILDS:
One row per country with:
  - Obesity_End, BP_End      (reused directly from country_typology.csv -
                               already computed as the 2010-2014 average)
  - UHC_End                  (computed here fresh: mean UHC_Index over
                               2010-2014, same logic, for consistency)
  - Gini_Index, Gini_Year    (the existing snapshot, unchanged)
  - Income_Group             (most recent available classification)
  - Continent, Cluster_Name  (carried over for plotting/colour-coding later)

No row is dropped for missing Gini/UHC/Income_Group at this stage - those
stay as NaN and are simply excluded automatically when each specific
correlation is computed (different tests will have different valid sample
sizes, and that sample size is reported explicitly, not hidden).
"""

import pandas as pd

RECENT_YEAR_START = 2010
RECENT_YEAR_END = 2014

INCOME_GROUP_ORDER = {
    "Low income": 1,
    "Lower middle income": 2,
    "Upper middle income": 3,
    "High income": 4,
}


def _compute_uhc_end(combined_panel: pd.DataFrame) -> pd.Series:
    """
    Mean UHC_Index over 2010-2014 per country - the same "recent average"
    treatment already used for Obesity_End/BP_End in typology_features.py,
    applied here to UHC for consistency.
    """
    window = combined_panel[
        (combined_panel["Year"] >= RECENT_YEAR_START) & (combined_panel["Year"] <= RECENT_YEAR_END)
    ]
    return window.groupby("Country")["UHC_Index"].mean().rename("UHC_End")


def build_hypothesis_snapshot(country_typology: pd.DataFrame, combined_panel: pd.DataFrame) -> pd.DataFrame:
    """
    Merges country_typology.csv (Obesity_End, BP_End, Cluster_Name, etc.)
    with a freshly computed UHC_End, plus Gini_Index/Income_Group pulled
    from the combined panel.

    Returns one row per country (200 rows), ready for the two hypothesis
    tests. Income_Group is also converted to an ordinal numeric column
    (Income_Group_Ordinal: Low=1 ... High=4) since the Equality Hypothesis
    regression needs a numeric predictor, not a text category.
    """
    uhc_end = _compute_uhc_end(combined_panel)

    gini_and_income = (
        combined_panel.sort_values("Year")
        .groupby("Country")[["Gini_Index", "Gini_Year", "Income_Group"]]
        .last()
    )

    # country_typology already carries an Income_Group column (added during
    # the typology stage for metadata purposes) - drop it here so the join
    # below doesn't collide; gini_and_income's version is the one used going
    # forward (same underlying source, just re-fetched alongside Gini).
    typology_without_income = country_typology.drop(columns=["Income_Group"], errors="ignore")

    snapshot = typology_without_income.set_index("Country").join(uhc_end).join(gini_and_income)
    snapshot["Income_Group_Ordinal"] = snapshot["Income_Group"].map(INCOME_GROUP_ORDER)

    return snapshot.reset_index()
