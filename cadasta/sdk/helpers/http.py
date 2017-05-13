import mimetypes


def get_mime_type(path):
    """
    Attempt to determine file's mimetype based on its path or URL.
    """
    return mimetypes.guess_type(path)[0]
