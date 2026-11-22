# NutriTrack - AI-Based Food Recognition & Nutrition Tracking System

**NutriTrack** is a production-grade, full-stack Python Flask web application and SQLite database engineered according to the 6-step methodology architecture diagram defined in `nutri.py`.

It combines real-time AI food recognition, macro-nutrient calculation, a complete vegetarian & non-vegetarian meals catalog, an extensive snacks menu, healthy dinner specials, and an end-to-end food delivery system with live order tracking and automated diary logging.

---

## 🌟 Core Modules & Features

### 1. 🏗️ 6 Methodology Steps
1. **User Profile & Targets (`/profile`)**:
   - Calculates BMR & TDEE using the Mifflin-St Jeor formula.
   - Computes daily calorie targets and protein/carbs/fat macro distributions based on goals (weight loss, muscle gain, maintenance).
2. **Upload Meal (`/upload`)**:
   - Multimodal inputs: drag-and-drop meal photo upload (JPG, PNG, WEBP) or natural language ingredient lists.
3. **AI Food Recognition (`ai_service.py`)**:
   - Dual-engine parsing: natural language entity parser and heuristic visual tag recognizer.
4. **Nutrition Database (`/database`)**:
   - 77+ pre-seeded nutritious items with food image thumbnails, search, category filter, and custom food creator.
5. **Portion Adjustment & User Review (`/review`, `/save-meal`)**:
   - Interactive review table with portion multipliers, real-time macro calculations, and diary logging.
6. **Daily Summary & Analytics (`/summary`)**:
   - Real-time calorie and macro progress rings, meal timeline with itemized image thumbnails, and intelligent AI recommendations.

### 2. 🍛 Veg & Non-Veg Meals Menu (`/meals`)
- **🥗 Vegetarian Meals**: Idli, Dosa, Vegetable Pulao, Paneer Butter Masala, Chapati, Dal Rice, Veg Biryani, Curd Rice.
- **🍗 Non-Vegetarian Meals**: Chicken Biryani, Chicken Curry, Egg Fried Rice, Boiled Eggs, Fish Curry, Chicken Tikka, Egg Curry, Chicken Rice.
- **🌙 Dinner Specials**: Palak Paneer, Dal Makhani, Butter Chicken, Chicken Korma, Moong Dal Khichdi, Tandoori Roti Basket, Methi Thepla, Grilled Fish with Steamed Veggies.
- Instant tab switching without page reload.
- Calibrated medium prices (₹15 to ₹190).
- One-click "+ Add to Diary" and "🛵 Order for Delivery".

### 3. 🍿 Complete Snacks Menu (`/snacks`)
- **15 Vegetarian Snacks**: Samosa, Masala Puri, Pani Puri, Bhel Puri, Veg Sandwich, Veg Puff, French Fries, Onion Pakoda, Paneer Tikka, Aloo Tikki, Dhokla, Spring Rolls, Roasted Peanuts, Sweet Corn, Banana Chips.
- **12 Non-Vegetarian Snacks**: Chicken Nuggets, Chicken Sandwich, Chicken Momos, Chicken Tikka, Chicken 65, Egg Puff, Boiled Eggs, Egg Roll, Fish Fingers, Chicken Cutlet, Chicken Pakoda, Egg Sandwich.
- Search by name, category filters, nutrition estimates, and AJAX logging.

### 4. 🛵 Healthy Food Delivery & Live Tracking (`/delivery`, `/orders`, `/track/<id>`)
- **Browse & Filter**: Filter by All, Dinner Specials, Full Meals, Snacks, Veg Only, and Non-Veg Only.
- **Slide-Over Cart Drawer**: Slide-over drawer with item thumbnails, quantity controls, live macro counter (order calories, protein, carbs, fat).
- **Checkout & Auto-Log Synergy**: Place order with delivery slot, address, and an optional toggle to automatically log the ordered food into today's NutriTrack diary.
- **Live 4-Step Order Tracking**: Visual pipeline status:
  `Confirmed` ➔ `Preparing with Fresh Ingredients` ➔ `Out for Delivery` ➔ `Delivered`.
- **Rider Card & Invoice**: Assigned delivery partner info, direct phone hotline, and itemized invoice breakdown.

### 5. 🎨 72+ Local Vector Food Illustrations (SVGs)
- All meal and snack cards feature custom, crisp SVG vector food graphics stored locally in `static/images/meals/` and `static/images/snacks/` (zero external CDN or network dependencies).

---

## 📂 Project Structure

```
NutriTrack/
├── nutri.py                  # Original 6-step methodology diagram (untouched)
├── app.py                    # Flask web application and all route handlers
├── database.py               # SQLite schema, migrations, CRUD, and orders engine
├── ai_service.py             # Entity parsing and visual heuristic recognition engine
├── nutritrack.db             # SQLite database file
├── test_nutritrack.py        # Automated test suite (all tests passing)
├── requirements.txt          # Python dependencies (Flask, Werkzeug)
├── start.bat                 # Windows one-click startup script
├── static/
│   ├── css/
│   │   └── style.css         # Modern responsive CSS, cart drawer & stepper styling
│   ├── images/
│   │   ├── meals/            # 45 vector SVG graphics for meals and dinner items
│   │   └── snacks/           # 27 vector SVG graphics for snacks
│   └── uploads/              # Upload folder for user meal photos
└── templates/
    ├── base.html             # Global header, navbar, footer & floating cart button
    ├── summary.html          # Daily diary, progress bars & AI recommendations
    ├── meals.html            # Veg & Non-Veg Meals and Dinner Specials Menu
    ├── snacks.html           # 27 snacks catalog with search & filters
    ├── delivery.html         # Delivery catalog, category tabs & slide-over cart
    ├── track_order.html      # Live 4-step order tracking pipeline
    ├── orders.html           # Order history & status badges
    ├── upload.html           # Meal upload & ingredient input
    ├── review.html           # AI recognition review & confirmation
    ├── database.html         # Nutrition database browser with food thumbnails
    └── profile.html          # User profile, BMR/TDEE & target recalculation
```

---

## 🚀 Quickstart Guide

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Run the Server
```powershell
python app.py
```
Open **http://127.0.0.1:5000** in your browser.

### 3. Run Automated Tests
```powershell
python test_nutritrack.py
```
"# nutritrack" 
