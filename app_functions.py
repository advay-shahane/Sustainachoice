import pandas as pd
import numpy as np

df = pd.read_csv("cleaned_data/ingredients2.csv")
nutrient_df = pd.read_csv("cleaned_data/nutrient_df.csv")
unit_df = pd.read_csv("cleaned_data/unit_conversion.csv")
footprints_df = pd.read_csv("cleaned_data/carbon_footprints.csv")

baseline_cutoff = ((((31368 * 1000000000) + (12577 * 1000000000)) / (15.3 * 1000000)) / 365 / 3) / 1000
vehicle_base = 650 / 1000
tree_cutoff = 68.5 / 1000

def convert_units(amount, from_unit) -> float:
    factor = unit_df[unit_df["from_unit"] == from_unit]["conversion_factor"].values[0]
    return amount * factor

def calculate_total_emission_individual(food_description, food_amount, food_unit):
    total_amount = convert_units(food_amount, food_unit)

    match = df[df["FoodDescription"].str.lower().str.strip() == food_description.lower().strip()]
    if match.empty:
        print(f"[⚠️ ERROR] Emission data not found for '{food_description}'")
        return 0.0

    food_emission = match["CO2 Emission per Kg"].values[0]
    print(food_emission)

    if pd.isna(food_emission):
        print(f"[⚠️ ERROR] Emission value is NaN for '{food_description}'")
        return 0.0

    print(f"[DEBUG] Emission for '{food_description}': {food_emission} kg/kg")

    return total_amount * food_emission

def create_ghg_label(label, baseline):
    if label > baseline:
        return "High Impact"
    elif (label <= baseline) & (label > (baseline * 0.5)):
        return "Medium Impact"
    elif label <= (baseline * 0.5):
        return "Low Impact"

def evaluate_recipe(df):
    total_emission_recipe = df["CO2 Emission (Kg):"].sum()
    label = create_ghg_label(total_emission_recipe, baseline_cutoff)
    return total_emission_recipe, label

map_category = {"Dairy and Egg Products": "Dairy Products",
                "Spices and Herbs": "Species",
                "Fats and Oils": "Oils",
                "Poultry Products": "Poultry Meat",
                "Soups, Sauces and Gravies": "Sauces",
                "Sausages and Luncheon meats": "Pig Meat",
                "Breakfast cereals": "Cereals",
                "Fruits and fruit juices": "Fruits",
                "Pork Products": "Pig Meat",
                "Vegetables and Vegetable Products": "Other Vegetables",
                "Nuts and Seeds": "Nuts",
                "Beef Products": "Beef (dairy herd)",
                "Finfish and Shellfish Products": "Fish (farmed)",
                "Legumes and Legume Products": "Legumes",
                "Lamb, Veal and Game": "Lamb & Mutton",
                "Baked Products": "Wheat & Rye",
                "Sweets": "Sweets",
                "Beverages": "Beverages",
                "Cereals, Grains and Pasta": "Cereals"}

def category_mapper(category, emission_df, map_category):
    mapped_category = map_category[category]
    emission_factor = emission_df.loc[emission_df["Entity"] == mapped_category]["GHG emissions per kilogram"].values[0]
    return emission_factor

def find_eligible_category(df, footprints_df, food):
    try:
        food_emission_value = df[df["FoodDescription"] == food]["CO2 Emission per Kg"].values[0]
        footprints_list = footprints_df[footprints_df["GHG emissions per kilogram"] == food_emission_value]
        filtered_footprints_list = footprints_df[footprints_df["GHG emissions per kilogram"] < food_emission_value][
            "Entity"].tolist()
        all_value_list = map_category.values()
        filtered_list = [category for category in filtered_footprints_list if category in all_value_list]
        filtered_list_keys = [k for k, v in map_category.items() if v in filtered_list]
    except:
        pass
    return filtered_list_keys

def calculate_num_trees(total_emission):
    tree_num = total_emission / tree_cutoff
    return tree_num

