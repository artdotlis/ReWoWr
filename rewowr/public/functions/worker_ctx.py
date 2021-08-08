# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
import multiprocessing
from typing import Final

from rewowr.public.errors.custom_errors import WrongContextError


_CTX: Final[multiprocessing.context.BaseContext] = multiprocessing.get_context("spawn")


def get_worker_ctx() -> multiprocessing.context.SpawnContext:
    if not isinstance(_CTX, multiprocessing.context.SpawnContext):
        raise WrongContextError(f"Expected SpawnContext got {type(_CTX).__name__}")
    return _CTX
