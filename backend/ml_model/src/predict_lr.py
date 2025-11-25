import pickle
import numpy as np

# Load model + scaler
model, scaler = pickle.load(open("model/difficulty_model_lr.pkl", "rb"))

def predict_difficulty(features):
    features_scaled = scaler.transform([features])
    pred = model.predict(features_scaled)[0]
    mapping = {0: "easy", 1: "medium", 2: "hard"}
    return mapping[pred]

# Example manual test
test_word_features = [1, 3, 1, 2, 0, 1]  # “cat”
print("Prediction:", predict_difficulty(test_word_features))
