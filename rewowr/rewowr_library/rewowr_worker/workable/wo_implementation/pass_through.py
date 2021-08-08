# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
from typing import AsyncIterable, final

from rewowr.public.constants.rewowr_worker_constants import WorkerTypeParam, PoolLoopCont, \
    ContainerTypes, DataContainer
from rewowr.public.interfaces.work_interface import WorkInterface
from rewowr.simple_logger.synchronised_standard_output import SyncStdout


@final
class PassThrough(WorkInterface):
    def __init__(self, container_proto: ContainerTypes) -> None:
        super().__init__()
        self.__container_proto: ContainerTypes = container_proto

    # Can block event queue

    def get_connection_in(self) -> ContainerTypes:
        return self.__container_proto

    def get_connection_out(self) -> ContainerTypes:
        return self.__container_proto

    def on_close(self, sync_out: SyncStdout, /) -> None:
        pass

    # Should not block event queue

    async def work(self, sync_out: SyncStdout, data_container: DataContainer,
                   container_types: WorkerTypeParam,
                   pool_loop: PoolLoopCont, /) -> AsyncIterable[DataContainer]:
        yield data_container
