# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
from typing import Tuple, Type, final

from rewowr.public.container.container_no_connection import NoConnectionContainer
from rewowr.public.interfaces.re_wr_interface import ReWrInterface
from rewowr.public.constants.rewowr_worker_constants import PoolLoopCont, DataContainer, \
    ContainerTypes


@final
class NoOutputSink(ReWrInterface):

    def __init__(self, container_proto: ContainerTypes, /) -> None:
        super().__init__()
        self.__container_proto: ContainerTypes = container_proto

    def get_connection_read(self) -> Tuple[Type[NoConnectionContainer]]:
        val = (NoConnectionContainer,)
        return val

    def get_connection_write(self) -> ContainerTypes:
        return self.__container_proto

    def get_blockable(self) -> bool:
        return False

    def wr_on_close(self) -> None:
        pass

    def on_error(self) -> None:
        pass

    async def read(self, container_types: ContainerTypes,
                   pool_loop: PoolLoopCont, /) -> DataContainer:
        raise NotImplementedError("Not implemented")

    async def write(self, data_container: DataContainer, container_types: ContainerTypes,
                    pool_loop: PoolLoopCont, /) -> bool:
        return False

    async def running(self, pool_loop: PoolLoopCont, provider_cnt: int, /) -> bool:
        raise NotImplementedError("Not implemented")
