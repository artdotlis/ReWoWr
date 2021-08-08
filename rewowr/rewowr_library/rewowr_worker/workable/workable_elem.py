# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""

from concurrent.futures import ThreadPoolExecutor
import multiprocessing
from multiprocessing import synchronize
import asyncio

from typing import List, Optional, AsyncIterable, final
from dataclasses import dataclass

from rewowr.public.interfaces.container_interface import ContainerInterface
from rewowr.public.container.container_no_connection import NoConnectionContainer
from rewowr.public.interfaces.re_wr_interface import ReWrInterface
from rewowr.public.interfaces.work_interface import WorkInterface
from rewowr.public.extra_types.custom_types import CustomProcessValueWrapper
from rewowr.public.constants.rewowr_worker_constants import WorkerTypeParam, \
    WorkerContainerTypes, PoolLoopCont
from rewowr.public.constants.rewowr_worker_constants import ContainerTypes, DataContainer

from rewowr.rewowr_library.rewowr_worker.errors.custom_errors import WorkableError, \
    ReWrProgressError
from rewowr.simple_logger.synchronised_standard_output import SyncStdout


@final
@dataclass
class _EndTypeInt:
    error: int
    term: int


@final
@dataclass
class _EndType:
    error: CustomProcessValueWrapper[int]
    term: CustomProcessValueWrapper[int]


@final
class ReWrProgress:

    def __init__(self, ctx: multiprocessing.context.SpawnContext, /) -> None:
        super().__init__()
        self.__end = _EndType(
            error=CustomProcessValueWrapper[int](ctx, 0),
            term=CustomProcessValueWrapper[int](ctx, -1)
        )
        self.__lock_re_wr: synchronize.RLock = ctx.RLock()

    # Can block event queue

    @property
    def end_type(self) -> _EndTypeInt:
        return _EndTypeInt(
            error=self.__end.error.value,
            term=self.__end.term.value
        )

    def add_provider(self) -> None:
        with self.__lock_re_wr:
            if self.__end.term.value == -1:
                self.__end.term.value = 1
            else:
                self.__end.term.value += 1

    def remove_provider(self) -> bool:
        last = False
        with self.__lock_re_wr:
            self.__end.term.value -= 1
            if self.__end.term.value < 0:
                raise ReWrProgressError("ReWrProgress had no provider left, but one was removed!")
            if not self.__end.term.value:
                last = True
        return last

    def set_error(self) -> None:
        with self.__lock_re_wr:
            self.__end.error.value = 1


@final
@dataclass
class _AsLock:
    writer_async: asyncio.locks.Lock
    reader_async: asyncio.locks.Lock
    worker_async: asyncio.locks.Lock


@final
@dataclass
class _Locks:
    as_lock: Optional[_AsLock]
    gl_lock: synchronize.Condition


