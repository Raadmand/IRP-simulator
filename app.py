
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from simulator import run_irp_simulation_with_interventions

st.set_page_config(page_title="IRP Simulator", layout="wide")
st.title("📊 International Reference Pricing (IRP) Simulator")

# --- Constants ---
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

# --- Section: Simulate (Interventions) ---
st.header("🔧 Simulate Price Events")
with st.expander("Define Price Changes (Interventions)", expanded=True):
    interventions = []
    num_events = st.number_input("How many price events would you like to simulate?", min_value=1, max_value=10, value=1, step=1)
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

# --- Section: IRP Rules ---
st.header("📘 IRP Rules")
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

# --- Section: Prices ---
st.header("💶 Initial Prices")
initial_prices = {DRUG_NAME: {}}
with st.expander("Set Initial Prices", expanded=False):
    for country, base_price in DEFAULT_COUNTRIES.items():
        price = st.number_input(f"{country} Initial Price (€)", value=base_price, min_value=0.01, step=0.1, key=f"price_{country}")
        initial_prices[DRUG_NAME][country] = price

# --- Section: Volumes ---
st.header("📦 Monthly Volumes")
volumes = {DRUG_NAME: {}}
with st.expander("Set Constant Monthly Volumes", expanded=False):
    for country in DEFAULT_COUNTRIES:
        vol = st.number_input(f"{country} Monthly Volume (units)", value=DEFAULT_VOLUME, step=1000, key=f"vol_{country}")
        volumes[DRUG_NAME][country] = {m: vol for m in range(TOTAL_MONTHS + 1)}

# --- Run Simulation ---
st.header("🚀 Run Simulation")

if st.button("Run IRP Simulation"):
    df = run_irp_simulation_with_interventions(
        initial_prices=initial_prices,
        volumes=volumes,
        irp_policies=irp_policies,
        interventions=interventions,
        years=YEARS,
        start_year=START_YEAR,
        start_month=START_MONTH
    )

    selected_country = st.selectbox("Select Country to View", list(DEFAULT_COUNTRIES.keys()))
    df_c = df[(df["Country"] == selected_country) & (df["Drug"] == DRUG_NAME)]

    st.subheader("📈 Revenue Over Time")
    fig, ax = plt.subplots()
    ax.plot(df_c["Month"] + (df_c["Year"] - START_YEAR) * 12, df_c["Revenue"], marker="o")
    ax.set_title(f"{selected_country} Revenue Over Time")
    ax.set_xlabel("Month Index")
    ax.set_ylabel("Revenue (€)")
    st.pyplot(fig)

    st.subheader("🧾 Full Simulation Results")
    st.dataframe(df)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, file_name="irp_simulation_results.csv", mime="text/csv")
