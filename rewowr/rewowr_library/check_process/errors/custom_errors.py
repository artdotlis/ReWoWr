# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
from typing import final

from rewowr.public.errors.custom_errors import KnownError


class KnownErrorChecks(KnownError):
    pass


@final
class CheckConnectionContainerError(KnownErrorChecks):
    pass


@final
class CheckArgumentsError(KnownErrorChecks):
    pass


@final
class ReadJsonReWoWrError(KnownErrorChecks):
    pass


@final
class CheckWorkerError(KnownErrorChecks):
    pass


@final
class CheckWorkerPathError(KnownErrorChecks):
    pass


@final
class CheckWorkableNumbersError(KnownErrorChecks):
    pass
