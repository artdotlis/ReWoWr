# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""

from typing import Type, final

from rewowr.public.interfaces.container_interface import ContainerInterface


@final
class NoConnectionContainer(ContainerInterface[None]):

    def __init__(self) -> None:
        raise NotImplementedError("NoConnectionContainer should never be used!")

    def get_data(self) -> None:
        raise NotImplementedError("NoConnectionContainer should never be used!")

    def set_data(self, value: None, /) -> None:
        raise NotImplementedError("NoConnectionContainer should never be used!")

    def serialize(self) -> bytes:
        raise NotImplementedError("NoConnectionContainer should never be used!")

    @classmethod
    def deserialize(cls: Type['NoConnectionContainer'], data: bytes, /) -> 'NoConnectionContainer':
        raise NotImplementedError("NoConnectionContainer should never be used!")
