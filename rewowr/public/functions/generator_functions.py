# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
from typing import Iterable, Iterator, TypeVar, Final

_IT: Final = TypeVar('_IT')


def custom_iterable(iterable: Iterator[_IT], limit: int, /) -> Iterable[_IT]:
    try:
        for _ in range(0, limit):
            yield next(iterable)
    except StopIteration:
        pass
