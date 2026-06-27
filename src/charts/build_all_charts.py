"""
build_all_charts.py
----------------------
Builds and saves EVERY chart in this project, in one run. This is the
literal, runnable version of what the README describes - run this file
directly and every HTML + PNG in visuals/ gets (re)generated.

Run with: python3 src/charts/build_all_charts.py   (from the project/ folder)

Each section loads only the data that specific chart needs, builds it, and
saves both an interactive .html and a static .png (for the written report)
into that chart's thread-named subfolder under visuals/.
"""

import os
import sys
# Absolute paths regardless of current working directory - see the same
# fix applied in every chart_XX.py module for why this matters. This file
# lives in src/charts/, so src/ is one level up and project/ is two levels up.
_CHARTS_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.dirname(_CHARTS_DIR)
_PROJECT_DIR = os.path.dirname(_SRC_DIR)
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)
if _PROJECT_DIR not in sys.path:
    sys.path.insert(0, _PROJECT_DIR)

# Also switch the working directory to project/ - every pd.read_csv() call
# below uses a path like "data/final/..." which assumes that as the cwd.
os.chdir(_PROJECT_DIR)

import pandas as pd
from charts.chart_theme import register_theme

register_theme()  # apply the shared design system once, before building anything

VISUALS_DIR = "visuals"

_OUTPUT_SUBDIRS = [
    "thread1_typology",
    "thread2_convergence",
    "thread3_equality_hypothesis",
    "thread4_access_hypothesis",
    "supplementary_overview",
    "thread5_gender",
    "interactive_dashboard",
]
for _subdir in _OUTPUT_SUBDIRS:
    os.makedirs(f"{VISUALS_DIR}/{_subdir}", exist_ok=True)


def build_chart_01_choropleth():
    from charts.chart_01_choropleth import build_choropleth, build_choropleth_static
    combined = pd.read_csv("data/final/combined_panel_with_risk_index.csv")

    chart = build_choropleth(combined)
    chart.save(f"{VISUALS_DIR}/thread1_typology/01_choropleth.html")

    static_chart = build_choropleth_static(combined, year=2014, metric_label="Metabolic Risk Index")
    static_chart.save(f"{VISUALS_DIR}/thread1_typology/01_choropleth_static_2014.png", ppi=150)
    print("Chart 1 (choropleth) saved.")


def build_chart_02_cluster_scatter():
    from charts.chart_02_cluster_scatter import build_cluster_scatter
    from typology_features import build_trajectory_feature_table
    from typology_clustering import scale_features

    combined = pd.read_csv("data/final/combined_panel_with_risk_index.csv")
    country_typology = pd.read_csv("data/analysis/country_typology.csv")

    features, _ = build_trajectory_feature_table(combined)
    scaled, _ = scale_features(features)

    chart = build_cluster_scatter(country_typology, scaled)
    chart.save(f"{VISUALS_DIR}/thread1_typology/02_cluster_scatter.html")
    chart.save(f"{VISUALS_DIR}/thread1_typology/02_cluster_scatter.png", ppi=150)
    print("Chart 2 (cluster scatter) saved.")


def build_chart_03_trajectory_small_multiples():
    from charts.chart_03_trajectory_small_multiples import build_trajectory_small_multiples

    combined = pd.read_csv("data/final/combined_panel_with_risk_index.csv")
    country_typology = pd.read_csv("data/analysis/country_typology.csv")

    chart = build_trajectory_small_multiples(combined, country_typology)
    chart.save(f"{VISUALS_DIR}/thread1_typology/03_trajectory_small_multiples.html")
    chart.save(f"{VISUALS_DIR}/thread1_typology/03_trajectory_small_multiples.png", ppi=150)
    print("Chart 3 (trajectory small multiples) saved.")


def build_chart_04_convergence_trend():
    from charts.chart_04_convergence_trend import build_convergence_trend_chart

    cv_by_year = pd.read_csv("data/analysis/convergence_cv_by_year.csv")
    trend_extrapolation = pd.read_csv("data/analysis/convergence_trend_extrapolation.csv")

    chart = build_convergence_trend_chart(cv_by_year, trend_extrapolation)
    chart.save(f"{VISUALS_DIR}/thread2_convergence/04_convergence_trend.html")
    chart.save(f"{VISUALS_DIR}/thread2_convergence/04_convergence_trend.png", ppi=150)
    print("Chart 4 (convergence trend) saved.")


def build_chart_05_equality_scatter():
    from charts.chart_05_equality_scatter import build_equality_scatter
    equality_results = pd.read_csv("data/analysis/equality_hypothesis_results.csv")

    chart = build_equality_scatter(equality_results)
    chart.save(f"{VISUALS_DIR}/thread3_equality_hypothesis/05_equality_scatter.html")
    chart.save(f"{VISUALS_DIR}/thread3_equality_hypothesis/05_equality_scatter.png", ppi=150)
    print("Chart 5 (equality scatter) saved.")


