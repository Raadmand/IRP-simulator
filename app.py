import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from simulator import run_irp_simulation_with_intervention

st.set_page_config(page_title="IRP Simulator", layout="wide")
st.title("International Reference Pricing Simulator")

# --- User Inputs ---
st.sidebar.header("Simulation Settings")

years_to_simulate = st.sidebar.slider("Years to Simulate", 5, 20, 10)

# Drug
drug_name = "Aspirin"

# Countries and default prices
default_prices = {
    "Germany": 12.5,
    "France": 11.8,
    "Spain": 10.0,
    "Italy": 13.2,
    "Norway": 14.0,
}

# Volumes
st.sidebar.subheader("Volumes per Country")
volumes = {drug_name: {}}
for country in default_prices:
    vol = st.sidebar.number_input(f"{country} Volume (per year)", value=100000, step=1000)
    volumes[drug_name][country] = {year: vol for year in range(years_to_simulate + 1)}

# Prices
st.sidebar.subheader("Prices per Country")
initial_prices = {drug_name: {}}
for country, price in default_prices.items():
    p = st.sidebar.number_input(f"{country} Price", value=price, step=0.1)
    initial_prices[drug_name][country] = p

# IRP Policies
st.sidebar.subheader("IRP Policies")
irp_policies = {}
for country in default_prices:
    st.sidebar.markdown(f"**{country} IRP Settings**")
    freq = st.sidebar.number_input(f"{country} Frequency", min_value=1, max_value=10, value=1, key=f"freq_{country}")
    delay = st.sidebar.number_input(f"{country} Delay", min_value=0, max_value=5, value=0, key=f"delay_{country}")
    rule = st.sidebar.selectbox(f"{country} Rule", ["min", "average", "median"], key=f"rule_{country}")
    basket = st.sidebar.multiselect(f"{country} Basket", options=[c for c in default_prices if c != country], default=[c for c in default_prices if c != country], key=f"basket_{country}")
    irp_policies[country] = {
        "frequency": freq,
        "enforcement_delay": delay,
        "rule": rule,
        "basket": basket
    }

# Intervention Scenario
st.sidebar.subheader("Scenario: Price Cut")
intervene = st.sidebar.checkbox("Apply Price Cut?")
intervention = None
if intervene:
    country_cut = st.sidebar.selectbox("Country to Reduce Price", list(default_prices.keys()))
    year_cut = st.sidebar.slider("Year of Cut", 1, years_to_simulate)
    pct_cut = st.sidebar.slider("Reduction %", 5, 90, 30)
    intervention = {
        "country": country_cut,
        "year": year_cut,
        "drug": drug_name,
        "reduction_pct": pct_cut / 100
    }

# Run simulation
if st.sidebar.button("Run Simulation"):
    df_base = run_irp_simulation_with_intervention(initial_prices, volumes, irp_policies, intervention=None, years=years_to_simulate)
    df_scenario = run_irp_simulation_with_intervention(initial_prices, volumes, irp_policies, intervention=intervention, years=years_to_simulate)

    df = df_scenario.copy()
    df = df.rename(columns={"Price": "Scenario_Price", "Revenue": "Scenario_Revenue"})
    df["Baseline_Price"] = df_base["Price"]
    df["Baseline_Revenue"] = df_base["Revenue"]
    df["Revenue_Diff"] = df["Baseline_Revenue"] - df["Scenario_Revenue"]
    df["Price_Diff"] = df["Baseline_Price"] - df["Scenario_Price"]

    # Charts
    st.subheader("Revenue Trend Over Time")
    selected_country = st.selectbox("Country to Plot", list(default_prices.keys()))
    df_c = df[df["Country"] == selected_country]
    fig, ax = plt.subplots()
    ax.plot(df_c["Year"], df_c["Baseline_Revenue"], label="Baseline", marker="o")
    ax.plot(df_c["Year"], df_c["Scenario_Revenue"], label="Scenario", marker="o")
    ax.set_title(f"Revenue Comparison in {selected_country}")
    ax.set_xlabel("Year")
    ax.set_ylabel("Revenue (€)")
    ax.legend()
    st.pyplot(fig)

    st.subheader("Revenue Difference Per Year")
    fig2, ax2 = plt.subplots()
    ax2.bar(df_c["Year"], df_c["Revenue_Diff"], color="red")
    ax2.set_title(f"Revenue Loss in {selected_country} Due to Intervention")
    ax2.set_xlabel("Year")
    ax2.set_ylabel("Δ Revenue (€)")
    st.pyplot(fig2)

    st.subheader("Simulation Results Table")
    st.dataframe(df)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "irp_simulation.csv", "text/csv")
