"""
NutriTrack Database Module
Handles SQLite database initialization, food seeding, snack catalog, delivery orders, and all CRUD operations.
"""

import sqlite3
import os
import shutil
import random
import tempfile
from datetime import datetime, date

def _is_serverless_env():
    """Detect if running in Vercel, AWS Lambda, or a read-only serverless filesystem."""
    serverless_vars = (
        "VERCEL", "VERCEL_ENV", "VERCEL_URL", "VERCEL_REGION",
        "AWS_LAMBDA_FUNCTION_NAME", "AWS_EXECUTION_ENV", "LAMBDA_TASK_ROOT"
    )
    if any(k in os.environ for k in serverless_vars):
        return True
    try:
        test_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".write_test")
        with open(test_path, "w") as f:
            f.write("1")
        os.remove(test_path)
        return False
    except Exception:
        return True

# On Vercel / serverless platforms, root filesystem is read-only. Use temp directory for writable SQLite db.
if _is_serverless_env():
    temp_dir = tempfile.gettempdir()
    DB_PATH = os.path.join(temp_dir, "nutritrack.db")
    bundled_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nutritrack.db")
    if not os.path.exists(DB_PATH) and os.path.exists(bundled_db):
        try:
            shutil.copy2(bundled_db, DB_PATH)
        except Exception:
            pass
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nutritrack.db")


