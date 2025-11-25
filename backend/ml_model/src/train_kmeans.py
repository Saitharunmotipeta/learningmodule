import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, homogeneity_score
import pickle
import os

# Load dataset
df = pd.read_excel("data/dyslexia_dataset_500.xlsx")

X = df[["syllables","length","vowel_count","consonant_count",
        "confusing_letters","phonetic_complexity"]]

y_true = df["difficulty"].map({"easy":0,"medium":1,"hard":2})

# Scale features (K-means needs scaling)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train K-Means with 3 clusters
kmeans = KMeans(n_clusters=3, random_state=42)
kmeans.fit(X_scaled)

# Predicted cluster labels
y_pred = kmeans.labels_

# Metrics
ari = adjusted_rand_score(y_true, y_pred)
hom = homogeneity_score(y_true, y_pred)

print("\n========== K-MEANS RESULT ==========")
print("Adjusted Rand Index (0 to 1):", ari)
print("Homogeneity Score:", hom)

# Save model
os.makedirs("model", exist_ok=True)
with open("model/kmeans_model.pkl", "wb") as f:
    pickle.dump((kmeans, scaler), f)

print("\nModel saved: model/kmeans_model.pkl")
