import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import pickle
import os

# Load dataset
df = pd.read_excel("data/dyslexia_dataset_500.xlsx")

# Extract features
X = df[["syllables", "length", "vowel_count", "consonant_count",
        "confusing_letters", "phonetic_complexity"]].values

# Encode labels
y = df["difficulty"].map({"easy": 0, "medium": 1, "hard": 2}).values

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Scale features (important for LR)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Model
lr = LogisticRegression(
    multi_class="multinomial",
    solver="lbfgs",
    max_iter=500
)

# Train model
lr.fit(X_train_scaled, y_train)

# Predictions
y_pred = lr.predict(X_test_scaled)

# Metrics
print("\n================ LOGISTIC REGRESSION ================")
print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# Save model
os.makedirs("model", exist_ok=True)
with open("model/difficulty_model_lr.pkl", "wb") as f:
    pickle.dump((lr, scaler), f)

print("\nModel saved successfully: model/difficulty_model_lr.pkl")
