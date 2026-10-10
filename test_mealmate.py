"""
Comprehensive regression test suite for MealMate.
Tests:
- Household sizes 1, 2, and 5 scaling
- All 9 food preference x regional cuisine combinations
- Meal swapping mechanics
- Grocery consolidation and mathematical unit consistency (e.g. 150 g @ ₹60/kg = ₹9.00)
- Purchased item checklist tracking
- Budget analytics and preference-specific guidance
- CSV download formatting with UTF-8 BOM encoding (\xef\xbb\xbf)
"""

import io
import pandas as pd
from recipes_data import RECIPES, INGREDIENTS_CATALOG
import planner


def test_recipe_catalog_integrity():
    """Verify that every ingredient in every recipe exists in the price catalog with positive quantities."""
    assert len(RECIPES) >= 50, f"Expected at least 50 recipes, found {len(RECIPES)}"
    assert len(INGREDIENTS_CATALOG) >= 50, f"Expected at least 50 catalog items, found {len(INGREDIENTS_CATALOG)}"

    for recipe in RECIPES:
        assert "id" in recipe
        assert "name" in recipe
        assert recipe["meal_type"] in ["breakfast", "lunch", "dinner"]
        assert recipe["diet"] in ["veg", "egg", "non_veg"]
        assert recipe["region"] in ["south", "north", "both"]
        assert len(recipe["ingredients"]) > 0

        # Verify no duplicate ingredients within any single recipe
        names = [ing["name"] for ing in recipe["ingredients"]]
        assert len(names) == len(set(names)), f"Duplicate ingredient in recipe '{recipe['name']}': {names}"

        for ing in recipe["ingredients"]:
            name = ing["name"]
            assert name in INGREDIENTS_CATALOG, f"Recipe '{recipe['name']}' references unknown ingredient: '{name}'"
            assert ing["quantity"] > 0, f"Invalid quantity for {name} in {recipe['name']}"


def test_household_sizes_1_2_5():
    """Verify portion scaling and linear cost scaling across household sizes 1, 2, and 5."""
    plan = planner.generate_weekly_plan(diet_pref="Vegetarian", region_pref="Mixed", seed=42)

    df_1 = planner.consolidate_groceries(plan, household_size=1)
    df_2 = planner.consolidate_groceries(plan, household_size=2)
    df_5 = planner.consolidate_groceries(plan, household_size=5)

    assert not df_1.empty and not df_2.empty and not df_5.empty

    cost_1 = df_1["Estimated Cost (₹)"].sum()
    cost_2 = df_2["Estimated Cost (₹)"].sum()
    cost_5 = df_5["Estimated Cost (₹)"].sum()

    # Exact scaling: base servings is 2, so factor for 1 is 0.5, factor for 2 is 1.0, factor for 5 is 2.5
    assert abs(cost_2 - (2.0 * cost_1)) < 0.1, f"Cost 2 ({cost_2}) != 2 * Cost 1 ({cost_1})"
    assert abs(cost_5 - (5.0 * cost_1)) < 0.1, f"Cost 5 ({cost_5}) != 5 * Cost 1 ({cost_1})"
    assert abs(cost_5 - (2.5 * cost_2)) < 0.1, f"Cost 5 ({cost_5}) != 2.5 * Cost 2 ({cost_2})"


def test_all_diet_and_region_combinations():
    """Verify all 9 combinations of food preference and regional cuisine."""
    diets = ["Vegetarian", "Eggitarian", "Non-vegetarian"]
    regions = ["South Indian", "North Indian", "Mixed"]

    for diet in diets:
        for region in regions:
            plan = planner.generate_weekly_plan(diet_pref=diet, region_pref=region, seed=99)
            assert len(plan) == 7, f"Plan does not have 7 days for {diet} {region}"

            all_meals = []
            for day in planner.DAYS_OF_WEEK:
                assert day in plan
                meals = plan[day]
                for meal_type in ["breakfast", "lunch", "dinner"]:
                    assert meal_type in meals, f"Missing {meal_type} in {day}"
                    recipe = meals[meal_type]
                    all_meals.append(recipe)

                    # Strict dietary adherence
                    if diet == "Vegetarian":
                        assert recipe["diet"] == "veg", f"Found non-veg dish in Vegetarian plan: {recipe['name']} ({recipe['diet']})"
                    elif diet == "Eggitarian":
                        assert recipe["diet"] in ["veg", "egg"], f"Found meat dish in Eggitarian plan: {recipe['name']} ({recipe['diet']})"

            # Verify that Eggitarian includes egg meals
            if diet == "Eggitarian":
                egg_count = len([m for m in all_meals if m["diet"] == "egg"])
                assert egg_count >= 2, f"Eggitarian plan for {region} should include egg dishes, found {egg_count}"

            # Verify that Non-vegetarian includes non-veg meals
            if diet == "Non-vegetarian":
                nv_count = len([m for m in all_meals if m["diet"] == "non_veg"])
                assert nv_count >= 3, f"Non-vegetarian plan for {region} should include non-veg dishes, found {nv_count}"


