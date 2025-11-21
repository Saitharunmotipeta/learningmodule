import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.ensemble import RandomForestClassifier
import pickle
import os

# Load dataset
df = pd.read_excel("data/dyslexia_dataset_500.xlsx")

# Features
X = df[["syllables","length","vowel_count","consonant_count",
        "confusing_letters","phonetic_complexity"]]

# Labels
y = df["difficulty"].map({"easy":0, "medium":1, "hard":2})

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Model
rf = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    max_depth=None,
    criterion="gini"
)

# Train
rf.fit(X_train, y_train)

# Predictions
y_pred = rf.predict(X_test)

# Metrics
print("\n========== RANDOM FOREST RESULT ==========")
print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# Save model
os.makedirs("model", exist_ok=True)
with open("model/difficulty_model_rf.pkl", "wb") as f:
    pickle.dump(rf, f)

print("\nModel saved: model/difficulty_model_rf.pkl")
