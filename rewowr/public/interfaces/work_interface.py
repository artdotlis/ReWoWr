# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
from typing import AsyncIterable

import abc

from rewowr.public.constants.rewowr_worker_constants import ContainerTypes, DataContainer, \
    WorkerTypeParam, PoolLoopCont
from rewowr.simple_logger.synchronised_standard_output import SyncStdout


class WorkInterface(abc.ABC):
    # Can block event queue

    @abc.abstractmethod
    def get_connection_in(self) -> ContainerTypes:
        raise NotImplementedError("Interface!")

    @abc.abstractmethod
    def get_connection_out(self) -> ContainerTypes:
        raise NotImplementedError("Interface!")

    @abc.abstractmethod
    def on_close(self, sync_out: SyncStdout, /) -> None:
        raise NotImplementedError("Interface!")

    # Should not block event queue

    @abc.abstractmethod
    async def work(self, sync_out: SyncStdout, data_container: DataContainer,
                   container_types: WorkerTypeParam,
                   pool_loop: PoolLoopCont, /) -> AsyncIterable[DataContainer]:
        yield tuple(tuple() for _ in container_types.cont_out)
        raise NotImplementedError("Interface!")
