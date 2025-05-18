
import streamlit as st
import pandas as pd
from irp_policies import irp_policies
from dummy_data import dummy_prices, dummy_volumes
from simulator import run_irp_simulation_with_interventions

st.set_page_config(page_title="HERCULES IRP Simulator", layout="wide")
st.title("HERCULES IRP Simulator")

all_countries = list(dummy_prices.keys())
drug_name = st.text_input("Drug Name", "Aspirin")

# Step 1.1: View & Edit IRP Rules
with st.expander("📘 View & Edit IRP Rules", expanded=False):
    st.caption("Edit the IRP rule configuration for each country.")
    irp_inputs = {}
    for country in all_countries:
        with st.expander(f"{country} IRP Settings", expanded=False):
            rule = st.selectbox(f"{country} Rule", ["min", "average", "median"], index=["min", "average", "median"].index(irp_policies[country]["rule"]), key=f"rule_{country}")
            freq = st.number_input("Review Frequency (months)", min_value=1, max_value=60, value=irp_policies[country]["frequency"], key=f"freq_{country}")
            delay = st.number_input("Enforcement Delay (months)", min_value=0, max_value=24, value=irp_policies[country]["enforcement_delay"], key=f"delay_{country}")
            allow = st.selectbox("Allow Price Increases?", ["No", "Yes"], index=1 if irp_policies[country]["allow_increase"] else 0, key=f"allow_{country}")
            basket = st.multiselect("Reference Basket", [c for c in all_countries if c != country], default=irp_policies[country]["basket"], key=f"basket_{country}")
            irp_inputs[country] = {
                "rule": rule,
                "frequency": freq,
                "enforcement_delay": delay,
                "allow_increase": allow == "Yes",
                "basket": basket,
                "review_month": irp_policies[country].get("review_month", 6),
                "performs_irp": irp_policies[country].get("performs_irp", True)
            }

# Step 1.2: Input & Review Prices
with st.expander("💶 Input & Review Prices", expanded=False):
    initial_prices = {}
    for country in all_countries:
        initial_prices[country] = st.number_input(f"{country} price (€)", value=dummy_prices[country], key=f"price_{country}")
    initial_prices_wrapped = {drug_name: initial_prices}

# Step 1.3: Input & Review Volumes
with st.expander("📦 Input & Review Volumes", expanded=False):
    volumes = {}
    for country in all_countries:
        vol = st.number_input(f"{country} monthly volume", value=dummy_volumes[country][0], key=f"vol_{country}")
        volumes[country] = {m: vol for m in range(121)}
    volumes_wrapped = {drug_name: volumes}

# Run Baseline
if st.button("▶️ Run Baseline Simulation"):
    baseline_df = run_irp_simulation_with_interventions(
        initial_prices=initial_prices_wrapped,
        volumes=volumes_wrapped,
        irp_policies=irp_inputs,
        interventions=[],
        years=10,
        start_year=2025,
        start_month=1
    )
    st.session_state["baseline_df"] = baseline_df
    st.session_state["irp_inputs"] = irp_inputs
    st.success("Baseline simulation complete.")

# Step 2: Scenario Builder
if "baseline_df" in st.session_state:
    st.markdown("---")
    st.markdown("## 🔧 Step 2: Define Scenario")

    interventions = []
    num_events = st.number_input("Number of intervention events", min_value=1, max_value=10, value=1)
    for i in range(num_events):
        st.markdown(f"### Event {i + 1}")
        col1, col2, col3 = st.columns(3)
        with col1:
            country = st.selectbox(f"Country", options=all_countries, key=f"intv_country_{i}")
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
            irp_policies=st.session_state["irp_inputs"],
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
        st.session_state["results_df"] = merged
        st.success("Scenario simulation complete.")

# Step 3: Results
if "results_df" in st.session_state:
    st.markdown("---")
    st.markdown("## 📊 Step 3: Results")

    merged = st.session_state["results_df"]
    summary = merged.groupby("Country")[["Baseline_Revenue", "Scenario_Revenue"]].sum().reset_index()
    summary["Impacted"] = summary["Scenario_Revenue"] < summary["Baseline_Revenue"]

    view_option = st.selectbox("Filter countries for bar chart:", ["Only impacted countries", "All countries"])
    summary_filtered = summary if view_option == "All countries" else summary[summary["Impacted"]]

    st.markdown("### 💵 Total Revenue by Country")
    summary_melted = pd.melt(
        summary_filtered,
        id_vars=["Country"],
        value_vars=["Baseline_Revenue", "Scenario_Revenue"],
        var_name="Scenario",
        value_name="Total Revenue (€)"
    )
    st.bar_chart(summary_melted.pivot(index="Country", columns="Scenario", values="Total Revenue (€)"))

    st.markdown("### 📈 Revenue Over Time")
    df_time = merged.groupby(["Year", "Month", "Country"])[["Baseline_Revenue", "Scenario_Revenue"]].sum().reset_index()
    df_time["Date"] = pd.to_datetime(df_time["Year"].astype(str) + "-" + df_time["Month"].astype(str) + "-01")

    impacted_countries = summary[summary["Impacted"]]["Country"].tolist()
    default_country = impacted_countries[0] if impacted_countries else all_countries[0]
    country_select = st.selectbox("Select country to view trend", options=all_countries, index=all_countries.index(default_country))
    df_country = df_time[df_time["Country"] == country_select].sort_values("Date")
    st.line_chart(df_country.set_index("Date")[["Baseline_Revenue", "Scenario_Revenue"]])
