# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
from typing import Type, final
import pickle as rick

from rewowr.public.interfaces.container_interface import ContainerInterface


@final
class EmptyContainer(ContainerInterface[None]):
    def __init__(self) -> None:
        super().__init__()
        self.__place_holder: None = None

    def get_data(self) -> None:
        return self.__place_holder

    def set_data(self, value: None, /) -> None:
        self.__place_holder = value

    def serialize(self) -> bytes:
        return rick.dumps("", protocol=rick.HIGHEST_PROTOCOL)

    @classmethod
    def deserialize(cls: Type[ContainerInterface[None]],
                    data: bytes, /) -> ContainerInterface[None]:
        puf: ContainerInterface[None] = cls()
        return puf
