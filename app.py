
import streamlit as st

st.set_page_config(page_title="HERCULES IRP - Choose Mode", layout="centered")

st.title("🔍 Choose Your Simulation Mode")

st.markdown("Welcome to **HERCULES IRP** – your tool for modeling international reference pricing strategies and risk.")

# Manual mode
st.markdown("## 🧰 Option B: Manual Simulation")
st.markdown("""
Use the interactive UI to:
- Review and edit IRP rules
- Set up baseline pricing and volumes
- Define your intervention scenarios
- View full charts and results
""")
if st.button("Enter Manual Mode"):
    st.switch_page("Manual Simulation")

st.markdown("---")

# AI mode (placeholder)
st.markdown("## 🤖 Option A: Talk to Your Pricing Analyst")
st.markdown("""
Use natural language to interact with your IRP model:
- "Drop Germany by 25% in 2028"
- "Show me all countries impacted by a cut in Spain"
- "Run a baseline for EU only"
""")
if st.button("Enter AI Mode"):
    st.info("AI mode coming soon – under development!")

st.markdown("---")

# Upload
st.markdown("## 📥 Optional: Upload Your Pricing & Volume Data")
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
if uploaded_file:
    st.success("File uploaded successfully.")
    st.dataframe(st.read_csv(uploaded_file))
