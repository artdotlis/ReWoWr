# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""

import datetime
import atexit
import json
import logging
import math
import os
import queue
import shutil
import sys
import time

from functools import reduce
import multiprocessing
from multiprocessing import synchronize, current_process
from pathlib import Path
from typing import Dict, Tuple, List, Callable, TextIO, Final, final, Optional
from dataclasses import dataclass

from rewowr.simple_logger.constants.synchronised_standard_output_const import SyncOutMsg, \
    get_time_format_pattern, get_new_line_pattern
from rewowr.simple_logger.functions.syncout_less_functions import format_message_time
from rewowr.simple_logger.errors.custom_errors import SyncStdoutError
from rewowr.public.container.json_stats_container import \
    JsonStatsContainerIntFloatList
from rewowr.public.extra_types.custom_types import CustomProcessValueWrapper, \
    CustomManagedDictWrapper
from rewowr.public.functions.path_functions import create_dirs_rec
from rewowr.public.interfaces.logger_interface import SyncStdoutInterface

_SyncOutSt: Final = Tuple[float, bool]
_MSG_STR: Final[Tuple[str, str, str, str]] = ("-", "\\", "|", "/")


@final
@dataclass
class _GlobalCounterCl:
    prog_counter: CustomProcessValueWrapper[int]
    done_object_counter: CustomProcessValueWrapper[int]
    current_msg_line: CustomProcessValueWrapper[int]
    first_print: CustomProcessValueWrapper[int]


@final
@dataclass
class _OutputWaitingProcessTypes:
    run: CustomProcessValueWrapper[int]
    status: CustomProcessValueWrapper[int]
    logger_cnt: CustomProcessValueWrapper[int]
    id_cnt: CustomProcessValueWrapper[int]
    started: float


def _print_at_exit(output_stream: TextIO, /) -> None:
    output_stream.write("\n")
    output_stream.flush()
    output_stream.close()


