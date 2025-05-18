
import streamlit as st
import pandas as pd
from irp_policies import irp_policies
from dummy_data import dummy_prices, dummy_volumes
from simulator import run_irp_simulation_with_interventions

st.set_page_config(page_title="HERCULES IRP Simulator", layout="wide")
st.title("HERCULES IRP Simulator")

# Step 1: Editable Baseline Setup
st.markdown("## 📘 Step 1: Set Up Baseline")

selected_countries = st.multiselect(
    "Select countries to include in simulation",
    options=list(irp_policies.keys()),
    default=list(irp_policies.keys())
)

with st.expander("📘 View & Edit IRP Rules (All Countries)", expanded=False):
    st.caption("Review IRP settings for all countries before simulation.")
    irp_df = pd.DataFrame.from_dict(irp_policies, orient="index").reset_index(names=["Country"])
    st.dataframe(irp_df)
irp_inputs = {}
for country in selected_countries:
    with st.expander(f"{country} IRP Settings", expanded=False):
        rule = st.selectbox("IRP Rule", ["min", "average", "median"], index=["min", "average", "median"].index(irp_policies[country]["rule"]), key=f"rule_{country}")
        frequency = st.number_input("Review Frequency (months)", min_value=1, max_value=60, value=irp_policies[country]["frequency"], key=f"freq_{country}")
        delay = st.number_input("Enforcement Delay (months)", min_value=0, max_value=24, value=irp_policies[country]["enforcement_delay"], key=f"delay_{country}")
        allow = st.selectbox("Allow Price Increases?", ["No", "Yes"], index=1 if irp_policies[country]["allow_increase"] else 0, key=f"allow_{country}")
        basket = st.multiselect("Reference Basket", [c for c in selected_countries if c != country], default=irp_policies[country]["basket"], key=f"basket_{country}")
        # Use default rule input instead of per-country dropdowns
    irp_inputs[country] = irp_policies.get(country, {})
    