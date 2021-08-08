# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
import atexit
import io
import os
import sys
from dataclasses import dataclass
from typing import final, TextIO

from rewowr.public.functions.syncout_dep_functions import RedirectWriteToLogger, \
    RedirectErrorToLogger


@final
@dataclass
class SysHandlerCon:
    sys_handler: RedirectWriteToLogger
    sys_error_h: RedirectErrorToLogger
    stderr_buffer: TextIO
    stdout_buffer: TextIO


@final
class RedirectSysHandler:
    def __init__(self, sys_handler: SysHandlerCon, /) -> None:
        super().__init__()
        self.__sys_hand = sys_handler

    def set_sys_handler(self) -> None:
        sys.stdout = self.__sys_hand.sys_handler
        sys.stderr = self.__sys_hand.sys_error_h

    def on_known_errors(self, msg: str, /) -> None:
        self.__sys_hand.sys_error_h.write(msg)

    def on_exception(self, msg: str, /) -> None:
        self.__sys_hand.sys_error_h.write(msg)
        self.__sys_hand.stderr_buffer = io.TextIOWrapper(open(os.devnull, 'wb'))
        atexit.register(self.__sys_hand.stderr_buffer.close)
        sys.stderr = self.__sys_hand.stderr_buffer

    def join_errors(self) -> None:
        self.__sys_hand.sys_error_h.join_thread()

    def close(self) -> None:
        sys.stdout = self.__sys_hand.stdout_buffer
        sys.stderr = self.__sys_hand.stderr_buffer
        self.__sys_hand.sys_handler.close()
        self.__sys_hand.sys_error_h.join_thread()
        self.__sys_hand.sys_error_h.close()
