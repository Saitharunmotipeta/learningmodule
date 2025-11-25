import pickle
import numpy as np

# Load model + scaler
kmeans, scaler = pickle.load(open("model/kmeans_model.pkl", "rb"))

def predict_cluster(features):
    features_scaled = scaler.transform([features])
    cluster = kmeans.predict(features_scaled)[0]
    return cluster  # 0,1,2 cluster index

if __name__ == "__main__":
    test_word = [1,4,2,2,0,1]
    print("Cluster:", predict_cluster(test_word))
