"""
hypothesis_tests.py
---------------------
Implements the two headline hypothesis tests as actual statistics, not
narration:

EQUALITY HYPOTHESIS: does income EQUALITY (Gini), not income LEVEL, explain
why some wealthy countries stay thin (Japan, South Korea) while others
(USA, UK) don't?
  Method: regress Obesity_End on Income_Group_Ordinal (income LEVEL).
  The residual (actual obesity minus what income level alone predicts) is
  the part of a country's obesity NOT explained by how rich it is.
  If that leftover residual correlates with Gini, income equality is
  explaining something income level alone could not.

ACCESS HYPOTHESIS: does healthcare ACCESS (UHC), not income/spending,
explain why some high-obesity countries escape high BP while others don't?
  Method: regress BP_End on Obesity_End. The residual (actual BP minus what
  obesity alone predicts) is the part of a country's BP NOT explained by
  its obesity level - i.e. is BP higher or lower than its obesity level
  alone would suggest. If that residual correlates with UHC, healthcare
  access is explaining the part obesity alone could not.

Both tests use simple linear regression (scipy.stats.linregress) - one
predictor, one outcome - because the hypotheses are specifically about ONE
relationship at a time (income level OR equality; obesity level OR access),
not a multi-variable model. Sample size is reported for every test, since
Gini/UHC/Income_Group are not available for every country (see README).
"""

import pandas as pd
import numpy as np
from scipy.stats import linregress, pearsonr


def _regression_residual(df: pd.DataFrame, predictor_col: str, outcome_col: str) -> pd.Series:
    """
    Fits outcome ~ predictor by simple linear regression on the rows where
    BOTH columns are present, and returns the residual (actual - predicted)
    re-indexed to match the full input DataFrame (rows missing either value
    get NaN residual, not a guessed one).
    """
    valid = df[[predictor_col, outcome_col]].dropna()

    fit = linregress(valid[predictor_col], valid[outcome_col])
    predicted = fit.intercept + fit.slope * valid[predictor_col]
    residual = valid[outcome_col] - predicted

    return residual.reindex(df.index), fit


def run_equality_hypothesis(snapshot: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Step 1: regress Obesity_End on Income_Group_Ordinal -> Obesity_Residual
    Step 2: correlate Obesity_Residual against Gini_Index (across all 200 countries)
    Step 3: a robustness check - the same correlation but restricted to the
             "Wealthy Decouplers" cluster only, since the original motivating
             anomaly (Japan/South Korea staying thin vs USA/UK not, despite
             similar wealth) is specifically a WITHIN-wealthy-world comparison,
             not a global one. A global test can dilute a real local pattern.

    Returns:
      - the snapshot table with two new columns added: Obesity_Residual,
        Obesity_Predicted_By_Income
      - a dict of summary statistics for all three steps
    """
    result = snapshot.copy()

    residual, income_fit = _regression_residual(result, "Income_Group_Ordinal", "Obesity_End")
    result["Obesity_Residual"] = residual
    result["Obesity_Predicted_By_Income"] = result["Obesity_End"] - result["Obesity_Residual"]

    corr_data = result[["Obesity_Residual", "Gini_Index"]].dropna()
    corr_r, corr_p = pearsonr(corr_data["Obesity_Residual"], corr_data["Gini_Index"])

    summary = {
        "step1_income_to_obesity_regression": {
            "slope": income_fit.slope,
            "intercept": income_fit.intercept,
            "r_squared": income_fit.rvalue ** 2,
            "n": result[["Income_Group_Ordinal", "Obesity_End"]].dropna().shape[0],
        },
        "step2_residual_vs_gini_correlation": {
            "pearson_r": corr_r,
            "p_value": corr_p,
            "n": corr_data.shape[0],
        },
    }

    if "Cluster_Name" in result.columns:
        wealthy_subset = result[result["Cluster_Name"] == "Wealthy Decouplers"]
        subset_data = wealthy_subset[["Obesity_End", "Gini_Index"]].dropna()
        if len(subset_data) >= 3:
            subset_r, subset_p = pearsonr(subset_data["Obesity_End"], subset_data["Gini_Index"])
            summary["step3_within_wealthy_cluster_robustness_check"] = {
                "pearson_r": subset_r,
                "p_value": subset_p,
                "n": subset_data.shape[0],
                "note": "Direct Obesity_End vs Gini_Index within the Wealthy Decouplers "
                        "cluster only - tests the original Japan/Korea vs USA/UK anomaly "
                        "directly, rather than diluted across all 200 countries.",
            }

    return result, summary


def run_access_hypothesis(snapshot: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Step 1: regress BP_End on Obesity_End -> BP_Residual
    Step 2: correlate BP_Residual against UHC_End

    Returns the same structure as run_equality_hypothesis, for BP/UHC instead
    of Obesity/Gini.
    """
    result = snapshot.copy()

    residual, obesity_fit = _regression_residual(result, "Obesity_End", "BP_End")
    result["BP_Residual"] = residual
    result["BP_Predicted_By_Obesity"] = result["BP_End"] - result["BP_Residual"]

    corr_data = result[["BP_Residual", "UHC_End"]].dropna()
    corr_r, corr_p = pearsonr(corr_data["BP_Residual"], corr_data["UHC_End"])

    summary = {
        "step1_obesity_to_bp_regression": {
            "slope": obesity_fit.slope,
            "intercept": obesity_fit.intercept,
            "r_squared": obesity_fit.rvalue ** 2,
            "n": result[["Obesity_End", "BP_End"]].dropna().shape[0],
        },
        "step2_residual_vs_uhc_correlation": {
            "pearson_r": corr_r,
            "p_value": corr_p,
            "n": corr_data.shape[0],
        },
    }
    return result, summary
