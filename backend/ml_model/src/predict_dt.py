import pickle
import numpy as np

# Load Decision Tree model
dt = pickle.load(open("model/difficulty_model_dt.pkl", "rb"))

def predict_difficulty_dt(features):
    result = dt.predict([features])[0]
    return {0:"easy", 1:"medium", 2:"hard"}[result]

# Manual test
if __name__ == "__main__":
    test_word = [1, 4, 2, 2, 0, 2]
    print("Prediction:", predict_difficulty_dt(test_word))
