# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
from typing import final

from rewowr.public.errors.custom_errors import KnownError


class KnownErrorReWoWr(KnownError):
    pass


@final
class WorkableError(KnownErrorReWoWr):
    pass


@final
class WorkerError(KnownErrorReWoWr):
    pass


@final
class ReWrProgressError(KnownErrorReWoWr):
    pass
