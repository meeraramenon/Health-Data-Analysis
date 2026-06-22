"""
trend_extrapolation.py
-------------------------
A deliberately simple linear trend extrapolation, used to give the
convergence/divergence chart a forward-looking element.

THIS IS NOT A FORECASTING MODEL. It fits a straight line to the existing
1980-2014 series and continues that line forward for a stated number of
years. There is no validation, no confidence interval, no claim that this
is what will actually happen - it answers a narrower, honest question:
"if the trend already observed simply continued at the same rate, where
would it be by year X?" This distinction must be stated explicitly
wherever this is used in the report.
"""

import pandas as pd
from scipy.stats import linregress


def extrapolate_linear_trend(series_df: pd.DataFrame, year_col: str, value_col: str,
                              years_forward: int = 10) -> pd.DataFrame:
    """
    Fits a straight line to (year_col, value_col) over the existing data,
    then extends it years_forward beyond the last available year.

    Returns a DataFrame with columns: Year, <value_col>, Is_Extrapolated
    covering BOTH the original observed years (Is_Extrapolated=False) and
    the projected future years (Is_Extrapolated=True) - so the two are kept
    in one continuous series for plotting, but always distinguishable.
    """
    valid = series_df[[year_col, value_col]].dropna()
    fit = linregress(valid[year_col], valid[value_col])

    last_year = int(valid[year_col].max())
    future_years = list(range(last_year + 1, last_year + 1 + years_forward))

    observed = valid.copy()
    observed["Is_Extrapolated"] = False

    projected = pd.DataFrame({
        year_col: future_years,
        value_col: [fit.intercept + fit.slope * y for y in future_years],
    })
    projected["Is_Extrapolated"] = True

    combined = pd.concat([observed, projected], ignore_index=True)
    combined = combined.rename(columns={year_col: "Year"})

    return combined, fit
