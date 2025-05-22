import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib

# Load data
df = pd.read_csv('calorie_data.csv')

# Features and target
X = df[['weight', 'sleep', 'exercise', 'previous_cal']]
y = df['target_calorie']

# Train model
model = LinearRegression()
model.fit(X, y)

# Save model
joblib.dump(model, 'calorie_predictor.pkl')

print("✅ Model trained and saved as calorie_predictor.pkl")
