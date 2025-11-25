import pronouncing

def get_phonetics_syllables(word: str):
    phones = pronouncing.phones_for_word(word.lower())

    if not phones:
        return {
            "word": word,
            "syllables": [word],
            "phonemes": [word],    
        }

    arpabet = phones[0]
    phoneme_list = arpabet.split()

    syllables = []
    current = []

    for p in phoneme_list:
        current.append(p)
        if any(x.isdigit() for x in p):
            syllables.append(" ".join(current))
            current = []

    if current:
        syllables.append(" ".join(current))

    return {
        "word": word,
        "syllables": syllables,
        "phonemes": phoneme_list
    }
