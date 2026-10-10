"""
Meal planning and grocery consolidation engine for MealMate.
Provides deterministic generation, dietary/regional filtering,
household portion scaling, ingredient aggregation, and budget analytics.
"""

import math
import random
from typing import Dict, List, Any, Optional
import pandas as pd
from recipes_data import RECIPES, INGREDIENTS_CATALOG

DAYS_OF_WEEK = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

MEAL_TYPES = ["breakfast", "lunch", "dinner"]


def filter_recipes(
    meal_type: str,
    diet_pref: str,
    region_pref: str,
    recipes: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Filter recipes matching meal type, dietary preference, and regional preference.
    """
    if recipes is None:
        recipes = RECIPES

    filtered = []
    # Normalize inputs
    diet_pref_lower = diet_pref.lower().strip()
    region_pref_lower = region_pref.lower().strip()

    for r in recipes:
        if r["meal_type"] != meal_type:
            continue

        # Diet matching
        # Vegetarian gets only 'veg'
        # Eggitarian gets 'veg' and 'egg'
        # Non-vegetarian gets 'veg', 'egg', and 'non_veg'
        recipe_diet = r["diet"]
        if "veg" in diet_pref_lower and "non" not in diet_pref_lower and "egg" not in diet_pref_lower:
            if recipe_diet != "veg":
                continue
        elif "egg" in diet_pref_lower:
            if recipe_diet not in ["veg", "egg"]:
                continue
        # Non-vegetarian allows any of veg, egg, non_veg

        # Regional matching
        recipe_region = r.get("region", "both")
        if "south" in region_pref_lower:
            if recipe_region not in ["south", "both"]:
                continue
        elif "north" in region_pref_lower:
            if recipe_region not in ["north", "both"]:
                continue
        # "Mixed" allows all regions

        filtered.append(r)

    return filtered


def generate_weekly_plan(
    diet_pref: str = "Vegetarian",
    region_pref: str = "Mixed",
    seed: Optional[int] = None,
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Generate a 7-day meal plan (breakfast, lunch, dinner) tailored to diet and region.
    Ensures variety without immediate repetitive meals.
    """
    rng = random.Random(seed)

    weekly_plan: Dict[str, Dict[str, Dict[str, Any]]] = {}

    for meal_type in MEAL_TYPES:
        candidates = filter_recipes(meal_type, diet_pref, region_pref)

        if not candidates:
            # Fallback to any valid diet recipe if regional pool is empty
            candidates = filter_recipes(meal_type, diet_pref, "Mixed")

        # Shuffled candidate pool
        shuffled = list(candidates)
        rng.shuffle(shuffled)

        # For Non-vegetarian preference:
        # Balanced realistic household cadence: 2-3 non-veg meals per week,
        # with remaining meals being wholesome veg and egg favorites.
        is_non_veg = "non" in diet_pref.lower()
        is_egg = "egg" in diet_pref.lower()

        if is_non_veg:
            non_veg_pool = [c for c in candidates if c["diet"] == "non_veg"]
            veg_egg_pool = [c for c in candidates if c["diet"] != "non_veg"]
            rng.shuffle(non_veg_pool)
            rng.shuffle(veg_egg_pool)

            selected_for_week = []
            # In lunch/dinner, allocate 2-3 non-veg dishes per week
            if meal_type in ["lunch", "dinner"] and non_veg_pool:
                num_nv = min(len(non_veg_pool), 3 if meal_type == "lunch" else 2)
                nv_choices = non_veg_pool[:num_nv]
                rem_choices = veg_egg_pool[: 7 - len(nv_choices)]
                # If still short, recycle
                combined = nv_choices + rem_choices
                while len(combined) < 7:
                    combined.append(rng.choice(candidates))
                rng.shuffle(combined)
                selected_for_week = combined[:7]
            else:
                # For breakfast, mostly veg & egg with occasional non-veg
                selected_for_week = (shuffled * ((7 // len(shuffled)) + 1))[:7]
        elif is_egg:
            egg_pool = [c for c in candidates if c["diet"] == "egg"]
            veg_pool = [c for c in candidates if c["diet"] == "veg"]
            rng.shuffle(egg_pool)
            rng.shuffle(veg_pool)

            selected_for_week = []
            if egg_pool:
                num_egg = min(len(egg_pool), 2)
                egg_choices = egg_pool[:num_egg]
                veg_choices = (veg_pool * ((7 // len(veg_pool)) + 1))[: 7 - len(egg_choices)] if veg_pool else []
                combined = egg_choices + veg_choices
                while len(combined) < 7:
                    combined.append(rng.choice(candidates))
                rng.shuffle(combined)
                selected_for_week = combined[:7]
            else:
                selected_for_week = (shuffled * ((7 // len(shuffled)) + 1))[:7]
        else:
            # Repeat cycle if fewer than 7 candidates
            selected_for_week = (shuffled * ((7 // len(shuffled)) + 1))[:7]

        # Assign to days
        for i, day in enumerate(DAYS_OF_WEEK):
            if day not in weekly_plan:
                weekly_plan[day] = {}
            weekly_plan[day][meal_type] = selected_for_week[i]

    return weekly_plan


def get_recipe_by_id(recipe_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve recipe object by its unique ID."""
    for r in RECIPES:
        if r["id"] == recipe_id:
            return r
    return None


def swap_single_meal(
    current_plan: Dict[str, Dict[str, Dict[str, Any]]],
    day: str,
    meal_type: str,
    diet_pref: str,
    region_pref: str,
    target_recipe_id: Optional[str] = None,
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Swap a single meal in the weekly plan.
    If target_recipe_id is provided, sets to that recipe.
    Otherwise, picks a random alternative matching current diet and region.
    """
    updated_plan = {d: dict(m) for d, m in current_plan.items()}

    if target_recipe_id:
        target_recipe = get_recipe_by_id(target_recipe_id)
        if target_recipe:
            updated_plan[day][meal_type] = target_recipe
            return updated_plan

    candidates = filter_recipes(meal_type, diet_pref, region_pref)
    current_id = updated_plan[day][meal_type]["id"]
    alternatives = [c for c in candidates if c["id"] != current_id]

    if alternatives:
        updated_plan[day][meal_type] = random.choice(alternatives)
    elif candidates:
        updated_plan[day][meal_type] = candidates[0]

    return updated_plan


def consolidate_groceries(
    meal_plan: Dict[str, Dict[str, Dict[str, Any]]],
    household_size: int = 4,
) -> pd.DataFrame:
    """
    Consolidates ingredients across all meals in the 7-day plan,
    scales quantities based on household size, and calculates estimated costs.
    Ensures unit consistency, unambiguous dual-unit display, and exact price math.
    """
    # Dictionary to aggregate quantities in recipe_unit
    aggregated: Dict[str, float] = {}

    for day in DAYS_OF_WEEK:
        day_meals = meal_plan.get(day, {})
        for meal_type in MEAL_TYPES:
            recipe = day_meals.get(meal_type)
            if not recipe:
                continue

            base_servings = recipe.get("base_servings", 2)
            portion_scale = household_size / float(base_servings)

            for ing in recipe.get("ingredients", []):
                name = ing["name"]
                qty = ing["quantity"] * portion_scale
                aggregated[name] = aggregated.get(name, 0.0) + qty

    # Compile grocery records with pricing and formatted quantities
    records = []
    for item_name, total_recipe_qty in aggregated.items():
        catalog_info = INGREDIENTS_CATALOG.get(item_name)
        if not catalog_info:
            continue

        category = catalog_info["category"]
        base_unit = catalog_info["base_unit"]
        conversion = catalog_info.get("conversion_to_base", 1.0)
        price_per_base = catalog_info["price_per_base_unit"]

        # Base unit quantity (exact recipe consumption requirement)
        base_qty = total_recipe_qty * conversion
        estimated_cost = round(base_qty * price_per_base, 2)

        # Discrete purchasable items: retail stores only sell whole pieces or whole packets
        is_discrete = base_unit in ["piece", "packet"]
        if is_discrete:
            # Practical store purchase quantity uses sensible ceiling rounding
            purchase_base_qty = float(math.ceil(round(base_qty, 3)))
            purchase_cost = round(purchase_base_qty * price_per_base, 2)
        else:
            # Items bought by weight, volume, or bunch: do NOT blindly round up
            purchase_base_qty = round(base_qty, 3)
            purchase_cost = estimated_cost

        # Unambiguous formatted display string distinguishing recipe need from purchase qty
        if base_unit == "kg":
            if base_qty < 1.0:
                required_display = f"{base_qty:.2f} kg ({int(round(total_recipe_qty))} g)"
            else:
                required_display = f"{base_qty:.2f} kg ({int(round(total_recipe_qty)):,} g)"
            purchase_display = required_display
        elif base_unit == "l":
            if base_qty < 1.0:
                required_display = f"{base_qty:.2f} L ({int(round(total_recipe_qty))} ml)"
            else:
                required_display = f"{base_qty:.2f} L ({int(round(total_recipe_qty)):,} ml)"
            purchase_display = required_display
        elif base_unit == "bunch":
            required_display = f"{base_qty:g} bunch{'es' if base_qty != 1 else ''}"
            purchase_display = required_display
        elif base_unit == "piece":
            required_display = f"{base_qty:g} pc{'s' if base_qty != 1 else ''}"
            purchase_display = f"{int(purchase_base_qty)} pc{'s' if purchase_base_qty != 1 else ''}"
        elif base_unit == "packet":
            required_display = f"{base_qty:g} pkt{'s' if base_qty != 1 else ''}"
            purchase_display = f"{int(purchase_base_qty)} pkt{'s' if purchase_base_qty != 1 else ''}"
        else:
            required_display = f"{base_qty:.2f} {base_unit}"
            purchase_display = required_display

        records.append({
            "Purchased": False,
            "Item": item_name,
            "Category": category,
            "Quantity to Buy": purchase_display,
            "Required Recipe Qty": required_display,
            "Quantity": purchase_display,  # backward compatibility
            "Raw Quantity": round(base_qty, 3),  # backward compatibility
            "Base Quantity": round(base_qty, 3),
            "Purchase Quantity": purchase_base_qty,
            "Unit": base_unit,
            "Rate (₹)": f"₹{price_per_base:g}/{base_unit}",
            "Estimated Cost (₹)": estimated_cost,  # exact recipe consumption cost
            "Estimated Purchase Cost (₹)": purchase_cost,  # practical purchase cost
            "Is Discrete": is_discrete,
        })

    df = pd.DataFrame(records)
    if not df.empty:
        # Sort logically by Category and Item
        category_order = {
            "Vegetables & Produce": 1,
            "Grains & Flours": 2,
            "Pulses & Lentils": 3,
            "Dairy & Eggs": 4,
            "Meat & Seafood": 5,
            "Spices & Pantry": 6,
        }
        df["cat_rank"] = df["Category"].map(lambda c: category_order.get(c, 99))
        df = df.sort_values(by=["cat_rank", "Item"]).drop(columns=["cat_rank"]).reset_index(drop=True)

    return df


def calculate_budget_summary(
    groceries_df: pd.DataFrame,
    budget: float,
    household_size: int,
) -> Dict[str, Any]:
    """
    Computes total grocery cost, variance against budget,
    per-person-per-day breakdown, and category distribution.
    Retains exact recipe consumption cost while also computing practical store purchase cost.
    """
    cost_col = "Estimated Cost (₹)" if "Estimated Cost (₹)" in groceries_df.columns else "Estimated Cost (INR)"
    total_cost = float(groceries_df[cost_col].sum()) if not groceries_df.empty and cost_col in groceries_df.columns else 0.0
    total_cost = round(total_cost, 2)
    difference = round(budget - total_cost, 2)
    percent_used = round((total_cost / budget * 100.0), 1) if budget > 0 else 0.0

    # Store purchase cost modeling discrete whole-unit purchasing
    if not groceries_df.empty and "Estimated Purchase Cost (₹)" in groceries_df.columns:
        total_purchase_cost = round(float(groceries_df["Estimated Purchase Cost (₹)"].sum()), 2)
    else:
        total_purchase_cost = total_cost
    purchase_difference = round(budget - total_purchase_cost, 2)

    cost_per_person = round(total_cost / max(1, household_size), 2)
    cost_per_person_day = round(cost_per_person / 7.0, 2)

    if total_cost <= budget:
        status = "within_budget"
        status_message = f"✅ ₹{difference:,.2f} under budget ({percent_used}% utilized)"
    elif total_cost <= budget * 1.10:
        status = "warning"
        status_message = f"⚠️ ₹{abs(difference):,.2f} slightly over budget ({percent_used}% utilized)"
    else:
        status = "exceeded"
        status_message = f"🚨 ₹{abs(difference):,.2f} over budget ({percent_used}% utilized)"

    # Category breakdown
    category_totals = {}
    if not groceries_df.empty and "Category" in groceries_df.columns and cost_col in groceries_df.columns:
        cat_grouped = groceries_df.groupby("Category")[cost_col].sum()
        for cat, val in cat_grouped.items():
            category_totals[cat] = round(float(val), 2)

    return {
        "total_cost": total_cost,
        "total_purchase_cost": total_purchase_cost,
        "budget": budget,
        "difference": difference,
        "purchase_difference": purchase_difference,
        "percent_used": percent_used,
        "status": status,
        "status_message": status_message,
        "cost_per_person": cost_per_person,
        "cost_per_person_day": cost_per_person_day,
        "category_totals": category_totals,
    }


def get_budget_guidance(
    diet_pref: str,
    household_size: int,
    weekly_budget: float,
    budget_summary: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Computes preference-tailored budget guidance, typical benchmark spending ranges,
    detailed overrun analysis, and practical actionable cost-reduction suggestions.
    Maintains the user's input budget unchanged and never silently shrinks quantities.
    """
    diet_lower = diet_pref.lower()

    if "non" in diet_lower:
        bench_low_pp = 750.0
        bench_high_pp = 1050.0
        diet_label = "Non-vegetarian"
        key_cost_driver = "Meat & Seafood (Chicken ₹240/kg, Fish ₹320/kg)"
        specific_tips = [
            "🥩 **Local Butcher vs Supermarket:** Purchasing fresh whole-bird curry cuts from local neighborhood butcher shops is typically 25–35% cheaper than pre-packaged supermarket trays.",
            "🔄 **Strategic Dish Swapping:** Meat and seafood make up 30–40% of non-vegetarian grocery spend. Swapping just 1 non-veg lunch or dinner for an Egg Curry, Rajma, or Dal Tadka saves ~₹180–₹260 for your household.",
            "🗓️ **Reserve for Weekend Specials:** Keep weekday family meals centered on hearty lentils and fresh vegetables, reserving biryanis and specialty meat dishes for weekend meals.",
            "❄️ **Batch Gravy Preparation:** Prepare base onion-tomato-ginger masala paste in bulk and portion it in the freezer to minimize spice and aromatics wastage across meals.",
        ]
    elif "egg" in diet_lower:
        bench_low_pp = 550.0
        bench_high_pp = 780.0
        diet_label = "Eggitarian"
        key_cost_driver = "Eggs, Paneer, and Cooking Oil"
        specific_tips = [
            "🥚 **Crate Purchasing:** Buying eggs by the 30-egg wholesale crate/tray (approx. ₹165–₹180/tray) saves ~₹30–₹45 compared to retail loose purchases at ₹7/egg.",
            "🧀 **Balanced High-Quality Protein:** Eggs provide first-class protein at a fraction of paneer cost (approx. ₹7 per egg vs ₹40 per 100g paneer). Use egg curries to balance dairy expenses.",
            "🌾 **Pair with Whole Grains:** Serve egg bhurji and curries with high-fiber whole wheat rotis or rice to enhance fullness and stretch meal portions naturally.",
            "🛒 **Wholesale Lentils:** Stock up on Moong, Chana, and Toor dal in monthly 5kg bags to capture 15% bulk discounts.",
        ]
    else:
        bench_low_pp = 500.0
        bench_high_pp = 700.0
        diet_label = "Vegetarian"
        key_cost_driver = "Dairy (Paneer, Ghee, Butter) and Fresh Vegetables"
        specific_tips = [
            "🥛 **Home-Set Curd:** Setting curd at home from fresh milk saves nearly 50% compared to buying branded packaged curd tubs weekly.",
            "🫘 **Power of Legumes:** Alternate paneer dishes with high-protein legumes like Rajma, Chole, and Kala Chana. Legumes cost ~₹140/kg compared to Paneer at ₹400/kg.",
            "🥬 **Seasonal Local Greens:** Buy seasonal vegetables and greens (palak, methi, gourds) from neighborhood weekly vegetable mandis rather than premium off-season imports.",
            "📦 **Staples in Bulk:** Purchase Atta (Wheat Flour) and Rice in 10kg bags, and cooking oil in 5L cans to lower unit costs by up to 20%.",
        ]

    bench_total_low = round(bench_low_pp * household_size, 2)
    bench_total_high = round(bench_high_pp * household_size, 2)

    total_cost = budget_summary.get("total_cost", 0.0)
    difference = round(weekly_budget - total_cost, 2)
    is_over = total_cost > weekly_budget
    overrun_amount = abs(difference) if is_over else 0.0
    overrun_pct = round((overrun_amount / weekly_budget * 100.0), 1) if weekly_budget > 0 else 0.0

    return {
        "diet_label": diet_label,
        "bench_low_pp": bench_low_pp,
        "bench_high_pp": bench_high_pp,
        "bench_total_low": bench_total_low,
        "bench_total_high": bench_total_high,
        "key_cost_driver": key_cost_driver,
        "is_over": is_over,
        "overrun_amount": overrun_amount,
        "overrun_pct": overrun_pct,
        "savings_amount": difference if not is_over else 0.0,
        "specific_tips": specific_tips,
    }