@final
class _SysOutPrinter:
    def __init__(self, manager: 'LogManager', /) -> None:
        super().__init__()
        atexit.register(_print_at_exit, sys.__stdout__)
        self.__log_manager = manager

    @staticmethod
    def _prog_bar_calc(count: int, wait_str: str, prog: float, /) -> str:
        if count <= int(prog):
            return '#'
        if count - 1 <= int(prog) and count < 10:
            return wait_str

        return " "

    @staticmethod
    def __format_global_status(wait_str: str, act_objects: int, done_objects: int,
                               time_started: float, prog: float, /) -> str:
        sec = time.time() - time_started
        time_form = get_time_format_pattern().search(str(datetime.timedelta(seconds=sec)))
        prog_bar = "".join(
            _SysOutPrinter._prog_bar_calc(x_n + 1, wait_str, prog)
            for x_n in range(10)
        )
        return " Uptime: {0} | {2}/{1} | [{3}] ".format(
            time_form.group(1) if time_form is not None else "ERROR",
            act_objects, done_objects, prog_bar
        )[:1000]

    def __print_status(self, new_line_number: int, term_size_columns: int, /) -> None:
        uptime_loc = self.__log_manager.wa_process_attributes.started
        with self.__log_manager.manager_lock:
            act_obj = len(self.__log_manager.sync_object_manager.managed_dict)
            if act_obj:
                prog: float = reduce(
                    (lambda x, y: x + y),
                    (
                        elem[0] for elem
                        in self.__log_manager.sync_object_manager.managed_dict.values()
                    )
                ) / (10 * act_obj)
            else:
                prog = 0.0
            self.__log_manager.manager_counter.prog_counter.value = \
                (self.__log_manager.manager_counter.prog_counter.value + 1) % len(_MSG_STR)
            sys.__stdout__.write(
                "\u001b[u\u001b[2K\u001b[1G{1}\u001b[48;5;240m{0}\u001b[0m\u001b[s".format(
                    self.__format_global_status(
                        _MSG_STR[self.__log_manager.manager_counter.prog_counter.value],
                        act_obj,
                        self.__log_manager.manager_counter.done_object_counter.value,
                        uptime_loc,
                        prog
                    )[0:term_size_columns], "".join('\n' for _ in range(new_line_number))
                )
            )
            sys.__stdout__.flush()

    @staticmethod
    def __check_message(message: SyncOutMsg, /) -> None:
        if message.status < 0 or message.status > 100:
            raise SyncStdoutError(
                "Status values for the SyncOutMsg type must be floats between 0 and 100!"
            )
        if not message.s_id:
            raise SyncStdoutError("Message id ca not be empty!")

    @staticmethod
    def __check_object_status(message: SyncOutMsg, to_check: _SyncOutSt, /) -> None:
        if message.done and to_check[1]:
            SyncStdoutError("The messaging object was already closed!")
        if message.status < to_check[0]:
            SyncStdoutError(
                "The messaging object had a higher progress value than stated in the message!"
            )

    def __print_to_stdout(self, message_msg: str, term_size_lines: int, term_size_columns: int,
                          format_func: Callable[[str], List[str]], /) -> None:
        form_msg = format_func(message_msg)
        print_size = term_size_lines - 4
        for x_mul in range(math.ceil(len(form_msg) / print_size)):
            extra_lines = 0
            line_diff = term_size_lines - (
                self.__log_manager.manager_counter.current_msg_line.value
                + len(form_msg[x_mul * print_size: (x_mul + 1) * print_size])
                + 2
            )
            if line_diff < 0:
                extra_lines += -1 * line_diff
                self.__log_manager.manager_counter.current_msg_line.value += line_diff
            self.__print_status(extra_lines, term_size_columns)
            sys.__stdout__.write("\u001b[{1};1H{0}\u001b[u".format(
                "\n".join(
                    line[0:term_size_columns]
                    for line in form_msg[x_mul * print_size: (x_mul + 1) * print_size]
                ),
                self.__log_manager.manager_counter.current_msg_line.value
            ))
            sys.__stdout__.flush()
            self.__log_manager.manager_counter.current_msg_line.value += len(
                form_msg[x_mul * print_size: (x_mul + 1) * print_size]
            )

    def print_to_console(self, message: SyncOutMsg,
                         format_func: Callable[[str], List[str]], /) -> None:

        with self.__log_manager.manager_lock:
            term_size = shutil.get_terminal_size(fallback=(80, 15))
            if term_size.lines < 10 or term_size.columns < 10:
                raise SyncStdoutError("Terminal size is to small!")
            if not self.__log_manager.manager_counter.first_print.value:
                self.__log_manager.manager_counter.first_print.value = 1
                sys.__stdout__.write("\u001b[2J\u001b[{0};1H\u001b[s".format(
                    term_size.lines
                ))
                sys.__stdout__.flush()

            self.__check_message(message)
            new_act_object = self.__log_manager.sync_object_manager.managed_dict.get(message.s_id)
            if new_act_object is not None:
                self.__check_object_status(message, new_act_object)

            new_act_object = (message.status, message.done)
            if message.done:
                self.__log_manager.manager_counter.done_object_counter.value += 1

            self.__log_manager.sync_object_manager.managed_dict[message.s_id] = new_act_object

            self.__print_to_stdout(message.msg, term_size.lines, term_size.columns, format_func)
            self.__print_status(0, term_size.columns)

    def get_manager(self) -> 'LogManager':
        return self.__log_manager


