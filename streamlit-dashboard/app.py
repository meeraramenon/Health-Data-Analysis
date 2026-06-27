"""
app.py — Global Health Trajectory Analysis Dashboard
Streamlit application bringing together all 5 analytical threads, 12 Altair
charts, hypotheses, findings, and data sources from the health data project.

Run from the project root:
    streamlit run app.py
"""

import os
import sys

# ── Path setup: must happen before any local imports ──────────────────────────
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_APP_DIR)
_SRC = os.path.join(_PROJECT_ROOT, "src")

if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

os.chdir(_PROJECT_ROOT)

import pandas as pd
import altair as alt
import streamlit as st
import streamlit.components.v1 as components

alt.data_transformers.disable_max_rows()

# ── Local chart imports ───────────────────────────────────────────────────────
from charts.chart_theme import register_theme, INDIGO, CORAL
from charts.chart_01_choropleth import build_choropleth
from charts.chart_02_cluster_scatter import build_cluster_scatter
from charts.chart_03_trajectory_small_multiples import build_trajectory_small_multiples
from charts.chart_04_convergence_trend import build_convergence_trend_chart
from charts.chart_05_equality_scatter import build_equality_scatter
from charts.chart_06_access_scatter import build_access_scatter
from charts.chart_07_risk_leaderboard import build_risk_leaderboard
from charts.chart_08_equality_followup import build_equality_followup_chart
from charts.chart_09_gender_gap import build_gender_gap_chart
from charts.chart_10_dashboard import build_dashboard
from charts.chart_11_convergence_by_income import build_convergence_by_income_chart
from charts.chart_12_gender_gap_by_cluster import build_gender_gap_by_cluster_chart
from charts.chart_13_temporal_heatmap import build_temporal_heatmap
from typology_features import build_trajectory_feature_table
from typology_clustering import scale_features

