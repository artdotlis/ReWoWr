# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
from typing import Dict

from rewowr.public.errors.custom_errors import CheckExtraArgsDictError


def check_extra_args_dict(dict_cont: Dict, /) -> None:
    for key, value in dict_cont.items():
        if not (isinstance(key, str) and isinstance(value, str)):
            raise CheckExtraArgsDictError("Key or value have not a string type!")