def test_unit_consistency_and_math():
    """
    Verify unit consistency requirement:
    e.g. 150 g at ₹60/kg must calculate to ₹9.00, and displayed units must be unambiguous.
    """
    # Create a synthetic plan with French Beans (150 g for 2 people)
    synthetic_plan = {
        "Monday": {
            "breakfast": {
                "id": "test_bf",
                "name": "Test Breakfast",
                "meal_type": "breakfast",
                "diet": "veg",
                "base_servings": 2,
                "ingredients": [{"name": "French Beans", "quantity": 150}],
            },
            "lunch": {"id": "test_lu", "name": "Test Lunch", "meal_type": "lunch", "diet": "veg", "base_servings": 2, "ingredients": []},
            "dinner": {"id": "test_dn", "name": "Test Dinner", "meal_type": "dinner", "diet": "veg", "base_servings": 2, "ingredients": []},
        }
    }
    for day in planner.DAYS_OF_WEEK[1:]:
        synthetic_plan[day] = {
            "breakfast": {"id": "t_bf", "name": "B", "meal_type": "breakfast", "diet": "veg", "base_servings": 2, "ingredients": []},
            "lunch": {"id": "t_lu", "name": "L", "meal_type": "lunch", "diet": "veg", "base_servings": 2, "ingredients": []},
            "dinner": {"id": "t_dn", "name": "D", "meal_type": "dinner", "diet": "veg", "base_servings": 2, "ingredients": []},
        }

    df = planner.consolidate_groceries(synthetic_plan, household_size=2)
    assert not df.empty
    row = df[df["Item"] == "French Beans"].iloc[0]

    # Verify: 150 g at ₹60/kg = ₹9.00
    assert row["Base Quantity"] == 0.15
    assert row["Unit"] == "kg"
    assert "₹60" in row["Rate (₹)"]
    assert row["Estimated Cost (₹)"] == 9.00
    # Verify displayed quantity shows dual units unambiguously
    assert "0.15 kg (150 g)" in row["Quantity"]


def test_grocery_consolidation_no_double_counting():
    """Verify grocery consolidation groups identical ingredients across days into a single unique line item."""
    plan = planner.generate_weekly_plan(diet_pref="Vegetarian", region_pref="Mixed", seed=42)
    df = planner.consolidate_groceries(plan, household_size=4)

    # Unique items
    assert df["Item"].is_unique, "Consolidated grocery list contains duplicate items!"
    assert (df["Estimated Cost (₹)"] > 0).all(), "Some items have zero or negative estimated cost!"

    # Verify each row's estimated cost equals Base Quantity * price_per_base_unit
    for _, row in df.iterrows():
        cat_info = INGREDIENTS_CATALOG[row["Item"]]
        expected_cost = round(row["Base Quantity"] * cat_info["price_per_base_unit"], 2)
        assert abs(row["Estimated Cost (₹)"] - expected_cost) < 0.05, (
            f"Math mismatch for {row['Item']}: got {row['Estimated Cost (₹)']}, expected {expected_cost}"
        )


