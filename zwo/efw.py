#! /usr/bin/env python3

"""Реализация класса клиента для управления колесом фильтров."""

from __future__ import annotations

import os
from ctypes import (CDLL, CFUNCTYPE, POINTER, RTLD_GLOBAL, Structure, byref,
                    c_bool, c_char, c_char_p, c_int, c_ubyte, c_void_p, cdll)
from enum import IntEnum, auto
from functools import partial
from platform import architecture
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from _ctypes import _CData, _PyCFuncPtrType


def _load_lib(arch: str, name: str) -> CDLL:
    if os.name == "posix":
        CDLL("libudev.so", mode=RTLD_GLOBAL)
    return cdll.LoadLibrary(os.path.join(os.path.dirname(__file__), "libs", "efw", arch, name))


arch = {"posix": {"32bit": ("linux32", "libEFWFilter.so"),
                  "64bit": ("linux64", "libEFWFilter.so")},
        "nt":    {"32bit": ("win32", "EFW_filter.dll"),
                  "64bit": ("win64", "EFW_filter.dll")},
       }[os.name][architecture()[0]]
_lib = _load_lib(*arch)


class ZwoFilterWheelError(Exception):
    pass


EFW_ID_MAX = 128


class EFW_INFO(Structure):
    """Filter wheel information."""

    _fields_ = [
        ("ID", c_int),
        ("Name", c_char * 64),
        ("slotNum", c_int),
    ]


class EFW_ID(Structure):
    """Filter wheel ID."""

    _fields_ = [
        ("id", c_ubyte * 8),
    ]


class EFW_ERROR_CODE(IntEnum):
    """Returned error code."""

    EFW_SUCCESS = 0
    EFW_ERROR_INVALID_INDEX = auto()
    EFW_ERROR_INVALID_ID = auto()
    EFW_ERROR_INVALID_VALUE = auto()
    EFW_ERROR_REMOVED = auto()
    EFW_ERROR_MOVING = auto()
    EFW_ERROR_ERROR_STATE = auto()
    EFW_ERROR_GENERAL_ERROR = auto()
    EFW_ERROR_NOT_SUPPORTED = auto()
    EFW_ERROR_CLOSED = auto()
    EFW_ERROR_END = -1


class ZwoEfwDevice(c_void_p):
    """Основной интерфейс для работы с колесом фильтров."""

    _functions_ = {
        "EFWGetNum": CFUNCTYPE(c_int),
        "EFWGetProductIDs": CFUNCTYPE(c_int, POINTER(c_int * EFW_ID_MAX)),
        "EFWGetID": CFUNCTYPE(c_int, c_int, POINTER(c_int)),
        "EFWOpen": CFUNCTYPE(c_int, c_int),
        "EFWClose": CFUNCTYPE(c_int, c_int),
        "EFWGetProperty": CFUNCTYPE(c_int, c_int, POINTER(EFW_INFO)),
        "EFWGetPosition": CFUNCTYPE(c_int, c_int, POINTER(c_int)),
        "EFWSetPosition": CFUNCTYPE(c_int, c_int, c_int),
        "EFWSetDirection": CFUNCTYPE(c_int, c_int, c_bool),
        "EFWGetDirection": CFUNCTYPE(c_int, c_int, POINTER(c_bool)),
        "EFWCalibrate": CFUNCTYPE(c_int, c_int),
        "EFWGetSDKVersion": CFUNCTYPE(c_char_p),
        "EFWGetHWErrorCode": CFUNCTYPE(c_int, c_int, POINTER(c_int)),
        "EFWGetFirmwareVersion": CFUNCTYPE(c_int, c_int, POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_ubyte)),
        "EFWGetSerialNumber": CFUNCTYPE(c_int, c_int, POINTER(EFW_ID)),
        "EFWSetID": CFUNCTYPE(c_int, c_int, EFW_ID),
    }

    def __call__(self, prototype: _PyCFuncPtrType, *arguments: tuple[_CData, ...]) -> int:
        result = prototype((self.name, _lib))(*arguments)

        special_names = {"EFWGetNum", "EFWGetProductIDs", "EFWGetSDKVersion"}
        if result and self.name not in special_names:
            msg = f"{self.name} error {result} ({EFW_ERROR_CODE(result).name})"
            raise ZwoFilterWheelError(msg)

        return result

    def __getattr__(self, name: str) -> Callable[..., int]:    # type: ignore
        self.name = name
        return partial(self.__call__, self._functions_[name])


