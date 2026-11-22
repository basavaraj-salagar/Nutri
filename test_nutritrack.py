"""
NutriTrack End-to-End Automated Test Suite
Verifies all 6 methodology steps:
1. User Profile & BMR/TDEE calculation
2. Meal Upload & Ingredient input
3. AI Food Recognition & Portion Estimation
4. Nutrition Database search & custom food addition
5. Meal review, portion adjustment & logging
6. Personalized Daily Summary & Recommendations
"""

import sys
import os
from datetime import date

# Ensure local directory is in path
sys.path.insert(0, os.path.dirname(__file__))

import database
import ai_service


def run_tests():
    print("=" * 60)
    print("🧪 Running NutriTrack End-to-End Test Suite")
    print("=" * 60)

    # -------------------------------------------------------------
    # Test 1: Step 1 - User Profile & Target Calculation
    # -------------------------------------------------------------
    print("\n[Test 1] Testing Step 1: User Profile & Target Calculation...")
    database.init_db()

    # Save test profile
    targets = database.save_profile(
        name="Alex Smith",
        age=28,
        gender="male",
        height_cm=180.0,
        weight_kg=78.0,
        activity_level="moderately_active",
        goal="weight_loss",
        diet_preference="all"
    )
    profile = database.get_profile()
    assert profile["name"] == "Alex Smith", f"Expected 'Alex Smith', got {profile['name']}"
    assert profile["daily_calorie_target"] > 1200, "Calorie target too low"
    assert profile["daily_protein_target"] > 0, "Protein target must be positive"
    print(f"  ✓ Profile saved: {profile['name']} ({profile['goal']})")
    print(f"  ✓ BMR/TDEE Targets: {profile['daily_calorie_target']} kcal, {profile['daily_protein_target']}g protein, {profile['daily_carb_target']}g carbs, {profile['daily_fat_target']}g fat")

    # -------------------------------------------------------------
    # Test 2: Step 4 - Nutrition Database Operations
    # -------------------------------------------------------------
    print("\n[Test 2] Testing Step 4: Nutrition Database Operations...")
    all_foods = database.get_all_foods()
    assert len(all_foods) >= 20, f"Expected at least 20 seeded foods, found {len(all_foods)}"
    print(f"  ✓ Database seeded with {len(all_foods)} food items across categories.")

    # Search for an item
    egg_search = database.search_foods("egg")
    assert len(egg_search) > 0, "Expected to find 'egg' in database"
    print(f"  ✓ Search query 'egg' returned {len(egg_search)} matches.")

    # Add custom food
    custom_name = "Greek Protein Salad Bowl"
    added = database.add_custom_food(
        name=custom_name,
        category="Dishes",
        serving_size=200,
        serving_unit="bowl",
        calories=250.0,
        protein=22.0,
        carbs=15.0,
        fat=8.0,
        fiber=4.0,
        diet_type="vegetarian"
    )
    custom_item = database.get_food_by_name(custom_name)
    assert custom_item is not None, "Failed to retrieve custom food"
    assert custom_item["calories"] == 250.0, "Custom food calories mismatch"
    print(f"  ✓ Added and verified custom food: '{custom_name}' ({custom_item['calories']} kcal).")

    # -------------------------------------------------------------
    # Test 3: Steps 2 & 3 - AI Food Recognition & Portion Estimation
    # -------------------------------------------------------------
    print("\n[Test 3] Testing Steps 2 & 3: AI Food Recognition & Portion Estimation...")
    sample_text = "2 boiled eggs, 1 slice whole wheat bread, 1 medium banana"
    recognized = ai_service.analyze_text_ingredients(sample_text)
    assert len(recognized) == 3, f"Expected 3 recognized items, got {len(recognized)}"

    egg_item = recognized[0]
    assert "Egg" in egg_item["name"], f"Expected Egg in item 0 name, got {egg_item['name']}"
    assert egg_item["quantity"] == 2.0, f"Expected quantity 2.0, got {egg_item['quantity']}"
    assert egg_item["calories"] > 100, "2 eggs should have >100 kcal"
    print(f"  ✓ Text AI parser successfully recognized {len(recognized)} items:")
    for r in recognized:
        print(f"    - {r['name']}: {r['quantity']} {r['unit']} ({r['calories']} kcal, {r['protein']}g protein)")

    # Test photo heuristic recognition
    photo_name = "healthy_lunch_chicken_curry_rice.png"
    photo_items = ai_service.analyze_meal_photo(photo_name)
    assert len(photo_items) >= 2, f"Expected at least 2 items from photo tags, got {len(photo_items)}"
    print(f"  ✓ Photo AI recognition successfully identified {len(photo_items)} items from '{photo_name}':")
    for pi in photo_items:
        print(f"    - {pi['name']} ({pi['confidence']}% confidence)")

    # -------------------------------------------------------------
    # Test 4: Step 5 - User Reviews & Save Meal to Diary
    # -------------------------------------------------------------
    print("\n[Test 4] Testing Step 5: User Reviews & Save Meal to Diary...")
    test_date = "2099-01-01"  # Isolated test date to ensure clean assertions
    log1 = database.log_meal_item(
        meal_date=test_date,
        meal_type="Breakfast",
        food_name="Boiled Egg",
        quantity=2.0,
        unit="egg (50g)",
        calories=156.0,
        protein=12.6,
        carbs=1.2,
        fat=10.6
    )
    log2 = database.log_meal_item(
        meal_date=test_date,
        meal_type="Breakfast",
        food_name="Whole Wheat Bread",
        quantity=1.0,
        unit="slice (35g)",
        calories=80.0,
        protein=4.0,
        carbs=14.0,
        fat=1.0
    )
    print(f"  ✓ Logged 2 meal items to database (IDs: {log1}, {log2}) for {test_date}")

    # -------------------------------------------------------------
    # Test 5: Step 6 - Daily Summary & Personalized Recommendations
    # -------------------------------------------------------------
    print("\n[Test 5] Testing Step 6: Daily Summary & Recommendations...")
    summary = database.get_daily_summary(test_date)
    assert summary["total_calories"] == 236.0, f"Expected 236.0 kcal, got {summary['total_calories']}"
    assert summary["total_protein"] == 16.6, f"Expected 16.6g protein, got {summary['total_protein']}"
    assert len(summary["meals_by_type"]["Breakfast"]) == 2, "Breakfast entries count mismatch"
    print(f"  ✓ Summary calculated: Total Calories = {summary['total_calories']} kcal, Remaining = {summary['remaining_calories']} kcal")
    print(f"  ✓ Protein progress: {summary['total_protein']}g / {summary['target_protein']}g ({summary['protein_pct']}%)")

    # Personalized AI suggestions
    suggestions = database.get_personalized_suggestions(test_date)
    assert len(suggestions) > 0, "Expected at least 1 suggestion"
    print(f"  ✓ Generated {len(suggestions)} personalized meal recommendations:")
    for s in suggestions:
        print(f"    - {s['food']['name']} ({s['food']['calories']} kcal): {s['reason']}")

    # Clean up test meal entries
    database.delete_log(log1)
    database.delete_log(log2)
    print("  ✓ Cleaned up test logs cleanly.")

    # -------------------------------------------------------------
    # Test 6: Snacks Menu - Veg, Non-Veg, Search, Log & Delete
    # -------------------------------------------------------------
    print("\n[Test 6] Testing Snacks Menu: Veg, Non-Veg, Search, Add to Meals & Removal...")
    veg_snacks = database.get_snacks(diet_filter="vegetarian")
    non_veg_snacks = database.get_snacks(diet_filter="non-veg")
    all_snacks = database.get_snacks()

    assert len(veg_snacks) == 15, f"Expected 15 vegetarian snacks, got {len(veg_snacks)}"
    assert len(non_veg_snacks) == 12, f"Expected 12 non-vegetarian snacks, got {len(non_veg_snacks)}"
    assert len(all_snacks) == 27, f"Expected 27 total snacks, got {len(all_snacks)}"
    print(f"  ✓ Verified snack catalog: {len(veg_snacks)} Veg + {len(non_veg_snacks)} Non-Veg = {len(all_snacks)} Total")

    # Search test
    search_res = database.get_snacks(search_query="chicken momos")
    assert len(search_res) == 1, "Expected 1 search result for 'chicken momos'"
    momos = search_res[0]
    assert momos["calories"] == 190.0, f"Expected 190 kcal for Momos, got {momos['calories']}"
    print(f"  ✓ Search query 'chicken momos' returned: {momos['name']} ({momos['calories']} kcal, {momos['protein']}g protein)")

    # Add snack to diary
    snack_log_id = database.log_meal_item(
        meal_date=test_date,
        meal_type="Snack",
        food_name="Samosa",
        quantity=1.0,
        unit="piece (80g)",
        calories=260.0,
        protein=3.5,
        carbs=32.0,
        fat=13.0,
        image_path="/static/images/snacks/samosa.svg"
    )
    assert snack_log_id > 0, "Failed to log snack item"
    print(f"  ✓ Successfully added 'Samosa' to diary under 'Snack' (Log ID: {snack_log_id})")

    # Verify summary includes the snack
    snack_summary = database.get_daily_summary(test_date)
    assert len(snack_summary["meals_by_type"]["Snack"]) >= 1, "Expected snack to be present in summary"
    print(f"  ✓ Verified daily summary updated: Snack count = {len(snack_summary['meals_by_type']['Snack'])}, Total kcal = {snack_summary['total_calories']}")

    # Remove snack and verify clean removal
    database.delete_log(snack_log_id)
    post_delete_summary = database.get_daily_summary(test_date)
    assert len(post_delete_summary["meals_by_type"]["Snack"]) == 0, "Expected snack to be removed"
    print("  ✓ Successfully removed snack from diary and verified meal history deletion.")

    # -------------------------------------------------------------
    # Test 7: Meals Menu & Dinner Specials
    # -------------------------------------------------------------
    print("\n[Test 7] Testing Meals Menu & Dinner Specials...")
    veg_meals = database.get_meals(diet_filter="vegetarian")
    non_veg_meals = database.get_meals(diet_filter="non-veg")
    all_meals = database.get_meals()
    assert len(veg_meals) >= 10, f"Expected at least 10 veg meals, got {len(veg_meals)}"
    assert len(non_veg_meals) >= 8, f"Expected at least 8 non-veg meals, got {len(non_veg_meals)}"
    print(f"  ✓ Verified meals catalog: {len(veg_meals)} Veg Meals, {len(non_veg_meals)} Non-Veg Meals ({len(all_meals)} total meals)")

    palak_paneer = database.get_food_by_name("Palak Paneer")
    assert palak_paneer is not None, "Palak Paneer must be present"
    assert palak_paneer["price"] == 140.0, f"Expected 140.0 price, got {palak_paneer['price']}"
    assert palak_paneer["image_url"] == "/static/images/meals/palak_paneer.svg", "Image URL mismatch"
    print(f"  ✓ Verified Dinner Special: {palak_paneer['name']} (₹{palak_paneer['price']}, {palak_paneer['calories']} kcal, {palak_paneer['image_url']})")

    # -------------------------------------------------------------
    # Test 8: Food Delivery Order & Auto-Logging to Diary
    # -------------------------------------------------------------
    print("\n[Test 8] Testing Food Delivery Order Creation & Auto-Logging...")
    cart_sample = [
        {"food_id": palak_paneer["id"], "quantity": 1.0},
        {"food_id": momos["id"], "quantity": 1.0}
    ]
    order_id, order_num = database.create_delivery_order(
        customer_name="Alex Smith",
        phone="+91 98765 43210",
        delivery_address="Flat 402, Green Meadows Apt, Indiranagar, Bengaluru",
        delivery_slot="Instant Delivery (30-40 mins)",
        payment_method="Cash on Delivery",
        cart_items=cart_sample,
        auto_log_to_diary=True
    )
    assert order_id > 0, "Failed to create delivery order"
    assert "NUTRI-" in order_num, f"Order number invalid: {order_num}"

    order_details = database.get_order_details(order_id)
    assert order_details is not None, "Failed to retrieve order details"
    assert len(order_details["items"]) == 2, f"Expected 2 order items, got {len(order_details['items'])}"
    assert order_details["order"]["status"] == "Confirmed", "Status must be Confirmed"
    print(f"  ✓ Order created successfully: {order_num} (Total: ₹{order_details['order']['total_price']}, {order_details['order']['total_calories']} kcal)")

    # Advance status
    database.update_order_status(order_id, "Out for Delivery")
    updated_order = database.get_order_details(order_id)
    assert updated_order["order"]["status"] == "Out for Delivery", "Status update failed"
    print("  ✓ Order live tracking pipeline status updated to 'Out for Delivery'.")

    # Clean up test logs generated by auto_log
    today_str = date.today().isoformat()
    today_logs = database.get_logs_for_date(today_str)
    for t_log in today_logs:
        if t_log["food_name"] in ["Palak Paneer", "Chicken Momos"]:
            database.delete_log(t_log["id"])
    print("  ✓ Cleaned up auto-logged order test diary entries.")

    print("\n" + "=" * 60)
    print("✅ ALL METHODOLOGY STEPS, MEALS, SNACKS & DELIVERY TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