@final
class LogManager:
    def __init__(self, ctx_local: multiprocessing.context.SpawnContext, /) -> None:
        super().__init__()
        self.__manager_counter = _GlobalCounterCl(
            prog_counter=CustomProcessValueWrapper[int](ctx_local, 0),
            done_object_counter=CustomProcessValueWrapper[int](ctx_local, 0),
            current_msg_line=CustomProcessValueWrapper[int](ctx_local, 1),
            first_print=CustomProcessValueWrapper[int](ctx_local, 0)
        )
        self.__sync_object_manager: CustomManagedDictWrapper[str, _SyncOutSt] = \
            CustomManagedDictWrapper[str, _SyncOutSt](ctx_local)
        self.__manager_lock: synchronize.RLock = ctx_local.RLock()
        self.__wa_process_attributes: _OutputWaitingProcessTypes = \
            _OutputWaitingProcessTypes(
                run=CustomProcessValueWrapper[int](ctx_local, 0),
                status=CustomProcessValueWrapper[int](ctx_local, 0),
                logger_cnt=CustomProcessValueWrapper[int](ctx_local, 0),
                started=time.time(),
                id_cnt=CustomProcessValueWrapper[int](ctx_local, 1)
            )
        self.__queue = ctx_local.Queue()
        self.__error = CustomProcessValueWrapper[int](ctx_local, 0)

    @property
    def manager_error(self) -> bool:
        return bool(self.__error.value)

    def set_manager_error(self) -> None:
        with self.__manager_lock:
            self.__error.value = 1

    def writer_to_queue(self, msg: Tuple[SyncOutMsg, Callable[[str], List[str]]], /) -> None:
        self.__queue.put(msg)

    def get_from_queue(self) -> Tuple[SyncOutMsg, Callable[[str], List[str]]]:
        return self.__queue.get(True, 2)

    @property
    def queue_empty(self) -> bool:
        return self.__queue.empty()

    @property
    def wa_process_attributes(self) -> _OutputWaitingProcessTypes:
        return self.__wa_process_attributes

    @property
    def manager_counter(self) -> _GlobalCounterCl:
        return self.__manager_counter

    @property
    def sync_object_manager(self) -> CustomManagedDictWrapper[str, _SyncOutSt]:
        return self.__sync_object_manager

    @property
    def manager_lock(self) -> synchronize.RLock:
        return self.__manager_lock

    @property
    def id_cnt(self) -> int:
        return self.__wa_process_attributes.id_cnt.value

    def zero_status(self) -> None:
        with self.__manager_lock:
            self.__wa_process_attributes.status.value = 0

    @property
    def logger_cnt(self) -> int:
        with self.__manager_lock:
            return self.__wa_process_attributes.logger_cnt.value

    @property
    def run(self) -> bool:
        with self.__manager_lock:
            return bool(self.__wa_process_attributes.run.value >= 1)

    def run_with_update(self, run_par: bool, /) -> bool:
        start_pr = False
        with self.__manager_lock:
            if run_par:
                if not self.__wa_process_attributes.status.value:
                    self.__wa_process_attributes.status.value = 1
                    start_pr = True
                    self.__wa_process_attributes.id_cnt.value += 1
                self.__wa_process_attributes.logger_cnt.value += 1
                self.__wa_process_attributes.run.value += 1
            else:
                if self.__wa_process_attributes.run.value <= 0:
                    raise SyncStdoutError("No logger was started!")
                self.__wa_process_attributes.run.value -= 1
        return start_pr

    def join(self) -> None:
        wait_bool = True
        while wait_bool:
            with self.__manager_lock:
                if not (self.__wa_process_attributes.status.value or self.run):
                    wait_bool = False
            time.sleep(1.5)


def _print_empty(printer: _SysOutPrinter, pid_cur: Optional[int], manager: LogManager, /) -> None:
    printer.print_to_console(SyncOutMsg(
        s_id="_OutputWaitingProcess_{0}_{1}".format(
            pid_cur, manager.id_cnt
        ),
        msg="",
        status=0.0,
        done=False
    ), format_message_time)


