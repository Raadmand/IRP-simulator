
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from simulator import run_irp_simulation_with_interventions

st.set_page_config(page_title="IRP Simulator", layout="wide")
st.image('https://via.placeholder.com/150x40.png?text=HERCULES+IRP', width=180)
st.title("HERCULES IRP Simulator")
st.caption("A streamlined tool to model international reference pricing impacts across markets.")
st.markdown("---")
st.caption("A streamlined tool to model international reference pricing impacts across markets.")
st.markdown("---")

# Constants
DRUG_NAME = "Aspirin"
DEFAULT_COUNTRIES = {
    "Germany": 12.5,
    "France": 11.8,
    "Spain": 10.0,
    "Italy": 13.2,
    "Norway": 14.0
}
DEFAULT_VOLUME = 100000
YEARS = 10
START_YEAR = 2025
START_MONTH = 1
TOTAL_MONTHS = YEARS * 12

# Session state to store baseline results
if "baseline_df" not in st.session_state:
    st.session_state["baseline_df"] = None

st.markdown("### 📘 Step 1: Configure and Run Baseline")
st.info("This baseline scenario assumes no price interventions. Use it as your benchmark.")

# IRP Policies
irp_policies = {}
with st.expander("Edit IRP Rules Per Country", expanded=True):
    for country in DEFAULT_COUNTRIES:
        st.markdown(f"**{country}**")
        col1, col2, col3 = st.columns(3)
        with col1:
            freq_months = st.number_input(f"{country} Frequency (months)", value=12, min_value=1, max_value=60, key=f"freq_{country}")
        with col2:
            delay = st.number_input(f"{country} Enforcement Delay (months)", value=0, min_value=0, max_value=24, key=f"delay_{country}")
        with col3:
            rule = st.selectbox(f"{country} Rule", ["min", "average", "median"], key=f"rule_{country}")
        basket = st.multiselect(f"{country} Reference Basket", [c for c in DEFAULT_COUNTRIES if c != country], default=[c for c in DEFAULT_COUNTRIES if c != country], key=f"basket_{country}")
        irp_policies[country] = {
            "frequency": freq_months,
            "enforcement_delay": delay,
            "rule": rule,
            "basket": basket
        }

# Prices
initial_prices = {DRUG_NAME: {}}
with st.expander("Set Initial Prices", expanded=False):
    for country, base_price in DEFAULT_COUNTRIES.items():
        price = st.number_input(f"{country} Initial Price (€)", value=base_price, min_value=0.01, step=0.1, key=f"price_{country}")
        initial_prices[DRUG_NAME][country] = price

# Volumes
volumes = {DRUG_NAME: {}}
with st.expander("Set Constant Monthly Volumes", expanded=False):
    for country in DEFAULT_COUNTRIES:
        vol = st.number_input(f"{country} Monthly Volume (units)", value=DEFAULT_VOLUME, step=1000, key=f"vol_{country}")
        volumes[DRUG_NAME][country] = {m: vol for m in range(TOTAL_MONTHS + 1)}

# Run baseline
if st.button("🚀 Run Baseline Simulation"):
    st.session_state["baseline_df"] = run_irp_simulation_with_interventions(
        initial_prices=initial_prices,
        volumes=volumes,
        irp_policies=irp_policies,
        interventions=[],
        years=YEARS,
        start_year=START_YEAR,
        start_month=START_MONTH
    )
    st.success("Baseline simulation completed.")

# If baseline has been run, allow scenario simulation
if st.session_state["baseline_df"] is not None:
    st.markdown("### 🔧 Step 2: Define Price Event Scenarios")
st.info("Now you can simulate how price changes in one country affect others via IRP.")

    interventions = []
    with st.expander("Define Price Events (Interventions)", expanded=True):
        num_events = st.number_input("Number of Price Events", min_value=1, max_value=10, value=1)
        for i in range(num_events):
            st.markdown(f"**Event {i + 1}**")
            col1, col2, col3 = st.columns(3)
            with col1:
                country = st.selectbox(f"Country", list(DEFAULT_COUNTRIES.keys()), key=f"intv_country_{i}")
            with col2:
                month = st.selectbox("Start Month", list(range(1, 13)), key=f"intv_month_{i}")
            with col3:
                year = st.selectbox("Start Year", list(range(START_YEAR, START_YEAR + YEARS)), key=f"intv_year_{i}")

            mode = st.radio("Change Mode", ["Percent", "Absolute"], horizontal=True, key=f"intv_mode_{i}")
            if mode == "Percent":
                value = st.slider("Percent Reduction (%)", min_value=1, max_value=90, value=30, key=f"intv_value_{i}")
                interventions.append({
                    "drug": DRUG_NAME,
                    "country": country,
                    "month": month,
                    "year": year,
                    "mode": "percent",
                    "value": value
                })
            else:
                value = st.number_input("Set New Absolute Price (€)", min_value=0.01, step=0.1, key=f"intv_value_{i}")
                interventions.append({
                    "drug": DRUG_NAME,
                    "country": country,
                    "month": month,
                    "year": year,
                    "mode": "absolute",
                    "value": value
                })

    if st.button("▶️ Run Scenario Simulation"):
        scenario_df = run_irp_simulation_with_interventions(
            initial_prices=initial_prices,
            volumes=volumes,
            irp_policies=irp_policies,
            interventions=interventions,
            years=YEARS,
            start_year=START_YEAR,
            start_month=START_MONTH
        )

        baseline_df = st.session_state["baseline_df"]
        merged = scenario_df.rename(columns={"Price": "Scenario_Price", "Revenue": "Scenario_Revenue"})
        merged["Baseline_Price"] = baseline_df["Price"]
        merged["Baseline_Revenue"] = baseline_df["Revenue"]
        merged["Revenue_Diff"] = merged["Baseline_Revenue"] - merged["Scenario_Revenue"]

        st.subheader("📊 Total Revenue Comparison by Country")
        totals = merged.groupby("Country")[["Baseline_Revenue", "Scenario_Revenue"]].sum().reset_index()
        fig, ax = plt.subplots()
        ax.bar(totals["Country"], totals["Baseline_Revenue"], label="Baseline")
        ax.bar(totals["Country"], totals["Scenario_Revenue"], label="Scenario", alpha=0.7)
        ax.set_ylabel("Total Revenue (€)")
        ax.set_title("Total Revenue per Country (Baseline vs Scenario)")
        ax.legend()
        st.pyplot(fig)

        st.markdown("### 📄 Detailed Results Table")
        st.dataframe(merged)

        csv = merged.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, file_name="irp_comparison_results.csv", mime="text/csv")