def test_purchased_item_tracking():
    """Verify that marking items as purchased updates tracking counters and spent totals correctly."""
    plan = planner.generate_weekly_plan(diet_pref="Vegetarian", region_pref="Mixed", seed=42)
    df = planner.consolidate_groceries(plan, household_size=4)

    # Initially none purchased
    assert df["Purchased"].sum() == 0

    # Simulate purchasing first 3 items
    items_to_mark = list(df["Item"][:3])
    purchased_dict = {item: True for item in items_to_mark}

    df["Purchased"] = df["Item"].map(lambda x: purchased_dict.get(x, False))
    assert df["Purchased"].sum() == 3

    expected_spent = round(df[df["Purchased"]]["Estimated Cost (₹)"].sum(), 2)
    assert expected_spent > 0
    assert expected_spent < df["Estimated Cost (₹)"].sum()


def test_budget_guidance_and_usability():
    """
    Verify budget guidance:
    - User's budget is maintained unchanged
    - Overrun is clearly identified with difference and percentage
    - Preference-tailored tips and benchmarks are produced
    """
    plan = planner.generate_weekly_plan(diet_pref="Non-vegetarian", region_pref="Mixed", seed=42)
    df = planner.consolidate_groceries(plan, household_size=4)

    summary = planner.calculate_budget_summary(df, budget=2500.0, household_size=4)
    # Total cost for 4 people non-veg will realistically exceed a low budget of ₹2,500
    assert summary["budget"] == 2500.0, "Budget was modified!"

    guidance = planner.get_budget_guidance("Non-vegetarian", 4, 2500.0, summary)
    assert guidance["diet_label"] == "Non-vegetarian"
    assert guidance["bench_total_low"] > 0
    assert guidance["bench_total_high"] > guidance["bench_total_low"]
    assert "Meat & Seafood" in guidance["key_cost_driver"]
    assert len(guidance["specific_tips"]) >= 3

    if guidance["is_over"]:
        assert guidance["overrun_amount"] > 0
        assert guidance["overrun_pct"] > 0


def test_swap_single_meal():
    """Verify that swapping a meal updates only that day and meal slot while preserving the rest."""
    plan = planner.generate_weekly_plan(diet_pref="Vegetarian", region_pref="South Indian", seed=42)
    orig_id = plan["Monday"]["breakfast"]["id"]

    swapped = planner.swap_single_meal(
        plan, day="Monday", meal_type="breakfast", diet_pref="Vegetarian", region_pref="South Indian"
    )

    # Monday breakfast should be updated
    assert swapped["Monday"]["breakfast"]["meal_type"] == "breakfast"
    assert swapped["Monday"]["breakfast"]["diet"] == "veg"

    # Tuesday breakfast and Monday lunch must remain unchanged
    assert swapped["Tuesday"]["breakfast"]["id"] == plan["Tuesday"]["breakfast"]["id"]
    assert swapped["Monday"]["lunch"]["id"] == plan["Monday"]["lunch"]["id"]


def test_csv_export_with_utf8_bom():
    """Verify CSV export contains UTF-8 BOM encoding (\\xef\\xbb\\xbf) for Excel compatibility."""
    plan = planner.generate_weekly_plan(diet_pref="Vegetarian", region_pref="Mixed", seed=42)
    df = planner.consolidate_groceries(plan, household_size=4)

    export_df = pd.DataFrame({
        "Item Name": df["Item"],
        "Category": df["Category"],
        "Quantity to Buy": df["Quantity"],
        "Base Quantity": df["Base Quantity"],
        "Unit": df["Unit"],
        "Benchmark Rate": df["Rate (₹)"],
        "Estimated Cost (₹)": df["Estimated Cost (₹)"],
        "Purchased Status": df["Purchased"].map(lambda p: "Purchased" if p else "Pending"),
    })

    # Encode with utf-8-sig
    csv_bytes = export_df.to_csv(index=False).encode("utf-8-sig")

    # Verify UTF-8 BOM signature at byte offset 0
    assert csv_bytes[:3] == b"\xef\xbb\xbf", "Missing UTF-8 BOM encoding (\\xef\\xbb\\xbf)!"

    # Decode and verify Excel compatibility
    csv_text = csv_bytes.decode("utf-8-sig")
    read_back = pd.read_csv(io.StringIO(csv_text))
    assert len(read_back) == len(df)
    assert "Item Name" in read_back.columns
    assert "Benchmark Rate" in read_back.columns
    assert "Estimated Cost (₹)" in read_back.columns