def find_closest_alternative(df, footprints_df, category, food, within_category_attempt):
    filtered_list = find_eligible_category(df, footprints_df, food)

    food_row = nutrient_df[nutrient_df["FoodDescription"] == food]
    if food_row.empty:
        print(f"Food '{food}' not found in the nutrient data.")
        return None

    # Extract nutrient values from the row
    alcohol = food_row["ALCOHOL"].values[0]
    caffeine = food_row["CAFFEINE"].values[0]
    calcium = food_row["CALCIUM"].values[0]
    carbohydrate = food_row["CARBOHYDRATE, TOTAL (BY DIFFERENCE)"].values[0]
    cholesterol = food_row["CHOLESTEROL"].values[0]
    lipid = food_row["FAT (TOTAL LIPIDS)"].values[0]
    poly_acid = food_row["FATTY ACIDS, POLYUNSATURATED, TOTAL"].values[0]
    saturated_acid = food_row["FATTY ACIDS, SATURATED, TOTAL"].values[0]
    iron = food_row["IRON"].values[0]
    lactose = food_row["LACTOSE"].values[0]

    # Make sure the 'Error Value' column is initialized before use
    nutrient_df["Error Value"] = 0.0

    def compute_ols(alcohol, caffeine, calcium, carbohydrate, cholesterol, lipid, poly_acid, saturated_acid, iron,
                    lactose, nutrient_df):
        # Always work with a copy to avoid SettingWithCopyWarning
        nutrient_df = nutrient_df[nutrient_df["FoodGroupName"] == category].copy()

        for ind, row in nutrient_df.iterrows():
            alcohol_error = (row["ALCOHOL"] - alcohol) ** 2
            caffeine_error = (row["CAFFEINE"] - caffeine) ** 2
            calcium_error = (row["CALCIUM"] - calcium) ** 2
            carbohydate_error = (row["CARBOHYDRATE, TOTAL (BY DIFFERENCE)"] - carbohydrate) ** 2
            cholesterol_error = (row["CHOLESTEROL"] - cholesterol) ** 2
            lipid_error = (row["FAT (TOTAL LIPIDS)"] - lipid) ** 2
            poly_acid_error = (row["FATTY ACIDS, POLYUNSATURATED, TOTAL"] - poly_acid) ** 2
            saturated_acid_error = (row["FATTY ACIDS, SATURATED, TOTAL"] - saturated_acid) ** 2
            iron_error = (row["IRON"] - iron) ** 2
            lactose_error = (row["LACTOSE"] - lactose) ** 2

            all_error = (
                    alcohol_error + caffeine_error + calcium_error + carbohydate_error +
                    cholesterol_error + lipid_error + poly_acid_error +
                    saturated_acid_error + iron_error + lactose_error
            )

            # Safely set the 'Error Value' on the copy
            nutrient_df.at[ind, "Error Value"] = all_error

        # Sort the DataFrame by 'Error Value' to find the best match
        min_error_df = nutrient_df.sort_values(by=["Error Value"], ascending=True)

        try:
            best_alternative = min_error_df.iloc[within_category_attempt]["FoodDescription"]
            best_alternative_emission = df[df["FoodDescription"] == best_alternative]["CO2 Emission per Kg"].values[0]
            original_food_emission = df[df["FoodDescription"] == food]["CO2 Emission per Kg"].values[0]

            # Check if the alternative can replace the original
            if best_alternative_emission < original_food_emission:
                print(f"Alternative: {best_alternative} can replace {food} with a lower emission!")

                # Update the original DataFrame with the alternative
                df.loc[df["FoodDescription"] == food, "FoodDescription"] = best_alternative
                df.loc[df["FoodDescription"] == best_alternative, "CO2 Emission per Kg"] = best_alternative_emission

                # You can also update any other columns in the DataFrame (e.g., Amount, Category) if needed
                # df.loc[df["FoodDescription"] == best_alternative, "Amount:"] = some_new_value
                return best_alternative
            else:
                print(f"Alternative: {best_alternative} cannot replace {food} with a lower emission.")
                return None
        except IndexError:
            print("No returning value!")
            return None

    return compute_ols(alcohol, caffeine, calcium, carbohydrate, cholesterol, lipid, poly_acid, saturated_acid,
                       iron, lactose, nutrient_df)

def compare_to_vehicle(kg):
    total_mile_travelled = kg / vehicle_base
    return total_mile_travelled

if __name__ == '__main__':
    result = find_closest_alternative(df, footprints_df, "Nuts and Seeds", "Pork, back ribs, lean and fat, raw", 0)
    print(result)
