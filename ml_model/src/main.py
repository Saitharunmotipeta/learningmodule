import pandas as pd
import numpy as np
import pickle
import os
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.cluster import KMeans

# ============================
# LOAD DATASET
# ============================
df = pd.read_excel("data/dyslexia_dataset_500.xlsx")

X = df[["syllables","length","vowel_count","consonant_count",
        "confusing_letters","phonetic_complexity"]]

y = df["difficulty"].map({"easy":0,"medium":1,"hard":2})


# SPLIT DATA
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Create report folder
os.makedirs("model", exist_ok=True)
os.makedirs("reports", exist_ok=True)

report_text = "\n=== MODEL COMPARISON REPORT ===\n\n"
accuracies = {}

# ============================
# LOGISTIC REGRESSION
# ============================
print("\n===== TRAINING LOGISTIC REGRESSION =====")

scaler_lr = StandardScaler()
X_train_lr = scaler_lr.fit_transform(X_train)
X_test_lr = scaler_lr.transform(X_test)

lr = LogisticRegression(max_iter=500, multi_class="multinomial")
lr.fit(X_train_lr, y_train)

lr_pred = lr.predict(X_test_lr)
lr_acc = accuracy_score(y_test, lr_pred)
accuracies["Logistic Regression"] = lr_acc

print("Accuracy:", lr_acc)
print(classification_report(y_test, lr_pred))

with open("model/lr_model.pkl", "wb") as f:
    pickle.dump((lr, scaler_lr), f)

report_text += f"Logistic Regression Accuracy: {lr_acc:.4f}\n"


# ============================
# RANDOM FOREST
# ============================
print("\n===== TRAINING RANDOM FOREST =====")

rf = RandomForestClassifier(n_estimators=200, random_state=42)
rf.fit(X_train, y_train)

rf_pred = rf.predict(X_test)
rf_acc = accuracy_score(y_test, rf_pred)
accuracies["Random Forest"] = rf_acc

print("Accuracy:", rf_acc)
print(classification_report(y_test, rf_pred))

with open("model/rf_model.pkl", "wb") as f:
    pickle.dump(rf, f)

report_text += f"Random Forest Accuracy: {rf_acc:.4f}\n"


# ============================
# SVM
# ============================
print("\n===== TRAINING SVM =====")

scaler_svm = StandardScaler()
X_train_svm = scaler_svm.fit_transform(X_train)
X_test_svm = scaler_svm.transform(X_test)

svm = SVC(kernel="rbf", probability=True)
svm.fit(X_train_svm, y_train)

svm_pred = svm.predict(X_test_svm)
svm_acc = accuracy_score(y_test, svm_pred)
accuracies["SVM"] = svm_acc

print("Accuracy:", svm_acc)
print(classification_report(y_test, svm_pred))

with open("model/svm_model.pkl", "wb") as f:
    pickle.dump((svm, scaler_svm), f)

report_text += f"SVM Accuracy: {svm_acc:.4f}\n"


# ============================
# DECISION TREE
# ============================
print("\n===== TRAINING DECISION TREE =====")

dt = DecisionTreeClassifier(random_state=42)
dt.fit(X_train, y_train)

dt_pred = dt.predict(X_test)
dt_acc = accuracy_score(y_test, dt_pred)
accuracies["Decision Tree"] = dt_acc

print("Accuracy:", dt_acc)
print(classification_report(y_test, dt_pred))

with open("model/dt_model.pkl", "wb") as f:
    pickle.dump(dt, f)

report_text += f"Decision Tree Accuracy: {dt_acc:.4f}\n"

# ============================
# K-MEANS (UNSUPERVISED)
# ============================
print("\n===== TRAINING K-MEANS =====")

# Scale features
scaler_km = StandardScaler()
X_scaled_km = scaler_km.fit_transform(X)

kmeans = KMeans(n_clusters=3, random_state=42)
kmeans.fit(X_scaled_km)

y_pred_km = kmeans.labels_

from sklearn.metrics import adjusted_rand_score, homogeneity_score
ari = adjusted_rand_score(y, y_pred_km)
hom = homogeneity_score(y, y_pred_km)

accuracies["K-means (ARI)"] = ari  # use ARI as accuracy metric

print("Adjusted Rand Index:", ari)
print("Homogeneity Score:", hom)

with open("model/kmeans_model.pkl", "wb") as f:
    pickle.dump((kmeans, scaler_km), f)

report_text += f"K-Means ARI Score: {ari:.4f}\n"


# ============================
# SAVE REPORT
# ============================
with open("reports/model_report.txt", "w") as f:
    f.write(report_text)

print("\nReport saved → reports/model_report.txt")


# ============================
# ACCURACY GRAPH
# ============================
plt.figure(figsize=(10,6))
plt.bar(accuracies.keys(), accuracies.values(), color=["blue","green","red","orange","purple"])
plt.title("Model Accuracy Comparison")
plt.ylabel("Accuracy Score")
plt.ylim(0,1.1)
plt.tight_layout()
plt.savefig("reports/model_accuracy_graph.png")

print("\nGraph saved → reports/model_accuracy_graph.png")
plt.show()
