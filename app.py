import sqlite3
import os
from flask import Flask, g, render_template, request, redirect, url_for, jsonify, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import date, timedelta, datetime
import joblib
import numpy as np
import bcrypt
from dotenv import load_dotenv
import json
from ai_nutrition_service import AInutritionService

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'fallback_secret_key_for_development')
DATABASE = "database.db"

# Initialize AI nutrition service
ai_service = AInutritionService()

# Load existing calorie prediction model if it exists
try:
    calorie_model = joblib.load("calorie_predictor.pkl")
except:
    calorie_model = None

def predict_calories(weight, sleep, exercise, previous_cal):
    if calorie_model:
        features = np.array([[weight, sleep, exercise, previous_cal]])
        return int(calorie_model.predict(features)[0])
    return 2000  # fallback

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

# Login Manager Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, password, profile_data=None):
        self.id = id
        self.username = username
        self.password = password
        self.profile_data = profile_data or {}

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if user:
        # Load user profile
        profile = db.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)).fetchone()
        profile_data = dict(profile) if profile else {}
        return User(user["id"], user["username"], user["password"], profile_data)
    return None

def init_db():
    db = get_db()

    # Users table
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Enhanced user profiles
    db.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            age INTEGER,
            gender TEXT,
            height_cm REAL,
            weight_kg REAL,
            activity_level TEXT DEFAULT 'moderate',
            health_goals TEXT,
            dietary_preferences TEXT,
            calorie_target INTEGER DEFAULT 2000,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Enhanced meals table with nutrition data
    db.execute("""
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            calories INTEGER NOT NULL,
            protein_g REAL DEFAULT 0,
            carbs_g REAL DEFAULT 0,
            fat_g REAL DEFAULT 0,
            fiber_g REAL DEFAULT 0,
            sodium_mg REAL DEFAULT 0,
            meal_category TEXT DEFAULT 'meal',
            health_score INTEGER DEFAULT 5,
            ai_analyzed BOOLEAN DEFAULT FALSE,
            day TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Keep existing tables for backward compatibility
    db.execute("""
        CREATE TABLE IF NOT EXISTS exercise (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            calories_burned INTEGER NOT NULL,
            duration_minutes INTEGER DEFAULT 0,
            exercise_type TEXT DEFAULT 'general',
            day TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS weight (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            weight REAL NOT NULL,
            day TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS sleep (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hours REAL NOT NULL,
            quality INTEGER DEFAULT 5,
            day TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS water (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            day TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # AI meal plans table
    db.execute("""
        CREATE TABLE IF NOT EXISTS meal_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan_name TEXT NOT NULL,
            plan_data TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            is_active BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Health insights table
    db.execute("""
        CREATE TABLE IF NOT EXISTS health_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            insight_type TEXT NOT NULL,
            insight_data TEXT NOT NULL,
            generated_date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    db.commit()

# Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        db = get_db()
        existing_user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if existing_user:
            flash("Username already exists! Try another.", "error")
            return render_template('register.html')

        # Insert user
        cursor = db.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                          (username, hashed_password))
        user_id = cursor.lastrowid
        
        # Create default profile
        db.execute("""INSERT INTO user_profiles (user_id, health_goals, dietary_preferences) 
                     VALUES (?, ?, ?)""", (user_id, "general health", ""))
        db.commit()
        
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            profile = db.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user['id'],)).fetchone()
            profile_data = dict(profile) if profile else {}
            user_obj = User(user['id'], user['username'], user['password'], profile_data)
            login_user(user_obj)
            return redirect(url_for('dashboard'))
        
        flash("Invalid username or password!", "error")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    db = get_db()
    
    if request.method == 'POST':
        # Update user profile
        age = request.form.get('age', type=int)
        gender = request.form.get('gender')
        height_cm = request.form.get('height_cm', type=float)
        weight_kg = request.form.get('weight_kg', type=float)
        activity_level = request.form.get('activity_level')
        health_goals = request.form.get('health_goals')
        dietary_preferences = request.form.get('dietary_preferences')
        calorie_target = request.form.get('calorie_target', type=int)
        
        # Check if profile exists
        existing_profile = db.execute("SELECT * FROM user_profiles WHERE user_id = ?", 
                                    (current_user.id,)).fetchone()
        
        if existing_profile:
            db.execute("""UPDATE user_profiles SET 
                         age=?, gender=?, height_cm=?, weight_kg=?, activity_level=?, 
                         health_goals=?, dietary_preferences=?, calorie_target=?, 
                         updated_at=CURRENT_TIMESTAMP 
                         WHERE user_id=?""",
                      (age, gender, height_cm, weight_kg, activity_level, 
                       health_goals, dietary_preferences, calorie_target, current_user.id))
        else:
            db.execute("""INSERT INTO user_profiles 
                         (user_id, age, gender, height_cm, weight_kg, activity_level, 
                          health_goals, dietary_preferences, calorie_target) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                      (current_user.id, age, gender, height_cm, weight_kg, activity_level, 
                       health_goals, dietary_preferences, calorie_target))
        
        db.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('profile'))
    
    # Get current profile
    profile = db.execute("SELECT * FROM user_profiles WHERE user_id = ?", 
                        (current_user.id,)).fetchone()
    
    return render_template('profile.html', profile=profile)

@app.route('/dashboard')
@login_required
def dashboard():
    today = date.today().isoformat()
    db = get_db()

    # Get user profile for calorie target
    profile = db.execute("SELECT * FROM user_profiles WHERE user_id = ?", 
                        (current_user.id,)).fetchone()
    calorie_target = profile['calorie_target'] if profile else 2000

    # Enhanced meals data
    meals = db.execute("""SELECT * FROM meals WHERE day = ? AND user_id = ? 
                         ORDER BY created_at DESC""", (today, current_user.id)).fetchall()
    total_cal = sum(m["calories"] for m in meals)
    total_protein = sum(m["protein_g"] or 0 for m in meals)
    total_carbs = sum(m["carbs_g"] or 0 for m in meals)
    total_fat = sum(m["fat_g"] or 0 for m in meals)

    # Water tracking
    water_row = db.execute("SELECT SUM(amount) AS total_water FROM water WHERE day = ? AND user_id = ?", 
                          (today, current_user.id)).fetchone()
    water = water_row["total_water"] or 0

    # Exercise data
    exercises = db.execute("SELECT * FROM exercise WHERE day = ? AND user_id = ? ORDER BY created_at DESC", 
                          (today, current_user.id)).fetchall()
    total_exercise_cal = sum(e["calories_burned"] for e in exercises)

    # Weight (latest)
    latest_weight_row = db.execute("SELECT weight, day FROM weight WHERE user_id = ? ORDER BY day DESC, id DESC LIMIT 1", 
                                  (current_user.id,)).fetchone()
    latest_weight = latest_weight_row["weight"] if latest_weight_row else None

    # Sleep
    sleep_row = db.execute("SELECT hours, quality FROM sleep WHERE day = ? AND user_id = ?", 
                          (today, current_user.id)).fetchone()
    sleep_hours = sleep_row["hours"] if sleep_row else 0
    sleep_quality = sleep_row["quality"] if sleep_row else 5

    # AI Smart Suggestions
    suggestions = generate_smart_suggestions(total_cal, water, sleep_hours, total_exercise_cal, 
                                           calorie_target, total_protein, total_carbs, total_fat)

    # Progress percentages
    calorie_progress = min((total_cal / calorie_target) * 100, 100) if calorie_target > 0 else 0
    water_progress = min((water / 2000) * 100, 100)  # 2L target
    exercise_progress = min((total_exercise_cal / 300) * 100, 100)  # 300 cal target

    return render_template("dashboard.html", 
                          meals=meals, total_cal=total_cal, calorie_target=calorie_target,
                          total_protein=total_protein, total_carbs=total_carbs, total_fat=total_fat,
                          water=water, exercises=exercises, total_exercise_cal=total_exercise_cal,
                          latest_weight=latest_weight, today=today, sleep_hours=sleep_hours,
                          sleep_quality=sleep_quality, suggestions=suggestions,
                          calorie_progress=calorie_progress, water_progress=water_progress,
                          exercise_progress=exercise_progress)

def generate_smart_suggestions(total_cal, water, sleep_hours, exercise_cal, calorie_target, protein, carbs, fat):
    """Generate AI-like smart suggestions based on daily data"""
    suggestions = []
    
    # Calorie suggestions
    if total_cal < calorie_target * 0.7:
        suggestions.append({"type": "warning", "icon": "🍽️", 
                          "text": "You're quite low on calories today. Consider a nutritious snack."})
    elif total_cal > calorie_target * 1.2:
        suggestions.append({"type": "info", "icon": "⚠️", 
                          "text": "You're over your calorie target. Light dinner might be wise."})

    # Water suggestions
    if water < 1500:
        suggestions.append({"type": "info", "icon": "💧", 
                          "text": "Stay hydrated! Aim for at least 2L of water daily."})

    # Sleep suggestions
    if sleep_hours < 6:
        suggestions.append({"type": "warning", "icon": "😴", 
                          "text": "Try to get 7-9 hours of sleep for optimal recovery."})

    # Exercise suggestions
    if exercise_cal < 150:
        suggestions.append({"type": "info", "icon": "🏃‍♂️", 
                          "text": "Consider some light exercise or a walk today."})

    # Nutrition balance
    if protein < 50:
        suggestions.append({"type": "info", "icon": "🥩", 
                          "text": "Try to include more protein-rich foods today."})

    return suggestions

# AI-Enhanced Meal Addition
@app.route("/add-meal", methods=["POST"])
@login_required
def add_meal():
    meal_description = request.form["description"]
    portion_size = request.form.get("portion_size", "normal")
    
    # Use AI to analyze the meal
    ai_analysis = ai_service.analyze_meal(meal_description, portion_size)
    
    today = date.today().isoformat()
    db = get_db()
    
    # Insert meal with AI analysis
    db.execute("""
        INSERT INTO meals (name, description, calories, protein_g, carbs_g, fat_g, fiber_g, 
                          sodium_mg, meal_category, health_score, ai_analyzed, day, user_id) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ai_analysis["meal_name"], meal_description, ai_analysis["calories"],
        ai_analysis["macronutrients"]["protein_g"], ai_analysis["macronutrients"]["carbohydrates_g"],
        ai_analysis["macronutrients"]["fat_g"], ai_analysis["macronutrients"]["fiber_g"],
        ai_analysis["micronutrients"]["sodium_mg"], ai_analysis["meal_category"],
        ai_analysis["health_score"], True, today, current_user.id
    ))
    
    db.commit()
    flash(f"Added {ai_analysis['meal_name']} with AI nutrition analysis!", "success")
    return redirect(url_for("dashboard"))

# Meal improvement suggestions
@app.route("/improve-meal/<int:meal_id>")
@login_required
def improve_meal(meal_id):
    db = get_db()
    meal = db.execute("SELECT * FROM meals WHERE id = ? AND user_id = ?", 
                     (meal_id, current_user.id)).fetchone()
    
    if not meal:
        flash("Meal not found!", "error")
        return redirect(url_for("dashboard"))
    
    # Get user health goals
    profile = db.execute("SELECT health_goals FROM user_profiles WHERE user_id = ?", 
                        (current_user.id,)).fetchone()
    health_goals = profile["health_goals"].split(",") if profile and profile["health_goals"] else []
    
    # Get AI suggestions
    suggestions = ai_service.suggest_meal_improvements(meal["description"], health_goals)
    
    return render_template("meal_improvements.html", meal=meal, suggestions=suggestions)

# AI Meal Planning
@app.route("/ai-meal-plan")
@login_required
def ai_meal_plan():
    db = get_db()
    profile = db.execute("SELECT * FROM user_profiles WHERE user_id = ?", 
                        (current_user.id,)).fetchone()
    
    if not profile:
        flash("Please complete your profile first!", "warning")
        return redirect(url_for("profile"))
    
    # Prepare user profile for AI
    user_profile = {
        "age": profile["age"],
        "gender": profile["gender"],
        "weight": profile["weight_kg"],
        "height": profile["height_cm"],
        "activity_level": profile["activity_level"],
        "goals": profile["health_goals"]
    }
    
    dietary_preferences = profile["dietary_preferences"].split(",") if profile["dietary_preferences"] else []
    calorie_target = profile["calorie_target"] or 2000
    
    # Generate 7-day meal plan
    meal_plan = ai_service.generate_meal_plan(user_profile, dietary_preferences, calorie_target, 7)
    
    # Save meal plan to database
    plan_data = json.dumps(meal_plan)
    start_date = date.today().isoformat()
    end_date = (date.today() + timedelta(days=6)).isoformat()
    
    db.execute("""INSERT INTO meal_plans (user_id, plan_name, plan_data, start_date, end_date, is_active) 
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (current_user.id, "AI Generated Plan", plan_data, start_date, end_date, True))
    db.commit()
    
    return render_template("ai_meal_plan.html", meal_plan=meal_plan)

# Health Insights
@app.route("/health-insights")
@login_required
def health_insights():
    db = get_db()
    
    # Get last 7 days of nutrition data
    end_date = date.today()
    start_date = end_date - timedelta(days=6)
    
    nutrition_data = {}
    for i in range(7):
        current_date = (start_date + timedelta(days=i)).isoformat()
        
        # Get meals for this day
        meals = db.execute("SELECT * FROM meals WHERE day = ? AND user_id = ?", 
                          (current_date, current_user.id)).fetchall()
        
        daily_nutrition = {
            "date": current_date,
            "calories": sum(m["calories"] for m in meals),
            "protein": sum(m["protein_g"] or 0 for m in meals),
            "carbs": sum(m["carbs_g"] or 0 for m in meals),
            "fat": sum(m["fat_g"] or 0 for m in meals),
            "fiber": sum(m["fiber_g"] or 0 for m in meals),
            "sodium": sum(m["sodium_mg"] or 0 for m in meals)
        }
        
        nutrition_data[current_date] = daily_nutrition
    
    # Get user goals
    profile = db.execute("SELECT health_goals FROM user_profiles WHERE user_id = ?", 
                        (current_user.id,)).fetchone()
    user_goals = profile["health_goals"].split(",") if profile and profile["health_goals"] else []
    
    # Get AI insights
    insights = ai_service.get_health_insights(nutrition_data, user_goals)
    
    # Save insights to database
    insights_data = json.dumps(insights)
    today = date.today().isoformat()
    db.execute("""INSERT INTO health_insights (user_id, insight_type, insight_data, generated_date) 
                 VALUES (?, ?, ?, ?)""",
              (current_user.id, "weekly_analysis", insights_data, today))
    db.commit()
    
    return render_template("health_insights.html", insights=insights, nutrition_data=nutrition_data)

# Keep existing routes for backward compatibility
@app.route("/meals")
@login_required
def meals_page():
    today = date.today().isoformat()
    db = get_db()
    cur = db.execute("SELECT * FROM meals WHERE day = ? AND user_id = ? ORDER BY created_at DESC", 
                    (today, current_user.id))
    meals = cur.fetchall()
    total_cal = sum(m["calories"] for m in meals)
    return render_template("meals.html", meals=meals, total_cal=total_cal, today=today)

@app.route("/exercise")
@login_required  
def exercise_page():
    today = date.today().isoformat()
    db = get_db()
    cur = db.execute("SELECT * FROM exercise WHERE day = ? AND user_id = ? ORDER BY created_at DESC", 
                    (today, current_user.id))
    exercises = cur.fetchall()
    total_exercise_cal = sum(e["calories_burned"] for e in exercises)
    return render_template("exercise.html", exercises=exercises, 
                          total_exercise_cal=total_exercise_cal, today=today)

@app.route("/water")
@login_required
def water_page():
    today = date.today().isoformat()
    db = get_db()
    cur = db.execute("SELECT SUM(amount) AS total_water FROM water WHERE day = ? AND user_id = ?", 
                    (today, current_user.id))
    water = cur.fetchone()["total_water"] or 0
    return render_template("water.html", water=water, today=today)

@app.route("/sleep")
@login_required
def sleep_page():
    today = date.today().isoformat()
    db = get_db()

    # Current day data
    cur = db.execute("SELECT hours, quality FROM sleep WHERE day = ? AND user_id = ?", 
                    (today, current_user.id))
    row = cur.fetchone()
    sleep_hours = row["hours"] if row else 0
    sleep_quality = row["quality"] if row else 5

    # Last 7 days
    cur = db.execute("""
        SELECT day, hours, quality FROM sleep 
        WHERE user_id = ? 
        ORDER BY day DESC 
        LIMIT 7
    """, (current_user.id,))
    rows = cur.fetchall()
    sleep_days = [r["day"] for r in reversed(rows)]
    sleep_hours_list = [r["hours"] for r in reversed(rows)]
    sleep_quality_list = [r["quality"] or 5 for r in reversed(rows)]

    weekly_average = round(sum(sleep_hours_list) / len(sleep_hours_list), 1) if sleep_hours_list else 0

    return render_template("sleep.html", sleep_hours=sleep_hours, sleep_quality=sleep_quality,
                          today=today, sleep_days=sleep_days, sleep_hours_list=sleep_hours_list,
                          sleep_quality_list=sleep_quality_list, weekly_average=weekly_average)

@app.route("/weight")
@login_required
def weight_page():
    today = date.today().isoformat()
    db = get_db()
    cur = db.execute("SELECT weight FROM weight WHERE day = ? AND user_id = ? ORDER BY id DESC LIMIT 1", 
                    (today, current_user.id))
    row = cur.fetchone()
    weight = row["weight"] if row else None
    
    # Get weight history for chart
    weight_history = db.execute("""
        SELECT day, weight FROM weight 
        WHERE user_id = ? 
        ORDER BY day DESC 
        LIMIT 30
    """, (current_user.id,)).fetchall()
    
    return render_template("weight.html", weight=weight, today=today, weight_history=weight_history)

# Keep all the existing add/delete routes but enhance some
@app.route("/add-sleep", methods=["POST"])
@login_required
def add_sleep():
    hours = float(request.form["hours"])
    quality = int(request.form.get("quality", 5))
    day = date.today().isoformat()
    db = get_db()
    
    # Check if sleep entry exists for today
    existing = db.execute("SELECT id FROM sleep WHERE day = ? AND user_id = ?", 
                         (day, current_user.id)).fetchone()
    
    if existing:
        db.execute("UPDATE sleep SET hours = ?, quality = ? WHERE day = ? AND user_id = ?",
                  (hours, quality, day, current_user.id))
    else:
        db.execute("INSERT INTO sleep (hours, quality, day, user_id) VALUES (?, ?, ?, ?)",
                  (hours, quality, day, current_user.id))
    
    db.commit()
    flash(f"Sleep logged: {hours} hours", "success")
    return redirect(url_for("dashboard"))

@app.route("/add-water", methods=["POST"])
@login_required
def add_water():
    amount = int(request.form["amount"])
    today = date.today().isoformat()
    db = get_db()
    db.execute("INSERT INTO water (amount, day, user_id) VALUES (?, ?, ?)", 
              (amount, today, current_user.id))
    db.commit()
    flash(f"Added {amount}ml water", "success")
    return redirect(url_for("dashboard"))

@app.route("/add-exercise", methods=["POST"])
@login_required
def add_exercise():
    name = request.form["name"]
    calories_burned = int(request.form["calories_burned"])
    duration = int(request.form.get("duration", 30))
    exercise_type = request.form.get("exercise_type", "general")
    today = date.today().isoformat()
    db = get_db()
    db.execute("""
        INSERT INTO exercise (name, calories_burned, duration_minutes, exercise_type, day, user_id) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, calories_burned, duration, exercise_type, today, current_user.id))
    db.commit()
    flash(f"Added {name} exercise", "success")
    return redirect(url_for("dashboard"))

@app.route("/add-weight", methods=["POST"])
@login_required
def add_weight():
    weight = float(request.form["weight"])
    today = date.today().isoformat()
    db = get_db()
    db.execute("INSERT INTO weight (weight, day, user_id) VALUES (?, ?, ?)", 
              (weight, today, current_user.id))
    db.commit()
    flash(f"Weight logged: {weight}kg", "success")
    return redirect(url_for("dashboard"))

# Delete routes
@app.route("/delete-meal/<int:meal_id>", methods=["POST"])
@login_required
def delete_meal(meal_id):
    db = get_db()
    db.execute("DELETE FROM meals WHERE id = ? AND user_id = ?", (meal_id, current_user.id))
    db.commit()
    flash("Meal deleted", "info")
    return redirect(url_for("meals_page"))

@app.route("/delete-exercise/<int:exercise_id>", methods=["POST"])
@login_required
def delete_exercise(exercise_id):
    db = get_db()
    db.execute("DELETE FROM exercise WHERE id = ? AND user_id = ?", (exercise_id, current_user.id))
    db.commit()
    flash("Exercise deleted", "info")
    return redirect(url_for("exercise_page"))

@app.route("/clear-water", methods=["POST"])
@login_required
def clear_water():
    today = date.today().isoformat()
    db = get_db()
    db.execute("DELETE FROM water WHERE day = ? AND user_id = ?", (today, current_user.id))
    db.commit()
    flash("Water intake cleared", "info")
    return redirect(url_for("water_page"))

# Weekly summary with enhanced analytics
@app.route("/weekly-summary")
@login_required
def weekly_summary():
    db = get_db()
    today = date.today()
    dates = [(today - timedelta(days=i)).isoformat() for i in reversed(range(7))]

    # Enhanced weekly data collection
    weekly_data = {
        "dates": dates,
        "calories": [],
        "protein": [],
        "carbs": [],
        "fat": [],
        "exercise_calories": [],
        "water": [],
        "sleep": [],
        "weights": []
    }

    for d in dates:
        # Nutrition data
        meals = db.execute("SELECT * FROM meals WHERE day = ? AND user_id = ?", 
                          (d, current_user.id)).fetchall()
        daily_calories = sum(m["calories"] for m in meals)
        daily_protein = sum(m["protein_g"] or 0 for m in meals)
        daily_carbs = sum(m["carbs_g"] or 0 for m in meals)
        daily_fat = sum(m["fat_g"] or 0 for m in meals)
        
        weekly_data["calories"].append(daily_calories)
        weekly_data["protein"].append(daily_protein)
        weekly_data["carbs"].append(daily_carbs)
        weekly_data["fat"].append(daily_fat)

        # Exercise data
        exercise_cal = db.execute("SELECT SUM(calories_burned) FROM exercise WHERE day = ? AND user_id = ?", 
                                 (d, current_user.id)).fetchone()[0] or 0
        weekly_data["exercise_calories"].append(exercise_cal)

        # Water data
        water_amount = db.execute("SELECT SUM(amount) FROM water WHERE day = ? AND user_id = ?", 
                                 (d, current_user.id)).fetchone()[0] or 0
        weekly_data["water"].append(water_amount)

        # Sleep data
        sleep_hours = db.execute("SELECT hours FROM sleep WHERE day = ? AND user_id = ?", 
                                (d, current_user.id)).fetchone()
        weekly_data["sleep"].append(sleep_hours["hours"] if sleep_hours else 0)

        # Weight data
        weight = db.execute("SELECT weight FROM weight WHERE day = ? AND user_id = ? ORDER BY id DESC LIMIT 1", 
                           (d, current_user.id)).fetchone()
        weekly_data["weights"].append(weight["weight"] if weight else None)

    return render_template("weekly_summary.html", data=weekly_data)

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
