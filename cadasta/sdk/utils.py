def slugify(string, max_length=50):
    """
    Naive slugify. WARNING: Results may not exactly match Cadasta's slugs.
    """
    string = string.lower().replace(' ', '-')
    if max_length:
        string = string[:max_length]
    return string
