import logging
import os


def get_basename(path, with_extension=False):
    """
    Extract the very filename from the path provided. The filename can be
    extracted with or without extension. Behaviour of the function is not
    validated against multiple extensions (e.g. nii.gz) and most probaby will
    not work properly.

    :param path: Path to extract filename from
    :type path: str

    :param with_extension: Decides wheter the filename will be extracted with
                           or without extension.
    :type with_extension: bool

    >>> get_basename("/home/user/file.txt")
    'file'

    >>> get_basename("/home/user/file.txt", with_extension = False)
    'file'

    >>> get_basename("/home/user/file.txt", with_extension = True)
    'file.txt'

    >>> get_basename("/home/user/file.txt", True)
    'file.txt'

    >>> get_basename("file.txt", True)
    'file.txt'

    >>> get_basename("/home/user/image.nii.gz", True)
    'image.nii.gz'

    >>> get_basename("/home/user/image.nii.gz")
    'image.nii'

    >>> get_basename(get_basename("/home/user/image.nii.gz"))
    'image'
    """

    if with_extension is True:
        return os.path.basename(path)
    else:
        return os.path.splitext(os.path.basename(path))[0]


def setup_logging(log_filename=None, log_level='WARNING'):
    """
    Initialize the logging subsystem. The logging is handled (suprisingly! :)
    by the :py:mod:`logging` module. Depending on the command line options, the
    log may be streamed to a specified file or printed directly to the stderr.

    :param log_filename: file to which the log will be redirected. If not
             provided, the logging is redirected to `sys.stderr`. `None` by default.
    :type log_filename: str

    :param log_level: Severity level of the logging module.
                      Supports all the default severity levels implemented
                      in python :py:mod:`logging` module. `WARNING` by default.
                      (see http://docs.python.org/2.6/library/logging.html
                      for more details.)
    :type log_level: str
    """

    # Intialize the logging module.
    logging.basicConfig(
            level=getattr(logging, log_level),
            filename=log_filename,
            format='%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s',
            datefmt='%m/%d/%Y %H:%M:%S')


def which(program):
    """
    Method that checks if a given if executable exists.
    Brutally copied from:
    http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python

    :param program: The executable name to test
    :type program: str

    >>> which("nonexistent_executable") == None
    True

    >>> which("ls") != None
    True

    >>> which("/bin/ls") == "/bin/ls"
    True
    """

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

def flatten(lst):
    """
    >>> list(flatten([10,11,[20,21]]))
    [10, 11, 20, 21]

    >>> list(flatten([10,11,["a", "b"]]))
    [10, 11, 'a', 'b']

    >>> list(flatten([10,11,["a", []]]))
    [10, 11, 'a']
    """
    for x in lst:
        if isinstance(x, list):
            for x in flatten(x):
                yield x
        else:
                yield x

if __name__ == 'possum.pos_common':
    import doctest
    doctest.testmod()
