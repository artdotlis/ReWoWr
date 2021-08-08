# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""

from typing import Callable, List, Dict

import abc

from rewowr.simple_logger.constants.synchronised_standard_output_const import SyncOutMsg


class SyncStdoutInterface(abc.ABC):
    @abc.abstractmethod
    def error_occurred(self) -> bool:
        raise NotImplementedError("Interface!")

    @abc.abstractmethod
    def print_message_simple(self, message: str, /) -> None:
        raise NotImplementedError("Interface!")

    @abc.abstractmethod
    def print_message(self, message: SyncOutMsg,
                      format_func: Callable[[str], List[str]], /) -> None:
        raise NotImplementedError("Interface!")

    @abc.abstractmethod
    def print_logger(self, message: str, log_level: int, /) -> None:
        raise NotImplementedError("Interface!")

    @abc.abstractmethod
    def save_stats(self, object_name: str, stats_to_merge: Dict, /) -> None:
        raise NotImplementedError("Interface!")

    @abc.abstractmethod
    def flush_stats(self) -> None:
        raise NotImplementedError("Interface!")

    @abc.abstractmethod
    def flush_log_stats(self) -> None:
        raise NotImplementedError("Interface!")

    @abc.abstractmethod
    def close_logger(self) -> None:
        raise NotImplementedError("Interface!")