def get_db_connection():
    """Returns a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes database tables, migrations, delivery schema, and seeds standard nutrition data."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. User Profile Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL DEFAULT 'User',
            age INTEGER NOT NULL DEFAULT 25,
            gender TEXT NOT NULL DEFAULT 'male',
            height_cm REAL NOT NULL DEFAULT 175.0,
            weight_kg REAL NOT NULL DEFAULT 70.0,
            activity_level TEXT NOT NULL DEFAULT 'moderately_active',
            goal TEXT NOT NULL DEFAULT 'maintenance',
            diet_preference TEXT NOT NULL DEFAULT 'all',
            daily_calorie_target REAL NOT NULL DEFAULT 2000.0,
            daily_protein_target REAL NOT NULL DEFAULT 120.0,
            daily_carb_target REAL NOT NULL DEFAULT 250.0,
            daily_fat_target REAL NOT NULL DEFAULT 60.0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Nutrition Database Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS foods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            serving_size REAL NOT NULL DEFAULT 100.0,
            serving_unit TEXT NOT NULL DEFAULT 'g',
            calories REAL NOT NULL,
            protein REAL NOT NULL,
            carbs REAL NOT NULL,
            fat REAL NOT NULL,
            fiber REAL NOT NULL DEFAULT 0.0,
            diet_type TEXT NOT NULL DEFAULT 'all',
            image_url TEXT,
            is_snack INTEGER DEFAULT 0,
            price REAL DEFAULT 99.0
        )
    """)

    # Migration check for existing tables without new columns
    cursor.execute("PRAGMA table_info(foods)")
    existing_cols = [row["name"] for row in cursor.fetchall()]
    if "image_url" not in existing_cols:
        cursor.execute("ALTER TABLE foods ADD COLUMN image_url TEXT")
    if "is_snack" not in existing_cols:
        cursor.execute("ALTER TABLE foods ADD COLUMN is_snack INTEGER DEFAULT 0")
    if "price" not in existing_cols:
        cursor.execute("ALTER TABLE foods ADD COLUMN price REAL DEFAULT 99.0")

    # 3. Meal Logs Table (Daily Diary)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meal_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 1,
            meal_date TEXT NOT NULL,
            meal_type TEXT NOT NULL,
            food_name TEXT NOT NULL,
            quantity REAL NOT NULL DEFAULT 1.0,
            unit TEXT NOT NULL DEFAULT 'serving',
            calories REAL NOT NULL,
            protein REAL NOT NULL,
            carbs REAL NOT NULL,
            fat REAL NOT NULL,
            image_path TEXT,
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 4. Delivery Orders Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL DEFAULT 1,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            delivery_address TEXT NOT NULL,
            delivery_slot TEXT NOT NULL,
            payment_method TEXT NOT NULL DEFAULT 'Cash on Delivery',
            subtotal REAL NOT NULL,
            delivery_fee REAL NOT NULL DEFAULT 30.0,
            total_price REAL NOT NULL,
            total_calories REAL NOT NULL DEFAULT 0.0,
            total_protein REAL NOT NULL DEFAULT 0.0,
            total_carbs REAL NOT NULL DEFAULT 0.0,
            total_fat REAL NOT NULL DEFAULT 0.0,
            status TEXT NOT NULL DEFAULT 'Confirmed',
            rider_name TEXT DEFAULT 'Rahul Sharma',
            rider_phone TEXT DEFAULT '+91 98765 43210',
            estimated_delivery_time TEXT DEFAULT '30-40 mins',
            auto_logged INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 5. Order Items Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            food_id INTEGER,
            food_name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity REAL NOT NULL DEFAULT 1.0,
            calories REAL NOT NULL,
            protein REAL NOT NULL,
            carbs REAL NOT NULL,
            fat REAL NOT NULL,
            image_url TEXT,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
        )
    """)

    conn.commit()

    # Seed Default Profile if empty
    cursor.execute("SELECT COUNT(*) FROM user_profile")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO user_profile (
                name, age, gender, height_cm, weight_kg,
                activity_level, goal, diet_preference,
                daily_calorie_target, daily_protein_target,
                daily_carb_target, daily_fat_target
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Alex", 25, "male", 175.0, 70.0,
            "moderately_active", "maintenance", "all",
            2200.0, 130.0, 260.0, 65.0
        ))
        conn.commit()

    # Comprehensive Catalog of Meals, Dinner Specials, Staples & Fruits with medium prices & proper SVGs
    base_foods = [
        # --- Dinner Specials (Vegetarian) ---
        ("Palak Paneer", "Dinner / Dishes", 1, "bowl (200g)", 280.0, 14.0, 10.0, 20.0, 4.2, "vegetarian", "/static/images/meals/palak_paneer.svg", 0, 140.0),
        ("Dal Makhani", "Dinner / Dishes", 1, "bowl (200g)", 310.0, 11.0, 32.0, 15.0, 6.5, "vegetarian", "/static/images/meals/dal_makhani.svg", 0, 125.0),
        ("Paneer Butter Masala", "Dinner / Dishes", 1, "bowl (200g)", 340.0, 12.0, 14.0, 26.0, 2.5, "vegetarian", "/static/images/meals/paneer_butter_masala.svg", 0, 145.0),
        ("Moong Dal Khichdi", "Dinner / Dishes", 1, "bowl (250g)", 220.0, 8.5, 39.0, 3.5, 4.0, "vegetarian", "/static/images/meals/khichdi.svg", 0, 85.0),
        ("Methi Thepla (3 pcs)", "Dinner / Grains", 3, "pieces (90g)", 215.0, 6.0, 35.0, 5.5, 3.8, "vegetarian", "/static/images/meals/methi_thepla.svg", 0, 45.0),
        ("Tandoori Roti Basket (3 pcs)", "Dinner / Grains", 3, "pieces (90g)", 210.0, 6.5, 42.0, 1.5, 4.5, "vegetarian", "/static/images/meals/tandoori_roti.svg", 0, 35.0),
        ("Veg Biryani", "Dinner / Dishes", 1, "plate (250g)", 320.0, 6.5, 52.0, 9.5, 4.5, "vegetarian", "/static/images/meals/veg_biryani.svg", 0, 130.0),
        ("Vegetable Pulao", "Dinner / Dishes", 1, "plate (250g)", 310.0, 6.0, 50.0, 9.0, 4.0, "vegetarian", "/static/images/meals/veg_pulao.svg", 0, 110.0),
        ("Curd Rice", "Dinner / Dishes", 1, "bowl (200g)", 190.0, 5.0, 30.0, 5.5, 1.2, "vegetarian", "/static/images/meals/curd_rice.svg", 0, 70.0),
        ("Dal Rice", "Dinner / Dishes", 1, "plate (250g)", 260.0, 9.0, 48.0, 3.5, 4.0, "vegetarian", "/static/images/meals/dal_rice.svg", 0, 80.0),
        ("Idli (2 pcs)", "Breakfast / Meals", 2, "pieces (100g)", 130.0, 4.0, 26.0, 0.6, 1.8, "vegetarian", "/static/images/meals/idli.svg", 0, 40.0),
        ("Masala Dosa", "Breakfast / Meals", 1, "dosa (150g)", 250.0, 5.0, 36.0, 9.0, 2.5, "vegetarian", "/static/images/meals/dosa.svg", 0, 60.0),
        ("Chapati (2 pcs)", "Grains", 2, "pieces (80g)", 208.0, 6.2, 40.0, 1.6, 6.0, "vegetarian", "/static/images/meals/chapati.svg", 0, 25.0),

        # --- Dinner Specials (Non-Vegetarian) ---
        ("Butter Chicken", "Dinner / Dishes", 1, "bowl (220g)", 390.0, 28.0, 12.0, 25.0, 1.5, "non-veg", "/static/images/meals/butter_chicken.svg", 0, 165.0),
        ("Chicken Korma", "Dinner / Dishes", 1, "bowl (200g)", 350.0, 26.0, 11.0, 22.0, 1.8, "non-veg", "/static/images/meals/chicken_korma.svg", 0, 155.0),
        ("Chicken Biryani", "Dinner / Dishes", 1, "plate (300g)", 420.0, 28.0, 46.0, 13.0, 2.5, "non-veg", "/static/images/meals/chicken_biryani.svg", 0, 160.0),
        ("Chicken Curry", "Dinner / Dishes", 1, "bowl (200g)", 290.0, 26.0, 9.0, 16.0, 1.5, "non-veg", "/static/images/meals/chicken_curry.svg", 0, 140.0),
        ("Chicken Rice", "Dinner / Dishes", 1, "plate (280g)", 360.0, 25.0, 44.0, 9.0, 2.0, "non-veg", "/static/images/meals/chicken_rice.svg", 0, 130.0),
        ("Egg Curry", "Dinner / Dishes", 1, "bowl (180g)", 230.0, 14.0, 8.0, 15.0, 1.0, "non-veg", "/static/images/meals/egg_curry.svg", 0, 95.0),
        ("Egg Fried Rice", "Dinner / Dishes", 1, "plate (250g)", 330.0, 13.0, 45.0, 11.0, 1.8, "non-veg", "/static/images/meals/egg_fried_rice.svg", 0, 110.0),
        ("Fish Curry", "Dinner / Dishes", 1, "bowl (200g)", 260.0, 24.0, 7.0, 14.0, 1.0, "non-veg", "/static/images/meals/fish_curry.svg", 0, 150.0),
        ("Grilled Fish with Steamed Veggies", "Dinner / Dishes", 1, "plate (250g)", 275.0, 31.0, 8.0, 12.0, 3.5, "non-veg", "/static/images/meals/grilled_fish_veggies.svg", 0, 175.0),

        # --- Base Nutrition Staples & Proteins ---
        ("Boiled Egg (Single)", "Protein", 1, "egg (50g)", 78.0, 6.3, 0.6, 5.3, 0.0, "all", "/static/images/meals/boiled_eggs.svg", 0, 15.0),
        ("Scrambled Eggs (2 eggs)", "Protein", 1, "plate (120g)", 182.0, 12.0, 1.8, 14.0, 0.0, "all", "/static/images/meals/scrambled_eggs.svg", 0, 50.0),
        ("Grilled Chicken Breast", "Protein", 100, "g", 165.0, 31.0, 0.0, 3.6, 0.0, "all", "/static/images/meals/grilled_chicken_breast.svg", 0, 135.0),
        ("Salmon Fillet", "Protein", 100, "g", 208.0, 20.0, 0.0, 13.0, 0.0, "all", "/static/images/meals/salmon_fillet.svg", 0, 190.0),
        ("Tofu (Firm)", "Protein", 100, "g", 83.0, 10.0, 2.0, 5.0, 1.0, "vegan", "/static/images/meals/tofu.svg", 0, 70.0),
        ("Paneer (Cottage Cheese)", "Protein", 100, "g", 265.0, 18.0, 3.5, 20.8, 0.0, "vegetarian", "/static/images/meals/paneer.svg", 0, 85.0),
        ("Dal / Yellow Lentil Curry", "Dishes", 1, "bowl (150g)", 140.0, 9.0, 20.0, 3.0, 4.0, "vegan", "/static/images/meals/dal_curry.svg", 0, 70.0),
        ("Cooked White Rice", "Grains", 1, "bowl (150g)", 195.0, 4.0, 42.0, 0.5, 0.6, "vegan", "/static/images/meals/white_rice.svg", 0, 45.0),
        ("Cooked Brown Rice", "Grains", 1, "bowl (150g)", 168.0, 3.8, 35.0, 1.4, 2.8, "vegan", "/static/images/meals/brown_rice.svg", 0, 55.0),
        ("Roti / Chapati", "Grains", 1, "piece (40g)", 104.0, 3.1, 20.0, 0.8, 3.0, "vegan", "/static/images/meals/chapati.svg", 0, 15.0),
        ("Whole Wheat Bread", "Grains", 1, "slice (35g)", 80.0, 4.0, 14.0, 1.0, 2.0, "vegan", "/static/images/meals/whole_wheat_bread.svg", 0, 15.0),
        ("Rolled Oatmeal (Cooked)", "Grains", 1, "bowl (200g)", 150.0, 5.0, 27.0, 2.5, 4.0, "vegan", "/static/images/meals/oatmeal.svg", 0, 55.0),
        ("Apple", "Fruits", 1, "medium (180g)", 95.0, 0.5, 25.0, 0.3, 4.4, "vegan", "/static/images/meals/apple.svg", 0, 25.0),
        ("Banana", "Fruits", 1, "medium (120g)", 105.0, 1.3, 27.0, 0.3, 3.1, "vegan", "/static/images/meals/banana.svg", 0, 15.0),
        ("Orange", "Fruits", 1, "medium (130g)", 62.0, 1.2, 15.4, 0.2, 3.1, "vegan", "/static/images/meals/orange.svg", 0, 20.0),
        ("Mixed Green Salad", "Vegetables", 1, "bowl (150g)", 45.0, 2.0, 8.0, 0.5, 3.0, "vegan", "/static/images/meals/salad.svg", 0, 50.0),
        ("Steamed Broccoli", "Vegetables", 1, "cup (100g)", 35.0, 2.8, 7.0, 0.4, 2.6, "vegan", "/static/images/meals/steamed_broccoli.svg", 0, 60.0),
        ("Greek Yogurt (Plain)", "Dairy", 1, "cup (150g)", 100.0, 15.0, 6.0, 0.5, 0.0, "vegetarian", "/static/images/meals/greek_yogurt.svg", 0, 45.0),
        ("Cow Milk (Whole)", "Dairy", 1, "glass (240ml)", 149.0, 8.0, 12.0, 8.0, 0.0, "vegetarian", "/static/images/meals/milk.svg", 0, 25.0),
        ("Almonds (Raw)", "Snacks", 1, "handful (28g)", 164.0, 6.0, 6.0, 14.0, 3.5, "vegan", "/static/images/snacks/roasted_peanuts.svg", 0, 45.0),
        ("Peanut Butter", "Snacks", 2, "tbsp (32g)", 188.0, 8.0, 7.0, 16.0, 2.0, "vegan", "/static/images/meals/peanut_butter.svg", 0, 35.0),
        ("Avocado", "Fruits", 1, "half (100g)", 160.0, 2.0, 8.5, 14.7, 6.7, "vegan", "/static/images/meals/avocado.svg", 0, 65.0),
        ("Pasta with Tomato Sauce", "Dishes", 1, "plate (250g)", 280.0, 8.0, 50.0, 4.5, 3.5, "vegan", "/static/images/meals/pasta.svg", 0, 95.0),
        ("Whey Protein Shake", "Protein", 1, "scoop with water", 120.0, 24.0, 2.0, 1.5, 0.0, "vegetarian", "/static/images/meals/protein_shake.svg", 0, 90.0),
    ]

    for item in base_foods:
        cursor.execute("SELECT id FROM foods WHERE LOWER(name) = LOWER(?)", (item[0],))
        exist = cursor.fetchone()
        if exist:
            cursor.execute("""
                UPDATE foods SET
                    category = ?,
                    serving_size = ?,
                    serving_unit = ?,
                    calories = ?,
                    protein = ?,
                    carbs = ?,
                    fat = ?,
                    fiber = ?,
                    diet_type = ?,
                    image_url = ?,
                    is_snack = ?,
                    price = ?
                WHERE id = ?
            """, (item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[8], item[9], item[10], item[11], item[12], exist[0]))
        else:
            cursor.execute("""
                INSERT INTO foods (
                    name, category, serving_size, serving_unit,
                    calories, protein, carbs, fat, fiber, diet_type, image_url, is_snack, price
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, item)

    # -------------------------------------------------------------
    # Complete Snacks Catalog (15 Vegetarian + 12 Non-Vegetarian)
    # -------------------------------------------------------------
    snack_items = [
        # Vegetarian Snacks (15 items) - Calibrated Medium Prices
        ("Samosa", "Snacks", 1, "piece (80g)", 260.0, 3.5, 32.0, 13.0, 2.1, "vegetarian", "/static/images/snacks/samosa.svg", 1, 20.0),
        ("Masala Puri", "Snacks", 1, "plate (180g)", 240.0, 6.0, 38.0, 7.5, 3.8, "vegetarian", "/static/images/snacks/masala_puri.svg", 1, 40.0),
        ("Pani Puri", "Snacks", 6, "pieces (150g)", 180.0, 3.2, 30.0, 5.5, 2.2, "vegetarian", "/static/images/snacks/pani_puri.svg", 1, 30.0),
        ("Bhel Puri", "Snacks", 1, "plate (150g)", 210.0, 4.8, 36.0, 6.0, 3.2, "vegetarian", "/static/images/snacks/bhel_puri.svg", 1, 35.0),
        ("Veg Sandwich", "Snacks", 1, "sandwich (160g)", 230.0, 6.5, 34.0, 8.0, 3.5, "vegetarian", "/static/images/snacks/veg_sandwich.svg", 1, 50.0),
        ("Veg Puff", "Snacks", 1, "piece (100g)", 280.0, 4.2, 32.0, 15.0, 2.4, "vegetarian", "/static/images/snacks/veg_puff.svg", 1, 25.0),
        ("French Fries", "Snacks", 1, "medium pack (110g)", 310.0, 3.4, 41.0, 15.0, 3.8, "vegetarian", "/static/images/snacks/french_fries.svg", 1, 55.0),
        ("Onion Pakoda", "Snacks", 1, "plate (120g)", 275.0, 5.0, 26.0, 16.5, 2.8, "vegetarian", "/static/images/snacks/onion_pakoda.svg", 1, 45.0),
        ("Paneer Tikka", "Snacks", 5, "pieces (150g)", 280.0, 16.0, 8.0, 20.0, 2.0, "vegetarian", "/static/images/snacks/paneer_tikka.svg", 1, 120.0),
        ("Aloo Tikki", "Snacks", 2, "patties (140g)", 220.0, 4.0, 32.0, 9.0, 3.0, "vegetarian", "/static/images/snacks/aloo_tikki.svg", 1, 35.0),
        ("Dhokla", "Snacks", 3, "pieces (120g)", 160.0, 6.5, 25.0, 4.0, 2.5, "vegetarian", "/static/images/snacks/dhokla.svg", 1, 40.0),
        ("Spring Rolls", "Snacks", 2, "rolls (120g)", 220.0, 4.5, 28.0, 10.5, 2.6, "vegetarian", "/static/images/snacks/spring_rolls.svg", 1, 65.0),
        ("Roasted Peanuts", "Snacks", 1, "handful (40g)", 230.0, 10.5, 6.5, 19.5, 3.4, "vegetarian", "/static/images/snacks/roasted_peanuts.svg", 1, 30.0),
        ("Sweet Corn", "Snacks", 1, "cup (150g)", 130.0, 4.5, 27.0, 1.8, 3.5, "vegetarian", "/static/images/snacks/sweet_corn.svg", 1, 40.0),
        ("Banana Chips", "Snacks", 1, "bowl (40g)", 210.0, 1.5, 24.0, 12.5, 2.0, "vegetarian", "/static/images/snacks/banana_chips.svg", 1, 35.0),

        # Non-Vegetarian Snacks (12 items) - Calibrated Medium Prices
        ("Chicken Nuggets", "Snacks", 5, "pieces (100g)", 270.0, 15.0, 16.0, 16.0, 0.8, "non-veg", "/static/images/snacks/chicken_nuggets.svg", 1, 85.0),
        ("Chicken Sandwich", "Snacks", 1, "sandwich (180g)", 320.0, 22.0, 30.0, 12.0, 2.8, "non-veg", "/static/images/snacks/chicken_sandwich.svg", 1, 75.0),
        ("Chicken Momos", "Snacks", 5, "pieces (130g)", 190.0, 12.5, 22.0, 6.0, 1.5, "non-veg", "/static/images/snacks/chicken_momos.svg", 1, 70.0),
        ("Chicken Tikka", "Snacks", 6, "pieces (150g)", 260.0, 32.0, 4.0, 12.0, 1.0, "non-veg", "/static/images/snacks/chicken_tikka.svg", 1, 135.0),
        ("Chicken 65", "Snacks", 1, "plate (140g)", 310.0, 24.0, 12.0, 18.0, 1.2, "non-veg", "/static/images/snacks/chicken_65.svg", 1, 115.0),
        ("Egg Puff", "Snacks", 1, "piece (110g)", 290.0, 8.5, 28.0, 16.0, 1.6, "non-veg", "/static/images/snacks/egg_puff.svg", 1, 35.0),
        ("Boiled Eggs", "Snacks", 2, "eggs (100g)", 156.0, 12.6, 1.2, 10.6, 0.0, "non-veg", "/static/images/snacks/boiled_eggs.svg", 1, 25.0),
        ("Egg Roll", "Snacks", 1, "roll (150g)", 310.0, 11.0, 36.0, 14.0, 2.2, "non-veg", "/static/images/snacks/egg_roll.svg", 1, 55.0),
        ("Fish Fingers", "Snacks", 5, "pieces (120g)", 240.0, 18.0, 15.0, 12.0, 0.8, "non-veg", "/static/images/snacks/fish_fingers.svg", 1, 125.0),
        ("Chicken Cutlet", "Snacks", 2, "patties (130g)", 280.0, 18.5, 18.0, 15.0, 1.8, "non-veg", "/static/images/snacks/chicken_cutlet.svg", 1, 70.0),
        ("Chicken Pakoda", "Snacks", 1, "plate (130g)", 320.0, 22.0, 14.0, 20.0, 1.4, "non-veg", "/static/images/snacks/chicken_pakoda.svg", 1, 95.0),
        ("Egg Sandwich", "Snacks", 1, "sandwich (160g)", 270.0, 14.0, 28.0, 11.5, 2.4, "non-veg", "/static/images/snacks/egg_sandwich.svg", 1, 60.0),
    ]

    for item in snack_items:
        cursor.execute("SELECT id FROM foods WHERE LOWER(name) = LOWER(?)", (item[0],))
        existing = cursor.fetchone()
        if existing:
            cursor.execute("""
                UPDATE foods SET
                    category = ?,
                    serving_size = ?,
                    serving_unit = ?,
                    calories = ?,
                    protein = ?,
                    carbs = ?,
                    fat = ?,
                    fiber = ?,
                    diet_type = ?,
                    image_url = ?,
                    is_snack = ?,
                    price = ?
                WHERE id = ?
            """, (item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[8], item[9], item[10], item[11], item[12], existing[0]))
        else:
            cursor.execute("""
                INSERT INTO foods (
                    name, category, serving_size, serving_unit,
                    calories, protein, carbs, fat, fiber, diet_type, image_url, is_snack, price
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, item)

    conn.commit()
    conn.close()


def calculate_nutrition_targets(weight_kg, height_cm, age, gender, activity_level, goal):
    """Calculates Daily Calorie and Macro targets."""
    if gender.lower() == "male":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

    activity_factors = {
        "sedentary": 1.2,
        "lightly_active": 1.375,
        "moderately_active": 1.55,
        "very_active": 1.725
    }
    multiplier = activity_factors.get(activity_level, 1.375)
    tdee = bmr * multiplier

    if goal == "weight_loss":
        target_calories = tdee - 500
        protein_per_kg = 1.8
    elif goal == "muscle_gain":
        target_calories = tdee + 350
        protein_per_kg = 2.0
    else:
        target_calories = tdee
        protein_per_kg = 1.5

    target_protein = round(weight_kg * protein_per_kg, 1)
    protein_calories = target_protein * 4

    fat_calories = target_calories * 0.25
    target_fat = round(fat_calories / 9, 1)

    remaining_calories = max(0, target_calories - protein_calories - fat_calories)
    target_carbs = round(remaining_calories / 4, 1)

    return {
        "bmr": round(bmr, 1),
        "tdee": round(tdee, 1),
        "target_calories": round(max(1200, target_calories), 1),
        "target_protein": target_protein,
        "target_carbs": target_carbs,
        "target_fat": target_fat
    }


def get_profile():
    """Fetches user profile, creating default if needed."""
    init_db()
    conn = get_db_connection()
    profile = conn.execute("SELECT * FROM user_profile WHERE id = 1").fetchone()
    conn.close()
    return profile


def save_profile(name, age, gender, height_cm, weight_kg, activity_level, goal, diet_preference):
    """Updates user profile and recalculates nutrition targets."""
    init_db()
    targets = calculate_nutrition_targets(
        weight_kg=float(weight_kg),
        height_cm=float(height_cm),
        age=int(age),
        gender=gender,
        activity_level=activity_level,
        goal=goal
    )

    conn = get_db_connection()
    conn.execute("""
        UPDATE user_profile SET
            name = ?,
            age = ?,
            gender = ?,
            height_cm = ?,
            weight_kg = ?,
            activity_level = ?,
            goal = ?,
            diet_preference = ?,
            daily_calorie_target = ?,
            daily_protein_target = ?,
            daily_carb_target = ?,
            daily_fat_target = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = 1
    """, (
        name, int(age), gender, float(height_cm), float(weight_kg),
        activity_level, goal, diet_preference,
        targets["target_calories"], targets["target_protein"],
        targets["target_carbs"], targets["target_fat"]
    ))
    conn.commit()
    conn.close()
    return targets


def get_all_foods(category_filter=None):
    """Returns list of foods, optionally filtered by category."""
    init_db()
    conn = get_db_connection()
    if category_filter and category_filter != "All":
        foods = conn.execute("SELECT * FROM foods WHERE category = ? ORDER BY name ASC", (category_filter,)).fetchall()
    else:
        foods = conn.execute("SELECT * FROM foods ORDER BY category, name ASC").fetchall()
    conn.close()
    return foods


def search_foods(query):
    """Searches food database by name or category."""
    init_db()
    conn = get_db_connection()
    term = f"%{query.strip()}%"
    results = conn.execute(
        "SELECT * FROM foods WHERE name LIKE ? OR category LIKE ? ORDER BY name ASC LIMIT 25",
        (term, term)
    ).fetchall()
    conn.close()
    return results


def get_food_by_name(name):
    """Fetches single food item by exact name."""
    init_db()
    conn = get_db_connection()
    food = conn.execute("SELECT * FROM foods WHERE LOWER(name) = LOWER(?)", (name.strip(),)).fetchone()
    conn.close()
    return food


def get_food_by_id(food_id):
    """Fetches single food item by ID."""
    init_db()
    conn = get_db_connection()
    food = conn.execute("SELECT * FROM foods WHERE id = ?", (food_id,)).fetchone()
    conn.close()
    return food


def get_snacks(diet_filter=None, search_query=None):
    """Fetches snack items with optional diet filter and search term filter."""
    init_db()
    conn = get_db_connection()
    query = "SELECT * FROM foods WHERE is_snack = 1"
    params = []

    if diet_filter in ["vegetarian", "veg"]:
        query += " AND diet_type = 'vegetarian'"
    elif diet_filter in ["non-veg", "non_veg"]:
        query += " AND diet_type = 'non-veg'"

    if search_query:
        query += " AND name LIKE ?"
        params.append(f"%{search_query.strip()}%")

    query += " ORDER BY diet_type DESC, name ASC"
    snacks = conn.execute(query, params).fetchall()
    conn.close()
    return snacks


def get_delivery_foods(category_filter=None, search_query=None):
    """Fetches items available for food delivery."""
    init_db()
    conn = get_db_connection()
    query = "SELECT * FROM foods WHERE 1=1"
    params = []

    if category_filter == "veg":
        query += " AND diet_type IN ('vegetarian', 'vegan')"
    elif category_filter == "nonveg":
        query += " AND diet_type = 'non-veg'"
    elif category_filter == "snacks":
        query += " AND is_snack = 1"
    elif category_filter == "meals":
        query += " AND is_snack = 0"
    elif category_filter == "dinner":
        query += " AND (category LIKE '%Dinner%' OR name IN ('Palak Paneer', 'Dal Makhani', 'Butter Chicken', 'Chicken Korma', 'Moong Dal Khichdi', 'Tandoori Roti Basket (3 pcs)', 'Methi Thepla (3 pcs)', 'Grilled Fish with Steamed Veggies', 'Paneer Butter Masala', 'Veg Biryani', 'Chicken Biryani', 'Chicken Curry', 'Fish Curry', 'Egg Curry', 'Curd Rice', 'Dal Rice'))"

    if search_query:
        query += " AND (name LIKE ? OR category LIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])

    query += " ORDER BY is_snack ASC, diet_type DESC, name ASC"
    foods = conn.execute(query, params).fetchall()
    conn.close()
    return foods


def get_meals(diet_filter=None, search_query=None):
    """Fetches full meal & dinner items (is_snack = 0)."""
    init_db()
    conn = get_db_connection()
    query = "SELECT * FROM foods WHERE is_snack = 0"
    params = []

    if diet_filter in ["vegetarian", "veg"]:
        query += " AND diet_type IN ('vegetarian', 'vegan')"
    elif diet_filter in ["non-veg", "nonveg"]:
        query += " AND diet_type = 'non-veg'"

    if search_query:
        query += " AND (name LIKE ? OR category LIKE ?)"
        params.extend([f"%{search_query.strip()}%", f"%{search_query.strip()}%"])

    query += " ORDER BY diet_type DESC, name ASC"
    meals = conn.execute(query, params).fetchall()
    conn.close()
    return meals


def add_custom_food(name, category, serving_size, serving_unit, calories, protein, carbs, fat, fiber=0.0, diet_type="all", image_url=None, is_snack=0, price=99.0):
    """Inserts a custom food into the database."""
    init_db()
    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO foods (
                name, category, serving_size, serving_unit,
                calories, protein, carbs, fat, fiber, diet_type, image_url, is_snack, price
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name.strip(), category.strip(), float(serving_size), serving_unit.strip(),
            float(calories), float(protein), float(carbs), float(fat), float(fiber), diet_type, image_url, int(is_snack), float(price)
        ))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    finally:
        conn.close()
    return success


def log_meal_item(meal_date, meal_type, food_name, quantity, unit, calories, protein, carbs, fat, image_path=None):
    """Logs a food item into the meal_logs table."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO meal_logs (
            user_id, meal_date, meal_type, food_name,
            quantity, unit, calories, protein, carbs, fat, image_path
        ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        meal_date, meal_type, food_name, float(quantity), unit,
        round(float(calories), 1), round(float(protein), 1),
        round(float(carbs), 1), round(float(fat), 1), image_path
    ))
    conn.commit()
    log_id = cursor.lastrowid
    conn.close()
    return log_id


