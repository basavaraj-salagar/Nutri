"""
NutriTrack - AI-Based Food Recognition & Nutrition Tracking System
Main Flask Application with SQLite integration, AI food recognition, and personal analytics.
"""

import os
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename

import database
import ai_service

# Initialize Flask App
app = Flask(__name__)
app.secret_key = "nutritrack_super_secret_key_change_in_production"

# Configure Uploads
import tempfile

def _is_serverless_env():
    serverless_vars = (
        "VERCEL", "VERCEL_ENV", "VERCEL_URL", "VERCEL_REGION",
        "AWS_LAMBDA_FUNCTION_NAME", "AWS_EXECUTION_ENV", "LAMBDA_TASK_ROOT"
    )
    if any(k in os.environ for k in serverless_vars):
        return True
    try:
        test_path = os.path.join(app.root_path, ".write_test")
        with open(test_path, "w") as f:
            f.write("1")
        os.remove(test_path)
        return False
    except Exception:
        return True

if _is_serverless_env():
    UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), "nutritrack_uploads")
else:
    UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except Exception:
    UPLOAD_FOLDER = tempfile.gettempdir()

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload


def allowed_file(filename):
    """Checks whether uploaded file has a supported image extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Initialize database tables on app startup
try:
    database.init_db()
except Exception as e:
    print(f"Database initialization note: {e}")


# -------------------------------------------------------------------------
# Step 1: User Profile & Goals
# -------------------------------------------------------------------------
@app.route("/profile", methods=["GET", "POST"])
def profile_view():
    """
    Step 1: User Profile
    Displays user data, handles BMR/TDEE calculations, and updates SQLite.
    """
    if request.method == "POST":
        name = request.form.get("name", "User")
        age = request.form.get("age", 25)
        gender = request.form.get("gender", "male")
        height_cm = request.form.get("height_cm", 175)
        weight_kg = request.form.get("weight_kg", 70)
        activity_level = request.form.get("activity_level", "moderately_active")
        goal = request.form.get("goal", "maintenance")
        diet_preference = request.form.get("diet_preference", "all")

        try:
            database.save_profile(
                name=name,
                age=int(age),
                gender=gender,
                height_cm=float(height_cm),
                weight_kg=float(weight_kg),
                activity_level=activity_level,
                goal=goal,
                diet_preference=diet_preference
            )
            flash("✅ Profile and daily nutrition targets updated successfully!", "success")
        except Exception as e:
            flash(f"❌ Error updating profile: {str(e)}", "error")

        return redirect(url_for("profile_view"))

    profile = database.get_profile()
    return render_template("profile.html", profile=profile, active_page="profile")


# -------------------------------------------------------------------------
# Step 2: Upload Meal & Enter Ingredients
# -------------------------------------------------------------------------
@app.route("/upload", methods=["GET", "POST"])
def upload_view():
    """
    Step 2: Upload Meal
    Accepts meal photo or text ingredients and passes to AI Food Recognition.
    """
    if request.method == "POST":
        input_type = request.form.get("input_type", "text")
        meal_type = request.form.get("meal_type", "Lunch")
        image_filename = None

        if input_type == "image":
            # Image upload mode
            if "meal_image" not in request.files:
                flash("No image file provided in upload.", "error")
                return redirect(request.url)

            file = request.files["meal_image"]
            if file.filename == "":
                flash("No image file selected.", "warning")
                return redirect(request.url)

            if file and allowed_file(file.filename):
                safe_name = secure_filename(file.filename)
                save_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
                file.save(save_path)
                image_filename = safe_name

                food_hint = request.form.get("food_hint", "").strip()
                # Step 3: Run AI Visual Recognition (with optional user dish hint / Gemini vision)
                detected_items = ai_service.analyze_meal_photo(safe_name, save_path, food_hint=food_hint)
            else:
                flash("Invalid image format. Supported formats: JPG, PNG, WEBP, GIF.", "error")
                return redirect(request.url)

        else:
            # Text ingredients mode
            ingredients_text = request.form.get("ingredients_text", "").strip()
            if not ingredients_text:
                flash("Please enter at least one food ingredient.", "warning")
                return redirect(request.url)

            # Step 3: Run AI Text Recognition
            detected_items = ai_service.analyze_text_ingredients(ingredients_text)

        today_date = date.today().isoformat()
        return render_template(
            "review.html",
            detected_items=detected_items,
            meal_type=meal_type,
            image_filename=image_filename,
            today_date=today_date,
            active_page="upload"
        )

    return render_template("upload.html", active_page="upload")


@app.route("/api/analyze-ingredients", methods=["POST"])
def api_analyze_ingredients():
    """
    Analyzes structured ingredients from the recipe builder,
    calculates nutrition totals and individual ingredient breakdowns.
    """
    data = request.get_json(silent=True) or request.form
    dish_name = data.get("dish_name", "").strip()
    cooking_method = data.get("cooking_method", "pan_cooked")
    try:
        portion_multiplier = float(data.get("portion_multiplier", 1.0))
    except (ValueError, TypeError):
        portion_multiplier = 1.0

    raw_ingredients = data.get("ingredients", [])
    if isinstance(raw_ingredients, str):
        try:
            import json
            raw_ingredients = json.loads(raw_ingredients)
        except Exception:
            raw_ingredients = []

    analysis = ai_service.analyze_structured_ingredients(
        dish_name=dish_name,
        ingredients_list=raw_ingredients,
        cooking_method=cooking_method,
        portion_multiplier=portion_multiplier
    )
    return jsonify({"success": True, "data": analysis})


@app.route("/api/save-analyzed-meal", methods=["POST"])
def api_save_analyzed_meal():
    """
    Saves an analyzed recipe/dish directly into SQLite meal_logs table.
    """
    data = request.get_json(silent=True) or request.form
    meal_date = data.get("meal_date") or date.today().isoformat()
    meal_type = data.get("meal_type") or "Lunch"
    dish_name = data.get("dish_name", "Analyzed Meal").strip()
    image_path = data.get("image_path", None)

    try:
        total_calories = float(data.get("calories", 0.0))
        total_protein = float(data.get("protein", 0.0))
        total_carbs = float(data.get("carbs", 0.0))
        total_fat = float(data.get("fat", 0.0))
        serving_description = data.get("serving_description", "1 portion")
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid nutrition numbers."}), 400

    log_id = database.log_meal_item(
        meal_date=meal_date,
        meal_type=meal_type,
        food_name=dish_name,
        quantity=1.0,
        unit=serving_description,
        calories=total_calories,
        protein=total_protein,
        carbs=total_carbs,
        fat=total_fat,
        image_path=image_path
    )

    if request.is_json:
        return jsonify({
            "success": True,
            "message": f"🎉 Saved {dish_name} ({total_calories} kcal) to your {meal_type} diary!",
            "log_id": log_id,
            "redirect_url": url_for("summary_view", date=meal_date)
        })

    flash(f"🎉 Saved {dish_name} ({total_calories} kcal) to your {meal_type} diary!", "success")
    return redirect(url_for("summary_view", date=meal_date))


# -------------------------------------------------------------------------
# Step 3 & 5: AI Recognition Review & Save Meal to Diary
# -------------------------------------------------------------------------
@app.route("/save-meal", methods=["POST"])
def save_meal_view():
    """
    Step 5: User Reviews & Log Meals
    Saves confirmed items with adjusted portions to SQLite meal_logs table.
    """
    try:
        total_items = int(request.form.get("total_items", 0))
        meal_date = request.form.get("meal_date", date.today().isoformat())
        meal_type = request.form.get("confirmed_meal_type", "Lunch")
        image_path = request.form.get("image_path", None)

        saved_count = 0
        for i in range(total_items):
            food_name = request.form.get(f"food_name_{i}")
            if not food_name:
                continue

            quantity = float(request.form.get(f"quantity_{i}", 1.0))
            unit = request.form.get(f"unit_{i}", "serving")
            calories = float(request.form.get(f"calories_{i}", 0.0))
            protein = float(request.form.get(f"protein_{i}", 0.0))
            carbs = float(request.form.get(f"carbs_{i}", 0.0))
            fat = float(request.form.get(f"fat_{i}", 0.0))

            database.log_meal_item(
                meal_date=meal_date,
                meal_type=meal_type,
                food_name=food_name,
                quantity=quantity,
                unit=unit,
                calories=calories,
                protein=protein,
                carbs=carbs,
                fat=fat,
                image_path=image_path
            )
            saved_count += 1

        flash(f"🎉 Successfully logged {saved_count} items for {meal_type} on {meal_date}!", "success")
    except Exception as e:
        flash(f"❌ Error saving meal: {str(e)}", "error")

    return redirect(url_for("summary_view", date=meal_date))


# -------------------------------------------------------------------------
# Step 4: Nutrition Database
# -------------------------------------------------------------------------
@app.route("/database", methods=["GET"])
def database_view():
    """
    Step 4: Nutrition Database
    Lists food items, supports real-time search, and category filtering.
    """
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "All")

    if query:
        foods = database.search_foods(query)
    elif category and category != "All":
        foods = database.get_all_foods(category_filter=category)
    else:
        foods = database.get_all_foods()

    return render_template(
        "database.html",
        foods=foods,
        search_query=query,
        selected_category=category,
        active_page="database"
    )


@app.route("/database/add", methods=["POST"])
def add_food_view():
    """
    Step 4: Add Custom Food
    Inserts a custom food into SQLite foods table.
    """
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "Dishes")
    serving_size = request.form.get("serving_size", 100)
    serving_unit = request.form.get("serving_unit", "g")
    calories = request.form.get("calories", 0)
    protein = request.form.get("protein", 0)
    carbs = request.form.get("carbs", 0)
    fat = request.form.get("fat", 0)
    diet_type = request.form.get("diet_type", "all")

    if not name:
        flash("Food name cannot be empty.", "warning")
        return redirect(url_for("database_view"))

    success = database.add_custom_food(
        name=name,
        category=category,
        serving_size=serving_size,
        serving_unit=serving_unit,
        calories=calories,
        protein=protein,
        carbs=carbs,
        fat=fat,
        diet_type=diet_type
    )

    if success:
        flash(f"✅ '{name}' was added to the Nutrition Database!", "success")
    else:
        flash(f"⚠️ A food item named '{name}' already exists in the database.", "warning")

    return redirect(url_for("database_view"))


@app.route("/database/quick-log", methods=["POST"])
def quick_log_view():
    """
    Quick log a food directly from the database table into today's diary.
    """
    food_id = request.form.get("food_id")
    meal_type = request.form.get("meal_type", "Snack")
    quantity = float(request.form.get("quantity", 1.0))
    today_date = date.today().isoformat()

    food = database.get_food_by_id(food_id)
    if food:
        cal = round(food["calories"] * quantity, 1)
        pro = round(food["protein"] * quantity, 1)
        carb = round(food["carbs"] * quantity, 1)
        fat = round(food["fat"] * quantity, 1)

        database.log_meal_item(
            meal_date=today_date,
            meal_type=meal_type,
            food_name=food["name"],
            quantity=quantity,
            unit=food["serving_unit"],
            calories=cal,
            protein=pro,
            carbs=carb,
            fat=fat
        )
        flash(f"✅ Added {quantity} &times; {food['name']} to {meal_type}!", "success")
    else:
        flash("Food item not found.", "error")

    return redirect(url_for("summary_view", date=today_date))


# -------------------------------------------------------------------------
# Veg & Non-Veg Meals Menu (Meals & Dinner Specials)
# -------------------------------------------------------------------------
@app.route("/meals", methods=["GET"])
def meals_view():
    """
    Renders the complete Meals & Dinner Specials Menu featuring:
    - 🥗 Veg Meals
    - 🍗 Non-Veg Meals
    - 🌙 Dinner Specials
    - 🍽️ All Meals
    """
    veg_meals = database.get_meals(diet_filter="vegetarian")
    non_veg_meals = database.get_meals(diet_filter="non-veg")
    all_meals = database.get_meals()

    dinner_names = {
        'Palak Paneer', 'Dal Makhani', 'Butter Chicken', 'Chicken Korma',
        'Moong Dal Khichdi', 'Tandoori Roti Basket (3 pcs)', 'Methi Thepla (3 pcs)',
        'Grilled Fish with Steamed Veggies', 'Paneer Butter Masala', 'Veg Biryani', 'Chicken Biryani'
    }
    dinner_meals = [m for m in all_meals if m["name"] in dinner_names or "dinner" in m["category"].lower()]

    today_date = date.today().isoformat()
    daily_summary = database.get_daily_summary(today_date)

    return render_template(
        "meals.html",
        veg_meals=veg_meals,
        non_veg_meals=non_veg_meals,
        dinner_meals=dinner_meals,
        all_meals=all_meals,
        today_date=today_date,
        daily_summary=daily_summary,
        active_page="meals"
    )


# -------------------------------------------------------------------------
# Snacks Menu (Veg, Non-Veg, All Snacks)
# -------------------------------------------------------------------------
@app.route("/snacks", methods=["GET"])
def snacks_view():
    """
    Renders the complete Snacks Menu featuring:
    - 🥗 Veg Snacks (15 items)
    - 🍗 Non-Veg Snacks (12 items)
    - 🍿 All Snacks (27 items)
    """
    veg_snacks = database.get_snacks(diet_filter="vegetarian")
    non_veg_snacks = database.get_snacks(diet_filter="non-veg")
    all_snacks = database.get_snacks()
    today_date = date.today().isoformat()
    daily_summary = database.get_daily_summary(today_date)

    return render_template(
        "snacks.html",
        veg_snacks=veg_snacks,
        non_veg_snacks=non_veg_snacks,
        all_snacks=all_snacks,
        today_date=today_date,
        daily_summary=daily_summary,
        active_page="snacks"
    )


@app.route("/api/add-snack", methods=["POST"])
def add_snack_api():
    """
    Adds a selected snack to the user's daily diary.
    Supports both AJAX JSON requests and standard form submissions.
    """
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json
    data = request.get_json(silent=True) or request.form

    food_id = data.get("food_id")
    quantity = float(data.get("quantity", 1.0))
    meal_date = data.get("meal_date", date.today().isoformat())
    meal_type = data.get("meal_type", "Snack")

    food = database.get_food_by_id(food_id)
    if not food:
        if is_ajax:
            return jsonify({"success": False, "message": "Snack item not found."}), 404
        flash("Snack item not found.", "error")
        return redirect(url_for("snacks_view"))

    cal = round(food["calories"] * quantity, 1)
    pro = round(food["protein"] * quantity, 1)
    carb = round(food["carbs"] * quantity, 1)
    fat = round(food["fat"] * quantity, 1)

    log_id = database.log_meal_item(
        meal_date=meal_date,
        meal_type=meal_type,
        food_name=food["name"],
        quantity=quantity,
        unit=food["serving_unit"],
        calories=cal,
        protein=pro,
        carbs=carb,
        fat=fat,
        image_path=food["image_url"]
    )

    updated_summary = database.get_daily_summary(meal_date)
    success_msg = f"Added {quantity}x {food['name']} ({cal} kcal) to today's {meal_type}!"

    if is_ajax:
        return jsonify({
            "success": True,
            "message": success_msg,
            "log_id": log_id,
            "item_name": food["name"],
            "calories": cal,
            "summary": {
                "total_calories": updated_summary["total_calories"],
                "total_protein": updated_summary["total_protein"],
                "total_carbs": updated_summary["total_carbs"],
                "total_fat": updated_summary["total_fat"],
                "remaining_calories": updated_summary["remaining_calories"]
            }
        })

    flash(f"✅ {success_msg}", "success")
    return redirect(url_for("summary_view", date=meal_date))


# -------------------------------------------------------------------------
# Step 6: Personalized Summary & Recommendations
# -------------------------------------------------------------------------
@app.route("/")
@app.route("/summary", methods=["GET"])
def summary_view():
    """
    Step 6: Personalized Summary & Recommendations
    Displays daily calorie/macro breakdown, logged meals, and AI suggestions.
    """
    selected_date = request.args.get("date", date.today().isoformat())
    profile = database.get_profile()
    summary = database.get_daily_summary(selected_date)
    suggestions = database.get_personalized_suggestions(selected_date)

    return render_template(
        "summary.html",
        profile=profile,
        summary=summary,
        suggestions=suggestions,
        selected_date=selected_date,
        active_page="summary"
    )


@app.route("/delete-log/<int:log_id>", methods=["POST"])
def delete_meal_log_view(log_id):
    """
    Deletes a logged meal entry from SQLite.
    """
    meal_date = request.form.get("date", date.today().isoformat())
    database.delete_log(log_id)
    flash("🗑️ Meal entry removed from your diary.", "success")
    return redirect(url_for("summary_view", date=meal_date))


@app.route("/edit-log/<int:log_id>", methods=["POST"])
def edit_meal_log_view(log_id):
    """
    Updates a logged meal's portion/quantity and updates daily nutrition totals.
    """
    meal_date = request.form.get("date", date.today().isoformat())
    try:
        new_quantity = float(request.form.get("quantity", 1.0))
        if new_quantity <= 0:
            flash("Portion quantity must be greater than zero.", "warning")
        else:
            success = database.update_meal_log_quantity(log_id, new_quantity)
            if success:
                flash(f"✏️ Meal portion updated to {new_quantity} serving(s).", "success")
            else:
                flash("Meal entry not found.", "error")
    except ValueError:
        flash("Invalid quantity entered.", "error")

    return redirect(url_for("summary_view", date=meal_date))


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    """Serves uploaded meal photos reliably in local and serverless environments."""
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# -------------------------------------------------------------------------
# JSON API (for dynamic search or frontend integration)
# -------------------------------------------------------------------------
@app.route("/api/search", methods=["GET"])
def api_search_foods():
    """Returns JSON list of matching foods for autocomplete."""
    q = request.args.get("q", "")
    foods = database.search_foods(q)
    results = [
        {
            "id": f["id"],
            "name": f["name"],
            "category": f["category"],
            "calories": f["calories"],
            "protein": f["protein"],
            "carbs": f["carbs"],
            "fat": f["fat"],
            "serving": f"{f['serving_size']} {f['serving_unit']}"
        }
        for f in foods
    ]
    return jsonify(results)


# -------------------------------------------------------------------------
# Food Delivery System Routes
# -------------------------------------------------------------------------
@app.route("/delivery", methods=["GET"])
def delivery_view():
    """
    Renders the NutriTrack Food Delivery Hub:
    Browse healthy meals and snacks with prices and nutrition,
    manage your delivery cart, and place orders.
    """
    category = request.args.get("cat", "all")
    query = request.args.get("q", "").strip()

    foods = database.get_delivery_foods(
        category_filter=category if category != "all" else None,
        search_query=query if query else None
    )
    profile = database.get_profile()

    return render_template(
        "delivery.html",
        foods=foods,
        profile=profile,
        selected_category=category,
        search_query=query,
        active_page="delivery"
    )


@app.route("/checkout", methods=["POST"])
def checkout_view():
    """
    Processes delivery checkout:
    Validates cart items, records order into SQLite orders & order_items,
    optionally auto-logs to today's diary, and redirects to live order tracking.
    """
    import json

    customer_name = request.form.get("customer_name", "Valued Customer").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    delivery_slot = request.form.get("delivery_slot", "Instant Delivery (30-40 mins)")
    payment_method = request.form.get("payment_method", "Cash on Delivery")
    auto_log = request.form.get("auto_log", "off") == "on"

    cart_raw = request.form.get("cart_data", "[]")
    try:
        cart_items = json.loads(cart_raw)
    except Exception:
        cart_items = []

    if not cart_items:
        flash("Your delivery cart is empty! Please add items before checking out.", "warning")
        return redirect(url_for("delivery_view"))

    if not address or not phone:
        flash("Please provide your delivery address and phone number.", "warning")
        return redirect(url_for("delivery_view"))

    order_id, order_num = database.create_delivery_order(
        customer_name=customer_name,
        phone=phone,
        delivery_address=address,
        delivery_slot=delivery_slot,
        payment_method=payment_method,
        cart_items=cart_items,
        auto_log_to_diary=auto_log
    )

    if auto_log:
        flash(f"🎉 Order {order_num} confirmed! Meal items were automatically logged to today's diary.", "success")
    else:
        flash(f"🎉 Order {order_num} placed successfully! Tracking your delivery below.", "success")

    return redirect(url_for("track_order_view", order_id=order_id))


@app.route("/track/<int:order_id>", methods=["GET"])
def track_order_view(order_id):
    """
    Live delivery order tracking page with visual pipeline status,
    assigned rider info, delivery address, and nutrition summary.
    """
    order_data = database.get_order_details(order_id)
    if not order_data:
        flash("Order not found.", "error")
        return redirect(url_for("delivery_view"))

    return render_template(
        "track_order.html",
        order=order_data["order"],
        items=order_data["items"],
        active_page="delivery"
    )


@app.route("/orders", methods=["GET"])
def orders_history_view():
    """
    Lists customer delivery order history with status, items, and re-track options.
    """
    orders = database.get_all_orders()
    return render_template(
        "orders.html",
        orders=orders,
        active_page="delivery"
    )


@app.route("/api/orders/<int:order_id>/status", methods=["POST"])
def api_update_order_status(order_id):
    """
    API endpoint to advance or test delivery status transitions:
    Confirmed -> Preparing with Fresh Ingredients -> Out for Delivery -> Delivered
    """
    data = request.get_json(silent=True) or request.form
    new_status = data.get("status")
    valid_statuses = [
        "Confirmed",
        "Preparing with Fresh Ingredients",
        "Out for Delivery",
        "Delivered"
    ]
    if new_status in valid_statuses:
        database.update_order_status(order_id, new_status)
        return jsonify({"success": True, "status": new_status})
    return jsonify({"success": False, "error": "Invalid status."}), 400


# -------------------------------------------------------------------------
# Application Entry Point
# -------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 60)
    print("🥗 NutriTrack - AI Food Recognition & Tracking System")
    print(f"🚀 Server running on http://127.0.0.1:{port}")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=False)
