# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
from typing import AsyncIterable, Tuple, Type, final

from rewowr.simple_logger.synchronised_standard_output import SyncStdout
from rewowr.public.interfaces.work_interface import WorkInterface
from rewowr.public.container.container_no_connection import NoConnectionContainer
from rewowr.public.constants.rewowr_worker_constants import WorkerTypeParam, PoolLoopCont, \
    DataContainer


@final
class EndWork(WorkInterface):
    # Can block event queue

    def get_connection_in(self) -> Tuple[Type[NoConnectionContainer]]:
        val = (NoConnectionContainer,)
        return val

    def get_connection_out(self) -> Tuple[Type[NoConnectionContainer]]:
        val = (NoConnectionContainer,)
        return val

    def on_close(self, sync_out: SyncStdout, /) -> None:
        raise NotImplementedError(f"{EndWork.__name__} should never be closed or called!")

    # Should not block event queue

    async def work(self, sync_out: SyncStdout, data_container: DataContainer,
                   container_types: WorkerTypeParam,
                   pool_loop: PoolLoopCont, /) -> AsyncIterable[DataContainer]:
        yield tuple(tuple() for _ in container_types.cont_out)
        raise NotImplementedError(f"{EndWork.__name__} should never be closed or called!")