def get_logs_for_date(date_str):
    """Fetches all logged meals for a specific date (YYYY-MM-DD)."""
    init_db()
    conn = get_db_connection()
    logs = conn.execute(
        "SELECT * FROM meal_logs WHERE meal_date = ? ORDER BY id ASC",
        (date_str,)
    ).fetchall()
    conn.close()
    return logs


def delete_log(log_id):
    """Deletes a meal log item by ID."""
    init_db()
    conn = get_db_connection()
    conn.execute("DELETE FROM meal_logs WHERE id = ?", (log_id,))
    conn.commit()
    conn.close()


def get_daily_summary(date_str):
    """Aggregates consumed calories and macros for a given date."""
    profile = get_profile()
    logs = get_logs_for_date(date_str)

    total_calories = sum(log["calories"] for log in logs)
    total_protein = sum(log["protein"] for log in logs)
    total_carbs = sum(log["carbs"] for log in logs)
    total_fat = sum(log["fat"] for log in logs)

    target_cal = profile["daily_calorie_target"]
    target_pro = profile["daily_protein_target"]
    target_carb = profile["daily_carb_target"]
    target_fat = profile["daily_fat_target"]

    remaining_cal = round(target_cal - total_calories, 1)
    is_surplus = remaining_cal < 0
    surplus_cal = round(abs(remaining_cal), 1) if is_surplus else 0.0

    # Real percentage achieved (can exceed 100%)
    cal_pct_raw = round((total_calories / target_cal * 100), 1) if target_cal > 0 else 0.0
    pro_pct_raw = round((total_protein / target_pro * 100), 1) if target_pro > 0 else 0.0
    carb_pct_raw = round((total_carbs / target_carb * 100), 1) if target_carb > 0 else 0.0
    fat_pct_raw = round((total_fat / target_fat * 100), 1) if target_fat > 0 else 0.0

    meals_by_type = {
        "Breakfast": [],
        "Lunch": [],
        "Dinner": [],
        "Snack": []
    }
    for log in logs:
        m_type = log["meal_type"]
        if m_type in meals_by_type:
            meals_by_type[m_type].append(log)
        else:
            meals_by_type.setdefault("Snack", []).append(log)

    return {
        "date": date_str,
        "logs": logs,
        "meals_by_type": meals_by_type,
        "total_calories": round(total_calories, 1),
        "total_protein": round(total_protein, 1),
        "total_carbs": round(total_carbs, 1),
        "total_fat": round(total_fat, 1),
        "target_calories": target_cal,
        "target_protein": target_pro,
        "target_carbs": target_carb,
        "target_fat": target_fat,
        "remaining_calories": remaining_cal,
        "is_surplus": is_surplus,
        "surplus_calories": surplus_cal,
        # Actual percentage values (correctly showing values > 100% when targets are exceeded)
        "calorie_pct": cal_pct_raw,
        "protein_pct": pro_pct_raw,
        "carb_pct": carb_pct_raw,
        "fat_pct": fat_pct_raw,
        # Clamped values strictly for CSS progress-bar widths (0% to 100%)
        "calorie_bar_pct": min(100.0, max(0.0, cal_pct_raw)),
        "protein_bar_pct": min(100.0, max(0.0, pro_pct_raw)),
        "carb_bar_pct": min(100.0, max(0.0, carb_pct_raw)),
        "fat_bar_pct": min(100.0, max(0.0, fat_pct_raw)),
    }


