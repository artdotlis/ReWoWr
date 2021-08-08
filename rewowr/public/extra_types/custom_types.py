# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
import multiprocessing
from multiprocessing.managers import SyncManager

from typing import TypeVar, Generic, Dict, Type, Callable, Optional, final, Final, Protocol

from rewowr.public.errors.custom_errors import CustomProcessValueWrapperError

_KeyT: Final = TypeVar('_KeyT')
_ValueT: Final = TypeVar('_ValueT')


@final
class CustomManagedDictWrapper(Generic[_KeyT, _ValueT]):

    def __init__(self, ctx: multiprocessing.context.SpawnContext,
                 manager: Optional[SyncManager] = None, /) -> None:
        super().__init__()
        manager_local = ctx.Manager() if manager is None else manager
        self.__managed_dict: Dict[_KeyT, _ValueT] = manager_local.dict({})
        self.__manager = manager is None

    @property
    def managed_dict(self) -> Dict[_KeyT, _ValueT]:
        return self.__managed_dict

    @property
    def manager(self) -> bool:
        return self.__manager


_PValT: Final = TypeVar('_PValT', int, float)


# noinspection PyPropertyDefinition
class _SyncCValue(Protocol[_PValT]):
    @property
    def value(self) -> _PValT:
        ...

    @value.setter
    def value(self, value: _PValT) -> None:
        ...


def _create_int_value(ctx: multiprocessing.context.SpawnContext,
                      value: float, /) -> _SyncCValue:
    return ctx.Value('i', int(value))


def _create_float_value(ctx: multiprocessing.context.SpawnContext,
                        value: float, /) -> _SyncCValue:
    return ctx.Value('f', value)


def _error(_ctx: multiprocessing.context.SpawnContext, _num: float, /) -> _SyncCValue:
    raise CustomProcessValueWrapperError("Type is not supported!")


@final
class CustomProcessValueWrapper(Generic[_PValT]):
    _switch: Final[Dict[
        Type, Callable[[multiprocessing.context.SpawnContext, float], _SyncCValue]
    ]] = {float: _create_float_value, int: _create_int_value}

    def __init__(self, ctx: multiprocessing.context.SpawnContext, value: _PValT, /) -> None:
        super().__init__()
        self.__value: _SyncCValue = self._switch.get(
            type(value), _error
        )(ctx, value)

    @property
    def value_cont(self) -> _SyncCValue:
        return self.__value

    @property
    def value(self) -> _PValT:
        return self.__value.value

    @value.setter
    def value(self, value: _PValT, /) -> None:
        self.__value.value = value