register_theme()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Global Health Trajectory Analysis",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Shared styles ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .verdict-confirmed {
        background: #d4edda; color: #155724; padding: 4px 12px;
        border-radius: 12px; font-weight: 700; font-size: 0.85rem;
        display: inline-block;
    }
    .verdict-not-confirmed {
        background: #f8d7da; color: #721c24; padding: 4px 12px;
        border-radius: 12px; font-weight: 700; font-size: 0.85rem;
        display: inline-block;
    }
    .verdict-mixed {
        background: #fff3cd; color: #856404; padding: 4px 12px;
        border-radius: 12px; font-weight: 700; font-size: 0.85rem;
        display: inline-block;
    }
    .thread-header {
        background: linear-gradient(90deg, #1B3A4B 0%, #2d5a73 100%);
        color: white; padding: 1rem 1.5rem; border-radius: 8px;
        margin-bottom: 1rem;
    }
    .finding-box {
        background: #FAF9F6; border-left: 4px solid #E8623D;
        padding: 0.8rem 1.2rem; margin: 1rem 0; border-radius: 0 6px 6px 0;
    }
    .method-box {
        background: #eef2f5; border-left: 4px solid #1B3A4B;
        padding: 0.8rem 1.2rem; margin: 1rem 0; border-radius: 0 6px 6px 0;
    }
    .open-question {
        background: #fff8e1; border: 1px solid #ffc107;
        padding: 0.8rem 1.2rem; margin: 1rem 0; border-radius: 6px;
    }
    div[data-testid="metric-container"] {
        background: white; border-radius: 8px; padding: 1rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }
    .section-title {
        font-size: 1.6rem; font-weight: 700; color: #1B3A4B;
        border-bottom: 2px solid #E8623D; padding-bottom: 0.4rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# ── Cached data loaders ───────────────────────────────────────────────────────

@st.cache_data
def load_combined():
    return pd.read_csv("data/final/combined_panel_with_risk_index.csv")

@st.cache_data
def load_master_panel():
    return pd.read_csv("data/final/master_panel_by_sex.csv")

@st.cache_data
def load_sex_gap():
    return pd.read_csv("data/final/sex_gap_table.csv")

@st.cache_data
def load_country_typology():
    return pd.read_csv("data/analysis/country_typology.csv")

@st.cache_data
def load_cluster_profiles():
    return pd.read_csv("data/analysis/cluster_profiles.csv")

@st.cache_data
def load_k_diagnostics():
    return pd.read_csv("data/analysis/k_selection_diagnostics.csv")

@st.cache_data
def load_equality_results():
    return pd.read_csv("data/analysis/equality_hypothesis_results.csv")

@st.cache_data
def load_access_results():
    return pd.read_csv("data/analysis/access_hypothesis_results.csv")

@st.cache_data
def load_cv_by_year():
    return pd.read_csv("data/analysis/convergence_cv_by_year.csv")

@st.cache_data
def load_trend_extrapolation():
    return pd.read_csv("data/analysis/convergence_trend_extrapolation.csv")

@st.cache_data
def load_convergence_by_income():
    return pd.read_csv("data/analysis/convergence_by_income_group.csv")

@st.cache_data
def load_gender_gap():
    return pd.read_csv("data/analysis/gender_gap_by_year.csv")

@st.cache_data
def load_gender_gap_by_cluster():
    return pd.read_csv("data/analysis/gender_gap_by_cluster.csv")

@st.cache_data
def load_followup():
    return pd.read_csv("data/analysis/equality_followup_wealthy_cluster.csv")

@st.cache_data
def load_robustness_text():
    with open("data/analysis/cluster_robustness_check.txt") as f:
        return f.read()

@st.cache_resource
def get_scaled_features():
    combined = load_combined()
    typology = load_country_typology()
    features, _ = build_trajectory_feature_table(combined)
    scaled, _ = scale_features(features)
    return scaled


# ── Helper components ─────────────────────────────────────────────────────────

def verdict_badge(kind: str) -> str:
    if kind == "confirmed":
        return '<span class="verdict-confirmed">✓ CONFIRMED</span>'
    elif kind == "not_confirmed":
        return '<span class="verdict-not-confirmed">✗ NOT CONFIRMED</span>'
    else:
        return '<span class="verdict-mixed">~ MIXED / PARTIAL</span>'


def research_question(text: str):
    st.markdown(f"""
    <div style="background:#eef2f5; border-left:4px solid #1B3A4B;
                padding:0.8rem 1.2rem; border-radius:0 6px 6px 0; margin:0.5rem 0;">
        <strong>Research question:</strong> {text}
    </div>""", unsafe_allow_html=True)


def finding_callout(text: str):
    st.markdown(f"""
    <div class="finding-box">
        <strong>Key finding:</strong> {text}
    </div>""", unsafe_allow_html=True)


def method_callout(text: str):
    st.markdown(f"""
    <div class="method-box">
        <strong>Method:</strong> {text}
    </div>""", unsafe_allow_html=True)


def open_question(text: str):
    st.markdown(f"""
    <div class="open-question">
        <strong>Open question:</strong> {text}
    </div>""", unsafe_allow_html=True)


# ── Sidebar navigation ────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🌍 Health Trajectories")
    st.markdown("*200 countries · 35 years · 3 diseases*")
    st.divider()
    page = st.radio(
        "Navigate",
        options=[
            "🏠 Overview",
            "🗺️ Thread 1 · Country Typology",
            "📉 Thread 2 · Global Convergence",
            "⚖️ Thread 3 · Equality Hypothesis",
            "🏥 Thread 4 · Access Hypothesis",
            "👥 Thread 5 · Gender Gaps",
            "🔍 Supplementary Exploration",
            "🎛️ Interactive Dashboard",
            "📋 Data & Methodology",
        ],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Data: 1975–2016 (core analysis window: 1980–2014)")
    st.caption("Branch: DataPreprocess")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Overview":
    st.markdown('<div class="section-title">Global Health Trajectory Analysis</div>',
                unsafe_allow_html=True)

    st.markdown("""
    This dashboard presents a complete, end-to-end analysis of blood pressure, obesity, and
    diabetes prevalence across **200 countries** from **1975 to 2016** (core analysis window: 1980–2014).
    The project moves beyond describing global health patterns to testing specific causal hypotheses:
    does income *equality* explain who stays thin? Does healthcare *access* explain who escapes high
    blood pressure? Are the gaps between countries — and between sexes — closing or widening?
    Each thread presents an honest answer, including two follow-up investigations where the first
    answer came back negative.
    """)

    st.divider()

    # KPI metric cards
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Countries", "200", help="ISO3-coded, no fuzzy name matching")
    c2.metric("Years", "1975–2016", help="Core analysis window: 1980–2014")
    c3.metric("Diseases", "3", help="Blood Pressure · Obesity · Diabetes")
    c4.metric("Typology clusters", "5", help="k-means on 12 trajectory features")
    c5.metric("Altair charts", "13", help="9 core + 1 self-correction + 3 supplementary")

    st.divider()
    st.subheader("Findings at a Glance")

    rows = [
        {
            "Thread": "1 · Typology",
            "Research Question": "Do countries follow one global health pattern, or do distinct groups exist?",
            "Verdict": "confirmed",
            "Verdict Label": "5 CLUSTERS FOUND",
            "Key Statistic": "k=5 silhouette ≈ 0.26; Pacific Outliers obesity 30%→51%",
            "Detail": "k-means on 12 features (start/end/slope/curvature × 3 diseases). "
                      "k=2 split 'everyone' from 27 extreme outliers; k=5 reveals genuinely "
                      "distinct journeys. Portugal lands in 'Lean Hypertension' despite being "
                      "high-income — trajectory shape beats wealth classification.",
        },
        {
            "Thread": "2 · Convergence",
            "Research Question": "Is the gap between the healthiest and sickest countries widening or narrowing?",
            "Verdict": "confirmed",
            "Verdict Label": "CONVERGING (obesity R²=0.999)",
            "Key Statistic": "Obesity CV: 0.918 (1980) → 0.603 (2014)",
            "Detail": "Coefficient of Variation computed per disease per year. Obesity converging "
                      "on an almost mechanical trend (R²=0.999). BP also converging but noisier "
                      "(R²=0.268). Diabetes essentially flat (R²=0.075). "
                      "Hidden finding: Lower-middle income countries show no convergence at all.",
        },
        {
            "Thread": "3 · Equality",
            "Research Question": "Does income equality (Gini), not income level, explain why some wealthy countries stay thin?",
            "Verdict": "not_confirmed",
            "Verdict Label": "NOT CONFIRMED",
            "Key Statistic": "r = 0.019, p = 0.81 globally; r = 0.143, p = 0.44 within wealthy cluster",
            "Detail": "Residualised obesity (after removing income level) shows no significant "
                      "correlation with Gini. Japan (Gini 32.3, obesity 3.8%) and UK (Gini 32.4, "
                      "obesity 26.3%) have nearly identical inequality yet wildly different outcomes. "
                      "Follow-up: sugar, alcohol, and physical inactivity also tested and ruled out.",
        },
        {
            "Thread": "4 · Access",
            "Research Question": "Does healthcare access (UHC), not obesity alone, explain who escapes high blood pressure?",
            "Verdict": "confirmed",
            "Verdict Label": "CONFIRMED",
            "Key Statistic": "r = −0.479, p < 0.0001, n = 192 countries",
            "Detail": "Residualised BP (after removing obesity's effect) correlates strongly and "
                      "negatively with UHC Service Coverage Index. Countries with stronger healthcare "
                      "access have blood pressure meaningfully lower than their obesity alone would "
                      "predict. This is the strongest statistical result in the entire analysis.",
        },
        {
            "Thread": "5 · Gender",
            "Research Question": "Is the male/female health gap widening or narrowing, and does it track the between-country story?",
            "Verdict": "mixed",
            "Verdict Label": "MIXED — 3 diseases, 3 stories",
            "Key Statistic": "Obesity gap r = −0.969 with between-country CV (p < 0.0001)",
            "Detail": "BP gap widening (−3.74 → −4.16 pp, men higher). Obesity gap widening "
                      "(+5.69 → +7.25 pp, women higher) AND moving in lockstep with between-country "
                      "convergence (r=−0.969). Diabetes gap narrowing AND the sign flips — by 2014 "
                      "men are slightly more affected than women, reversing the 1980 picture.",
        },
    ]

    for r in rows:
        with st.expander(
            f"**Thread {r['Thread']}** — {r['Research Question']}", expanded=False
        ):
            col_v, col_s = st.columns([1, 3])
            with col_v:
                badge_html = verdict_badge(r["Verdict"])
                st.markdown(badge_html, unsafe_allow_html=True)
                st.markdown(f"**{r['Verdict Label']}**")
            with col_s:
                st.info(r["Key Statistic"])
            st.markdown(r["Detail"])

    st.divider()
    st.subheader("The Five Typology Clusters")
    cluster_summary = pd.DataFrame([
        {"Cluster": "Pacific Extreme Outliers", "n": 13,
         "Defining pattern": "Obesity 30%→51%, the syndemic-trap group",
         "Income mix": "Mixed (Pacific islands)"},
        {"Cluster": "Lean Hypertension / Low-Obesity Rising-BP", "n": 64,
         "Defining pattern": "Obesity near 2–8%; the only cluster where BP is still rising",
         "Income mix": "Mostly low / lower-middle"},
        {"Cluster": "Wealthy Decouplers", "n": 41,
         "Defining pattern": "Sharpest BP decline (−0.41/yr) despite rising obesity — Japan, Korea, US, UK all here",
         "Income mix": "High income"},
        {"Cluster": "High-Starting-BP Recovery", "n": 39,
         "Defining pattern": "Started highest on BP (37%), fell hard — Eastern Europe + Gulf states",
         "Income mix": "Upper-middle to high"},
        {"Cluster": "Moderate Transition", "n": 43,
         "Defining pattern": "Unremarkable middle ground; all three metrics rising moderately",
         "Income mix": "Mixed"},
    ])
    st.dataframe(cluster_summary, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: THREAD 1 — COUNTRY TYPOLOGY
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🗺️ Thread 1 · Country Typology":
    st.markdown('<div class="section-title">Thread 1 · Country Typology</div>',
                unsafe_allow_html=True)
    st.markdown(f"{verdict_badge('confirmed')} **Five distinct trajectory types identified**",
                unsafe_allow_html=True)

    research_question(
        "Do all countries follow one global health pattern, or do genuinely distinct groups exist "
        "in how BP, obesity, and diabetes have moved over 35 years?"
    )
    method_callout(
        "Each country's 1980–2014 trajectory converted into 12 numeric features: Start level, "
        "End level, Slope, and Curvature for each of the 3 diseases. k-means clustering on these "
        "12 features, with k selected by silhouette score (k=2 maximised the score at 0.47 but "
        "only split 27 extreme outliers from everyone else; k=5 was chosen for its five "
        "genuinely distinct and interpretable groups)."
    )

    finding_callout(
        "Five clearly distinct health journeys emerge — not one global story. The Pacific cluster "
        "is a syndemic trap (obesity 30%→51%). The Lean Hypertension group is the only one still "
        "seeing rising BP. The Wealthy Decouplers show the steepest BP decline despite rising obesity. "
        "Portugal lands in 'Lean Hypertension' despite being high-income — trajectory shape beats "
        "wealth classification."
    )

    tabs = st.tabs([
        "🌡️ Temporal Heatmap",
        "🗺️ Choropleth Map",
        "🔵 Cluster Scatter (PCA)",
        "📈 Cluster Trajectories",
        "📊 Cluster Profiles",
        "📐 K Selection",
    ])

    with tabs[0]:
        st.markdown(
            "**Temporal heatmap** — each row is a continent, time runs left to right, and colour "
            "deepens as average disease prevalence rises. Use the dropdown to switch between "
            "Metabolic Risk Index, Blood Pressure, Obesity, and Diabetes."
        )
        st.caption(
            "This is the 'global warming of disease' orientation view: the full 1980–2014 story "
            "for every continent in a single glance, before any clustering or modelling. A heatmap "
            "is used instead of a line chart because the eye picks up 'deepening colour over time' "
            "instantly without needing to trace individual lines."
        )
        combined = load_combined()
        chart = build_temporal_heatmap(combined)
        st.altair_chart(chart, use_container_width=True)

    with tabs[1]:
        st.markdown("**Interactive world map** — drag the year slider and change the metric dropdown.")
        st.caption(
            "32 small island/micro-states are absent from the map geometry but included in every "
            "other chart. The colour scale uses Viridis (perceptually uniform, colourblind-safe)."
        )
        combined = load_combined()
        chart = build_choropleth(combined)
        components.html(chart.to_html(), height=700, scrolling=False)

    with tabs[2]:
        st.markdown(
            "**PCA scatter** — each point is a country, positioned by the 2-component reduction "
            "of the 12-feature trajectory space. Click a cluster name in the legend to isolate it."
        )
        combined = load_combined()
        typology = load_country_typology()
        scaled = get_scaled_features()
        chart = build_cluster_scatter(typology, scaled)
        st.altair_chart(chart, use_container_width=True)
        st.caption(
            "PCA retains approximately 55% of the original 12-feature variation in 2 dimensions — "
            "the clusters are real in 12D; the 2D projection is for visualisation only."
        )

    with tabs[3]:
        st.markdown(
            "**Trajectory small multiples** — the average BP, Obesity, and Diabetes curve per "
            "cluster, 1980–2014. Same y-axis scale across all five panels for fair comparison."
        )
        combined = load_combined()
        typology = load_country_typology()
        chart = build_trajectory_small_multiples(combined, typology)
        st.altair_chart(chart, use_container_width=True)

    with tabs[4]:
        st.markdown("**Cluster profiles** — average trajectory statistics per cluster.")
        profiles = load_cluster_profiles()
        cluster_names = {
            0: "Moderate Transition",
            1: "Pacific Extreme Outliers",
            2: "Wealthy Decouplers",
            3: "High-Starting-BP Recovery",
            4: "Lean Hypertension / Low-Obesity Rising-BP",
        }
        profiles["Cluster_Name"] = profiles["Cluster"].map(cluster_names)
        display_cols = [
            "Cluster_Name", "N_Countries",
            "BP_Start", "BP_End", "BP_Slope",
            "Obesity_Start", "Obesity_End", "Obesity_Slope",
            "Diabetes_Start", "Diabetes_End", "Diabetes_Slope",
        ]
        profiles_display = profiles[display_cols].rename(columns={
            "Cluster_Name": "Cluster", "N_Countries": "n",
            "BP_Start": "BP Start", "BP_End": "BP End", "BP_Slope": "BP Slope/yr",
            "Obesity_Start": "Ob. Start", "Obesity_End": "Ob. End", "Obesity_Slope": "Ob. Slope/yr",
            "Diabetes_Start": "Diab. Start", "Diabetes_End": "Diab. End",
            "Diabetes_Slope": "Diab. Slope/yr",
        })
        st.dataframe(
            profiles_display.style.format({c: "{:.2f}" for c in profiles_display.columns
                                           if profiles_display[c].dtype == "float64"}),
            use_container_width=True, hide_index=True,
        )

        st.markdown("#### Countries per cluster")
        typology = load_country_typology()
        size_chart = (
            alt.Chart(typology)
            .mark_bar()
            .encode(
                x=alt.X("count():Q", title="Number of countries"),
                y=alt.Y(
                    "Cluster_Name:N", title=None,
                    sort=alt.SortField("count", order="descending"),
                ),
                color=alt.Color("Cluster_Name:N", legend=None),
                tooltip=[
                    alt.Tooltip("Cluster_Name:N", title="Cluster"),
                    alt.Tooltip("count():Q", title="Countries"),
                ],
            )
            .properties(height=220)
        )
        st.altair_chart(size_chart, use_container_width=True)

        st.markdown("#### Member countries by cluster")
        selected_cluster = st.selectbox(
            "Show countries in cluster:",
            options=sorted(typology["Cluster_Name"].unique()),
        )
        cluster_countries = typology[typology["Cluster_Name"] == selected_cluster][
            ["Country", "Country_Code", "Continent", "Income_Group",
             "BP_End", "Obesity_End", "Diabetes_End"]
        ].sort_values("Country")
        st.dataframe(
            cluster_countries.rename(columns={
                "BP_End": "BP End (%)", "Obesity_End": "Obesity End (%)",
                "Diabetes_End": "Diabetes End (%)",
            }).style.format({
                "BP End (%)": "{:.1f}", "Obesity End (%)": "{:.1f}",
                "Diabetes End (%)": "{:.1f}",
            }),
            use_container_width=True, hide_index=True,
        )

    with tabs[5]:
        st.markdown(
            "**K selection** — silhouette scores for k=2 through k=8. k=2 maximises the score "
            "at 0.47 but only splits 27 extreme outliers from everyone else. k=5 sits in the "
            "plateau (0.25–0.28) and yields five genuinely distinct, interpretable groups."
        )
        diag = load_k_diagnostics()
        k_chart = (
            alt.Chart(diag)
            .mark_line(point=True, strokeWidth=2.5, color=INDIGO)
            .encode(
                x=alt.X("k:Q", title="Number of clusters (k)", axis=alt.Axis(tickMinStep=1)),
                y=alt.Y("silhouette_score:Q", title="Silhouette score",
                         scale=alt.Scale(zero=False)),
                tooltip=[
                    alt.Tooltip("k:Q"),
                    alt.Tooltip("silhouette_score:Q", format=".3f"),
                ],
            )
            .properties(height=320, title="Silhouette Score vs. K — Why k=5?")
        )
        chosen_k = (
            alt.Chart(pd.DataFrame({"x": [5]}))
            .mark_rule(strokeDash=[4, 3], color=CORAL, strokeWidth=2)
            .encode(x="x:Q")
        )
        label = (
            alt.Chart(pd.DataFrame({"x": [5.1], "y": [0.27], "text": ["k=5 chosen"]}))
            .mark_text(align="left", color=CORAL, fontWeight="bold", fontSize=12)
            .encode(x="x:Q", y="y:Q", text="text:N")
        )
        st.altair_chart(k_chart + chosen_k + label, use_container_width=True)

        st.info(
            "**Why not k=2?** k=2 just separates the 13 Pacific Extreme Outlier countries from "
            "everything else — not a useful typology. k=5 reveals the full complexity of trajectories "
            "while remaining interpretable. The silhouette plateau from k=3 to k=8 means there is no "
            "single mathematically 'correct' k; k=5's content is the justification."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: THREAD 2 — GLOBAL CONVERGENCE
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📉 Thread 2 · Global Convergence":
    st.markdown('<div class="section-title">Thread 2 · Global Convergence</div>',
                unsafe_allow_html=True)
    st.markdown(f"{verdict_badge('confirmed')} **Obesity inequality converging at R²=0.999**",
                unsafe_allow_html=True)

    research_question(
        "Is the gap between the healthiest and sickest countries narrowing or widening, "
        "and is this consistent across all three diseases?"
    )
    method_callout(
        "Coefficient of Variation (CV = standard deviation / mean) computed across all 200 countries "
        "for each year from 1980 to 2014, separately for each disease. A declining CV means the "
        "distribution of country values is becoming less dispersed — countries are converging. "
        "Linear regression on CV over time gives the R² for trend reliability. A 10-year "
        "straight-line extrapolation to 2024 is shown as a projection (NOT a validated forecast)."
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Obesity convergence R²", "0.999",
              help="Near-perfect linear fit — obesity inequality between countries is closing at a mechanically consistent rate")
    c2.metric("BP convergence R²", "0.268",
              help="Real but noisy convergence — the trend exists but is not as reliable")
    c3.metric("Diabetes convergence R²", "0.075",
              help="Essentially no trend — diabetes inequality between countries is flat")

    finding_callout(
        "Obesity inequality between countries is converging at an almost perfectly consistent "
        "rate (R²=0.999) — poorer countries are not being left behind on obesity, they are "
        "catching up to richer ones. This directly challenges the framing that obesity is a "
        "'rich country problem'. BP is also converging but noisily. Diabetes shows no trend."
    )

    tabs = st.tabs(["📉 Global CV Trend", "🏦 Convergence by Income Tier"])

    with tabs[0]:
        cv = load_cv_by_year()
        extrap = load_trend_extrapolation()
        chart = build_convergence_trend_chart(cv, extrap)
        st.altair_chart(chart, use_container_width=True)
        st.caption(
            "Solid lines = observed 1980–2014 data. Dashed lines = straight-line projection to 2024 "
            "(not a validated forecast — labeled as such). Vertical rule at 2014 marks the "
            "boundary between observed and projected."
        )

        st.markdown("#### Observed CV values, 1980–2014")
        cv_display = cv[["Year", "BP_CV", "Obesity_CV", "Diabetes_CV"]].copy()
        cv_display.columns = ["Year", "BP CV", "Obesity CV", "Diabetes CV"]
        st.dataframe(
            cv_display.style.format({"BP CV": "{:.3f}", "Obesity CV": "{:.3f}",
                                     "Diabetes CV": "{:.3f}"}),
            use_container_width=True, hide_index=True, height=280,
        )

    with tabs[1]:
        by_income = load_convergence_by_income()
        chart = build_convergence_by_income_chart(by_income)
        st.altair_chart(chart, use_container_width=True)

        finding_callout(
            "The global convergence story (Thread 2) is NOT uniform across income tiers. "
            "High-income and Low-income countries are both converging strongly on obesity. "
            "Lower-middle income countries are almost completely flat (0.674 → 0.677 over 35 years) "
            "— effectively stuck. The global headline is real but driven by the top and bottom of "
            "the income ladder, not by every tier equally."
        )

        st.markdown("#### Obesity CV by income group (1980 vs 2014)")
        summary = (
            by_income[by_income["Year"].isin([1980, 2014])]
            .pivot(index="Income_Group", columns="Year", values="Obesity_CV")
            .rename(columns={1980: "CV 1980", 2014: "CV 2014"})
            .reset_index()
        )
        summary["Change"] = summary["CV 2014"] - summary["CV 1980"]
        summary["Direction"] = summary["Change"].apply(
            lambda x: "↓ Converging" if x < -0.01 else ("↑ Diverging" if x > 0.01 else "→ Flat")
        )
        st.dataframe(
            summary.style.format({"CV 1980": "{:.3f}", "CV 2014": "{:.3f}", "Change": "{:+.3f}"}),
            use_container_width=True, hide_index=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: THREAD 3 — EQUALITY HYPOTHESIS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "⚖️ Thread 3 · Equality Hypothesis":
    st.markdown('<div class="section-title">Thread 3 · Equality Hypothesis</div>',
                unsafe_allow_html=True)
    st.markdown(f"{verdict_badge('not_confirmed')} **Gini index does not explain obesity differences**",
                unsafe_allow_html=True)

    research_question(
        "Does income *equality* (Gini index), rather than income *level*, explain why some wealthy "
        "countries (Japan, South Korea) stay thin while others (USA, UK) do not?"
    )
    method_callout(
        "Two-step residual analysis. Step 1: regress Obesity_End on Income_Group_Ordinal → income "
        "level alone explains 26% of obesity variation (R²=0.260, n=197). Step 2: correlate the "
        "residual (the part NOT explained by income level) with Gini_Index → tests whether "
        "income *equality* explains what income *level* cannot."
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Income level explains", "26%", "R² = 0.260", delta_color="off")
    c2.metric("Gini global correlation", "r = 0.019", "p = 0.81 (not significant)", delta_color="off")
    c3.metric("Within wealthy cluster", "r = 0.143", "p = 0.44 (not significant)", delta_color="off")
    c4.metric("Japan vs UK Gini", "32.3 vs 32.4", "Nearly identical — wildly different obesity", delta_color="off")

    tabs = st.tabs(["📊 Main Result", "🔬 Follow-up: Sugar, Alcohol, Inactivity"])

    with tabs[0]:
        st.markdown(
            "**Obesity residual vs. Gini index.** If income equality explained the Japan/Korea vs. "
            "UK/USA anomaly, the circled countries (Japan, South Korea, UK, USA) would form a clear "
            "pattern. They do not — Japan and the UK sit at almost identical Gini scores yet opposite "
            "ends of the y-axis."
        )
        equality = load_equality_results()
        chart = build_equality_scatter(equality)
        st.altair_chart(chart, use_container_width=True)

        open_question(
            "Japan (Gini 32.3, obesity 3.8%) and the UK (Gini 32.4, obesity 26.3%) have nearly "
            "identical income equality yet wildly different obesity outcomes. The US (Gini 41.8, "
            "highest of the group) does have the highest obesity (34.6%) — so the hypothesis holds "
            "for the US specifically, but the UK comparison breaks it. Income equality is part of "
            "the picture but not sufficient on its own. Something else (diet, food culture, urban "
            "design) separates Japan/Korea from the UK, and this dataset cannot identify what."
        )

        with st.expander("See full equality hypothesis data table"):
            cols_to_show = ["Country", "Income_Group", "Gini_Index", "Gini_Year",
                            "Obesity_End", "Obesity_Residual", "Obesity_Predicted_By_Income",
                            "Cluster_Name", "WHO_Region"]
            st.dataframe(
                equality[cols_to_show].dropna(subset=["Gini_Index"])
                .sort_values("Obesity_Residual", ascending=False)
                .rename(columns={
                    "Obesity_End": "Obesity End (%)",
                    "Obesity_Residual": "Residual",
                    "Obesity_Predicted_By_Income": "Income-Predicted",
                    "Cluster_Name": "Cluster",
                })
                .style.format({
                    "Obesity End (%)": "{:.1f}", "Residual": "{:+.1f}",
                    "Income-Predicted": "{:.1f}", "Gini_Index": "{:.1f}",
                }),
                use_container_width=True, hide_index=True, height=350,
            )

    with tabs[1]:
        st.markdown("""
        **Self-correction chart.** After the Gini hypothesis failed, three more candidate
        explanations were tested for the Wealthy Decouplers cluster (~41 countries) only.
        """)
        st.info(
            "**Why a comparison chart, not a scatter with a trend line?** With only ~30–40 countries "
            "in this cluster (fewer with complete data), a regression coefficient would not be "
            "statistically reliable. Showing the 4 specific anomaly countries directly is the honest "
            "approach for a sample this small — no false precision."
        )
        followup = load_followup()
        chart = build_equality_followup_chart(followup)
        st.altair_chart(chart, use_container_width=True)

        finding_callout(
            "None of the three additional candidates explain the anomaly. Physical inactivity "
            "runs *backwards* from intuition — Japan (50.6%) and South Korea (60.7%) report "
            "MORE inactivity than the UK (21.9%) and US (36.4%), despite far lower obesity. "
            "Sugar and alcohol consumption don't cleanly separate the pairs either."
        )

        open_question(
            "Income level, income equality, sugar consumption, alcohol consumption, and physical "
            "inactivity have all been tested and ruled out as explanations for the Japan/Korea vs. "
            "UK/USA obesity gap. This is reported as a genuine, unresolved open question. "
            "Candidates remaining outside this dataset: food culture, meal frequency, portion norms, "
            "urban walkability, and genetic/metabolic factors."
        )

        st.markdown("#### Follow-up data: Wealthy Decouplers cluster")
        st.dataframe(
            followup.sort_values("Obesity_End")
            .rename(columns={
                "Obesity_End": "Obesity End (%)",
                "Sugar_Sweeteners_kg_per_capita": "Sugar (kg/cap/yr)",
                "Alcohol_kg_per_capita": "Alcohol (kg/cap/yr)",
                "Physical_Inactivity_pct": "Inactivity (%)",
            })
            .style.format({
                "Obesity End (%)": "{:.1f}",
                "Sugar (kg/cap/yr)": "{:.1f}",
                "Alcohol (kg/cap/yr)": "{:.1f}",
                "Inactivity (%)": "{:.1f}",
            }),
            use_container_width=True, hide_index=True, height=400,
        )
        st.caption(
            "Sugar & Alcohol: 2013 values (last year FAO data covers). "
            "Physical Inactivity: each country's most recent observed year (2022 for all 38 "
            "countries with data; 3 countries have no inactivity data and are correctly left blank)."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: THREAD 4 — ACCESS HYPOTHESIS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🏥 Thread 4 · Access Hypothesis":
    st.markdown('<div class="section-title">Thread 4 · Access Hypothesis</div>',
                unsafe_allow_html=True)
    st.markdown(f"{verdict_badge('confirmed')} **Healthcare access strongly predicts who escapes high BP**",
                unsafe_allow_html=True)

    research_question(
        "Does healthcare access (UHC Service Coverage Index), not obesity alone, explain why "
        "some high-obesity countries nevertheless escape high blood pressure?"
    )
    method_callout(
        "Two-step residual analysis. Step 1: regress BP_End on Obesity_End → obesity alone "
        "explains 10.6% of BP variation (R²=0.106, n=200). Step 2: correlate the residual "
        "(BP that obesity cannot explain) with UHC_End → tests whether healthcare access "
        "is the 'shield' mechanism that keeps BP down in high-obesity countries."
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Obesity explains BP", "R² = 0.106", "10.6% of BP variation")
    c2.metric("UHC correlation", "r = −0.479", "p < 0.0001, n = 192")
    c3.metric("Direction", "Negative", "Higher UHC → lower residual BP")
    c4.metric("Verdict", "CONFIRMED", "Strongest result in the analysis")

    finding_callout(
        "Countries with stronger healthcare access have blood pressure meaningfully lower than "
        "their obesity level alone would predict. This provides real, statistically tested "
        "evidence for the 'shield' mechanism the original reference report only asserted. "
        "With r=−0.479, p<0.0001, n=192, this is the strongest finding in the entire project."
    )

    access = load_access_results()
    chart = build_access_scatter(access)
    st.altair_chart(chart, use_container_width=True)

    st.markdown(
        "Points are coloured by **WHO Region** to show that the relationship holds across "
        "regions — it is not just a wealthy-country effect. The coral regression line has "
        "a meaningful negative slope (higher UHC → lower residual BP), shown solid rather "
        "than dashed because this is a confirmed, significant result."
    )

    with st.expander("See full access hypothesis data table"):
        cols_to_show = ["Country", "WHO_Region", "Income_Group", "UHC_End",
                        "BP_End", "Obesity_End", "BP_Residual", "BP_Predicted_By_Obesity"]
        st.dataframe(
            access[cols_to_show].dropna(subset=["UHC_End"])
            .sort_values("BP_Residual", ascending=False)
            .rename(columns={
                "UHC_End": "UHC Index",
                "BP_End": "BP End (%)",
                "Obesity_End": "Obesity End (%)",
                "BP_Residual": "BP Residual",
                "BP_Predicted_By_Obesity": "BP Predicted by Obesity",
                "WHO_Region": "WHO Region",
                "Income_Group": "Income Group",
            })
            .style.format({
                "UHC Index": "{:.1f}",
                "BP End (%)": "{:.1f}",
                "Obesity End (%)": "{:.1f}",
                "BP Residual": "{:+.1f}",
                "BP Predicted by Obesity": "{:.1f}",
            }),
            use_container_width=True, hide_index=True, height=380,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: THREAD 5 — GENDER GAPS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "👥 Thread 5 · Gender Gaps":
    st.markdown('<div class="section-title">Thread 5 · Gender Gaps</div>',
                unsafe_allow_html=True)
    st.markdown(f"{verdict_badge('mixed')} **Three diseases, three completely different gender stories**",
                unsafe_allow_html=True)

    research_question(
        "Is the global male/female health gap widening or narrowing, and does this sex-level "
        "story track the between-country convergence story (Thread 2) or move independently?"
    )
    method_callout(
        "Sex gap = Female minus Male prevalence (positive = higher in women, negative = higher "
        "in men), computed globally for each year 1980–2014 using the sex-disaggregated panel. "
        "Widening/narrowing judged on the trend of the ABSOLUTE gap — not the raw signed slope "
        "(a gap moving from −3.74 to −4.16 is widening in magnitude even though the slope is negative)."
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("BP gap", "−3.74 → −4.16 pp", "WIDENING (men higher, gap growing)")
    c2.metric("Obesity gap", "+5.69 → +7.25 pp", "WIDENING (women higher, gap growing)")
    c3.metric("Diabetes gap", "+0.68 → −0.12 pp", "NARROWING + SIGN FLIPS")

    finding_callout(
        "Obesity is uniquely linked: as countries converge on obesity between themselves (Thread 2), "
        "the gender gap within countries simultaneously widens — in near-lockstep (r=−0.969, "
        "p<0.0001). BP and Diabetes show no such coupling. For Diabetes, the gap not only narrows "
        "but reverses direction — by 2014 men are slightly more affected than women, the opposite "
        "of 1980."
    )

    tabs = st.tabs(["📊 Gender Gap Trend", "🗂️ Gap by Typology Cluster"])

    with tabs[0]:
        gender_gap = load_gender_gap()
        chart = build_gender_gap_chart(gender_gap)
        st.altair_chart(chart, use_container_width=True)

        st.markdown(
            "**Left panel:** 1980 vs. 2014 diverging bars — bars extending right (coral) mean "
            "women are more affected; bars extending left (indigo) mean men are more affected. "
            "**Right panel:** full 35-year trend — note the Diabetes line crossing zero (sign flip)."
        )

        st.markdown("#### Full gender gap time series")
        gap_display = gender_gap.copy()
        gap_display.columns = ["Year", "BP Gap (pp)", "Obesity Gap (pp)", "Diabetes Gap (pp)"]
        st.dataframe(
            gap_display.style.format({c: "{:+.2f}" for c in gap_display.columns if c != "Year"}),
            use_container_width=True, hide_index=True, height=300,
        )
        st.caption("Positive = higher in women; negative = higher in men. Gap = Female − Male.")

    with tabs[1]:
        by_cluster = load_gender_gap_by_cluster()
        chart = build_gender_gap_by_cluster_chart(by_cluster)
        st.altair_chart(chart, use_container_width=True)

        finding_callout(
            "The global 'widening obesity gender gap' headline is real — but only in 2 of the 5 "
            "typology clusters. Lean Hypertension and Moderate Transition show widening; the other "
            "three clusters (including Wealthy Decouplers) show narrowing. Direction depends entirely "
            "on which cluster a country belongs to."
        )

        st.dataframe(
            by_cluster.rename(columns={
                "Cluster_Name": "Cluster",
                "Gap_1980": "Gap 1980 (pp)",
                "Gap_2014": "Gap 2014 (pp)",
                "Change": "Change (pp)",
                "N_Countries": "n",
            }).style.format({
                "Gap 1980 (pp)": "{:+.2f}",
                "Gap 2014 (pp)": "{:+.2f}",
                "Change (pp)": "{:+.2f}",
            }),
            use_container_width=True, hide_index=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: SUPPLEMENTARY EXPLORATION
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Supplementary Exploration":
    st.markdown('<div class="section-title">Supplementary Exploration</div>',
                unsafe_allow_html=True)
    st.markdown(
        "Additional charts, robustness checks, and a country deep-dive tool. "
        "None of these introduce new hypotheses — they add depth and verification to "
        "the five main threads."
    )

    tabs = st.tabs([
        "🏆 Risk Leaderboard",
        "🔄 Cluster Robustness",
        "🔎 Country Deep-Dive",
    ])

    with tabs[0]:
        st.markdown(
            "**Metabolic Risk Index leaderboard** — the composite of BP, Obesity, and Diabetes "
            "(equally weighted, normalised to 0–100 scale). Use the slider to explore any year."
        )
        year_slider = st.slider("Year", min_value=1980, max_value=2014, value=2014, step=1)
        combined = load_combined()
        chart = build_risk_leaderboard(combined, year=year_slider, n=10)
        st.altair_chart(chart, use_container_width=True)

        st.caption(
            "Metabolic Risk Index = equally-weighted, min-max normalised combination of all three "
            "disease prevalences scaled to 0–100. This composite makes it possible to rank countries "
            "on their overall metabolic burden rather than on one disease alone."
        )

    with tabs[1]:
        st.markdown(
            "**Cluster robustness check** — does the 5-cluster typology depend on k-means, "
            "or is it a genuine structure in the data?"
        )
        st.metric(
            "Adjusted Rand Index (k-means vs. hierarchical)",
            "0.684",
            help="1.0 = perfect agreement; 0.684 = strong agreement. The 5 clusters are "
                 "not a k-means artifact — hierarchical clustering agrees with the same structure.",
        )
        st.markdown("""
        **What was tested:** the same 200-country 12-feature dataset was clustered two ways —
        k-means (used throughout the project) and agglomerative hierarchical clustering. The
        Adjusted Rand Index (ARI) measures how much the two clusterings agree, correcting for
        chance agreement.

        **ARI = 0.684** means strong agreement. The 5-cluster typology is a real structure
        in the data, not an artefact of the k-means algorithm choice. A score this high in
        a 200-country dataset with 12 continuous features is considered reliable.
        """)
        robustness_text = load_robustness_text()
        with st.expander("Raw robustness check output"):
            st.code(robustness_text)

    with tabs[2]:
        st.markdown(
            "**Country deep-dive** — select any of the 200 countries to see its full 1980–2014 "
            "trajectory across all three diseases, plus its key context metrics."
        )
        combined = load_combined()
        typology = load_country_typology()

        all_countries = sorted(combined["Country"].unique())
        selected_country = st.selectbox("Select a country:", options=all_countries, index=0)

        country_data = combined[
            (combined["Country"] == selected_country) &
            (combined["Year"] >= 1980) & (combined["Year"] <= 2014)
        ].copy()

        if country_data.empty:
            st.warning(f"No 1980–2014 data found for {selected_country}.")
        else:
            # Context metrics
            ctx = typology[typology["Country"] == selected_country]
            ctx_combined = combined[combined["Country"] == selected_country].sort_values("Year")

            col_a, col_b, col_c, col_d = st.columns(4)
            if not ctx.empty:
                col_a.metric("Typology Cluster", ctx.iloc[0]["Cluster_Name"])
                col_b.metric("Income Group", ctx.iloc[0]["Income_Group"])
                col_c.metric("Continent", ctx.iloc[0]["Continent"])
            latest = ctx_combined.sort_values("Year").iloc[-1]
            if pd.notna(latest.get("UHC_Index")):
                col_d.metric("UHC Index (latest)", f"{latest['UHC_Index']:.0f}")

            # Trajectory chart
            long_df = country_data.melt(
                id_vars=["Year"],
                value_vars=["BP_Prevalence_pct", "Obesity_Prevalence_pct", "Diabetes_Prevalence_pct"],
                var_name="Disease_Raw",
                value_name="Prevalence_pct",
            )
            long_df["Disease"] = long_df["Disease_Raw"].map({
                "BP_Prevalence_pct": "Blood Pressure",
                "Obesity_Prevalence_pct": "Obesity",
                "Diabetes_Prevalence_pct": "Diabetes",
            })

            color_map = {"Blood Pressure": INDIGO, "Obesity": CORAL, "Diabetes": "#8a8a3c"}

            traj_chart = (
                alt.Chart(long_df.dropna(subset=["Prevalence_pct"]))
                .mark_line(strokeWidth=2.5, point=alt.OverlayMarkDef(size=30))
                .encode(
                    x=alt.X("Year:Q", title=None,
                             axis=alt.Axis(format="d", values=[1980, 1985, 1990, 1995, 2000, 2005, 2010, 2014])),
                    y=alt.Y("Prevalence_pct:Q", title="Prevalence (%)"),
                    color=alt.Color(
                        "Disease:N", title="Disease",
                        scale=alt.Scale(
                            domain=list(color_map.keys()),
                            range=list(color_map.values()),
                        ),
                    ),
                    tooltip=[
                        alt.Tooltip("Disease:N"),
                        alt.Tooltip("Year:Q", format="d"),
                        alt.Tooltip("Prevalence_pct:Q", title="Prevalence (%)", format=".2f"),
                    ],
                )
                .properties(
                    height=380,
                    title=f"{selected_country} — Full 1980–2014 Trajectory",
                )
            )
            st.altair_chart(traj_chart, use_container_width=True)

            # Risk index over time
            risk_data = country_data.dropna(subset=["Metabolic_Risk_Index"])
            if not risk_data.empty:
                risk_chart = (
                    alt.Chart(risk_data)
                    .mark_area(opacity=0.3, color=CORAL)
                    .encode(
                        x=alt.X("Year:Q", title=None, axis=alt.Axis(format="d")),
                        y=alt.Y("Metabolic_Risk_Index:Q", title="Metabolic Risk Index (0–100)"),
                        tooltip=[
                            alt.Tooltip("Year:Q", format="d"),
                            alt.Tooltip("Metabolic_Risk_Index:Q", title="Risk Index", format=".1f"),
                        ],
                    )
                    .properties(height=200, title="Metabolic Risk Index over time")
                ) + alt.Chart(risk_data).mark_line(color=CORAL, strokeWidth=2).encode(
                    x="Year:Q", y="Metabolic_Risk_Index:Q"
                )
                st.altair_chart(risk_chart, use_container_width=True)

            with st.expander("Raw trajectory data"):
                st.dataframe(
                    country_data[["Year", "BP_Prevalence_pct", "Obesity_Prevalence_pct",
                                  "Diabetes_Prevalence_pct", "UHC_Index", "Metabolic_Risk_Index"]]
                    .rename(columns={
                        "BP_Prevalence_pct": "BP (%)",
                        "Obesity_Prevalence_pct": "Obesity (%)",
                        "Diabetes_Prevalence_pct": "Diabetes (%)",
                        "UHC_Index": "UHC Index",
                        "Metabolic_Risk_Index": "Risk Index",
                    })
                    .style.format({c: "{:.2f}" for c in ["BP (%)", "Obesity (%)", "Diabetes (%)",
                                                          "UHC Index", "Risk Index"]}),
                    use_container_width=True, hide_index=True,
                )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: INTERACTIVE DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🎛️ Interactive Dashboard":
    st.markdown('<div class="section-title">Interactive Dashboard — All Threads Linked</div>',
                unsafe_allow_html=True)

    st.markdown("""
    A two-panel linked dashboard bringing all typology threads together:

    - **Left panel:** every country positioned by its end-of-period Obesity vs. Blood Pressure,
      coloured by typology cluster. Filter by WHO Region using the dropdown.
    - **Right panel:** stays empty until you **click a point** on the left — clicking draws that
      country's full 1980–2014 BP, Obesity, and Diabetes trajectory.

    This is the "drill from overview to detail" pattern: the left panel shows where a country
    sits relative to everyone else; the right panel shows how it got there.
    """)

    st.info(
        "**Tip:** Use the WHO Region dropdown to narrow the left panel, then click any point "
        "to reveal that country's 35-year trajectory on the right. The point grows and brightens "
        "when selected."
    )

    combined = load_combined()
    typology = load_country_typology()
    dashboard = build_dashboard(typology, combined)
    components.html(dashboard.to_html(), height=850, scrolling=False)

    st.caption(
        "Why click-to-reveal rather than showing all 200 trajectories at once? With 200 countries, "
        "a trajectory chart showing everyone simultaneously is unreadable — this is exactly the "
        "problem that the Thread 1 small-multiples chart solved by aggregating to 5 cluster averages. "
        "The dashboard solves the same problem differently: one country on demand, chosen by the reader."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DATA & METHODOLOGY
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Data & Methodology":
    st.markdown('<div class="section-title">Data Sources & Methodology</div>',
                unsafe_allow_html=True)

    tabs = st.tabs(["📂 Data Sources", "⚙️ Analysis Pipeline", "⚠️ Caveats & Integrity"])

    with tabs[0]:
        st.markdown(
            "Eight data sources were used. Every merge was done using verified **ISO3 country codes** "
            "— fuzzy name matching was tested and rejected after it silently mapped 'Niger' to "
            "Nigeria's code."
        )

        sources = pd.DataFrame([
            {
                "Source": "Core health dataset",
                "File": "data/raw/cw1_dataset.xlsx",
                "What it provides": "BP, Obesity, Diabetes prevalence by sex",
                "Coverage": "1975–2016, 200 countries",
                "Publisher": "Coursework dataset (NCD-RisC basis)",
                "Caveats": "Original file, untouched throughout",
            },
            {
                "Source": "Gini Index",
                "File": "data/external/gini_worldbank_raw.csv",
                "What it provides": "Income inequality (0=perfect equality, 100=max inequality)",
                "Coverage": "Sparse years per country, latest used as static snapshot",
                "Publisher": "World Bank (SI.POV.GINI)",
                "Caveats": "Very sparse — many countries have data only every 5–10 years",
            },
            {
                "Source": "UHC Service Coverage Index",
                "File": "data/external/uhc_who_raw.csv",
                "What it provides": "Healthcare access score (0–100) + WHO Region",
                "Coverage": "2000–2023",
                "Publisher": "WHO Global Health Observatory",
                "Caveats": "Carried back to pre-2000 years using earliest real value (flagged)",
            },
            {
                "Source": "Historical Income Group",
                "File": "data/external/income_group_historical_raw.xlsx",
                "What it provides": "World Bank income classification (L / LM / UM / H) per year",
                "Coverage": "1987–present",
                "Publisher": "World Bank OGHIST",
                "Caveats": "Carried back to pre-1987 years using earliest real value (flagged)",
            },
            {
                "Source": "Current Income Group (fallback)",
                "File": "data/external/income_group_current_raw.xlsx",
                "What it provides": "2025 income classification — used only for countries missing from historical file",
                "Coverage": "2025 (single year)",
                "Publisher": "World Bank CLASS.xlsx",
                "Caveats": "Only used as last-resort fallback for small territories",
            },
            {
                "Source": "FAO Food Balance Sheets",
                "File": "data/external/consumption.xlsx",
                "What it provides": "Sugar & Sweeteners and Alcoholic Beverages supply (kg/capita/year)",
                "Coverage": "1970–2013",
                "Publisher": "FAO (Food and Agriculture Organization)",
                "Caveats": "Used only for the equality follow-up, 2013 values only",
            },
            {
                "Source": "WHO Physical Inactivity",
                "File": "data/external/physical_inactivity.csv",
                "What it provides": "% adults insufficiently physically active",
                "Coverage": "2000–2022",
                "Publisher": "WHO Global Health Observatory",
                "Caveats": "Each country's most recent real year used (2022 for all 38 with data)",
            },
            {
                "Source": "World Map geometry",
                "File": "data/geo/world-110m.json",
                "What it provides": "Country polygon geometry for the choropleth",
                "Coverage": "Static (geography doesn't change)",
                "Publisher": "Natural Earth (via TopoJSON 110m resolution)",
                "Caveats": "32 small island/micro-states absent from 110m resolution — included in every other chart",
            },
        ])

        st.dataframe(sources, use_container_width=True, hide_index=True, height=400)

        st.markdown("""
        #### Why ISO3 codes, not country name matching?

        Country name matching was explicitly tested and rejected. The fuzzy matcher silently
        mapped "Niger" to Nigeria's ISO3 code — the two countries are on different continents
        with vastly different data. A single silent wrong merge of this kind would corrupt
        every analysis that touched those rows. Every merge in this project uses verified ISO3
        country codes as the join key, with a curated list of name-to-code overrides for
        countries with inconsistent naming across sources (e.g. "Republic of Korea" → KOR).
        """)

    with tabs[1]:
        st.markdown("#### Six-stage pipeline — run in order from the project root")

        stages = [
            {
                "Stage": "1 — Data Preparation",
                "Script": "python src/main.py",
                "What it does": "Loads 3 health sheets, cleans, merges Continent/WHO Region/"
                                 "UHC/Gini/Income Group via ISO3 codes. Produces 3 files in data/final/.",
                "Outputs": "master_panel_by_sex.csv, sex_gap_table.csv, combined_panel_with_risk_index.csv",
            },
            {
                "Stage": "2 — Typology",
                "Script": "python src/typology_main.py",
                "What it does": "Builds 12 trajectory features per country (1980–2014 window), "
                                 "runs k-means for k=2 to k=8, selects k=5.",
                "Outputs": "k_selection_diagnostics.csv, country_typology.csv, cluster_profiles.csv",
            },
            {
                "Stage": "3 — Hypothesis Tests",
                "Script": "python src/hypothesis_main.py",
                "What it does": "Runs Thread 3 (Equality, Gini) and Thread 4 (Access, UHC) "
                                 "residual analyses. Two-step regression → correlation.",
                "Outputs": "equality_hypothesis_results.csv, access_hypothesis_results.csv",
            },
            {
                "Stage": "4a — Convergence",
                "Script": "python src/convergence_main.py",
                "What it does": "Computes CV per disease per year (1980–2014). "
                                 "Linear regression for trend reliability. 10-year projection.",
                "Outputs": "convergence_cv_by_year.csv, convergence_trend_extrapolation.csv",
            },
            {
                "Stage": "4b — Gender",
                "Script": "python src/gender_main.py",
                "What it does": "Computes Female−Male gap per disease per year from sex-disaggregated panel. "
                                 "Correlates obesity gender gap with between-country CV.",
                "Outputs": "gender_gap_by_year.csv",
            },
            {
                "Stage": "5 — Follow-up & Free Exploration",
                "Script": "python src/exploration_main.py",
                "What it does": "Equality follow-up (FAO + WHO inactivity data). Cluster robustness "
                                 "(ARI). Convergence by income group. Gender gap by cluster.",
                "Outputs": "equality_followup_wealthy_cluster.csv, convergence_by_income_group.csv, "
                            "gender_gap_by_cluster.csv, cluster_robustness_check.txt",
            },
            {
                "Stage": "6 — Altair Charts",
                "Script": "python src/charts/build_all_charts.py",
                "What it does": "Builds all 12 Altair charts as HTML (interactive) and PNG (static). "
                                 "Charts use absolute __file__-relative paths so they run from any directory.",
                "Outputs": "12 .html + 12 .png files in visuals/ (organised by thread)",
            },
        ]

        for s in stages:
            with st.expander(f"**{s['Stage']}** — `{s['Script']}`"):
                st.markdown(f"**What it does:** {s['What it does']}")
                st.code(s["Script"], language="bash")
                st.markdown(f"**Outputs:** `{s['Outputs']}`")

    with tabs[2]:
        st.markdown("#### Data integrity decisions and known limitations")

        st.markdown("""
        ##### 1. Carry-back assumption (UHC Index and Income Group)
        UHC data exists from 2000 onward; historical Income Group from 1987. For years before
        each source's real coverage starts, this project carries each country's **earliest
        available real value backward** as a stated simplifying assumption (e.g. a country's
        1990 UHC value = its year-2000 value, because UHC reflects slow-moving health-system
        structure, not something that swings year to year).

        This is the **one place where a value is extended beyond what was actually measured**.
        It is never silent — every such row is flagged `True` in `UHC_Index_Is_Carried_Back`
        or `Income_Group_Is_Carried_Back` in the combined panel.

        ##### 2. Equality follow-up data — NO carry-back
        - **Sugar & Alcohol (FAO):** a single fixed real year, **2013** (the last year FAO's
          file covers) — the same real, directly-observed 2013 value for every country.
        - **Physical Inactivity (WHO):** each country's own most recent **real** observed year
          (2022 for every country with data). Three countries have no inactivity data and are
          correctly left blank.

        The exact year behind every number is visible in the output CSV via `Sugar_Alcohol_Year`
        and `Inactivity_Year` columns — not just asserted in documentation.

        ##### 3. Core panel: NaN means NaN, never guessed
        The merged panel deliberately keeps the full available range (BP/Obesity: 1975–2015/2016,
        Diabetes: 1980–2014). For years where Diabetes has no data (pre-1980, post-2014), the
        cell is left as NaN — nothing is calculated or guessed. The 1980–2014 common window is
        applied inside specific analyses that need all three diseases simultaneously.

        ##### 4. Map: 32 small countries absent from choropleth
        The world-110m.json map geometry omits 32 small island/micro-states at 110m resolution.
        These 32 countries **are included** in every other chart and analysis. This limitation is
        disclosed in the choropleth subtitle and is a map resolution issue, not a data gap.

        ##### 5. Open limitation: no population-weighted comparison
        The convergence analysis uses simple averages (each country equally weighted). A
        population-weighted version would give different results — e.g. China and India would
        dominate. A population-weighted chart was planned but parked because no annual
        population data was sourced for this project. Documented as an open decision rather
        than quietly omitted.

        ##### 6. 2024 projection is NOT a validated forecast
        The Thread 2 extrapolation to 2024 is a straight-line continuation of the 1980–2014
        trend. It is labeled as "projected, not measured" throughout (dashed lines, subtitle
        disclosure) and should not be interpreted as a prediction.
        """)


# ═══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════════
st.divider()
st.caption(
    "Global Health Trajectory Analysis · 200 countries · 1975–2016 · "
    "Branch: DataPreprocess · Built with Streamlit + Altair"
)
