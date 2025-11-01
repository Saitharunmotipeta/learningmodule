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
