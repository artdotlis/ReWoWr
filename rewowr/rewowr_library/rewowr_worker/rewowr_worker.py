# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
import asyncio
import sys
import logging
import random

from multiprocessing import current_process

import traceback
from typing import List, Tuple, Optional, Union, final, Final
from dataclasses import dataclass

from rewowr.rewowr_library.rewowr_worker.workable.workable_elem import WorkerInOut
from rewowr.rewowr_library.rewowr_worker.workable.workable_manager import WorkableManager
from rewowr.rewowr_library.rewowr_worker.errors.custom_errors import WorkerError
from rewowr.simple_logger.synchronised_standard_output import SyncStdout
from rewowr.public.functions.error_handling import RedirectSysHandler, SysHandlerCon
from rewowr.public.errors.custom_errors import KnownError
from rewowr.public.functions.syncout_dep_functions import logger_send_error, \
    logger_print_log, logger_print_con, logger_send_warning, RedirectWriteToLogger, \
    RedirectErrorToLogger
from rewowr.public.constants.rewowr_worker_constants import WorkerContainerTypes, \
    WorkerPref, DataContainer, ContainerTypes
from rewowr.public.container.container_simple_generic import SimpleGenericContainer


_RoutineReturnA: Final = Tuple[
    Union[List[int], BaseException],
    Union[List[int], BaseException],
    Optional[BaseException]
]


def check_given_data(container_types: ContainerTypes, data: DataContainer,
                     worker_name: str, sync_out: SyncStdout, to_warn: bool, /) -> bool:
    if len(container_types) != len(data):
        raise WorkerError(f"The {worker_name} creates unexpected size of data!")
    warning_found = False
    for cont_index, cont_type in enumerate(container_types):
        for list_elem in data[cont_index]:
            if not warning_found and SimpleGenericContainer == type(list_elem):
                warning_found = True
            if not isinstance(list_elem, cont_type):
                raise WorkerError(f"The {worker_name} has mismatching types in given data!")

    if to_warn and warning_found:
        logger_send_warning(
            sync_out, 'Using SimpleGenericContainer is not recommended', worker_name
        )
    return not warning_found


@final
@dataclass
class _EventQueues:
    reader_queue: asyncio.queues.Queue
    worker_queue: asyncio.queues.Queue
    stop_event_reader: asyncio.locks.Event
    stop_event_worker: asyncio.locks.Event
    stop_event_error: asyncio.locks.Event


@final
@dataclass
class _Warned:
    reader: bool = True
    worker: bool = True


@final
@dataclass
class ErrorHandling:
    warned: _Warned = _Warned()
    error: bool = False