def _waiting_output_str(manager: LogManager, /) -> None:
    pid_cur = current_process().pid
    running = True
    printer = _SysOutPrinter(manager)
    _print_empty(printer, pid_cur, manager)
    try:
        while running:
            try:
                erg = manager.get_from_queue()
            except queue.Empty:
                _print_empty(printer, pid_cur, manager)
            else:
                if isinstance(erg, tuple) and len(erg) == 2:
                    printer.print_to_console(erg[0], erg[1])
            running = manager.run or not manager.queue_empty
        out_msg = "_OutputWaitingProcess [done]"
        act_obj = len(manager.sync_object_manager.managed_dict) - 1
        act_obj -= manager.manager_counter.done_object_counter.value
        if act_obj:
            out_msg = f"{out_msg} unfinished objects: {act_obj}"
        printer.print_to_console(SyncOutMsg(
            s_id="_OutputWaitingProcess_{0}_{1}".format(pid_cur, manager.id_cnt),
            msg=out_msg,
            status=100.0,
            done=True
        ), format_message_time)
    except Exception as exc:
        manager.set_manager_error()
        raise exc
    finally:
        manager.zero_status()


@final
@dataclass
class _LoggingStats:
    errors_cnt: CustomProcessValueWrapper[int]
    info_cnt: CustomProcessValueWrapper[int]
    warn_cnt: CustomProcessValueWrapper[int]
    other_cnt: CustomProcessValueWrapper[int]


@final
@dataclass
class _General:
    g_id: int
    step: str
    working_dir: str
    global_manager: LogManager


@final
@dataclass
class _EndConD:
    flush_stats: CustomProcessValueWrapper[int]
    flush_log: CustomProcessValueWrapper[int]


def _increase_error(log_stats: _LoggingStats, /) -> None:
    log_stats.errors_cnt.value += 1


def _increase_warning(log_stats: _LoggingStats, /) -> None:
    log_stats.warn_cnt.value += 1


def _increase_info(log_stats: _LoggingStats, /) -> None:
    log_stats.info_cnt.value += 1


def _increase_other(log_stats: _LoggingStats, /) -> None:
    log_stats.other_cnt.value += 1


@final
@dataclass
class _LoggerData:
    lock: synchronize.RLock
    queue: multiprocessing.Queue
    running: CustomProcessValueWrapper[int]
    finished: CustomProcessValueWrapper[int]


@final
@dataclass
class _LoggerMsg:
    msg: str
    level: int


def _logger_process(working_data: _LoggerData, working_dir: Path, step_name: str, /) -> None:
    logger: logging.Logger = logging.getLogger(step_name)
    logger.setLevel(logging.INFO)

    ch_handler = logging.FileHandler(
        "{0}{1}{2}.log".format(str(working_dir), os.sep, step_name), 'w'
    )
    ch_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(processName)s - %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p'
    )

    ch_handler.setFormatter(formatter)

    logger.addHandler(ch_handler)
    running = True
    while running:
        try:
            erg = working_data.queue.get(True, 10)
        except queue.Empty:
            erg = None
        with working_data.lock:
            if working_data.queue.empty() and not working_data.running.value:
                running = False
        if erg is not None and isinstance(erg, _LoggerMsg):
            logger.log(erg.level, erg.msg, exc_info=False)

    with working_data.lock:
        working_data.finished.value = 0


def _simple_formatter(msg: str, /) -> List[str]:
    return [msg_el for msg_el in get_new_line_pattern().split(msg) if msg_el]


@final
@dataclass
class SyncStdoutArgs:
    step_name: str
    working_dir: Path


