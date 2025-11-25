import numpy as np

def extract_features(word_row):
    return np.array([
        word_row["syllables"],
        word_row["length"],
        word_row["vowel_count"],
        word_row["consonant_count"],
        word_row["confusing_letters"],
        word_row["phonetic_complexity"],
    ])
