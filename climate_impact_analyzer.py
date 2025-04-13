import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Climate Impact Analyzer", layout="centered")

st.title("🌱 Predictive Climate Impact Analyzer")
st.subheader("See how your meal swaps add up over time")

# User inputs
st.sidebar.header("Your Diet Info")

current_emission = st.sidebar.number_input("❌ Current meal CO2 (kg)", min_value=0.0, value=5.0, step=0.1)
new_emission = st.sidebar.number_input("✅ New meal CO2 (kg)", min_value=0.0, value=2.0, step=0.1)
meals_per_week = st.sidebar.slider("🥗 Meals per week you're changing", 1, 21, 7)
weeks_to_project = st.sidebar.slider("📅 Weeks to forecast", 4, 104, 52)

# Calculate CO2 savings
emission_saved_per_meal = current_emission - new_emission
weekly_savings = emission_saved_per_meal * meals_per_week
weeks = np.arange(1, weeks_to_project + 1)
total_savings = weekly_savings * weeks

# Equivalents
trees_offset = total_savings / 21  # 1 tree absorbs ~21kg CO2 per year
flights_offset = total_savings / 250  # 1 short-haul flight ~250kg CO2

# Chart
st.markdown("### 📈 Projected CO2 Savings Over Time")
fig, ax = plt.subplots()
ax.plot(weeks, total_savings, color="green", linewidth=2)
ax.set_xlabel("Weeks")
ax.set_ylabel("Total CO2 Saved (kg)")
ax.set_title("CO2 Reduction Forecast")
ax.grid(True)
st.pyplot(fig)

# Summary
st.markdown("### 🌍 Your Potential Impact")
st.success(f"By changing {meals_per_week} meals per week for {weeks_to_project} weeks:")
st.markdown(f"- You will save **{total_savings[-1]:,.1f} kg** of CO2")
st.markdown(f"- That's like planting **{trees_offset[-1]:,.0f} trees** 🌳")
st.markdown(f"- Or avoiding **{flights_offset[-1]:,.1f} short-haul flights** ✈️")

st.caption("Estimates are approximations. Based on general CO2 equivalents.")

