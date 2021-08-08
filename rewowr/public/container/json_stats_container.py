# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
import abc
from copy import deepcopy
from typing import Dict, TypeVar, List, final

from rewowr.public.errors.custom_errors import StatsContainerError


class JsonStatsContainer(abc.ABC):

    def __init__(self) -> None:
        super().__init__()
        self.__stats_container: Dict = {}

    @final
    @property
    def stats_container(self) -> Dict:
        return self.__stats_container

    @abc.abstractmethod
    def _validate_stats(self, stats: Dict, /) -> None:
        raise NotImplementedError("Abstract method!")

    @final
    def __merge_rec(self, stats_to_merge: Dict, cont_destiny: Dict, /) -> None:
        for n_keys, n_value in stats_to_merge.items():
            if n_keys not in cont_destiny:
                cont_destiny[n_keys] = deepcopy(n_value)
            elif isinstance(cont_destiny[n_keys], (list, int)) and \
                    isinstance(n_value, type(cont_destiny[n_keys])):
                cont_destiny[n_keys] += deepcopy(n_value)
            elif isinstance(n_value, dict) \
                    and isinstance(cont_destiny[n_keys], dict):
                self.__merge_rec(n_value, cont_destiny[n_keys])
            else:
                raise StatsContainerError(
                    'JsonStatsContainer and to be merged container have different structure!'
                )

    @final
    def merge_stats_dict(self, stats: Dict, /) -> None:
        self._validate_stats(stats)
        self.__merge_rec(stats, self.__stats_container)


_FloatInt = TypeVar('_FloatInt', int, float)


@final
class JsonStatsContainerIntFloatList(JsonStatsContainer):
    def _validate_stats(self, stats: Dict, /) -> None:
        def check_float_int(list_to_check: List[_FloatInt]) -> None:
            for list_elem in list_to_check:
                if not isinstance(list_elem, (int, float)):
                    raise StatsContainerError(
                        "JsonStatsContainer's array elements should be int or float type!"
                    )

        for keys, value in stats.items():
            if not isinstance(keys, str) or not keys:
                raise StatsContainerError(
                    "JsonStatsContainer's keys should always have the str type!"
                )
            if isinstance(value, dict):
                self._validate_stats(value)
            elif isinstance(value, list):
                check_float_int(value)
            elif not isinstance(value, int):
                raise StatsContainerError(
                    "JsonStatsContainer's last element should always have the int type!"
                )


@final
class JsonStatsContainerInt(JsonStatsContainer):
    def _validate_stats(self, stats: Dict, /) -> None:
        for keys, value in stats.items():
            if not isinstance(keys, str) or not keys:
                raise StatsContainerError(
                    "JsonStatsContainer's keys should always have the str type!"
                )
            if isinstance(value, dict):
                self._validate_stats(value)
            elif not isinstance(value, int):
                raise StatsContainerError(
                    "JsonStatsContainer's last element should always have the int type!"
                )
