# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
import abc
from typing import TypeVar, Generic, Type, Final

_PT: Final = TypeVar('_PT')


class ContainerInterface(Generic[_PT], abc.ABC):
    @abc.abstractmethod
    def get_data(self) -> _PT:
        raise NotImplementedError("Interface!")

    @abc.abstractmethod
    def set_data(self, value: _PT, /) -> None:
        raise NotImplementedError("Interface!")

    @abc.abstractmethod
    def serialize(self) -> bytes:
        raise NotImplementedError("Interface!")

    @classmethod
    @abc.abstractmethod
    def deserialize(cls: Type['ContainerInterface'], data: bytes, /) -> 'ContainerInterface':
        raise NotImplementedError("Interface!")