def get_meal_log_by_id(log_id):
    """Fetches a single meal log entry by ID."""
    init_db()
    conn = get_db_connection()
    log = conn.execute("SELECT * FROM meal_logs WHERE id = ?", (log_id,)).fetchone()
    conn.close()
    return log


def update_meal_log_quantity(log_id, new_quantity):
    """
    Updates the portion/quantity of a logged meal in SQLite and accurately recalculates macros.
    """
    init_db()
    conn = get_db_connection()
    log = conn.execute("SELECT * FROM meal_logs WHERE id = ?", (log_id,)).fetchone()
    if not log:
        conn.close()
        return False

    old_qty = float(log["quantity"]) if float(log["quantity"]) > 0 else 1.0
    ratio = float(new_quantity) / old_qty

    new_cals = round(float(log["calories"]) * ratio, 1)
    new_pro = round(float(log["protein"]) * ratio, 1)
    new_carb = round(float(log["carbs"]) * ratio, 1)
    new_fat = round(float(log["fat"]) * ratio, 1)

    conn.execute("""
        UPDATE meal_logs SET
            quantity = ?,
            calories = ?,
            protein = ?,
            carbs = ?,
            fat = ?
        WHERE id = ?
    """, (float(new_quantity), new_cals, new_pro, new_carb, new_fat, log_id))
    conn.commit()
    conn.close()
    return True


