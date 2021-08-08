# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
from typing import final


class KnownError(Exception):
    pass


@final
class PathError(KnownError):
    pass


@final
class StatsContainerError(KnownError):
    pass


@final
class StringError(KnownError):
    pass


@final
class CustomProcessValueWrapperError(KnownError):
    pass


@final
class WrongExtraArgsPubError(KnownError):
    pass


@final
class CheckExtraArgsDictError(KnownError):
    pass


@final
class SimpleGenericContainerError(KnownError):
    pass


@final
class WrongContainerError(KnownError):
    pass


@final
class WrongContextError(KnownError):
    pass