def build_chart_06_access_scatter():
    from charts.chart_06_access_scatter import build_access_scatter
    access_results = pd.read_csv("data/analysis/access_hypothesis_results.csv")

    chart = build_access_scatter(access_results)
    chart.save(f"{VISUALS_DIR}/thread4_access_hypothesis/06_access_scatter.html")
    chart.save(f"{VISUALS_DIR}/thread4_access_hypothesis/06_access_scatter.png", ppi=150)
    print("Chart 6 (access scatter) saved.")


def build_chart_07_risk_leaderboard():
    from charts.chart_07_risk_leaderboard import build_risk_leaderboard
    combined = pd.read_csv("data/final/combined_panel_with_risk_index.csv")

    chart = build_risk_leaderboard(combined, year=2014, n=10)
    chart.save(f"{VISUALS_DIR}/supplementary_overview/07_risk_leaderboard.html")
    chart.save(f"{VISUALS_DIR}/supplementary_overview/07_risk_leaderboard.png", ppi=150)
    print("Chart 7 (risk leaderboard, supplementary) saved.")


def build_chart_08_equality_followup():
    from charts.chart_08_equality_followup import build_equality_followup_chart
    followup = pd.read_csv("data/analysis/equality_followup_wealthy_cluster.csv")

    chart = build_equality_followup_chart(followup)
    chart.save(f"{VISUALS_DIR}/thread3_equality_hypothesis/08_equality_followup.html")
    chart.save(f"{VISUALS_DIR}/thread3_equality_hypothesis/08_equality_followup.png", ppi=150)
    print("Chart 8 (equality follow-up, self-correction story) saved.")


def build_chart_09_gender_gap():
    from charts.chart_09_gender_gap import build_gender_gap_chart
    gender_gap = pd.read_csv("data/analysis/gender_gap_by_year.csv")

    chart = build_gender_gap_chart(gender_gap)
    chart.save(f"{VISUALS_DIR}/thread5_gender/09_gender_gap.html")
    chart.save(f"{VISUALS_DIR}/thread5_gender/09_gender_gap.png", ppi=150)
    print("Chart 9 (gender gap) saved.")


def build_chart_10_dashboard():
    from charts.chart_10_dashboard import build_dashboard
    country_typology = pd.read_csv("data/analysis/country_typology.csv")
    combined = pd.read_csv("data/final/combined_panel_with_risk_index.csv")

    chart = build_dashboard(country_typology, combined)
    chart.save(f"{VISUALS_DIR}/interactive_dashboard/10_dashboard.html")
    chart.save(f"{VISUALS_DIR}/interactive_dashboard/10_dashboard.png", ppi=150)
    print("Chart 10 (interactive dashboard) saved.")


def build_chart_11_convergence_by_income():
    from charts.chart_11_convergence_by_income import build_convergence_by_income_chart
    by_income = pd.read_csv("data/analysis/convergence_by_income_group.csv")

    chart = build_convergence_by_income_chart(by_income)
    chart.save(f"{VISUALS_DIR}/supplementary_overview/11_convergence_by_income.html")
    chart.save(f"{VISUALS_DIR}/supplementary_overview/11_convergence_by_income.png", ppi=150)
    print("Chart 11 (convergence by income group, supplementary) saved.")


def build_chart_12_gender_gap_by_cluster():
    from charts.chart_12_gender_gap_by_cluster import build_gender_gap_by_cluster_chart
    by_cluster = pd.read_csv("data/analysis/gender_gap_by_cluster.csv")

    chart = build_gender_gap_by_cluster_chart(by_cluster)
    chart.save(f"{VISUALS_DIR}/supplementary_overview/12_gender_gap_by_cluster.html")
    chart.save(f"{VISUALS_DIR}/supplementary_overview/12_gender_gap_by_cluster.png", ppi=150)
    print("Chart 12 (gender gap by cluster, supplementary) saved.")


def build_chart_13_temporal_heatmap():
    from charts.chart_13_temporal_heatmap import build_temporal_heatmap
    combined = pd.read_csv("data/final/combined_panel_with_risk_index.csv")

    chart = build_temporal_heatmap(combined)
    chart.save(f"{VISUALS_DIR}/supplementary_overview/13_temporal_heatmap.html")
    chart.save(f"{VISUALS_DIR}/supplementary_overview/13_temporal_heatmap.png", ppi=150)
    print("Chart 13 (temporal heatmap) saved.")


if __name__ == "__main__":
    build_chart_01_choropleth()
    build_chart_02_cluster_scatter()
    build_chart_03_trajectory_small_multiples()
    build_chart_04_convergence_trend()
    build_chart_05_equality_scatter()
    build_chart_06_access_scatter()
    build_chart_07_risk_leaderboard()
    build_chart_08_equality_followup()
    build_chart_09_gender_gap()
    build_chart_10_dashboard()
    build_chart_11_convergence_by_income()
    build_chart_12_gender_gap_by_cluster()
    build_chart_13_temporal_heatmap()
    print("\nAll available charts rebuilt.")
