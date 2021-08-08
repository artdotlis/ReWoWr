# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
from rewowr.public.errors.custom_errors import StringError


def create_not_empty_str(string: str, /) -> str:
    if string:
        return string

    raise StringError("String cant be empty!")