def get_personalized_suggestions(date_str):
    """Generates intelligent meal and snack suggestions."""
    summary = get_daily_summary(date_str)
    profile = get_profile()
    remaining_cal = summary["remaining_calories"]
    remaining_protein = summary["target_protein"] - summary["total_protein"]

    conn = get_db_connection()
    diet_pref = profile["diet_preference"]

    if diet_pref == "vegan":
        query = "SELECT * FROM foods WHERE diet_type = 'vegan'"
    elif diet_pref == "vegetarian":
        query = "SELECT * FROM foods WHERE diet_type IN ('vegan', 'vegetarian')"
    else:
        query = "SELECT * FROM foods"

    candidates = conn.execute(query).fetchall()
    conn.close()

    suggestions = []
    if remaining_cal > 80:
        for food in candidates:
            if food["calories"] <= (remaining_cal + 50):
                score = 0
                reason = "Fits nicely into your remaining calories"

                if remaining_protein > 15 and food["protein"] >= 10:
                    score += 20
                    reason = f"High protein ({food['protein']}g) to hit your protein goal"
                elif food["calories"] <= remaining_cal:
                    score += 10

                suggestions.append({
                    "food": food,
                    "score": score,
                    "reason": reason
                })

        suggestions.sort(key=lambda x: x["score"], reverse=True)
        return suggestions[:4]
    else:
        return [{
            "food": {"name": "Hydration / Green Tea", "calories": 2, "protein": 0, "carbs": 0, "fat": 0, "serving_size": 1, "serving_unit": "cup"},
            "score": 100,
            "reason": "You have met your daily calorie target! Hydrate well with water or warm green tea."
        }]


