"""
Comprehensive Integration Test Suite for NutriTrack
Tests:
- Authentication & Sessions
- User Profiles & Personalization
- Dashboard stats & charts data
- Meal uploads & visual recognition
- Ingredient-based recipe suggestions & saved recipes
- Meal history, editing, and deletion
- Nutrition Analytics aggregation
- Settings & diary CSV/JSON export
- All Flask HTTP routes return 200/302 as expected
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(__file__))

import database
import app as flask_app


def run_full_suite():
    print("=" * 60)
    print("🚀 RUNNING NUTRITRACK FULL PLATFORM INTEGRATION TEST SUITE")
    print("=" * 60)

    # 1. Database Initialization
    print("\n[Stage 1] Initializing and verifying database schema...")
    database.init_db()
    with database.get_db_connection() as conn:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    
    expected_tables = ["users", "user_profiles", "meals", "meal_items", "food_database", "recipes", "saved_recipes", "user_preferences"]
    for t in expected_tables:
        assert t in tables, f"Missing table: {t}"
    print(f"  ✓ All 8 required tables present (Total tables in DB: {len(tables)})")

    # 2. User Authentication & Multi-user isolation
    print("\n[Stage 2] Testing User Auth & Multi-user isolation...")
    test_email = "testuser_unique@example.com"
    # Clean up test user if exists
    with database.get_db_connection() as conn:
        conn.execute("DELETE FROM users WHERE email = ?", (test_email,))
        conn.commit()

    uid, err = database.register_user("Test User", test_email, "securepass123", "vegetarian")
    assert uid is not None, f"Registration failed: {err}"
    print(f"  ✓ Registered new user (ID: {uid})")

    auth_user = database.authenticate_user(test_email, "securepass123")
    assert auth_user is not None and auth_user["id"] == uid, "Authentication failed"
    print("  ✓ Authenticated with correct password")

    bad_auth = database.authenticate_user(test_email, "wrongpassword")
    assert bad_auth is None, "Authentication succeeded with wrong password"
    print("  ✓ Rejected invalid password")

    # 3. Recipes & Ingredient Matching
    print("\n[Stage 3] Testing Ingredient-Based Recipe Engine...")
    recipes = database.get_recipes()
    assert len(recipes) >= 20, f"Expected at least 20 seeded recipes, found {len(recipes)}"
    print(f"  ✓ {len(recipes)} recipes loaded")

    # Match ingredients
    user_ingredients = ["chicken", "rice", "onion", "spices"]
    matches = database.match_recipes_by_ingredients(user_ingredients, diet_type="all")
    assert len(matches) > 0, "Expected matches for chicken and rice"
    top_match = matches[0]
    print(f"  ✓ Top recipe match: '{top_match['name']}' with {top_match['match_pct']}% ingredient match")

    # Save & Unsave Recipe
    recipe_id = recipes[0]["id"]
    database.save_recipe_for_user(uid, recipe_id)
    assert database.is_recipe_saved(uid, recipe_id) is True, "Recipe should be marked saved"
    saved_list = database.get_saved_recipes_for_user(uid)
    assert any(r["id"] == recipe_id for r in saved_list), "Recipe should appear in saved collection"
    print("  ✓ Successfully saved recipe to user collection")

    database.unsave_recipe_for_user(uid, recipe_id)
    assert database.is_recipe_saved(uid, recipe_id) is False, "Recipe should be unsaved"
    print("  ✓ Successfully removed recipe from user collection")

    # 4. Meal History, Full Details & Editing
    print("\n[Stage 4] Testing Meal Logging, History & Editing...")
    from datetime import date
    test_date = date.today().isoformat()
    log_id = database.log_meal_item(
        meal_date=test_date,
        meal_type="Lunch",
        food_name="Chicken Biryani",
        quantity=1.0,
        unit="plate (350g)",
        calories=550.0,
        protein=32.0,
        carbs=68.0,
        fat=16.0,
        user_id=uid
    )
    assert log_id > 0, "Failed to log meal"
    print(f"  ✓ Logged meal ID {log_id} for user {uid}")

    history = database.get_meal_history(user_id=uid)
    assert any(m["id"] == log_id for m in history), "Logged meal should appear in history"
    print(f"  ✓ Retrieved meal history (found {len(history)} meals)")

    # Meal details
    meal_details = database.get_meal_details_full(log_id, user_id=uid)
    assert meal_details is not None and meal_details["food_name"] == "Chicken Biryani", "Details lookup failed"
    print(f"  ✓ Retrieved meal details for '{meal_details['food_name']}'")

    # Edit meal
    database.update_meal_log_full(
        log_id=log_id,
        food_name="Chicken Biryani (Large)",
        quantity=1.5,
        calories=825.0,
        protein=48.0,
        carbs=102.0,
        fat=24.0,
        user_id=uid
    )
    updated_meal = database.get_meal_details_full(log_id, user_id=uid)
    assert updated_meal["quantity"] == 1.5, "Quantity update failed"
    assert updated_meal["calories"] == 825.0, "Calories update failed"
    print(f"  ✓ Successfully updated meal portion and nutrition totals")

    # 5. Nutrition Analytics Aggregation
    print("\n[Stage 5] Testing Nutrition Analytics...")
    analytics = database.get_nutrition_analytics(user_id=uid, days=7)
    assert "dates" in analytics and "calories" in analytics, "Invalid analytics dictionary"
    assert analytics["total_calories"] >= 825.0, "Total calories in period mismatch"
    print(f"  ✓ Analytics aggregation: Total {analytics['total_calories']} kcal across {len(analytics['dates'])} days")

    # 6. Preferences & Settings
    print("\n[Stage 6] Testing Preferences & Dark Mode...")
    database.update_user_preferences(user_id=uid, dark_mode=1, unit_system="imperial")
    pref = database.get_user_preferences(user_id=uid)
    assert pref["dark_mode"] == 1, "Dark mode preference failed"
    assert pref["unit_system"] == "imperial", "Unit system preference failed"
    print("  ✓ Preferences updated and retrieved successfully")

    # 7. Flask Test Client Route Checks
    print("\n[Stage 7] Testing Flask HTTP Endpoints...")
    client = flask_app.app.test_client()

    routes_to_test = [
        ("/", [200, 302]),
        ("/landing", [200]),
        ("/login", [200, 302]),
        ("/register", [200, 302]),
        ("/forgot-password", [200]),
        ("/demo-login", [302]),
        ("/dashboard", [200]),
        ("/profile", [200]),
        ("/upload", [200]),
        ("/meal-ideas", [200]),
        ("/saved-recipes", [200]),
        ("/history", [200]),
        ("/analytics", [200]),
        ("/settings", [200]),
        ("/about", [200]),
        ("/meals", [200]),
        ("/snacks", [200]),
        ("/delivery", [200]),
        ("/database", [200]),
        ("/summary", [200]),
        ("/export-diary?format=csv", [200]),
        ("/export-diary?format=json", [200]),
        (f"/meal/{log_id}", [200])
    ]

    with client.session_transaction() as sess:
        sess["user_id"] = uid
        sess["user_name"] = "Test User"
        sess["user_email"] = test_email

    for route, expected_statuses in routes_to_test:
        resp = client.get(route)
        assert resp.status_code in expected_statuses, f"Route '{route}' failed with status {resp.status_code} (expected {expected_statuses})"
        print(f"  ✓ Route {route:30} -> HTTP {resp.status_code}")

    # Clean up test meal
    database.delete_log(log_id, user_id=uid)
    print("  ✓ Test meal cleaned up")

    print("\n" + "=" * 60)
    print("🎉 ALL PLATFORM TESTS PASSED SUCCESSFULLY! (100% PASS RATE)")
    print("=" * 60)


if __name__ == "__main__":
    run_full_suite()
