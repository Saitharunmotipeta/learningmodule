import pronouncing

def word_to_phonemes(word: str):
    """
    Convert a word to its phonetic representation using CMUdict.
    If not found, fallback to the original word.
    """
    word = word.lower().strip()
    phones = pronouncing.phones_for_word(word)
    if phones:
        return phones[0]
    return word  # fallback to actual word

def arpabet_to_visual(arpabet_str: str):
    """
    Convert ARPAbet string to a list of visual boxes for frontend display.
    Example: "HH AH0 L OW1" -> [{'text': 'HH'}, {'text': 'AH0'}, ...]
    """
    tokens = arpabet_str.split()
    return [{"text": t} for t in tokens]

# ✅ NEW: NON-BREAKING ADDITION
def get_phonetics_syllables(word: str):
    """
    Returns syllable groupings + phonemes.
    Safely falls back to plain word if unavailable.
    """
    phones = pronouncing.phones_for_word(word.lower())

    # fallback
    if not phones:
        return {
            "word": word,
            "syllables": [word],
            "phonemes": word
        }

    arpabet = phones[0]
    phoneme_list = arpabet.split()

    # syllable segmentation based on stress markers
    syllables = []
    current = []

    for p in phoneme_list:
        current.append(p)
        if any(x.isdigit() for x in p):  # stress → syllable boundary
            syllables.append(" ".join(current))
            current = []

    if current:
        syllables.append(" ".join(current))

    return {
        "word": word,
        "syllables": syllables,
        "phonemes": phoneme_list
    }
