import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import pickle
import os

# Load dataset
df = pd.read_excel("data/dyslexia_dataset_500.xlsx")

# Features & labels
X = df[["syllables","length","vowel_count","consonant_count",
        "confusing_letters","phonetic_complexity"]]
y = df["difficulty"].map({"easy":0, "medium":1, "hard":2})

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Model
dt = DecisionTreeClassifier(
    criterion="gini",
    max_depth=None,
    random_state=42
)

# Train
dt.fit(X_train, y_train)

# Predict
y_pred = dt.predict(X_test)

# Metrics
print("\n========== DECISION TREE RESULT ==========")
print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nConfusion Matrix:\n", confusion_matrix(y_test, y_pred))
print("\nClassification Report:\n", classification_report(y_test, y_pred))

# Save model
os.makedirs("model", exist_ok=True)
with open("model/difficulty_model_dt.pkl", "wb") as f:
    pickle.dump(dt, f)

print("\nModel saved: model/difficulty_model_dt.pkl")