@final
class Worker:
    def __init__(self, pref_params: WorkerPref, worker_in_out: WorkerInOut,
                 container_types: WorkerContainerTypes, /) -> None:
        super().__init__()
        self.__workable_manager = WorkableManager(
            worker_in_out.workable_in, worker_in_out.workable_out
        )
        self.__name_id = pref_params.name_id
        self.__sync_out = pref_params.sync_out

        self.__loop: Optional[asyncio.AbstractEventLoop] = None
        self.__event_queues: Optional[_EventQueues] = None
        self.__container_types = container_types
        self.__workable_manager.provider_process_started()
        self.__error_handler: ErrorHandling = ErrorHandling()

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        if self.__loop is None:
            raise WorkerError("Loop-create wasn't used!")
        return self.__loop

    @property
    def event_queues(self) -> _EventQueues:
        if self.__event_queues is None:
            raise WorkerError("Loop-create wasn't used!")
        return self.__event_queues

    @staticmethod
    async def _create_event_queues() -> _EventQueues:
        return _EventQueues(
            reader_queue=asyncio.Queue(),
            worker_queue=asyncio.Queue(),
            stop_event_reader=asyncio.Event(),
            stop_event_worker=asyncio.Event(),
            stop_event_error=asyncio.Event()
        )

    async def _reader(self, p_name: str, /) -> List[int]:
        counter_read = [0 for _ in self.__container_types.reader_cont]
        reader_pointer_list: List[int] = []
        last_active = 0
        reader_len = len(self.__workable_manager.workable_in)
        try:
            while last_active < reader_len and not self.event_queues.stop_event_error.is_set():
                if not reader_pointer_list:
                    last_active = 0
                    reader_pointer_list = list(range(0, reader_len))

                pos_puf = random.randint(0, len(reader_pointer_list) - 1)
                reader_pointer = reader_pointer_list[pos_puf]
                del reader_pointer_list[pos_puf]

                val_new: DataContainer = tuple(
                    tuple() for _ in self.__container_types.reader_cont
                )
                new_elements_cnt = 0
                if await self.__workable_manager.workable_in[reader_pointer].workable_running():
                    val_new = await self.__workable_manager.workable_in[
                        reader_pointer
                    ].workable_read(
                        self.__container_types.reader_cont
                    )
                    for type_index, value_list in enumerate(val_new):
                        new_elements_cnt += len(value_list)
                        counter_read[type_index] += len(value_list)
                else:
                    last_active += 1

                if new_elements_cnt:
                    self.__error_handler.warned.reader = check_given_data(
                        self.__container_types.worker_cont.cont_in, val_new,
                        f"{self.__name_id}_reader", self.__sync_out,
                        self.__error_handler.warned.reader
                    )
                    logger_print_con(
                        self.__sync_out,
                        self.__name_id,
                        "{1} process_read {2} workable_running, {0}-th element!".format(
                            sum(counter_read), p_name, self.__name_id
                        ),
                        0.0,
                        False
                    )
                    await self._await_job(
                        self.event_queues.reader_queue, self.event_queues.stop_event_error
                    )
                    await self.event_queues.reader_queue.put((reader_pointer, val_new))
        except Exception as exc:
            self.event_queues.stop_event_error.set()
            raise exc
        finally:
            self.event_queues.stop_event_reader.set()
            return counter_read

    async def _writer_pointer(self, writer_pointer: int, writer_len: int,
                              erg: DataContainer, /) -> None:
        local_pointer = writer_pointer
        while await self.__workable_manager.workable_out[local_pointer].workable_write(
                erg, self.__container_types.writer_cont
        ):
            local_pointer = (local_pointer + 1) % writer_len

    async def _writer(self, p_name: str, /) -> List[int]:
        counter_write = [0 for _ in self.__container_types.writer_cont]
        writer_pointer_list: List[int] = []
        writer_len = len(self.__workable_manager.workable_out)
        try:
            while not (
                    (self.event_queues.stop_event_worker.is_set()
                     and self.event_queues.worker_queue.empty())
                    or self.event_queues.stop_event_error.is_set()
            ):
                try:
                    erg: DataContainer = await asyncio.wait_for(
                        self.event_queues.worker_queue.get(), timeout=1
                    )
                except asyncio.TimeoutError:
                    pass
                else:
                    if not writer_pointer_list:
                        writer_pointer_list = list(range(0, writer_len))

                    pos_puf = random.randint(0, len(writer_pointer_list) - 1)
                    writer_pointer = writer_pointer_list[pos_puf]
                    del writer_pointer_list[pos_puf]

                    new_elements_cnt = 0
                    for type_index, value_list in enumerate(erg):
                        counter_write[type_index] += len(value_list)
                        new_elements_cnt += len(value_list)

                    if new_elements_cnt:
                        await self._writer_pointer(writer_pointer, writer_len, erg)
                        logger_print_con(
                            self.__sync_out,
                            self.__name_id,
                            "{1} process_write {2} workable_running, {0}-th element!".format(
                                sum(counter_write), p_name, self.__name_id
                            ),
                            0.0,
                            False
                        )
                    self.event_queues.worker_queue.task_done()
        except Exception as exc:
            self.event_queues.stop_event_error.set()
            raise exc
        finally:
            return counter_write

    @staticmethod
    async def _await_job(queue: asyncio.Queue, event: asyncio.Event, /) -> None:
        job_done = False
        while not (event.is_set() or job_done):
            try:
                await asyncio.wait_for(queue.join(), timeout=1)
            except asyncio.TimeoutError:
                pass
            else:
                job_done = True

    async def _worker(self) -> None:
        try:
            while not (
                    (self.event_queues.stop_event_reader.is_set()
                     and self.event_queues.reader_queue.empty())
                    or self.event_queues.stop_event_error.is_set()
            ):
                try:
                    erg: Tuple[int, DataContainer] = await asyncio.wait_for(
                        self.event_queues.reader_queue.get(), timeout=1
                    )
                except asyncio.TimeoutError:
                    pass
                else:
                    self.event_queues.reader_queue.task_done()
                    async for list_worked in self.__workable_manager.workable_in[erg[0]]\
                            .workable_work(erg[1], self.__container_types.worker_cont):
                        if sum(len(list_elem) for list_elem in list_worked):
                            self.__error_handler.warned.worker = check_given_data(
                                self.__container_types.writer_cont,
                                list_worked, f"{self.__name_id}_worker",
                                self.__sync_out, self.__error_handler.warned.worker
                            )
                            await self._await_job(
                                self.event_queues.worker_queue, self.event_queues.stop_event_error
                            )
                            await self.event_queues.worker_queue.put(list_worked)
                        if self.event_queues.stop_event_error.is_set():
                            break
        except Exception as exc:
            self.event_queues.stop_event_error.set()
            raise exc
        finally:
            self.event_queues.stop_event_worker.set()

    async def _start_coroutines(self, p_name: str, /) -> _RoutineReturnA:
        self.event_queues.stop_event_worker.clear()
        self.event_queues.stop_event_reader.clear()
        self.event_queues.stop_event_error.clear()
        erg = await asyncio.gather(
            self._reader(p_name), self._writer(p_name),
            self._worker(), return_exceptions=True
        )
        return erg

    def _init_worker_loop_events(self) -> None:
        self.__loop = asyncio.new_event_loop()
        self.__event_queues = self.__loop.run_until_complete(self._create_event_queues())

    def _finished(self, p_name: str, counter_read: List[int], counter_write: List[int], /) -> None:
        if not self.__sync_out.error_occurred():
            for index_num, value in enumerate(self.__container_types.reader_cont):
                logger_print_log(
                    self.__sync_out,
                    "[{2}] Container({0})-elements received: {1}".format(
                        value.__name__,
                        counter_read[index_num],
                        self.__name_id
                    ),
                    logging.INFO
                )
            for index_num, value in enumerate(self.__container_types.writer_cont):
                logger_print_log(
                    self.__sync_out,
                    "[{2}] Container({0})-elements send: {1}".format(
                        value.__name__,
                        counter_write[index_num],
                        self.__name_id
                    ),
                    logging.INFO
                )
            logger_print_con(
                self.__sync_out,
                self.__name_id,
                "Worker {0} ({1}) [done]".format(self.__name_id, p_name),
                100.0,
                True
            )
            self.__workable_manager.provider_process_stopped()

    def _error_handling(self, known_error: KnownError,
                        sys_handlers: RedirectSysHandler, /) -> None:
        try:
            raise known_error
        except KnownError as local_error:
            logger_send_error(
                self.__sync_out, 'Expected', local_error,
                self.__name_id, traceback.format_exc()
            )
            sys_handlers.on_known_errors(str(known_error))
            self.__error_handler.error = True

    def run(self) -> None:
        sys_handlers = RedirectSysHandler(SysHandlerCon(
            sys_handler=RedirectWriteToLogger(self.__sync_out),
            sys_error_h=RedirectErrorToLogger(self.__sync_out),
            stdout_buffer=sys.stdout,
            stderr_buffer=sys.stderr
        ))
        sys_handlers.set_sys_handler()
        try:
            self._init_worker_loop_events()
            self.__workable_manager.init_all_workables(self.loop)
            p_name = current_process().name
            # check block
            self.__workable_manager.check_block()
            output = self.loop.run_until_complete(
                self._start_coroutines(p_name)
            )
            for p_err in output:
                if isinstance(p_err, KnownError):
                    self._error_handling(p_err, sys_handlers)
                elif isinstance(p_err, Exception):
                    raise p_err
            if not (isinstance(output[0], list) and isinstance(output[1], list)):
                raise WorkerError("Fatal check error!")
            counter_read = output[0]
            counter_write = output[1]
        except KnownError as known_error:
            self._error_handling(known_error, sys_handlers)
        except Exception as error:
            self.__error_handler.error = True
            logger_send_error(
                self.__sync_out, 'Not expected', error,
                self.__name_id, traceback.format_exc()
            )
            sys_handlers.on_exception(str(error))
            raise error
        else:
            self._finished(p_name, counter_read, counter_write)
        finally:
            if self.loop.is_running():
                self.loop.stop()
            if not self.loop.is_closed():
                self.loop.close()
            if self.__error_handler.error:
                self.__workable_manager.set_error_in_workables()
            sys_handlers.close()
