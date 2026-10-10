"""
MealMate — Indian Weekly Meal & Grocery Planner
A beginner-friendly Streamlit web application helping Indian households
plan 7 days of authentic meals, scale ingredient portions, and manage
grocery shopping lists within a custom budget.
"""

import math
import random
import streamlit as st
import pandas as pd

from recipes_data import RECIPES, INGREDIENTS_CATALOG
import planner

# --- Page Configuration ---
st.set_page_config(
    page_title="MealMate — Indian Weekly Meal & Grocery Planner",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom Styling for Clean, Mobile-Friendly UI ---
st.markdown(
    """
    <style>
    /* Global accents */
    :root {
        --primary-color: #E65100;
        --secondary-color: #FFF3E0;
    }
    
    /* Header hero styling */
    .hero-container {
        background: linear-gradient(135deg, #FF6F00 0%, #E65100 50%, #BF360C 100%);
        padding: 1.6rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 14px rgba(230, 81, 0, 0.25);
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
        color: #FFFFFF !important;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #FFE0B2;
        margin-top: 0.35rem;
        margin-bottom: 0;
    }

    /* Metric Card Styling */
    .stat-card {
        background: #FFFFFF;
        border: 1px solid #FFE0B2;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        text-align: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }
    .stat-label {
        font-size: 0.85rem;
        color: #666;
        text-transform: uppercase;
        font-weight: 600;
    }
    .stat-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #E65100;
        margin-top: 0.2rem;
    }

    /* Meal card styling */
    .meal-box {
        background: #FFFFFF;
        border-radius: 10px;
        border: 1px solid #F0E6DF;
        padding: 1rem 1.1rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .meal-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.4rem;
    }
    .meal-type-badge {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        padding: 0.2rem 0.55rem;
        border-radius: 6px;
    }
    .badge-breakfast { background-color: #FFF3E0; color: #E65100; }
    .badge-lunch { background-color: #E8F5E9; color: #2E7D32; }
    .badge-dinner { background-color: #EDE7F6; color: #512DA8; }

    .diet-badge-veg { color: #2E7D32; font-weight: 700; font-size: 0.8rem; }
    .diet-badge-egg { color: #F57F17; font-weight: 700; font-size: 0.8rem; }
    .diet-badge-nonveg { color: #C62828; font-weight: 700; font-size: 0.8rem; }

    .dish-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #212121;
        margin: 0.3rem 0;
        line-height: 1.3;
    }
    .dish-desc {
        font-size: 0.85rem;
        color: #616161;
        margin-bottom: 0.6rem;
        line-height: 1.4;
    }

    /* Disclaimer box */
    .disclaimer-box {
        background-color: #F8F9FA;
        border-left: 4px solid #FF9800;
        padding: 0.85rem 1.1rem;
        border-radius: 4px;
        font-size: 0.82rem;
        color: #555555;
        margin-top: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --- Session State Initialization ---
if "seed" not in st.session_state:
    st.session_state.seed = random.randint(1, 999999)

if "purchased_items" not in st.session_state:
    st.session_state.purchased_items = {}

# --- Sidebar Inputs ---
with st.sidebar:
    st.markdown("## ⚙️ Planner Settings")
    st.caption("Customize household preferences & weekly budget")

    # 1. Household Size (1-8)
    household_size = st.number_input(
        "👥 Household Size (People)",
        min_value=1,
        max_value=8,
        value=4,
        step=1,
        help="Ingredient quantities scale automatically based on the number of people.",
    )

    # 2. Food Preference
    food_options = ["Vegetarian", "Eggitarian", "Non-vegetarian"]
    food_pref = st.selectbox(
        "🥗 Food Preference",
        options=food_options,
        index=0,
        help="Vegetarian includes dairy; Eggitarian includes eggs; Non-vegetarian includes chicken & fish.",
    )

    # 3. Regional Cuisine Preference
    region_options = ["Mixed", "South Indian", "North Indian"]
    region_pref = st.selectbox(
        "🗺️ Regional Cuisine",
        options=region_options,
        index=0,
        help="Choose South Indian classics, North Indian staples, or a balanced Mixed menu.",
    )

    # 4. Weekly Budget in INR
    weekly_budget = st.number_input(
        "💰 Weekly Grocery Budget (₹ INR)",
        min_value=500,
        max_value=25000,
        value=3200,
        step=100,
        help="Estimated shopping target in Indian Rupees.",
    )

    st.markdown("---")

    # Regenerate Button
    if st.button("🎲 Regenerate Meal Plan", type="primary", use_container_width=True):
        st.session_state.seed = random.randint(1, 999999)
        st.session_state.purchased_items = {}
        st.rerun()

    # Track preferences to detect change
    pref_key = f"{food_pref}_{region_pref}"
    if "last_pref_key" not in st.session_state:
        st.session_state.last_pref_key = pref_key
    elif st.session_state.last_pref_key != pref_key:
        st.session_state.last_pref_key = pref_key
        st.session_state.seed = random.randint(1, 999999)
        st.session_state.purchased_items = {}
        st.rerun()

    st.markdown("### 📌 Planning Parameters")
    st.markdown(
        f"""
        - **Portion factor:** {household_size / 2.0:.1f}x (base: 2 servings)
        - **Diet:** {food_pref}
        - **Cuisine:** {region_pref}
        - **Budget:** ₹{weekly_budget:,}
        """
    )


# --- Core Meal Plan Generation ---
@st.cache_data
def get_cached_meal_plan(diet: str, region: str, seed: int):
    return planner.generate_weekly_plan(diet_pref=diet, region_pref=region, seed=seed)


# Generate meal plan
raw_plan = get_cached_meal_plan(food_pref, region_pref, st.session_state.seed)

# Make a session copy if not present to enable single meal swaps
if "active_meal_plan" not in st.session_state or st.session_state.get("active_seed") != st.session_state.seed:
    st.session_state.active_meal_plan = {day: dict(meals) for day, meals in raw_plan.items()}
    st.session_state.active_seed = st.session_state.seed

active_plan = st.session_state.active_meal_plan

# Consolidate grocery data and calculate budget
groceries_df = planner.consolidate_groceries(active_plan, household_size=household_size)

# Sync purchased state from session state
if not groceries_df.empty:
    groceries_df["Purchased"] = groceries_df["Item"].map(
        lambda item: st.session_state.purchased_items.get(item, False)
    )

budget_summary = planner.calculate_budget_summary(
    groceries_df, budget=weekly_budget, household_size=household_size
)
budget_guidance = planner.get_budget_guidance(
    diet_pref=food_pref,
    household_size=household_size,
    weekly_budget=weekly_budget,
    budget_summary=budget_summary,
)

# --- Header Hero Banner ---
st.markdown(
    """
    <div class="hero-container">
        <h1 class="hero-title">🥘 MealMate</h1>
        <p class="hero-subtitle">Indian Weekly Meal & Grocery Planner — 7 Days of Authentic Meals Within Your Budget</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Key Metrics Bar ---
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
    st.metric(
        label="Total Estimated Cost",
        value=f"₹{budget_summary['total_cost']:,.2f}",
        delta=f"₹{budget_summary['difference']:+,.2f} vs Budget",
        delta_color="normal" if budget_summary["difference"] >= 0 else "inverse",
    )

with col_m2:
    st.metric(
        label="Weekly Budget",
        value=f"₹{weekly_budget:,.2f}",
    )

with col_m3:
    st.metric(
        label="Budget Status",
        value=f"{budget_summary['percent_used']}% Used",
        delta="Within Budget" if budget_summary["status"] == "within_budget" else "Over Budget",
        delta_color="normal" if budget_summary["status"] == "within_budget" else "inverse",
    )

with col_m4:
    st.metric(
        label="Cost Per Person / Day",
        value=f"₹{budget_summary['cost_per_person_day']:,.1f}",
        help=f"Total cost split across {household_size} members over 7 days (21 meals).",
    )

# Budget Status Callout Banner
if budget_summary["status"] == "within_budget":
    st.success(
        f"**✅ Within Budget!** Estimated grocery cost is **₹{budget_summary['total_cost']:,.2f}**, leaving **₹{budget_summary['difference']:,.2f}** remaining from your weekly budget of **₹{weekly_budget:,.2f}**. (Typical {budget_guidance['diet_label']} benchmark for {household_size} members: ₹{budget_guidance['bench_total_low']:,.0f}–₹{budget_guidance['bench_total_high']:,.0f}/week)."
    )
elif budget_summary["status"] == "warning":
    st.warning(
        f"**⚠️ Slightly Over Budget:** Estimated grocery cost is **₹{budget_summary['total_cost']:,.2f}** (exceeds budget of ₹{weekly_budget:,.2f} by **₹{budget_guidance['overrun_amount']:,.2f}** / **{budget_guidance['overrun_pct']}%**). Primary cost driver: {budget_guidance['key_cost_driver']}. Check the 'Budget & Category Analytics' tab for tailored cost-reduction tips!"
    )
else:
    st.error(
        f"**🚨 Budget Exceeded:** Estimated grocery cost is **₹{budget_summary['total_cost']:,.2f}** (exceeds budget of ₹{weekly_budget:,.2f} by **₹{budget_guidance['overrun_amount']:,.2f}** / **{budget_guidance['overrun_pct']}%**). Primary cost driver: {budget_guidance['key_cost_driver']}. Check the 'Budget & Category Analytics' tab for actionable suggestions to lower your bill without reducing portions."
    )

st.write("")

# --- Navigation Tabs ---
tab_weekly, tab_groceries, tab_budget_analytics, tab_recipes_explorer = st.tabs(
    [
        "📅 Weekly Meal Plan",
        "🛒 Grocery Shopping List",
        "📊 Budget & Category Analytics",
        "📖 Recipe Catalog Explorer",
    ]
)

# Helper function for diet badge
def get_diet_badge(diet_type: str) -> str:
    if diet_type == "veg":
        return "<span class='diet-badge-veg'>🟢 Pure Veg</span>"
    elif diet_type == "egg":
        return "<span class='diet-badge-egg'>🟡 Egg</span>"
    else:
        return "<span class='diet-badge-nonveg'>🔴 Non-Veg</span>"


# ==============================================================================
# TAB 1: WEEKLY MEAL PLAN
# ==============================================================================
with tab_weekly:
    st.markdown("### 🗓️ Seven-Day Menu (Breakfast, Lunch & Dinner)")
    st.caption("Each recipe is automatically portion-scaled for your household. You can swap any individual meal!")

    # Day selection via radio or subtabs for seamless mobile & desktop browsing
    selected_day = st.radio(
        "Select Day to Inspect or Modify:",
        options=["All Days (Overview)"] + planner.DAYS_OF_WEEK,
        horizontal=True,
    )

    st.markdown("---")

    def render_meal_card(day_name: str, meal_type: str, recipe: dict):
        meal_icons = {"breakfast": "🌅 Breakfast", "lunch": "☀️ Lunch", "dinner": "🌙 Dinner"}
        badge_classes = {
            "breakfast": "badge-breakfast",
            "lunch": "badge-lunch",
            "dinner": "badge-dinner",
        }

        # Calculate ingredient preview scaled for household
        portion_scale = household_size / float(recipe.get("base_servings", 2))
        ing_highlights = []
        for ing in recipe.get("ingredients", [])[:4]:
            qty_scaled = ing["quantity"] * portion_scale
            ing_highlights.append(f"{ing['name']} ({qty_scaled:g}{'g' if ing['quantity']>5 else ''})")
        ing_text = ", ".join(ing_highlights) + ("..." if len(recipe.get("ingredients", [])) > 4 else "")

        st.markdown(
            f"""
            <div class="meal-box">
                <div>
                    <div class="meal-header">
                        <span class="meal-type-badge {badge_classes[meal_type]}">{meal_icons[meal_type]}</span>
                        {get_diet_badge(recipe['diet'])}
                    </div>
                    <div class="dish-title">{recipe['name']}</div>
                    <div class="dish-desc">{recipe['description']}</div>
                    <div style="font-size:0.78rem; color:#888; margin-top:0.3rem;">
                        <strong>Key items ({household_size}p):</strong> {ing_text}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Interactive Swap Button
        col_swap, col_exp = st.columns([1, 1.3])
        with col_swap:
            if st.button("🔄 Swap", key=f"swap_{day_name}_{meal_type}", help="Pick another recipe for this slot"):
                st.session_state.active_meal_plan = planner.swap_single_meal(
                    st.session_state.active_meal_plan,
                    day=day_name,
                    meal_type=meal_type,
                    diet_pref=food_pref,
                    region_pref=region_pref,
                )
                st.rerun()

        with col_exp:
            with st.expander("Ingredients"):
                for ing in recipe.get("ingredients", []):
                    q = ing["quantity"] * portion_scale
                    st.write(f"- {ing['name']}: **{q:g}**")

    # Render days
    days_to_show = planner.DAYS_OF_WEEK if selected_day == "All Days (Overview)" else [selected_day]

    for day in days_to_show:
        with st.container():
            st.markdown(f"#### 📆 {day}")
            col1, col2, col3 = st.columns(3)

            with col1:
                render_meal_card(day, "breakfast", active_plan[day]["breakfast"])

            with col2:
                render_meal_card(day, "lunch", active_plan[day]["lunch"])

            with col3:
                render_meal_card(day, "dinner", active_plan[day]["dinner"])

            st.write("")


# ==============================================================================
# TAB 2: GROCERY SHOPPING LIST
# ==============================================================================
with tab_groceries:
    st.markdown("### 🛒 Consolidated Grocery Shopping List")
    st.caption(
        f"Consolidated and scaled for **{household_size} people** across 21 meals. Check off items as you shop in the market!"
    )

    if groceries_df.empty:
        st.info("No grocery items found. Generate a meal plan to populate your shopping list.")
    else:
        # Shopping Progress Tracker
        total_items_count = len(groceries_df)
        purchased_count = int(groceries_df["Purchased"].sum())
        purchased_cost = float(groceries_df[groceries_df["Purchased"]]["Estimated Cost (₹)"].sum())
        progress_val = (purchased_count / total_items_count) if total_items_count > 0 else 0.0

        pcol1, pcol2 = st.columns([2.5, 1.5])
        with pcol1:
            st.progress(progress_val, text=f"Shopping Progress: {purchased_count} of {total_items_count} items purchased")
        with pcol2:
            st.markdown(f"**Purchased:** ₹{purchased_cost:,.2f} / ₹{budget_summary['total_cost']:,.2f}")
            if budget_summary.get("total_purchase_cost", budget_summary["total_cost"]) != budget_summary["total_cost"]:
                st.caption(f"Store Checkout Total (whole packs): **₹{budget_summary['total_purchase_cost']:,.2f}**")

        # Quick Filter by Category
        categories = ["All Categories"] + sorted(list(groceries_df["Category"].unique()))
        selected_cat = st.selectbox("Filter by aisle/category:", categories, index=0)

        display_df = groceries_df.copy()
        if selected_cat != "All Categories":
            display_df = display_df[display_df["Category"] == selected_cat]

        # Interactive Checklist using st.data_editor
        columns_to_show = [
            "Purchased",
            "Item",
            "Category",
            "Quantity to Buy",
            "Required Recipe Qty",
            "Unit",
            "Rate (₹)",
            "Estimated Cost (₹)",
        ]
        edited_df = st.data_editor(
            display_df[columns_to_show],
            column_config={
                "Purchased": st.column_config.CheckboxColumn(
                    "Bought?",
                    help="Mark item as bought",
                    default=False,
                ),
                "Item": st.column_config.TextColumn("Item", width="medium"),
                "Category": st.column_config.TextColumn("Aisle / Category", width="medium"),
                "Quantity to Buy": st.column_config.TextColumn("To Buy (Market)", width="medium", help="Practical whole-unit quantity to purchase at the store"),
                "Required Recipe Qty": st.column_config.TextColumn("Recipe Required", width="medium", help="Exact portion-scaled quantity needed for meals"),
                "Unit": st.column_config.TextColumn("Base Unit", width="small"),
                "Rate (₹)": st.column_config.TextColumn("Benchmark Rate", width="small"),
                "Estimated Cost (₹)": st.column_config.NumberColumn(
                    "Est. Cost (₹)", format="₹ %.2f", width="small", help="Consumption cost calculated from exact recipe requirements"
                ),
            },
            disabled=["Item", "Category", "Quantity to Buy", "Required Recipe Qty", "Unit", "Rate (₹)", "Estimated Cost (₹)"],
            hide_index=True,
            use_container_width=True,
            key=f"grocery_editor_{selected_cat}",
        )

        # Update session state with edited purchases
        for _, row in edited_df.iterrows():
            st.session_state.purchased_items[row["Item"]] = bool(row["Purchased"])

        # Quick Actions: Clear or Check All
        btn_col1, btn_col2, btn_col3 = st.columns([1.2, 1.2, 2.5])
        with btn_col1:
            if st.button("✅ Mark All Bought"):
                for itm in groceries_df["Item"]:
                    st.session_state.purchased_items[itm] = True
                st.rerun()

        with btn_col2:
            if st.button("🔄 Reset Checklist"):
                st.session_state.purchased_items = {}
                st.rerun()

        # CSV Download with UTF-8 BOM encoding for Excel compatibility
        with btn_col3:
            # Prepare export DataFrame
            export_df = pd.DataFrame({
                "Item Name": groceries_df["Item"],
                "Category": groceries_df["Category"],
                "Quantity to Buy": groceries_df["Quantity to Buy"],
                "Required Recipe Qty": groceries_df["Required Recipe Qty"],
                "Purchase Quantity": groceries_df["Purchase Quantity"],
                "Base Quantity": groceries_df["Base Quantity"],
                "Unit": groceries_df["Unit"],
                "Benchmark Rate": groceries_df["Rate (₹)"],
                "Estimated Cost (₹)": groceries_df["Estimated Cost (₹)"],
                "Estimated Purchase Cost (₹)": groceries_df["Estimated Purchase Cost (₹)"],
                "Purchased Status": groceries_df["Purchased"].map(lambda p: "Purchased" if p else "Pending"),
            })
            csv_data = export_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="📥 Download Grocery List as CSV",
                data=csv_data,
                file_name=f"MealMate_Grocery_List_{food_pref}_{household_size}p.csv",
                mime="text/csv",
                use_container_width=True,
            )


# ==============================================================================
# TAB 3: BUDGET & CATEGORY ANALYTICS
# ==============================================================================
with tab_budget_analytics:
    st.markdown("### 📊 Budget Breakdown & Category Distribution")

    col_b1, col_b2 = st.columns([1.2, 1.1])

    with col_b1:
        st.markdown("#### Spend Distribution by Grocery Category")
        cat_data = []
        for cat, amount in budget_summary["category_totals"].items():
            pct = round((amount / budget_summary["total_cost"] * 100.0), 1) if budget_summary["total_cost"] > 0 else 0
            cat_data.append({
                "Category": cat,
                "Estimated Cost (₹)": amount,
                "Share (%)": f"{pct}%",
            })
        cat_df = pd.DataFrame(cat_data).sort_values(by="Estimated Cost (₹)", ascending=False)
        st.dataframe(cat_df, hide_index=True, use_container_width=True)

        if budget_summary.get("total_purchase_cost", budget_summary["total_cost"]) != budget_summary["total_cost"]:
            st.info(
                f"ℹ️ **Recipe Need vs Store Checkout:**\n\n"
                f"- **Exact Recipe Need:** ₹{budget_summary['total_cost']:,.2f}\n"
                f"- **Store Checkout (Whole Packs/Pieces):** ₹{budget_summary['total_purchase_cost']:,.2f} "
                f"(accounts for whole-unit purchases of discrete items like coconuts, eggs, and bread)."
            )

    with col_b2:
        st.markdown(f"#### 💡 Budget Guidance for {budget_guidance['diet_label']}")
        st.caption(f"Benchmark target for {household_size} people: ₹{budget_guidance['bench_total_low']:,.0f} – ₹{budget_guidance['bench_total_high']:,.0f} / week")

        if budget_guidance["is_over"]:
            st.warning(
                f"**Overrun: ₹{budget_guidance['overrun_amount']:,.2f} ({budget_guidance['overrun_pct']}% above your ₹{weekly_budget:,.2f} budget)**\n\n"
                f"**Primary Cost Driver:** {budget_guidance['key_cost_driver']}.\n\n"
                "**Actionable Suggestions to Reduce Cost:**"
            )
        else:
            st.success(
                f"**Within Budget: ₹{budget_guidance['savings_amount']:,.2f} cushion.**\n\n"
                f"Your estimated cost of ₹{budget_summary['total_cost']:,.2f} is comfortably within your entered budget of ₹{weekly_budget:,.2f}.\n\n"
                "**Smart Household Practices:**"
            )

        for tip in budget_guidance["specific_tips"]:
            st.markdown(f"- {tip}")

    st.markdown("---")
    st.markdown("#### Weekly Meal Plan Summary Export")
    # Build text export of the meal plan
    plan_rows = []
    for d in planner.DAYS_OF_WEEK:
        plan_rows.append({
            "Day": d,
            "Breakfast": active_plan[d]["breakfast"]["name"],
            "Lunch": active_plan[d]["lunch"]["name"],
            "Dinner": active_plan[d]["dinner"]["name"],
        })
    plan_df = pd.DataFrame(plan_rows)
    st.dataframe(plan_df, hide_index=True, use_container_width=True)

    st.download_button(
        label="📥 Download 7-Day Meal Plan as CSV",
        data=plan_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"MealMate_7Day_Meal_Plan_{food_pref}.csv",
        mime="text/csv",
    )


# ==============================================================================
# TAB 4: RECIPE CATALOG EXPLORER
# ==============================================================================
with tab_recipes_explorer:
    st.markdown("### 📖 Curated Indian Recipe Catalog")
    st.caption("Browse all curated recipes in the local dataset with authentic ingredients and regional origins.")

    search_query = st.text_input("🔍 Search recipes by name or ingredient:", placeholder="e.g. Paneer, Idli, Dal, Chicken...")

    filtered_catalog = RECIPES
    if search_query:
        sq = search_query.lower().strip()
        filtered_catalog = [
            r for r in RECIPES
            if sq in r["name"].lower()
            or sq in r["description"].lower()
            or any(sq in ing["name"].lower() for ing in r["ingredients"])
        ]

    st.markdown(f"Showing **{len(filtered_catalog)} of {len(RECIPES)}** recipes:")

    for r in filtered_catalog:
        with st.expander(f"{r['name']} ({r['meal_type'].title()} • {r['region'].title()} Indian • {r['diet'].title()})"):
            st.write(r["description"])
            st.markdown("**Ingredients (for 2 servings):**")
            ing_list = [f"{ing['name']}: {ing['quantity']:g}" for ing in r["ingredients"]]
            st.write(", ".join(ing_list))


# --- Mandatory Realism Disclaimer Banner ---
st.markdown(
    """
    <div class="disclaimer-box">
        <strong>⚠️ Estimation Disclaimer:</strong> Grocery prices displayed are deterministic sample estimates based on retail market benchmarks (in Indian Rupees ₹) across urban Indian markets. Actual market prices vary depending on regional availability, seasonal fluctuations, local vendor rates, and brand selections. MealMate is designed as an everyday planning assistant and does not claim clinical or nutritional optimization.
    </div>
    """,
    unsafe_allow_html=True,
)
