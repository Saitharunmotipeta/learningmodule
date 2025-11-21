import pickle
import numpy as np

# Load SVM model + scaler
svm, scaler = pickle.load(open("model/difficulty_model_svm.pkl", "rb"))

def predict_difficulty_svm(features):
    features_scaled = scaler.transform([features])
    result = svm.predict(features_scaled)[0]
    return {0:"easy", 1:"medium", 2:"hard"}[result]

# Manual test
if __name__ == "__main__":
    test_word = [1, 4, 2, 2, 0, 2]
    print("Prediction:", predict_difficulty_svm(test_word))
