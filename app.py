import sqlite3
from flask import Flask, g, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import date, timedelta
import joblib
import numpy as np

app = Flask(__name__)
app.secret_key = "my_super_secret_1234"
DATABASE = "database.db"

calorie_model = joblib.load("calorie_predictor.pkl")

def predict_calories(weight, sleep, exercise, previous_cal):
    features = np.array([[weight, sleep, exercise, previous_cal]])
    return int(calorie_model.predict(features)[0])

# --- Step 1: Add routes for each feature ---

@app.route("/meals")
@login_required
def meals_page():
    today = date.today().isoformat()
    db = get_db()
    cur = db.execute("SELECT * FROM meals WHERE day = ? AND user_id = ? ORDER BY id DESC", (today, current_user.id))
    meals = cur.fetchall()
    total_cal = sum(m["calories"] for m in meals)
    return render_template("meals.html", meals=meals, total_cal=total_cal, today=today)


@app.route("/exercise")
@login_required
def exercise_page():
    today = date.today().isoformat()
    db = get_db()
    cur = db.execute("SELECT * FROM exercise WHERE day = ? AND user_id = ? ORDER BY id DESC", (today, current_user.id))
    exercises = cur.fetchall()
    total_exercise_cal = sum(e["calories_burned"] for e in exercises)
    return render_template("exercise.html", exercises=exercises, total_exercise_cal=total_exercise_cal, today=today)


@app.route("/water")
@login_required
def water_page():
    today = date.today().isoformat()
    db = get_db()
    cur = db.execute("SELECT SUM(amount) AS total_water FROM water WHERE day = ? AND user_id = ?", (today, current_user.id))
    water = cur.fetchone()["total_water"] or 0
    return render_template("water.html", water=water, today=today)


@app.route("/sleep")
@login_required
def sleep_page():
    today = date.today().isoformat()
    db = get_db()

    # Current day data
    cur = db.execute("SELECT hours FROM sleep WHERE day = ? AND user_id = ?", (today, current_user.id))
    row = cur.fetchone()
    sleep_hours = row["hours"] if row else 0

    # Last 7 days
    cur = db.execute("""
        SELECT day, hours FROM sleep 
        WHERE user_id = ? 
        ORDER BY day DESC 
        LIMIT 7
    """, (current_user.id,))
    rows = cur.fetchall()
    sleep_days = [r["day"] for r in reversed(rows)]
    sleep_hours_list = [r["hours"] for r in reversed(rows)]

    return render_template("sleep.html", sleep_hours=sleep_hours, today=today,
                           sleep_days=sleep_days, sleep_hours_list=sleep_hours_list, weekly_average=round(sum(sleep_hours_list) / len(sleep_hours_list), 1) if sleep_hours_list else 0)


@app.route("/weight")
@login_required
def weight_page():
    today = date.today().isoformat()
    db = get_db()
    cur = db.execute("SELECT weight FROM weight WHERE day = ? AND user_id = ? ORDER BY id DESC LIMIT 1", (today, current_user.id))
    row = cur.fetchone()
    weight = row["weight"] if row else None
    return render_template("weight.html", weight=weight, today=today)


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if user:
        return User(user["id"], user["username"], user["password"])
    return None

