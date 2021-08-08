# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
import os
import re
from pathlib import Path
from typing import Pattern, List, Final

from rewowr.public.errors.custom_errors import PathError

_FILE_PATH: Final[Pattern[str]] = re.compile(r'^.*' + os.sep + r'(.+)' + r'\.(.+)$')


def get_file_path_pattern() -> Pattern[str]:
    """This function returns the compiled pattern for a file path.

    Returns:
        Pattern: The compiled pattern for a file path.
    """
    return _FILE_PATH


def check_absolute_path(path_str: str, /) -> Path:
    str_path = Path(path_str)
    if not str_path.is_absolute():
        raise PathError("Path needs to be absolute!")
    return str_path


def check_dir_path(dir_path: str, /) -> Path:
    path_abs = Path(check_absolute_path(dir_path))
    _check_rec_dir(path_abs)
    return path_abs


def create_dirs_rec(path_given: Path, /) -> None:
    _check_rec_dir(path_given)
    _create_dirs_rec(path_given)


def _create_dirs_rec(path_given: Path, /) -> None:
    if not path_given.exists():
        _create_dirs_rec(path_given.parent)
    if not path_given.is_dir():
        path_given.mkdir()


def _check_rec_dir(path_given: Path, /) -> None:
    if str(path_given.suffix):
        raise PathError("No points in directory name allowed!")
    if not path_given.exists():
        _check_rec_dir(path_given.parent)
    elif not path_given.is_dir():
        raise PathError("Path is not a directory!")


def remove_dir_rec(path_given: str, /) -> None:
    checked_path = check_absolute_path(path_given)
    if checked_path.exists() and checked_path.is_dir():
        for path_names in checked_path.iterdir():
            if path_names.is_file():
                path_names.unlink()
            if path_names.is_dir():
                remove_dir_rec(str(path_names))

    if checked_path.exists() and checked_path.is_dir():
        checked_path.rmdir()


def add_to_environ(environ: str, paths_str: List[str], /) -> None:
    if paths_str:
        new_paths = ":".join(paths_str)
        old_path = os.environ.get(environ, "")
        if old_path:
            os.environ[environ] = ":".join([old_path, new_paths])
        else:
            os.environ[environ] = new_paths


def set_environ(environ: str, paths_str: List[str], /) -> None:
    if paths_str:
        os.environ[environ] = ":".join(paths_str)
