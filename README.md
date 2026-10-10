# MealMate — Indian Weekly Meal & Grocery Planner 🍲

MealMate is a beginner-friendly Streamlit web application designed to help everyday Indian households plan 7 days of authentic meals (breakfast, lunch, and dinner) and generate a consolidated, portion-scaled grocery shopping list within a target weekly budget in Indian Rupees (₹).

---

## 🌟 Key Features

1. **Customizable Household Parameters (Sidebar)**:
   - **Household Size**: 1–8 people (portions scale automatically).
   - **Dietary Preference**:
     - *Vegetarian* (pure vegetarian including dairy).
     - *Eggitarian* (vegetarian staples plus egg dishes).
     - *Non-vegetarian* (balanced mix of chicken/fish highlights alongside wholesome veg/egg staples).
   - **Regional Cuisine Preference**:
     - *South Indian* (Idli, Dosa, Sambar, Rasam, Pongal, Chettinad, etc.)
     - *North Indian* (Parathas, Dal Tadka, Rajma, Chole, Paneer, Khichdi, etc.)
     - *Mixed* (balanced pan-Indian menu).
   - **Weekly Grocery Budget**: In INR (₹) with real-time budget tracking and variance indicators.
   - **Regenerate Meal Plan Button**: Re-rolls all 7 days with fresh, curated meal selections.

2. **Clean 7-Day Meal Plan (21 Meals)**:
   - Displays Breakfast 🌅, Lunch ☀️, and Dinner 🌙 for Monday through Sunday.
   - Dietary badges (🟢 Pure Veg, 🟡 Egg, 🔴 Non-Veg).
   - Real ingredients and dish descriptions.
   - **Individual Meal Swapping**: Swap any dish you don't feel like eating with a single click.

3. **Consolidated Grocery Shopping List**:
   - Aggregates ingredients across all 21 meals in the week.
   - Converts and normalizes units into standard Indian market quantities (e.g., kg, g, liters, ml, bunches, packets, pieces).
   - Categorized by shopping aisle (Vegetables & Produce, Grains & Flours, Pulses & Lentils, Dairy & Eggs, Meat & Seafood, Spices & Pantry).
   - **Interactive Checklist**: Mark items as bought directly in the app.
   - **Shopping Progress Tracker**: Visual progress bar showing how many items and how much money has been spent.

4. **Budget & Spend Analytics**:
   - Total estimated grocery cost, remaining budget, and percent utilized.
   - Cost per person per day calculation.
   - Category-wise expenditure breakdown table.
   - Practical household grocery budget optimization tips.

5. **Data Export**:
   - Download consolidated grocery list as **CSV**.
   - Download 7-day meal plan schedule as **CSV**.

6. **Local & Zero-Dependency Architecture**:
   - 100% offline-ready: uses curated local Python datasets.
   - No external APIs, third-party authentication, or paid services required.
   - No database setup needed for version 1.

---

## 📁 Project Structure

```text
mealmate/
├── app.py              # Streamlit frontend user interface & session state
├── planner.py          # Meal planning engine, portion scaling & grocery consolidation
├── recipes_data.py     # Curated Indian recipe catalog & ingredient price benchmark database
├── test_mealmate.py    # Automated test suite (recipe integrity, scaling, consolidation, CSV)
├── requirements.txt    # Application dependencies (Streamlit & Pandas)
└── README.md           # Documentation & setup guide
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.9 or higher (tested on Python 3.12)
- pip

### 1. Set Up Virtual Environment (Optional but Recommended)
```bash
python3 -m venv .venv
source .venv/bin/activate       # On Linux / macOS
# or
.venv\Scripts\activate          # On Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Application
```bash
streamlit run app.py
```
Open your web browser and navigate to `http://localhost:8501`.

---

## 🧪 Running Automated Tests

To run the automated test suite verifying recipe integrity, portion scaling, consolidation, and budget calculations:

```bash
python3 test_mealmate.py
```

Expected output:
```text
ALL COMPREHENSIVE REGRESSION TESTS PASSED SUCCESSFULLY!
```

---

## 🧠 Engineering & Design Details

- **Base Servings**: Each recipe in `recipes_data.py` is defined for a base portion of 2 people. Portion scaling is computed as:
  $$\text{Scaling Factor} = \frac{\text{Household Size}}{2.0}$$
- **Ingredient Aggregation & Unit Consistency**: Common ingredients across meals (e.g., onions, tomatoes, rice, cooking oil, mustard seeds) are aggregated into a single line item with unambiguous dual units (e.g. `0.15 kg (150 g)` @ `₹60/kg = ₹9.00`).
- **Discrete Item Purchasing vs. Recipe Consumption**: Discrete purchasable items sold strictly in whole units at retail markets (such as whole coconuts, eggs, bread packets, and whole cauliflower/lemon heads) calculate a practical purchase quantity using sensible whole-number ceiling rounding (e.g., 8.125 coconuts $\rightarrow$ 9 pcs to buy). Exact recipe quantities and consumption costs are preserved separately, while store checkout costs are modeled explicitly.
- **Weight and Volume Non-Rounding**: Non-discrete items (vegetables sold loose, grains, pulses, dairy, cooking oil, spices, and leafy bunches) are never blindly rounded up, preserving exact market purchasing by weight or volume.
- **Deterministic Pricing**: Prices are benchmarked against standard Indian retail market rates (e.g. Rice: ₹55–₹110/kg, Toor Dal: ₹160/kg, Milk: ₹60/L, Eggs: ₹7/pc, Chicken: ₹240/kg).
- **Excel-Compatible CSV Export**: All CSV exports utilize `UTF-8 with BOM` (`utf-8-sig`) encoding, ensuring that the Indian Rupee symbol (₹) and all special characters render seamlessly in Microsoft Excel without encoding glitches.

---

## ⚠️ Realism & Health Disclaimer

- **Price Estimates**: Grocery prices are deterministic benchmark estimates (in INR ₹) based on urban Indian retail averages. Actual costs vary depending on city, neighborhood vendor rates, brand choices, and seasonal agricultural shifts.
- **Nutritional Notice**: MealMate provides practical homestyle meal suggestions and does not claim clinical nutritional optimization or dietary medical advice.
