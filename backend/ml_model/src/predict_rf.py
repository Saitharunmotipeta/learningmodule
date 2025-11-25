import pickle
import numpy as np

# Load the Random Forest model
with open("model/difficulty_model_rf.pkl", "rb") as f:
    rf_model = pickle.load(f)

def predict_difficulty_rf(features):
    """
    features = [syllables, length, vowel_count, consonant_count, confusing_letters, phonetic_complexity]
    Example: [1, 3, 1, 2, 0, 1]  # for ‘cat’
    """

    features = np.array([features])  # convert to 2D array
    prediction = rf_model.predict(features)[0]

    label_map = {0: "easy", 1: "medium", 2: "hard"}
    return label_map[prediction]

# Test the model manually
if __name__ == "__main__":
    test_word = [1, 4, 2, 2, 0, 2]  # example features
    print("Prediction:", predict_difficulty_rf(test_word))
