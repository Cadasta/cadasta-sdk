from tempfile import mkdtemp
import os
import shutil


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
        yield os.path.join(path, file)


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
        if (hidden is not None) and (f.split('/')[-1].startswith('.') != hidden):
            continue
        yield f


class TemporaryDirectory(object):
    """
    Create and return a temporary directory.  This has the same behavior as
    mkdtemp but can be used as a context manager.  For example:

        with TemporaryDirectory() as tmpdir:
            ...

    Upon exiting the context, the directory and everything contained
    in it are removed.
    """

    def __init__(self, suffix="", prefix="tmp", dir=None):
        self._closed = False
        self.path = mkdtemp(suffix, prefix, dir)

    def __enter__(self):
        return self.path

    def __exit__(self, exc, value, tb):
        shutil.rmtree(self.path)
