import os


def ls(path, isfile=None):
    """
    List files and dirs in a provided path.

    Args:
        isfile (bool, optional): Limit output to only include files or
        non-files (directories). Defaults to None, showing both hidden and
        not-hidden.
    """
    for file in os.listdir(path):
        if (isfile is not None):
            if not os.path.isfile(os.path.join(path, file)) == isfile:
                continue
        yield file


def ls_dirs(path):
    """
    List directoris in a provided path.
    """
    return ls(path, isfile=False)


def ls_files(path, hidden=None):
    """
    List files in a provided path.

    Args:
        hidden (bool, optional): Limit output to only include hidden or
        non-hidden files. Hidden is defined by beginning with a period ('.').
        Defaults to None, showing both hidden and not-hidden.
    """
    for f in ls(path, isfile=True):
        if (hidden is not None) and (f.startswith('.') != hidden):
                continue
        yield f
