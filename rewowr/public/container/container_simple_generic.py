# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
from typing import TypeVar, Optional, Type, final, Final
import pickle as rick

from rewowr.public.errors.custom_errors import SimpleGenericContainerError
from rewowr.public.interfaces.container_interface import ContainerInterface

_CusType: Final = TypeVar('_CusType')


class SimpleGenericContainer(ContainerInterface[_CusType]):

    def __init__(self) -> None:
        super().__init__()
        self.__place_holder: Optional[_CusType] = None

    @final
    def get_data(self) -> _CusType:
        if self.__place_holder is None:
            raise SimpleGenericContainerError('JsonDictCon is empty!')
        return self.__place_holder

    @final
    def set_data(self, value: _CusType, /) -> None:
        self.__place_holder = value

    @final
    def serialize(self) -> bytes:
        return rick.dumps(self.get_data(), protocol=rick.HIGHEST_PROTOCOL)

    @classmethod
    @final
    def deserialize(cls: Type[ContainerInterface[_CusType]],
                    data: bytes, /) -> ContainerInterface[_CusType]:
        puf: ContainerInterface[_CusType] = cls()
        puf.set_data(rick.loads(data))
        return puf