@final
class Workable:

    def __init__(self, sync_out: SyncStdout, ctx: multiprocessing.context.SpawnContext,
                 work_instance: WorkInterface, re_wr_instance: ReWrInterface, /) -> None:
        super().__init__()
        self.__sync_out: SyncStdout = sync_out
        self.__work_obj: WorkInterface = work_instance
        self.__re_wr_obj: ReWrInterface = re_wr_instance
        self.__re_wr_progress: ReWrProgress = ReWrProgress(ctx)
        self.__loop_pool: Optional[PoolLoopCont] = None
        self.__locks: _Locks = _Locks(
            as_lock=None,
            gl_lock=ctx.Condition()
        )
        self.__writer_active: bool = True
        for cont_type in self.__re_wr_obj.get_connection_write():
            if cont_type in (ContainerInterface, NoConnectionContainer):
                self.__writer_active = False

    # WorkInterface and ReWrProgress static. Managed by WorkableManager.
    @property
    def _loop_pool(self) -> PoolLoopCont:
        if self.__loop_pool is None:
            raise WorkableError("Loop-login wasn't used or this workable was shutdown!")
        return self.__loop_pool

    @property
    def _lock_async(self) -> _AsLock:
        if self.__locks.as_lock is None:
            raise WorkableError("Loop-login wasn't used or this workable was shutdown!")
        return self.__locks.as_lock

    def login_loop_th_pool(self, loop: asyncio.AbstractEventLoop, /) -> None:

        async def _create_lock() -> _AsLock:
            return _AsLock(
                writer_async=asyncio.Lock(),
                worker_async=asyncio.Lock(),
                reader_async=asyncio.Lock()
            )

        if self.__loop_pool is not None:
            raise WorkableError("Loop-login can't be used twice!")
        self.__loop_pool = PoolLoopCont(
            th_exec=ThreadPoolExecutor(
                max_workers=4
            ),
            loop=loop
        )

        self.__locks.as_lock = self.__loop_pool.loop.run_until_complete(_create_lock())

    def workable_re_wr_wo_connections(self) -> WorkerContainerTypes:
        return WorkerContainerTypes(
            reader_cont=self.__re_wr_obj.get_connection_read(),
            writer_cont=self.__re_wr_obj.get_connection_write(),
            worker_cont=WorkerTypeParam(
                cont_in=self.__work_obj.get_connection_in(),
                cont_out=self.__work_obj.get_connection_out()
            )
        )

    def workable_check_block(self) -> bool:
        if self.__re_wr_progress.end_type.error == 1:
            raise WorkableError("Workable error was set!")

        if self.__re_wr_obj.get_blockable():
            with self.__locks.gl_lock:
                self.__locks.gl_lock.wait(600)

            return self.__re_wr_progress.end_type.term != 0

        return False

    def workable_on_close(self) -> None:
        self.__work_obj.on_close(self.__sync_out)

    def workable_add_provider(self) -> None:
        self.__re_wr_progress.add_provider()
        with self.__locks.gl_lock:
            self.__locks.gl_lock.notify_all()

    def workable_remove_provider(self) -> None:
        if self.__re_wr_progress.remove_provider():
            self.__re_wr_obj.wr_on_close()
            with self.__locks.gl_lock:
                self.__locks.gl_lock.notify_all()

    def workable_set_error(self) -> None:
        self.__re_wr_progress.set_error()
        self.__re_wr_obj.on_error()
        with self.__locks.gl_lock:
            self.__locks.gl_lock.notify_all()
        if self.__loop_pool is not None:
            self.workable_shutdown()

    def terminated_set_error(self) -> None:
        self.__re_wr_obj.on_error()

    def workable_shutdown(self) -> None:
        pol = self._loop_pool
        pol.th_exec.shutdown(True)
        self.__loop_pool = None
        self.__locks.as_lock = None

    # For coroutines etc. WorkInterface and ReWrProgress custom

    async def workable_running(self) -> bool:
        pol = self._loop_pool
        if pol.loop != asyncio.get_running_loop():
            raise WorkableError("Not the same event-loop!")
        if self.__re_wr_progress.end_type.error == 1 or self.__sync_out.error_occurred():
            raise WorkableError("Workable error was set!")
        async with self._lock_async.reader_async:
            return await self.__re_wr_obj.running(
                pol, self.__re_wr_progress.end_type.term
            )

    async def workable_read(self, container_types: ContainerTypes, /) -> DataContainer:
        pol = self._loop_pool
        if pol.loop != asyncio.get_running_loop():
            raise WorkableError("Not the same event-loop!")
        if self.__re_wr_progress.end_type.error == 1 or self.__sync_out.error_occurred():
            raise WorkableError("Workable error was set!")
        if self.__writer_active and self.__re_wr_progress.end_type.term == -1:
            self.__sync_out.print_message_simple("Waiting for providers!")
            empty_erg: DataContainer = tuple(tuple() for _ in container_types)
            with self.__locks.gl_lock:
                self.__locks.gl_lock.wait(20)
            return empty_erg
        async with self._lock_async.reader_async:
            return await self.__re_wr_obj.read(
                container_types, pol
            )

    async def workable_write(self, data_container: DataContainer,
                             container_types: ContainerTypes, /) -> bool:
        pol = self._loop_pool
        if pol.loop != asyncio.get_running_loop():
            raise WorkableError("Not the same event-loop!")
        if self.__re_wr_progress.end_type.error == 1 or self.__sync_out.error_occurred():
            raise WorkableError("Workable error was set!")
        async with self._lock_async.writer_async:
            return await self.__re_wr_obj.write(
                data_container, container_types, pol
            )

    async def workable_work(self, data_container: DataContainer,
                            container_types: WorkerTypeParam, /) -> AsyncIterable[DataContainer]:
        pol = self._loop_pool
        if pol.loop != asyncio.get_running_loop():
            raise WorkableError("Not the same event-loop!")
        async with self._lock_async.worker_async:
            async for subtotals in self.__work_obj.work(
                    self.__sync_out, data_container, container_types, pol
            ):
                if self.__re_wr_progress.end_type.error == 1 or self.__sync_out.error_occurred():
                    raise WorkableError("Workable error was set!")
                yield subtotals


@final
@dataclass
class WorkerInOut:
    workable_in: List[Workable]
    workable_out: List[Workable]