@final
class SyncStdout(SyncStdoutInterface):
    _logger_switch: Final[Dict[int, Callable[[_LoggingStats], None]]] = {
        logging.ERROR: _increase_error,
        logging.WARNING: _increase_warning,
        logging.INFO: _increase_info
    }

    def __init__(self, stdout_args: SyncStdoutArgs,
                 ctx_local: multiprocessing.context.SpawnContext, manager: LogManager,
                 pr_list: List[multiprocessing.context.SpawnProcess], /) -> None:
        super().__init__()
        create_dirs_rec(stdout_args.working_dir)
        if manager.run_with_update(True):
            pr_list.append(ctx_local.Process(
                target=_waiting_output_str, args=(manager,)
            ))
            pr_list[-1].start()
        self.__logger_data = _LoggerData(
            lock=ctx_local.RLock(),
            queue=ctx_local.Queue(),
            running=CustomProcessValueWrapper[int](ctx_local, 1),
            finished=CustomProcessValueWrapper[int](ctx_local, 1)
        )
        pr_list.append(ctx_local.Process(
            target=_logger_process, args=(
                self.__logger_data, stdout_args.working_dir, stdout_args.step_name
            )
        ))
        pr_list[-1].start()
        self.__stats_lock = ctx_local.RLock()
        self.__logging_stats: _LoggingStats = _LoggingStats(
            errors_cnt=CustomProcessValueWrapper[int](ctx_local, 0),
            info_cnt=CustomProcessValueWrapper[int](ctx_local, 0),
            warn_cnt=CustomProcessValueWrapper[int](ctx_local, 0),
            other_cnt=CustomProcessValueWrapper[int](ctx_local, 0)
        )
        self.__general: _General = _General(
            g_id=manager.logger_cnt,
            step=stdout_args.step_name,
            working_dir=str(stdout_args.working_dir),
            global_manager=manager
        )
        self.__stats: CustomManagedDictWrapper[str, JsonStatsContainerIntFloatList] = \
            CustomManagedDictWrapper[str, JsonStatsContainerIntFloatList](ctx_local)
        self.__end_con: _EndConD = _EndConD(
            flush_stats=CustomProcessValueWrapper[int](ctx_local, 1),
            flush_log=CustomProcessValueWrapper[int](ctx_local, 1)
        )
        if self.__general.global_manager.manager_error:
            _increase_error(self.__logging_stats)
            sys.__stdout__.write("ERROR occurred in output process (init step)!")
            sys.__stdout__.flush()
        else:
            manager.writer_to_queue((SyncOutMsg(
                s_id="SyncStdout_{0}".format(
                    self.__general.g_id
                ),
                msg="SyncStdout_{0} started!".format(
                    self.__general.g_id
                ),
                status=0.0,
                done=False
            ), format_message_time))

    def error_occurred(self) -> bool:
        with self.__stats_lock:
            return bool(self.__logging_stats.errors_cnt.value > 0)

    def print_message_simple(self, message: str, /) -> None:
        if self._check_closed():
            raise SyncStdoutError("The logger was already closed!")
        if self.__general.global_manager.manager_error:
            _increase_error(self.__logging_stats)
            sys.__stdout__.write("ERROR occurred in output process (printing message simple)!")
            sys.__stdout__.flush()
        else:
            self.__general.global_manager.writer_to_queue((SyncOutMsg(
                s_id="SyncStdout_{0}".format(
                    self.__general.g_id
                ),
                msg=message,
                status=0.0,
                done=False
            ), _simple_formatter))

    def print_message(self, message: SyncOutMsg,
                      format_func: Callable[[str], List[str]], /) -> None:
        if self._check_closed():
            raise SyncStdoutError("The logger was already closed!")

        message.s_id = "SyncStdout_{0}_{1}".format(
            self.__general.g_id, message.s_id
        )
        if self.__general.global_manager.manager_error:
            _increase_error(self.__logging_stats)
            sys.__stdout__.write("ERROR occurred in output process (printing message)!")
            sys.__stdout__.flush()
        else:
            self.__general.global_manager.writer_to_queue((message, format_func))

    def print_logger(self, message: str, log_level: int, /) -> None:
        if self._check_closed():
            raise SyncStdoutError("The logger was already closed!")

        self.__logger_data.queue.put(_LoggerMsg(msg=message, level=log_level))

        with self.__stats_lock:
            self._logger_switch.get(log_level, _increase_other)(self.__logging_stats)

    def save_stats(self, object_name: str, stats_to_merge: Dict, /) -> None:
        if self._check_closed():
            raise SyncStdoutError("The logger was already closed!")
        if not object_name:
            raise SyncStdoutError("object_name should not be empty!")

        with self.__stats_lock:
            puf = self.__stats.managed_dict.get(object_name, JsonStatsContainerIntFloatList())
            puf.merge_stats_dict(stats_to_merge)
            self.__stats.managed_dict[object_name] = puf

    # can be flushed several times, but only the first time are the stats saved
    def flush_stats(self) -> None:
        with self.__stats_lock:
            if self.__end_con.flush_stats.value:
                dict_json = {}
                for keys, dict_value in self.__stats.managed_dict.items():
                    dict_json[keys] = dict_value.stats_container

                if dict_json:
                    fi_puf = Path(
                        "{0}{1}{2}_stats.json".format(
                            self.__general.working_dir, os.sep, self.__general.step
                        )
                    )

                    with fi_puf.open('w') as file_hand:
                        json.dump(dict_json, file_hand, indent=4)

                self.__end_con.flush_stats.value = 0

    # can be flushed several times, but only the first time are the stats saved
    def flush_log_stats(self) -> None:
        with self.__stats_lock:
            flushed = self.__end_con.flush_log.value
            self.__end_con.flush_log.value = 0

        if flushed:
            msg = "Step {0}: Errors: {1}; Warnings: {2}; Info: {3}; Other: {4}".format(
                self.__general.step,
                self.__logging_stats.errors_cnt.value,
                self.__logging_stats.warn_cnt.value,
                self.__logging_stats.info_cnt.value,
                self.__logging_stats.other_cnt.value
            )
            if self.__general.global_manager.manager_error:
                _increase_error(self.__logging_stats)
                sys.__stdout__.write("ERROR occurred in output process (flushing step)!")
                sys.__stdout__.flush()
            else:
                self.__general.global_manager.writer_to_queue((SyncOutMsg(
                    s_id="SyncStdout_{0}".format(
                        self.__general.g_id
                    ),
                    msg=msg,
                    status=50.0,
                    done=False
                ), format_message_time))

    def _check_closed(self) -> bool:
        with self.__stats_lock:
            return not (self.__end_con.flush_log.value and self.__end_con.flush_stats.value)

    def _join_logger(self) -> None:
        wait_bool = True
        while wait_bool:
            with self.__logger_data.lock:
                if not self.__logger_data.finished.value:
                    wait_bool = False
            time.sleep(1.5)

    # should be used only once
    def close_logger(self) -> None:
        @final
        @dataclass
        class _LStatus:
            flush_log: int
            flush_stats: int

        msg = ""
        with self.__stats_lock:
            erg_flush = _LStatus(
                flush_log=self.__end_con.flush_log.value,
                flush_stats=self.__end_con.flush_stats.value
            )
            self.__end_con.flush_log.value = 0
            self.__end_con.flush_stats.value = 0

        if erg_flush.flush_log:
            msg += "The logger log_stats were not flushed!\n"
        if erg_flush.flush_stats:
            msg += "The logger stats were not flushed!\n"
        if not (erg_flush.flush_log or erg_flush.flush_stats):
            msg += "The logger was closed correctly!\n"

        if self.__general.global_manager.manager_error:
            _increase_error(self.__logging_stats)
            sys.__stdout__.write("ERROR occurred in output process (closing step)!")
            sys.__stdout__.flush()
        else:
            self.__general.global_manager.writer_to_queue((SyncOutMsg(
                s_id="SyncStdout_{0}".format(
                    self.__general.g_id
                ),
                msg=msg,
                status=100.0,
                done=True
            ), format_message_time))

        _ = self.__general.global_manager.run_with_update(False)
        with self.__logger_data.lock:
            self.__logger_data.running.value = 0

        self._join_logger()
        self.__general.global_manager.join()