# =========================================================================
# Delivery System Operations
# =========================================================================

def create_delivery_order(customer_name, phone, delivery_address, delivery_slot, payment_method, cart_items, auto_log_to_diary=True):
    """
    Creates a new delivery order, calculates subtotal & nutrition totals,
    links order items, and optionally auto-logs items to today's diary.
    """
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    order_num = f"NUTRI-{random.randint(1000, 9999)}"
    subtotal = 0.0
    total_cals = 0.0
    total_pro = 0.0
    total_carbs = 0.0
    total_fat = 0.0

    today_str = date.today().isoformat()

    # Pre-calculate totals across cart items
    resolved_items = []
    for item in cart_items:
        f_id = item.get("food_id")
        qty = float(item.get("quantity", 1.0))
        food = get_food_by_id(f_id)
        if not food:
            continue

        item_price = float(food["price"] or 99.0)
        item_subtotal = item_price * qty
        item_cals = round(food["calories"] * qty, 1)
        item_pro = round(food["protein"] * qty, 1)
        item_carb = round(food["carbs"] * qty, 1)
        item_fat = round(food["fat"] * qty, 1)

        subtotal += item_subtotal
        total_cals += item_cals
        total_pro += item_pro
        total_carbs += item_carb
        total_fat += item_fat

        resolved_items.append({
            "food_id": food["id"],
            "food_name": food["name"],
            "price": item_price,
            "quantity": qty,
            "unit": food["serving_unit"],
            "calories": item_cals,
            "protein": item_pro,
            "carbs": item_carb,
            "fat": item_fat,
            "image_url": food["image_url"],
            "is_snack": food["is_snack"]
        })

    # Delivery fee: Free for orders >= ₹250, otherwise ₹30
    delivery_fee = 0.0 if subtotal >= 250 else 30.0
    total_price = subtotal + delivery_fee

    # Insert Order record
    cursor.execute("""
        INSERT INTO orders (
            order_number, user_id, customer_name, phone,
            delivery_address, delivery_slot, payment_method,
            subtotal, delivery_fee, total_price,
            total_calories, total_protein, total_carbs, total_fat,
            status, rider_name, rider_phone, estimated_delivery_time, auto_logged
        ) VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Confirmed', 'Rahul Sharma', '+91 98765 43210', '30-40 mins', ?)
    """, (
        order_num, customer_name, phone, delivery_address,
        delivery_slot, payment_method, round(subtotal, 2), delivery_fee, round(total_price, 2),
        round(total_cals, 1), round(total_pro, 1), round(total_carbs, 1), round(total_fat, 1),
        1 if auto_log_to_diary else 0
    ))
    order_id = cursor.lastrowid

    # Insert items
    for rit in resolved_items:
        cursor.execute("""
            INSERT INTO order_items (
                order_id, food_id, food_name, price, quantity,
                calories, protein, carbs, fat, image_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_id, rit["food_id"], rit["food_name"], rit["price"], rit["quantity"],
            rit["calories"], rit["protein"], rit["carbs"], rit["fat"], rit["image_url"]
        ))

        # Auto-log to today's diary if selected
        if auto_log_to_diary:
            meal_type = "Snack" if rit["is_snack"] else "Lunch"
            cursor.execute("""
                INSERT INTO meal_logs (
                    user_id, meal_date, meal_type, food_name,
                    quantity, unit, calories, protein, carbs, fat, image_path
                ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                today_str, meal_type, rit["food_name"], float(rit["quantity"]),
                rit["unit"], round(float(rit["calories"]), 1), round(float(rit["protein"]), 1),
                round(float(rit["carbs"]), 1), round(float(rit["fat"]), 1), rit["image_url"]
            ))

    conn.commit()
    conn.close()
    return order_id, order_num


def get_order_details(order_id):
    """Fetches order and its line items by ID."""
    init_db()
    conn = get_db_connection()
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        conn.close()
        return None

    items = conn.execute("SELECT * FROM order_items WHERE order_id = ? ORDER BY id ASC", (order_id,)).fetchall()
    conn.close()
    return {
        "order": order,
        "items": items
    }


def get_order_by_number(order_number):
    """Fetches order by its human-readable order number (e.g. NUTRI-8472)."""
    init_db()
    conn = get_db_connection()
    order = conn.execute("SELECT * FROM orders WHERE order_number = ?", (order_number.strip(),)).fetchone()
    if not order:
        conn.close()
        return None

    items = conn.execute("SELECT * FROM order_items WHERE order_id = ? ORDER BY id ASC", (order["id"],)).fetchall()
    conn.close()
    return {
        "order": order,
        "items": items
    }


def get_all_orders():
    """Fetches all customer delivery orders sorted newest first."""
    init_db()
    conn = get_db_connection()
    orders = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    conn.close()
    return orders


def update_order_status(order_id, new_status):
    """Updates the live status of an order."""
    init_db()
    conn = get_db_connection()
    conn.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
    conn.commit()
    conn.close()
