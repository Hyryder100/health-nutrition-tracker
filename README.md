# Calm Companion

Simple mental health chatbot with a calming UI. Runs fully client-side, and optionally with a small Node/Express backend for the reply API.

## Run (no backend)
Open `index.html` directly in your browser (double-click or drag into a tab).

## Run with backend
1. Install Node.js 18+.
2. In this folder:
   ```bash
   npm install
   npm run start
   ```
3. Open `http://localhost:3000`.

The frontend auto-detects the backend. If the API is unreachable, it falls back to local keyword replies.

## Features
- Calming UI with soft colors and rounded corners
- Onboarding greeting and empathetic, supportive responses
- Keyword matching and quick replies
- Local chat history via localStorage
- Crisis Support modal with contacts and breathing animation

# 🩺 Health and Nutrition Tracker

A full-stack web application that allows users to log and manage their daily health data — including meals, water intake, sleep, exercise, and weight. Built with Flask and SQLite, this app also includes a weekly summary dashboard with interactive visualizations using Chart.js.

---

## 🚀 Features

- 🥗 **Meal Tracker** – Log daily meals and view calorie totals
- 🚰 **Water Intake** – Track water consumption (ml)
- 🏋️ **Exercise Tracker** – Log workout sessions with duration and calories burned
- 💤 **Sleep Tracker** – Enter hours slept and visualize trends
- ⚖️ **Weight Tracker** – Log and monitor weight over time
- 📊 **Weekly Summary** – Visual graphs for meals, sleep, weight, water, and exercise
- 🔐 **User Authentication** – Register/login system with secure user data handling

---

## 🛠️ Tech Stack

| Layer       | Tools Used                    |
|-------------|-------------------------------|
| Frontend    | HTML, CSS, JavaScript         |
| Backend     | Python, Flask                 |
| Database    | SQLite                        |
| Charts      | Chart.js                      |
| Auth System | Flask-Login                   |

---

## ⚙️ How to Run the App

### 🔧 Prerequisites
- Python 3.7+
- pip
- Virtual environment (recommended)

### 📥 Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/health-nutrition-tracker.git
cd health-nutrition-tracker

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
