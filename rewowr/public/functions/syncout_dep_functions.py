# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
import atexit
import os

import io

import logging
from multiprocessing import current_process

import threading
from queue import Queue, Empty
from typing import Optional, final

from rewowr.public.interfaces.logger_interface import SyncStdoutInterface
from rewowr.simple_logger.constants.synchronised_standard_output_const import SyncOutMsg, \
    get_new_line_pattern
from rewowr.simple_logger.functions.syncout_less_functions import format_message_time


def logger_print_con(sync_out: SyncStdoutInterface, object_name: str,
                     message: str, status: float, done: bool, /) -> None:
    sync_out.print_message(SyncOutMsg(
        s_id="{0}_{1}".format(
            object_name, current_process().pid
        ),
        msg=message,
        status=status,
        done=done
    ), format_message_time)


def logger_send_error(sync_out: SyncStdoutInterface, string: str, error: Exception,
                      object_name: str, trace_back: str, /) -> None:
    logger_print_log(
        sync_out,
        "{0} error: {1} in {2}\n{3}".format(string, error, object_name, trace_back),
        logging.ERROR
    )


def logger_send_warning(sync_out: SyncStdoutInterface, string: str, object_name: str, /) -> None:
    logger_print_log(
        sync_out,
        f"Warning in: {object_name}\n{string}",
        logging.WARNING
    )


def logger_print_log(sync_out: SyncStdoutInterface, message: str,
                     log_level: int, /) -> None:
    sync_out.print_logger(message, log_level)


def logger_print_to_console(sync_out: SyncStdoutInterface, message: str, /) -> None:
    sync_out.print_message_simple(message)


@final
class RedirectWriteToLogger(io.TextIOWrapper):

    def __init__(self, sync_out: SyncStdoutInterface, /) -> None:
        dev_nul = open(os.devnull, 'wb')
        atexit.register(dev_nul.close)
        super().__init__(dev_nul)
        self.__sync_out = sync_out

    def write(self, s: str) -> int:
        msg = s
        if [line_msg for line_msg in get_new_line_pattern().split(msg) if line_msg]:
            logger_print_to_console(
                self.__sync_out, f"{current_process().name} ({current_process().pid}):\n\t{msg}"
            )
        return len(msg)


def _writer_thread(sync_out: SyncStdoutInterface, queue: Queue, /) -> None:
    running = True
    wrapper_str = f"Error: {current_process().name} ({current_process().pid}):"
    msg_out = ""
    while running:
        try:
            erg = queue.get(True, 2)
        except Empty:
            erg = None
        if erg == "X_DONE_X":
            running = False
        elif isinstance(erg, str):
            new_msg = '\n\t'.join(
                line_msg for line_msg in get_new_line_pattern().split(erg) if line_msg
            )
            if new_msg:
                msg_out += f"\n\t{new_msg}"

    logger_print_to_console(
        sync_out, f"\u001b[31m{wrapper_str}{msg_out}\u001b[0m"
    )


@final
class RedirectErrorToLogger(io.TextIOWrapper):

    def __init__(self, sync_out: SyncStdoutInterface, /) -> None:
        dev_nul = open(os.devnull, 'wb')
        atexit.register(dev_nul.close)
        super().__init__(dev_nul)
        self.__sync_out = sync_out
        self.__queue: Queue = Queue()
        self.__writer_thread: Optional[threading.Thread] = None
        self.__closed = False

    def write(self, s: str) -> int:
        msg = s
        new_msg = '\n'.join(
            line_msg for line_msg in get_new_line_pattern().split(msg) if line_msg
        )
        if self.__closed and new_msg:
            logger_print_to_console(
                self.__sync_out,
                f"\u001b[31mTHE MESSAGE WAS SEND AFTER CLOSING WRITER:\n{new_msg}\u001b[0m"
            )
        elif new_msg:
            if self.__writer_thread is None:
                self.__writer_thread = threading.Thread(
                    target=_writer_thread, args=(self.__sync_out, self.__queue)
                )
                self.__writer_thread.start()
            self.__queue.put(msg)

        return len(msg)

    def join_thread(self) -> None:
        if not self.__closed and self.__writer_thread is not None:
            self.__queue.put("X_DONE_X")
            self.__writer_thread.join()
        self.__closed = True
