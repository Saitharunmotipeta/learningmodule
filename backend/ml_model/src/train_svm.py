import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import pickle
import os

# Load dataset
df = pd.read_excel("data/dyslexia_dataset_500.xlsx")

# Features
X = df[["syllables","length","vowel_count","consonant_count",
        "confusing_letters","phonetic_complexity"]]

# Labels
y = df["difficulty"].map({"easy":0, "medium":1, "hard":2})

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Scale inputs
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Model
svm = SVC(kernel="rbf", probability=True)

# Train
svm.fit(X_train_scaled, y_train)

# Predict
y_pred = svm.predict(X_test_scaled)

# Metrics
print("\n========== SVM RESULT ==========")
print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nConfusion Matrix:\n", confusion_matrix(y_test, y_pred))
print("\nClassification Report:\n", classification_report(y_test, y_pred))

# Save model
os.makedirs("model", exist_ok=True)
with open("model/difficulty_model_svm.pkl", "wb") as f:
    pickle.dump((svm, scaler), f)

print("\nModel saved: model/difficulty_model_svm.pkl")
