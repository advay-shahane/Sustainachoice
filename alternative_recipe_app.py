import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import math

import requests
from bs4 import BeautifulSoup
from io import BytesIO
from PIL import Image
from datetime import datetime
import lxml

from email.message import EmailMessage
import ssl
import smtplib

from app_functions import calculate_total_emission_individual, convert_units, baseline_cutoff, evaluate_recipe, find_eligible_category, find_closest_alternative, compare_to_vehicle, calculate_num_trees
from email_sender import email_sender, email_password

st.set_page_config(
    page_title="Alternative Recipe",
    page_icon="🍽️",
    layout="wide"
)

df = pd.read_csv("cleaned_data/ingredients2.csv")
nutrient_df = pd.read_csv("cleaned_data/nutrient_df.csv")
unit_df = pd.read_csv("cleaned_data/unit_conversion.csv")
footprints_df = pd.read_csv("cleaned_data/carbon_footprints.csv")

st.markdown("<h1 style='text-align: center;'>Alternative Recipe</h1>", unsafe_allow_html=True)

image_columns = st.columns(3)
with image_columns[0]:
    st.write("")
with image_columns[1]:
    vegetable_image = Image.open("image/vegetable.png")
    st.image(vegetable_image, width=250)
with image_columns[2]:
    st.write("")

user_df = pd.DataFrame(columns=["Category:", "Ingredient:", "Amount:", "Unit:", "CO2 Emission (Kg):"])

if "df" not in st.session_state:
    st.session_state.df = user_df

if "eval_button" not in st.session_state:
    st.session_state["eval_button"] = False

def google_search_image(query):
    url = 'https://www.google.com/search?q={0}&tbm=isch'.format(query)
    content = requests.get(url).content
    soup = BeautifulSoup(content, 'lxml' )
    images = soup.findAll('img')
    all_image_list = []
    for image in images:
        all_image_list.append(image.get('src'))
    return all_image_list[1]

placeholder = st.empty()

with st.expander("➕ Click to Add Ingredient"):
    ingredient_columns = st.columns([2,3,1,1])
    with ingredient_columns[0]:
        st.session_state["is_expanded"] = True
        selected_category = st.selectbox("Category:", df["FoodGroupName"].unique(), key="input_col1")
    with ingredient_columns[1]:
        df_ingredient = df[df["FoodGroupName"] == st.session_state.input_col1]
        selected_ingredient = st.selectbox("Ingredient:", df_ingredient["FoodDescription"].unique(), key="input_col2")
    with ingredient_columns[2]:
        selected_amount = st.number_input("Amount: ", key="input_col3", step=0.1, min_value=0.0)
        if type(selected_amount) == str:
            st.error("Please enter a numeric value.")
    with ingredient_columns[3]:
        selected_unit = st.selectbox("Unit:", unit_df["from_unit"].unique(), key="input_col4")

    nutrition_tab, metrics_tab = st.tabs(["Nutritional Information", "Summary Metrics"])
    with nutrition_tab:
        st.subheader(f"{selected_ingredient}")
        nutrient_df_selected = nutrient_df[nutrient_df["FoodDescription"] == selected_ingredient].iloc[:, 3:15]
        st.image(google_search_image(selected_ingredient), width=200)
        columns = ["Alcohol", "Caffeine", "Calcium", "Carbohydrate", "Cholesterol", "Copper", "Fats",
                   "Fatty Acids (Polysaturated)", "Fatty Acids (Unsaturated)", "Fibre", "Iron", "Lactose"]
        nutrient_df_selected.columns = columns
        st.write(f"Nutrition Information for 100g of {selected_ingredient}, retrieved from [Statistics Canada](https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/nutrient-data/canadian-nutrient-file-2015-download-files.html).")
        st.table(nutrient_df_selected)

    with metrics_tab:
        st.subheader(f"{selected_ingredient}")
        selected_amount = float(selected_amount)
        try:
            total_emission = calculate_total_emission_individual(selected_ingredient, selected_amount, selected_unit)
            st.session_state["total_emission"] = (total_emission / 1000)
            total_amount = convert_units(selected_amount, selected_unit)
        except:
            total_emission = 0

        tab2_col1, tab2_col2 = st.columns(2)
        with tab2_col1:
            st.metric(label="Total Amount of Food in Kg", value=(total_amount / 1000))
        with tab2_col2:
            st.metric(label="Total CO2 Emission in Kg", value=(total_emission / 1000))

    submit = st.button("Add Ingredient", key="submit_button")
    if submit:
        st.session_state.df.loc[len(st.session_state.df)] = [selected_category, selected_ingredient, selected_amount,
                                                             selected_unit, (total_emission / 1000)]