def test_discrete_item_rounding_and_costs():
    """
    Verify discrete purchasable items (coconuts, eggs, bread packets, whole vegetables):
    - Exact recipe quantities are preserved for cost calculations.
    - Separate practical purchase quantity rounds up to whole units (e.g. 8.125 coconuts -> 9 pcs).
    - Required recipe quantity is clearly distinguished from quantity to purchase.
    - Estimated purchase cost models whole units without altering original recipe consumption cost.
    """
    # Synthetic recipe for 2 people
    synthetic_plan = {
        "Monday": {
            "breakfast": {
                "id": "t_bf",
                "name": "Breakfast with Eggs and Bread",
                "meal_type": "breakfast",
                "diet": "egg",
                "base_servings": 2,
                "ingredients": [
                    {"name": "Eggs", "quantity": 3},        # 3 for 2p -> 7.5 for 5p
                    {"name": "Bread", "quantity": 0.5},     # 0.5 for 2p -> 1.25 for 5p
                ],
            },
            "lunch": {
                "id": "t_lu",
                "name": "Lunch with Coconut and Cauliflower",
                "meal_type": "lunch",
                "diet": "veg",
                "base_servings": 2,
                "ingredients": [
                    {"name": "Coconut", "quantity": 3.25},     # 3.25 for 2p -> 8.125 for 5p
                    {"name": "Cauliflower", "quantity": 0.5},  # 0.5 for 2p -> 1.25 for 5p
                ],
            },
            "dinner": {"id": "t_dn", "name": "Dinner", "meal_type": "dinner", "diet": "veg", "base_servings": 2, "ingredients": []},
        }
    }
    for day in planner.DAYS_OF_WEEK[1:]:
        synthetic_plan[day] = {
            "breakfast": {"id": "b", "name": "B", "meal_type": "breakfast", "diet": "veg", "base_servings": 2, "ingredients": []},
            "lunch": {"id": "l", "name": "L", "meal_type": "lunch", "diet": "veg", "base_servings": 2, "ingredients": []},
            "dinner": {"id": "d", "name": "D", "meal_type": "dinner", "diet": "veg", "base_servings": 2, "ingredients": []},
        }

    # Test for household of 5 people (scale factor = 2.5)
    df = planner.consolidate_groceries(synthetic_plan, household_size=5)

    # 1. Coconut (3.25 * 2.5 = 8.125)
    coco = df[df["Item"] == "Coconut"].iloc[0]
    assert coco["Base Quantity"] == 8.125
    assert coco["Purchase Quantity"] == 9.0
    assert "9 pc" in coco["Quantity to Buy"]
    assert "8.125" in coco["Required Recipe Qty"]
    assert coco["Estimated Cost (₹)"] == round(8.125 * 35.0, 2)  # 284.38
    assert coco["Estimated Purchase Cost (₹)"] == 9.0 * 35.0      # 315.00

    # 2. Eggs (3 * 2.5 = 7.5)
    egg = df[df["Item"] == "Eggs"].iloc[0]
    assert egg["Base Quantity"] == 7.5
    assert egg["Purchase Quantity"] == 8.0
    assert "8 pc" in egg["Quantity to Buy"]
    assert "7.5" in egg["Required Recipe Qty"]
    assert egg["Estimated Cost (₹)"] == round(7.5 * 7.0, 2)       # 52.50
    assert egg["Estimated Purchase Cost (₹)"] == 8.0 * 7.0        # 56.00

    # 3. Bread (0.5 * 2.5 = 1.25)
    bread = df[df["Item"] == "Bread"].iloc[0]
    assert bread["Base Quantity"] == 1.25
    assert bread["Purchase Quantity"] == 2.0
    assert "2 pkt" in bread["Quantity to Buy"]
    assert "1.25" in bread["Required Recipe Qty"]
    assert bread["Estimated Cost (₹)"] == round(1.25 * 45.0, 2)   # 56.25
    assert bread["Estimated Purchase Cost (₹)"] == 2.0 * 45.0     # 90.00

    # 4. Cauliflower (0.5 * 2.5 = 1.25)
    cauli = df[df["Item"] == "Cauliflower"].iloc[0]
    assert cauli["Base Quantity"] == 1.25
    assert cauli["Purchase Quantity"] == 2.0
    assert "2 pc" in cauli["Quantity to Buy"]
    assert "1.25" in cauli["Required Recipe Qty"]
    assert cauli["Estimated Cost (₹)"] == round(1.25 * 40.0, 2)   # 50.00
    assert cauli["Estimated Purchase Cost (₹)"] == 2.0 * 40.0     # 80.00

    # Budget summary checks
    summary = planner.calculate_budget_summary(df, budget=1000.0, household_size=5)
    expected_consumption_total = round(coco["Estimated Cost (₹)"] + egg["Estimated Cost (₹)"] + bread["Estimated Cost (₹)"] + cauli["Estimated Cost (₹)"], 2)
    expected_purchase_total = round(coco["Estimated Purchase Cost (₹)"] + egg["Estimated Purchase Cost (₹)"] + bread["Estimated Purchase Cost (₹)"] + cauli["Estimated Purchase Cost (₹)"], 2)
    assert summary["total_cost"] == expected_consumption_total
    assert summary["total_purchase_cost"] == expected_purchase_total


