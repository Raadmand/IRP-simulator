
import streamlit as st
import pandas as pd
from irp_policies import irp_policies
from dummy_data import dummy_prices, dummy_volumes
from simulator import run_irp_simulation_with_interventions

st.set_page_config(page_title="HERCULES IRP Simulator", layout="wide")
st.title("HERCULES IRP Simulator")

st.markdown("## 📘 Step 1: Select Countries for Simulation")
selected_countries = st.multiselect(
    "Select countries to simulate",
    options=list(irp_policies.keys()),
    default=list(irp_policies.keys())
)

st.markdown("## 💊 Step 2: Define Drug and Pricing Data")

drug_name = st.text_input("Drug name", "Aspirin")
initial_prices = {}
volumes = {}

for country in selected_countries:
    col1, col2 = st.columns(2)
    with col1:
        price = st.number_input(f"Initial price in {country} (€)", value=dummy_prices.get(country, 10.0), key=f"price_{country}")
    with col2:
        volume = st.number_input(f"Monthly volume in {country}", value=dummy_volumes.get(country, {}).get(0, 100000), key=f"vol_{country}")
    initial_prices[country] = price
    volumes[country] = {m: volume for m in range(121)}

initial_prices_wrapped = {drug_name: initial_prices}
volumes_wrapped = {drug_name: volumes}

# Include policies for all countries, but only use IRP logic where it applies
policies_wrapped = {}
for country in selected_countries:
    policy = irp_policies[country]
    if policy["performs_irp"]:
        policies_wrapped[country] = policy
    else:
        # No IRP performed, skip application by setting long frequency
        policies_wrapped[country] = {
            **policy,
            "frequency": 9999,
            "rule": "average",
            "basket": [],
            "enforcement_delay": 0,
            "allow_increase": False
        }

if st.button("▶️ Run Baseline Simulation"):
    baseline_df = run_irp_simulation_with_interventions(
        initial_prices=initial_prices_wrapped,
        volumes=volumes_wrapped,
        irp_policies=policies_wrapped,
        interventions=[],
        years=10,
        start_year=2025,
        start_month=1
    )
    st.session_state["baseline_df"] = baseline_df
    st.success("Baseline simulation complete.")

if "baseline_df" in st.session_state:
    st.markdown("---")
    st.markdown("## 🔧 Step 3: Add Intervention Scenario")

    interventions = []
    num_events = st.number_input("Number of intervention events", min_value=1, max_value=10, value=1)
    for i in range(num_events):
        st.markdown(f"### Event {i + 1}")
        col1, col2, col3 = st.columns(3)
        with col1:
            country = st.selectbox(f"Country", selected_countries, key=f"intv_country_{i}")
        with col2:
            year = st.selectbox("Year", list(range(2025, 2036)), key=f"intv_year_{i}")
        with col3:
            month = st.selectbox("Month", list(range(1, 13)), key=f"intv_month_{i}")

        mode = st.radio("Change Mode", ["Percent", "Absolute"], horizontal=True, key=f"intv_mode_{i}")
        if mode == "Percent":
            value = st.slider("Percent Reduction (%)", 1, 90, 30, key=f"intv_val_{i}")
        else:
            value = st.number_input("New Price (€)", min_value=0.01, value=5.0, key=f"intv_val_{i}")

        interventions.append({
            "drug": drug_name,
            "country": country,
            "year": year,
            "month": month,
            "mode": "percent" if mode == "Percent" else "absolute",
            "value": value
        })

    if st.button("▶️ Run Scenario Simulation"):
        scenario_df = run_irp_simulation_with_interventions(
            initial_prices=initial_prices_wrapped,
            volumes=volumes_wrapped,
            irp_policies=policies_wrapped,
            interventions=interventions,
            years=10,
            start_year=2025,
            start_month=1
        )

        baseline_df = st.session_state["baseline_df"]
        merged = scenario_df.rename(columns={"Price": "Scenario_Price", "Revenue": "Scenario_Revenue"})
        merged["Baseline_Price"] = baseline_df["Price"]
        merged["Baseline_Revenue"] = baseline_df["Revenue"]
        merged["Revenue_Diff"] = merged["Baseline_Revenue"] - merged["Scenario_Revenue"]

        
        st.markdown("## 📊 Step 3: Results")

        # Compute total revenue by country
        summary = (
            merged.groupby("Country")[["Baseline_Revenue", "Scenario_Revenue"]]
            .sum()
            .reset_index()
        )
        summary["Impacted"] = summary["Scenario_Revenue"] < summary["Baseline_Revenue"]

        show_impacted_only = st.selectbox(
            "Filter countries in chart:", ["Only impacted countries", "All countries"]
        )
        if show_impacted_only == "Only impacted countries":
            summary_filtered = summary[summary["Impacted"]]
        else:
            summary_filtered = summary

        st.markdown("### 📊 Total Revenue by Country")
        summary_melted = pd.melt(
            summary_filtered,
            id_vars=["Country"],
            value_vars=["Baseline_Revenue", "Scenario_Revenue"],
            var_name="Scenario",
            value_name="Total Revenue (€)"
        )
        st.bar_chart(
            data=summary_melted.pivot(index="Country", columns="Scenario", values="Total Revenue (€)")
        )

        st.markdown("### 📈 Revenue Over Time by Country")
        df_time = merged.groupby(["Year", "Month", "Country"])[
            ["Baseline_Revenue", "Scenario_Revenue"]
        ].sum().reset_index()

        # Convert to datetime for x-axis
        df_time["Date"] = pd.to_datetime(df_time["Year"].astype(str) + "-" + df_time["Month"].astype(str) + "-01")

        # Filter impacted countries
        impacted_countries = summary[summary["Impacted"]]["Country"].tolist()
        countries_to_plot = st.multiselect(
            "Select countries for time-based revenue view",
            options=merged["Country"].unique().tolist(),
            default=impacted_countries if impacted_countries else merged["Country"].unique().tolist()
        )

        for country in countries_to_plot:
            df_country = df_time[df_time["Country"] == country].sort_values("Date")
            st.line_chart(
                df_country.set_index("Date")[["Baseline_Revenue", "Scenario_Revenue"]],
                height=300
            )
