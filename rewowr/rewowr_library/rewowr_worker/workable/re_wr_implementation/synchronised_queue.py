# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
import multiprocessing
from multiprocessing import synchronize, connection
from typing import List, Tuple, Dict, Callable, TypeVar, final, Final
from dataclasses import dataclass

from rewowr.public.functions.decorator_functions import remove_all_args
from rewowr.public.interfaces.re_wr_interface import ReWrInterface
from rewowr.public.extra_types.custom_types import CustomProcessValueWrapper
from rewowr.public.constants.rewowr_worker_constants import PoolLoopCont, ContainerTypes, \
    DataContainer


@final
@dataclass
class _Locks:
    writer: List[synchronize.Lock]
    reader: List[synchronize.Lock]


@final
@dataclass
class _Heads:
    writer: CustomProcessValueWrapper[int]
    reader: CustomProcessValueWrapper[int]


@final
@dataclass
class _BufferStructure:
    locks: _Locks
    heads: _Heads
    pipes: List[Tuple[connection.Connection, connection.Connection]]


def _thread_send(data_container: DataContainer, container_types: ContainerTypes,
                 buffer_structure: Dict[str, _BufferStructure], max_puf: int,
                 global_lock: synchronize.RLock, /) -> Callable[[], bool]:
    def thread_send_inner() -> bool:
        head_pos: List[int] = [-1 for _ in container_types]
        conveyable = True
        with global_lock:
            for cont_index, cont_type in enumerate(container_types):
                cont_str = cont_type.__name__
                if (buffer_structure[cont_str].heads.reader.value
                        != (buffer_structure[cont_str].heads.writer.value + 1) % max_puf):
                    head_pos[cont_index] = buffer_structure[cont_str].heads.writer.value
                else:
                    conveyable = False

            if conveyable:
                for cont_type in container_types:
                    cont_str = cont_type.__name__
                    buffer_structure[cont_str].heads.writer.value = \
                        (buffer_structure[cont_str].heads.writer.value + 1) % max_puf
        if conveyable:
            for head_index, cont_type in enumerate(container_types):
                cont_type_name = cont_type.__name__
                with buffer_structure[cont_type_name].locks.writer[head_pos[head_index]]:
                    buffer_structure[cont_type_name].pipes[head_pos[head_index]][1].send(
                        [ser_val.serialize() for ser_val in data_container[head_index]]
                    )
            return False

        return True

    return thread_send_inner


def _thread_recv(container_types: ContainerTypes, buffer_structure: Dict[str, _BufferStructure],
                 max_puf: int, global_lock: synchronize.RLock, /) \
        -> Callable[[], List[List[bytes]]]:
    def thread_recv_inner() -> List[List[bytes]]:
        value_bytes: List[List[bytes]] = [[] for _ in container_types]
        head_pos: List[int] = [-1 for _ in container_types]
        receivable = True
        with global_lock:
            for cont_index, cont_type in enumerate(container_types):
                cont_str = cont_type.__name__
                if (
                        buffer_structure[cont_str].heads.reader.value
                        != buffer_structure[cont_str].heads.writer.value
                ):
                    head_pos[cont_index] = buffer_structure[cont_str].heads.reader.value
                else:
                    receivable = False

            if receivable:
                for cont_type in container_types:
                    cont_str = cont_type.__name__
                    buffer_structure[cont_str].heads.reader.value = \
                        (buffer_structure[cont_str].heads.reader.value + 1) % max_puf

        if receivable:
            for head_index, cont_type in enumerate(container_types):
                cont_type_name = cont_type.__name__
                with buffer_structure[cont_type_name].locks.reader[head_pos[head_index]]:
                    buffer_val: List[bytes] = \
                        buffer_structure[cont_type_name].pipes[head_pos[head_index]][0].recv()
                    value_bytes[head_index] = buffer_val

        return value_bytes

    return thread_recv_inner


_InnerType: Final = TypeVar('_InnerType')


def _check_run(lock_global: synchronize.RLock, buffer_structure: Dict[str, _BufferStructure],
               container_proto: ContainerTypes, /) -> Callable[[], bool]:
    def check_run_inner() -> bool:
        run = True
        with lock_global:
            for cont_type in container_proto:
                cont_str = cont_type.__name__
                buffer_structure_el = buffer_structure[cont_str]
                if buffer_structure_el.heads.reader.value == buffer_structure_el.heads.writer.value:
                    run = False
        return run

    return check_run_inner


@final
class SyncQueue(ReWrInterface):

    def __init__(self, ctx: multiprocessing.context.SpawnContext,
                 container_proto: ContainerTypes, puffer_size: int, /) -> None:
        super().__init__()
        self.__container_proto: ContainerTypes = container_proto
        self.__lock_global: synchronize.RLock = ctx.RLock()
        self.__max: int = puffer_size
        self.__buffer_structure: Dict[str, _BufferStructure] = {}

        def create_structure() -> _BufferStructure:
            return _BufferStructure(
                locks=_Locks(
                    writer=[ctx.Lock() for _ in range(self.__max)],
                    reader=[ctx.Lock() for _ in range(self.__max)]
                ),
                heads=_Heads(
                    reader=CustomProcessValueWrapper[int](ctx, 0),
                    writer=CustomProcessValueWrapper[int](ctx, 0)
                ),
                pipes=[ctx.Pipe(False) for _ in range(self.__max)]
            )

        for cont_type in container_proto:
            self.__buffer_structure[cont_type.__name__] = create_structure()

    def get_blockable(self) -> bool:
        return False

    def get_connection_read(self) -> ContainerTypes:
        return self.__container_proto

    def get_connection_write(self) -> ContainerTypes:
        return self.__container_proto

    def wr_on_close(self) -> None:
        pass

    def on_error(self) -> None:
        pass

    # For coroutines etc.!
    async def read(self, container_types: ContainerTypes,
                   pool_loop: PoolLoopCont, /) -> DataContainer:
        values_bytes = await pool_loop.loop.run_in_executor(
            pool_loop.th_exec, remove_all_args(_thread_recv(
                container_types, self.__buffer_structure, self.__max, self.__lock_global
            ))
        )
        value = tuple(
            tuple(
                cont_type.deserialize(elem_byte)
                for elem_byte in values_bytes[head_index]
            )
            for head_index, cont_type in enumerate(container_types)
        )

        return value

    async def write(self, data_container: DataContainer, container_types: ContainerTypes,
                    pool_loop: PoolLoopCont, /) -> bool:
        erg_write = await pool_loop.loop.run_in_executor(
            pool_loop.th_exec, remove_all_args(_thread_send(
                data_container, container_types, self.__buffer_structure,
                self.__max, self.__lock_global
            ))
        )
        return erg_write

    async def running(self, pool_loop: PoolLoopCont, provider_cnt: int, /) -> bool:
        running: bool = await pool_loop.loop.run_in_executor(
            pool_loop.th_exec, remove_all_args(_check_run(
                self.__lock_global, self.__buffer_structure, self.__container_proto
            ))
        )
        return running or provider_cnt != 0