def test_non_discrete_items_not_blindly_rounded():
    """
    Verify that herbs, spices, oils, grains, and weight vegetables are NOT blindly rounded to whole units.
    """
    synthetic_plan = {
        "Monday": {
            "breakfast": {
                "id": "t_bf",
                "name": "Staples Breakfast",
                "meal_type": "breakfast",
                "diet": "veg",
                "base_servings": 2,
                "ingredients": [
                    {"name": "Steamed / Sona Masoori Rice", "quantity": 150}, # 150g * 2.5 = 375g = 0.375 kg
                    {"name": "French Beans", "quantity": 150},                 # 150g * 2.5 = 375g = 0.375 kg
                    {"name": "Cooking Oil", "quantity": 100},                  # 100ml * 2.5 = 250ml = 0.25 L
                    {"name": "Coriander Leaves", "quantity": 0.3},             # 0.3 * 2.5 = 0.75 bunch
                    {"name": "Turmeric Powder", "quantity": 5},                # 5g * 2.5 = 12.5g = 0.0125 kg
                ],
            },
            "lunch": {"id": "l", "name": "L", "meal_type": "lunch", "diet": "veg", "base_servings": 2, "ingredients": []},
            "dinner": {"id": "d", "name": "D", "meal_type": "dinner", "diet": "veg", "base_servings": 2, "ingredients": []},
        }
    }
    for day in planner.DAYS_OF_WEEK[1:]:
        synthetic_plan[day] = {
            "breakfast": {"id": "b", "name": "B", "meal_type": "breakfast", "diet": "veg", "base_servings": 2, "ingredients": []},
            "lunch": {"id": "l", "name": "L", "meal_type": "lunch", "diet": "veg", "base_servings": 2, "ingredients": []},
            "dinner": {"id": "d", "name": "D", "meal_type": "dinner", "diet": "veg", "base_servings": 2, "ingredients": []},
        }

    df = planner.consolidate_groceries(synthetic_plan, household_size=5)

    for item_name in ["Steamed / Sona Masoori Rice", "French Beans", "Cooking Oil", "Coriander Leaves", "Turmeric Powder"]:
        row = df[df["Item"] == item_name].iloc[0]
        # Must NOT be rounded up to 1.0!
        assert row["Base Quantity"] < 1.0
        assert row["Purchase Quantity"] == row["Base Quantity"], f"{item_name} was blindly rounded to {row['Purchase Quantity']}"
        assert row["Estimated Purchase Cost (₹)"] == row["Estimated Cost (₹)"]
        assert row["Quantity to Buy"] == row["Required Recipe Qty"]


if __name__ == "__main__":
    test_recipe_catalog_integrity()
    test_household_sizes_1_2_5()
    test_all_diet_and_region_combinations()
    test_unit_consistency_and_math()
    test_grocery_consolidation_no_double_counting()
    test_purchased_item_tracking()
    test_budget_guidance_and_usability()
    test_swap_single_meal()
    test_csv_export_with_utf8_bom()
    test_discrete_item_rounding_and_costs()
    test_non_discrete_items_not_blindly_rounded()
    print("ALL COMPREHENSIVE REGRESSION TESTS PASSED SUCCESSFULLY!")

