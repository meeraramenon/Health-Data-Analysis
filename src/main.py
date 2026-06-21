"""
main.py
--------
Runs the full data preparation pipeline end-to-end:

  1. Load + clean the 3 original health sheets -> one long panel
  2. Attach verified ISO3 country codes
  3. Attach Continent, WHO Region, UHC Index, Gini Index, Income Group
  4. Build the combined (sex-averaged) country/year panel
  5. Build the sex-gap table
  6. Add the Metabolic Risk Index
  7. Save every output to data/final/, and print a final summary so the
     results can be sanity-checked at a glance.

Run with:  python3 src/main.py   (from the project/ folder)
"""

import sys
sys.path.insert(0, "src")

from merge_all_data import build_merged_master
from feature_engineering import (
    build_combined_sex_panel,
    build_sex_gap_table,
    add_metabolic_risk_index,
)

FINAL_DIR = "data/final"


def main():
    print("Step 1-3: Building merged master panel (health data + all external sources)...")
    master_long = build_merged_master()
    master_long.to_csv(f"{FINAL_DIR}/master_panel_by_sex.csv", index=False)
    print(f"  -> Saved: {FINAL_DIR}/master_panel_by_sex.csv  (shape: {master_long.shape})")

    print("\nStep 4: Building combined (sex-averaged) country/year panel...")
    combined = build_combined_sex_panel(master_long)
    print(f"  -> shape: {combined.shape}")

    print("\nStep 5: Building sex-gap table...")
    sex_gap = build_sex_gap_table(master_long)
    sex_gap.to_csv(f"{FINAL_DIR}/sex_gap_table.csv", index=False)
    print(f"  -> Saved: {FINAL_DIR}/sex_gap_table.csv  (shape: {sex_gap.shape})")

    print("\nStep 6: Adding Metabolic Risk Index...")
    combined_with_index = add_metabolic_risk_index(combined)
    combined_with_index.to_csv(f"{FINAL_DIR}/combined_panel_with_risk_index.csv", index=False)
    print(f"  -> Saved: {FINAL_DIR}/combined_panel_with_risk_index.csv  (shape: {combined_with_index.shape})")

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE - SUMMARY")
    print("=" * 70)
    print(f"Countries: {master_long['Country'].nunique()}")
    print(f"Year range: {master_long['Year'].min()}-{master_long['Year'].max()}")
    print(f"\nNull counts in final combined+risk-index table:")
    print(combined_with_index.isnull().sum())
    print(f"\nSample rows:")
    print(combined_with_index.sample(5, random_state=42).to_string())

    return master_long, sex_gap, combined_with_index


if __name__ == "__main__":
    main()
