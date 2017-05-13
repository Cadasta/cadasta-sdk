from difflib import SequenceMatcher


def slugify(string, max_length=50):
    """
    Naive slugify. WARNING: Results may not exactly match Cadasta's slugs.
    """
    string = string.lower().replace(' ', '-')
    if max_length:
        string = string[:max_length]
    return string


def similarity(str1, str2):
    """
    Return the percentage of simularity between two strings. Useful when
    working with datasets that contain many typos.
    """
    return SequenceMatcher(None, str1, str2).ratio()