def init_db():
    db = get_db()

    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            calories INTEGER NOT NULL,
            day TEXT NOT NULL,
            user_id INTEGER NOT NULL
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS exercise (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            calories_burned INTEGER NOT NULL,
            day TEXT NOT NULL,
            user_id INTEGER NOT NULL
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS weight (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            weight REAL NOT NULL,
            day TEXT NOT NULL,
            user_id INTEGER NOT NULL
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS sleep (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hours REAL NOT NULL,
            day TEXT NOT NULL,
            user_id INTEGER NOT NULL
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS water (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            day TEXT NOT NULL,
            user_id INTEGER NOT NULL
        )
    """)

    db.commit()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']  # Plain text for now; not secure for production

        db = get_db()
        existing_user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if existing_user:
            return "Username already exists! Try another."

        db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        db.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and user['password'] == password:
            user_obj = User(user['id'], user['username'], user['password'])
            login_user(user_obj)
            return redirect(url_for('dashboard'))
        return "Invalid username or password!"
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/dashboard')
@login_required
def dashboard():
    today = date.today().isoformat()
    db = get_db()

    # Meals
    meals = db.execute("SELECT * FROM meals WHERE day = ? AND user_id = ?", (today, current_user.id)).fetchall()
    total_cal = sum(m["calories"] for m in meals)

    # Water
    water_row = db.execute("SELECT SUM(amount) AS total_water FROM water WHERE day = ? AND user_id = ?", (today, current_user.id)).fetchone()
    water = water_row["total_water"] or 0

    # Exercises
    exercises = db.execute("SELECT * FROM exercise WHERE day = ? AND user_id = ? ORDER BY id DESC", (today, current_user.id)).fetchall()
    total_exercise_cal = sum(e["calories_burned"] for e in exercises)
    
    cur = db.execute("SELECT * FROM exercise WHERE day = ? AND user_id = ? ORDER BY id DESC", (today, current_user.id))
    exercises = cur.fetchall()


    # Weight (latest entry)
    latest_weight_row = db.execute("SELECT weight, day FROM weight WHERE user_id = ? ORDER BY day DESC, id DESC LIMIT 1", (current_user.id,)).fetchone()
    latest_weight = latest_weight_row["weight"] if latest_weight_row else None
    weight_day = latest_weight_row["day"] if latest_weight_row else None

    # Sleep
    sleep_row = db.execute("SELECT hours FROM sleep WHERE day = ? AND user_id = ?", (today, current_user.id)).fetchone()
    sleep_hours = sleep_row["hours"] if sleep_row else 0

    # AI-like Smart Suggestions (rule-based)
    suggestions = []

    # Suggest water
    if water < 2000:
        suggestions.append("💧 Try to drink at least 2 liters of water today.")

    # Suggest sleep
    if sleep_hours < 6:
        suggestions.append("😴 Try to get at least 7 hours of sleep for better recovery.")

    # Suggest exercise
    if total_exercise_cal < 100:
        suggestions.append("🏃‍♂️ Try to get some light exercise to stay active.")

    # Suggest meal balance
    if total_cal < 1200:
        suggestions.append("🍽️ Consider eating a bit more for balanced energy.")
    elif total_cal > 2500:
        suggestions.append("⚠️ Your calorie intake seems high today. Keep an eye on it.")

    if latest_weight and total_cal:
        predicted_cal = predict_calories(latest_weight, sleep_hours, total_exercise_cal, total_cal)
    else:
        predicted_cal = None



    return render_template("dashboard.html", meals=meals, total_cal=total_cal, water=water, exercises=exercises,
                       total_exercise_cal=total_exercise_cal, latest_weight=latest_weight,
                       weight_day=weight_day, today=today, sleep_hours=sleep_hours, suggestions=suggestions, predicted_cal=predicted_cal)

@app.route('/meals')
@login_required
def meals():
    today = date.today().isoformat()
    db = get_db()
    meals = db.execute("SELECT * FROM meals WHERE day = ? AND user_id = ? ORDER BY id DESC", (today, current_user.id)).fetchall()
    total_cal = sum(m["calories"] for m in meals)
    return render_template("meals.html", meals=meals, total_cal=total_cal, today=today)


@app.route("/add-meal", methods=["POST"])
@login_required
def add_meal():
    name = request.form["name"]
    calories = int(request.form["calories"])
    today = date.today().isoformat()
    db = get_db()
    db.execute(
        "INSERT INTO meals (name, calories, day, user_id) VALUES (?, ?, ?, ?)",
        (name, calories, today, current_user.id)
    )
    db.commit()
    return redirect(url_for("dashboard"))

@app.route("/delete-meal/<int:meal_id>", methods=["POST"])
@login_required
def delete_meal(meal_id):
    db = get_db()
    db.execute("DELETE FROM meals WHERE id = ? AND user_id = ?", (meal_id, current_user.id))
    db.commit()
    return redirect(url_for("meals_page"))


@app.route("/add-sleep", methods=["POST"])
@login_required
def add_sleep():
    hours = float(request.form["hours"])
    day = date.today().isoformat()
    db = get_db()
    db.execute(
        "INSERT INTO sleep (hours, day, user_id) VALUES (?, ?, ?)",
        (hours, day, current_user.id)
    )
    db.commit()
    return redirect(url_for("dashboard"))

@app.route("/add-water", methods=["POST"])
@login_required
def add_water():
    amount = int(request.form["amount"])  # amount in ml
    today = date.today().isoformat()
    db = get_db()
    db.execute("INSERT INTO water (amount, day, user_id) VALUES (?, ?, ?)", (amount, today, current_user.id))
    db.commit()
    return redirect(url_for("dashboard"))

@app.route("/clear-water", methods=["POST"])
@login_required
def clear_water():
    today = date.today().isoformat()
    db = get_db()
    db.execute("DELETE FROM water WHERE day = ? AND user_id = ?", (today, current_user.id))
    db.commit()
    return redirect(url_for("water_page"))


@app.route("/add-exercise", methods=["POST"])
@login_required
def add_exercise():
    name = request.form["name"]
    calories_burned = int(request.form["calories_burned"])
    today = date.today().isoformat()
    db = get_db()
    db.execute(
        "INSERT INTO exercise (name, calories_burned, day, user_id) VALUES (?, ?, ?, ?)",
        (name, calories_burned, today, current_user.id)
    )
    db.commit()
    return redirect(url_for("dashboard"))

@app.route("/delete-exercise/<int:exercise_id>", methods=["POST"])
@login_required
def delete_exercise(exercise_id):
    db = get_db()
    db.execute("DELETE FROM exercise WHERE id = ? AND user_id = ?", (exercise_id, current_user.id))
    db.commit()
    return redirect(url_for("dashboard"))


@app.route("/add-weight", methods=["POST"])
@login_required
def add_weight():
    weight = float(request.form["weight"])  # weight in kg or lbs
    today = date.today().isoformat()
    db = get_db()
    db.execute("INSERT INTO weight (weight, day, user_id) VALUES (?, ?, ?)", (weight, today, current_user.id))
    db.commit()
    return redirect(url_for("dashboard"))

@app.route("/weekly-summary")
@login_required
def weekly_summary():
    db = get_db()
    today = date.today()
    dates = [(today - timedelta(days=i)).isoformat() for i in reversed(range(7))]

    # Get meals calories per day
    calories_per_day = []
    for d in dates:
        cur = db.execute("SELECT SUM(calories) FROM meals WHERE day = ? AND user_id = ?", (d, current_user.id))
        total = cur.fetchone()[0]
        calories_per_day.append(total or 0)

    # Get calories burned per day from exercises
    burned_per_day = []
    for d in dates:
        cur = db.execute("SELECT SUM(calories_burned) FROM exercise WHERE day = ? AND user_id = ?", (d, current_user.id))
        total = cur.fetchone()[0]
        burned_per_day.append(total or 0)

    # Get latest weight per day (or None)
    weights = []
    for d in dates:
        cur = db.execute("SELECT weight FROM weight WHERE day = ? AND user_id = ? ORDER BY id DESC LIMIT 1", (d, current_user.id))
        w = cur.fetchone()
        weights.append(w["weight"] if w else None)

    # Return after all loops are done
    return render_template("weekly_summary.html", 
                           dates=dates, 
                           calories_per_day=calories_per_day, 
                           burned_per_day=burned_per_day, 
                           weights=weights)


if __name__ == "__main__":
    with app.app_context():
        init_db()  # <--- This is IMPORTANT
    app.run(debug=True)

'''from flask import Flask

app = Flask(__name__)

@app.before_first_request
def hello():
    print("Before first request triggered!")

@app.route("/")
def index():
    return "Hello, Flask!"

if __name__ == "__main__":
    app.run(debug=True)'''
