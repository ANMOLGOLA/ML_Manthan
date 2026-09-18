import streamlit as st
import pandas as pd
import joblib

st.set_page_config(page_title="Loan Verification Dashboard", layout="wide")

st.title("🏦 Financial Document Consistency & Audit Dashboard")
st.markdown("Automated Mismatch & Fraud Risk Detection Engine")

# Load Audit Summary
try:
    df = pd.read_csv("reports/audit_summary.csv")

    # Top Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Cases Audited", len(df))
    m2.metric("Consistent Cases", len(df[df["Predicted Status"] == "CONSISTENT"]))
    m3.metric("Flagged Mismatches", len(df[df["Predicted Status"] != "CONSISTENT"]))
    m4.metric("Data Quality Alerts", len(df[df["Predicted Status"] == "DATA_QUALITY_ISSUE"]))

    st.markdown("---")

    # Data Table View
    st.subheader("📋 Case Audit Summary")
    st.dataframe(df, use_container_width=True)

    # Distribution Plot
    st.subheader("📊 Mismatch Category Distribution")
    status_counts = df["Predicted Status"].value_counts()
    st.bar_chart(status_counts)

except Exception as e:
    st.error("Audit summary file not found. Please run 'python src/audit_pipeline.py' first.")