# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
from typing import final

from rewowr.public.errors.custom_errors import KnownError


class KnownErrorSimLog(KnownError):
    pass


@final
class SyncStdoutError(KnownErrorSimLog):
    pass
