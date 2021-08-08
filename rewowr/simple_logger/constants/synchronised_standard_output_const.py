# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
import re
from typing import Pattern, Final, final
from dataclasses import dataclass

_NOT_SPACE: Final[Pattern[str]] = re.compile(r'[^\s]')


def get_not_space_pattern() -> Pattern[str]:
    return _NOT_SPACE


_TIME_FORMAT: Final[Pattern[str]] = re.compile(r'(.*\d+:\d+:\d+)\..*$')


def get_time_format_pattern() -> Pattern[str]:
    return _TIME_FORMAT


_NEW_LINE: Final[Pattern[str]] = re.compile(r'\n')


def get_new_line_pattern() -> Pattern[str]:
    return _NEW_LINE


@final
@dataclass
class SyncOutMsg:
    s_id: str
    msg: str
    status: float
    done: bool
