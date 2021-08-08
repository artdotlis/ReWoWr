# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
import abc

from rewowr.public.constants.rewowr_worker_constants import ContainerTypes, PoolLoopCont, \
    DataContainer


class ReWrInterface(abc.ABC):

    # Can block event queue

    @abc.abstractmethod
    def get_connection_read(self) -> ContainerTypes:
        raise NotImplementedError("Interface!")

    @abc.abstractmethod
    def get_connection_write(self) -> ContainerTypes:
        raise NotImplementedError("Interface!")

    @abc.abstractmethod
    def get_blockable(self) -> bool:
        raise NotImplementedError("Interface!")

    @abc.abstractmethod
    def wr_on_close(self) -> None:
        raise NotImplementedError("Interface!")

    @abc.abstractmethod
    def on_error(self) -> None:
        raise NotImplementedError("Interface!")

    # Should not block event queue

    @abc.abstractmethod
    async def read(self, container_types: ContainerTypes, pool_loop: PoolLoopCont, /) \
            -> DataContainer:
        raise NotImplementedError("Interface!")

    @abc.abstractmethod
    async def write(self, data_container: DataContainer,
                    container_types: ContainerTypes, pool_loop: PoolLoopCont, /) -> bool:
        raise NotImplementedError("Interface!")

    @abc.abstractmethod
    async def running(self, pool_loop: PoolLoopCont, provider_cnt: int, /) -> bool:
        raise NotImplementedError("Interface!")