class FilterWheel:
    """Класс клиента для работы с колесом фильтров ZWO."""

    def __init__(self) -> None:
        """Инициализация класса клиента с указанными параметрами."""

        self._efw = ZwoEfwDevice()

    def EFWGetNum(self) -> int:
        """Get number of connected EFW filter wheel, call this API to refresh
        device list if EFW is connected or disconnected.
        """

        return self._efw.EFWGetNum()

    def EFWGetProductIDs(self) -> tuple[int, ...]:
        """Get the product ID of each wheel, at first set pPIDs as 0 and get
        length and then malloc a buffer to load the PIDs.
        """

        pid_array = (c_int * EFW_ID_MAX)(0)

        pid_array_len = self._efw.EFWGetProductIDs(byref(pid_array))
        return tuple(pid_array[:pid_array_len])

    def EFWGetID(self, index: int) -> int:
        """Get ID of filter wheel."""

        ids = c_int()

        self._efw.EFWGetID(c_int(index), byref(ids))
        return ids.value

    def EFWOpen(self, ids: int) -> bool:
        """Open filter wheel."""

        self._efw.EFWOpen(c_int(ids))
        return True

    def EFWClose(self, ids: int) -> bool:
        """Close filter wheel."""

        self._efw.EFWClose(c_int(ids))
        return True

    def EFWGetProperty(self, ids: int) -> EFW_INFO:
        """Get property of filter wheel. SlotNum is 0 if not opened."""

        info = EFW_INFO()

        self._efw.EFWGetProperty(c_int(ids), byref(info))
        return info

    def EFWGetPosition(self, ids: int) -> int:
        """Get position of slot."""

        position = c_int()

        self._efw.EFWGetPosition(c_int(ids), byref(position))
        return position.value

    def EFWSetPosition(self, ids: int, position: int) -> bool:
        """Set position of slot."""

        self._efw.EFWSetPosition(c_int(ids), c_int(position))
        return True

    def EFWSetDirection(self, ids: int, direction: bool) -> bool:
        """Set unidirection of filter wheel. If set as true, the filter wheel
        will rotate along one direction.
        """

        self._efw.EFWSetDirection(c_int(ids), c_bool(direction))
        return True

    def EFWGetDirection(self, ids: int) -> bool:
        """Get unidirection of filter wheel."""

        direction = c_bool()

        self._efw.EFWGetDirection(c_int(ids), byref(direction))
        return direction.value

    def EFWCalibrate(self, ids: int) -> bool:
        """Calibrate filter wheel."""

        self._efw.EFWCalibrate(c_int(ids))
        return True

    def EFWGetSDKVersion(self) -> bytes:
        """Get version string."""

        return bytes(self._efw.EFWGetSDKVersion())

    def EFWGetHWErrorCode(self, ids: int) -> int:
        """Get hardware error code of filter wheel."""

        errcode = c_int()

        self._efw.EFWGetHWErrorCode(c_int(ids), byref(errcode))
        return errcode.value

    def EFWGetFirmwareVersion(self, ids: int) -> tuple[int, ...]:
        """Get firmware version of filter wheel."""

        major = c_ubyte()
        minor = c_ubyte()
        build = c_ubyte()

        self._efw.EFWGetFirmwareVersion(c_int(ids), byref(major), byref(minor), byref(build))
        return (major.value, minor.value, build.value)

    def EFWGetSerialNumber(self, ids: int) -> EFW_ID:
        """Get the serial number from a EFW."""

        serial = EFW_ID()

        self._efw.EFWGetSerialNumber(c_int(ids), byref(serial))
        return serial

    def EFWSetID(self, ids: int, efw_id: EFW_ID) -> bool:
        """Set the alias to a EFW."""

        self._efw.EFWSetID(c_int(ids), efw_id)
        return True


__all__ = ["FilterWheel"]
