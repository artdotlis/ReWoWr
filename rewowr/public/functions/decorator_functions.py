# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
import sys
import traceback
from typing import TypeVar, Callable, Final

from rewowr.public.errors.custom_errors import KnownError
from rewowr.public.functions.error_handling import SysHandlerCon, RedirectSysHandler
from rewowr.public.functions.syncout_dep_functions import RedirectWriteToLogger, \
    RedirectErrorToLogger, logger_send_error
from rewowr.public.interfaces.logger_interface import SyncStdoutInterface

_FunType: Final = TypeVar('_FunType')
_FunTypeAny1: Final = TypeVar('_FunTypeAny1')
_FunTypeAny2: Final = TypeVar('_FunTypeAny2')


def remove_all_args(fun: Callable[[], _FunType], /) -> Callable[..., _FunType]:
    def inner_fun(*args: _FunTypeAny1, **kwargs: _FunTypeAny2) -> _FunType:
        _ = args, kwargs
        return fun()

    return inner_fun


_FunTypeTuple: Final = TypeVar('_FunTypeTuple', bound=tuple)
ProcessWrapperFun: Final = Callable[
    [SyncStdoutInterface, str, Callable[..., None], _FunTypeTuple], None
]


def rewowr_process_wrapper(sync_out: SyncStdoutInterface, pr_name: str,
                           callable_fun: Callable[..., None],
                           fun_args: _FunTypeTuple, /) -> None:
    sys_handlers = RedirectSysHandler(SysHandlerCon(
        sys_handler=RedirectWriteToLogger(sync_out),
        sys_error_h=RedirectErrorToLogger(sync_out),
        stdout_buffer=sys.stdout,
        stderr_buffer=sys.stderr
    ))
    sys_handlers.set_sys_handler()
    try:
        callable_fun(*fun_args)
    except KnownError as known_error:
        logger_send_error(sync_out, 'Expected', known_error, pr_name, traceback.format_exc())
        sys_handlers.on_known_errors(str(known_error))
    except Exception as error:
        logger_send_error(sync_out, 'Not expected', error, pr_name, traceback.format_exc())
        sys_handlers.on_exception(str(error))
        raise error
    finally:
        sys_handlers.close()
