#! /usr/bin/env python3

"""Реализация класса клиента для управления фокусером."""

from __future__ import annotations

import os
from ctypes import (CDLL, CFUNCTYPE, POINTER, RTLD_GLOBAL, Structure, byref,
                    c_bool, c_char, c_char_p, c_float, c_int, c_ubyte, c_void_p)
from enum import IntEnum, auto
from functools import partial
from platform import architecture
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from _ctypes import _CData, _PyCFuncPtrType


def _load_lib(arch: str, name: str) -> CDLL:
    if os.name == "posix":
        CDLL("libudev.so", mode=RTLD_GLOBAL)
    return CDLL(os.path.join(os.path.dirname(__file__), "libs", arch, name))


arch = {"posix": {"32bit": ("linux32", "libEAFFocuser.so"),
                  "64bit": ("linux64", "libEAFFocuser.so")},
        "nt":    {"32bit": ("win32", "EAF_focuser.dll"),
                  "64bit": ("win64", "EAF_focuser.dll")},
       }[os.name][architecture()[0]]
_lib = _load_lib(*arch)


class ZwoFocuserError(Exception):
    pass


EAF_ID_MAX = 128


class EAF_INFO(Structure):
    """Focuser information."""

    _fields_ = [
        ("ID", c_int),
        ("Name", c_char * 64),
        ("MaxStep", c_int),
    ]


class EAF_ID(Structure):
    """Focuser ID."""

    _fields_ = [
        ("id", c_ubyte * 8),
    ]


class EAF_ERROR_CODE(IntEnum):
    """Returned error code."""

    EAF_SUCCESS = 0
    EAF_ERROR_INVALID_INDEX = auto()
    EAF_ERROR_INVALID_ID = auto()
    EAF_ERROR_INVALID_VALUE = auto()
    EAF_ERROR_REMOVED = auto()
    EAF_ERROR_MOVING = auto()
    EAF_ERROR_ERROR_STATE = auto()
    EAF_ERROR_GENERAL_ERROR = auto()
    EAF_ERROR_NOT_SUPPORTED = auto()
    EAF_ERROR_CLOSED = auto()
    EAF_ERROR_END = -1


class ZwoEafDevice(c_void_p):
    """Основной интерфейс для работы с фокусером."""

    _functions_ = {
        "EAFGetNum": CFUNCTYPE(c_int),
        "EAFGetProductIDs": CFUNCTYPE(c_int, POINTER(c_int * EAF_ID_MAX)),
        "EAFCheck": CFUNCTYPE(c_int, c_int, c_int),
        "EAFGetID": CFUNCTYPE(c_int, c_int, POINTER(c_int)),
        "EAFOpen": CFUNCTYPE(c_int, c_int),
        "EAFGetProperty": CFUNCTYPE(c_int, c_int, POINTER(EAF_INFO)),
        "EAFMove": CFUNCTYPE(c_int, c_int, c_int),
        "EAFStop": CFUNCTYPE(c_int, c_int),
        "EAFIsMoving": CFUNCTYPE(c_int, c_int, POINTER(c_bool), POINTER(c_bool)),
        "EAFGetPosition": CFUNCTYPE(c_int, c_int, POINTER(c_int)),
        "EAFResetPostion": CFUNCTYPE(c_int, c_int, c_int),
        "EAFGetTemp": CFUNCTYPE(c_int, c_int, POINTER(c_float)),
        "EAFSetBeep": CFUNCTYPE(c_int, c_int, c_bool),
        "EAFGetBeep": CFUNCTYPE(c_int, c_int, POINTER(c_bool)),
        "EAFSetMaxStep": CFUNCTYPE(c_int, c_int, c_int),
        "EAFGetMaxStep": CFUNCTYPE(c_int, c_int, POINTER(c_int)),
        "EAFStepRange": CFUNCTYPE(c_int, c_int, POINTER(c_int)),
        "EAFSetReverse": CFUNCTYPE(c_int, c_int, c_bool),
        "EAFGetReverse": CFUNCTYPE(c_int, c_int, POINTER(c_bool)),
        "EAFSetBacklash": CFUNCTYPE(c_int, c_int, c_int),
        "EAFGetBacklash": CFUNCTYPE(c_int, c_int, POINTER(c_int)),
        "EAFClose": CFUNCTYPE(c_int, c_int),
        "EAFGetSDKVersion": CFUNCTYPE(c_char_p),
        "EAFGetFirmwareVersion": CFUNCTYPE(c_int, c_int, POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_ubyte)),
        "EAFGetSerialNumber": CFUNCTYPE(c_int, c_int, POINTER(EAF_ID)),
        "EAFSetID": CFUNCTYPE(c_int, c_int, EAF_ID),
    }

    def __call__(self, prototype: _PyCFuncPtrType, *arguments: tuple[_CData, ...]) -> int:
        result = prototype((self.name, _lib))(*arguments)

        special_names = {"EAFGetNum", "EAFGetProductIDs", "EAFGetSDKVersion", "EAFCheck"}
        if result and self.name not in special_names:
            msg = EAF_ERROR_CODE(result).name
            raise ZwoFocuserError(msg)

        return result

    def __getattr__(self, name: str) -> Callable[..., int]:    # type: ignore
        self.name = name
        return partial(self.__call__, self._functions_[name])


class Focuser:
    """Класс клиента для работы с фокусером ZWO."""

    def __init__(self) -> None:
        """Инициализация класса клиента с указанными параметрами."""

        self._eaf = ZwoEafDevice()

    def EAFGetNum(self) -> int:
        """Get number of connected EAF focuser, call this API to refresh device
        list if EAF is connected or disconnected.
        """

        return self._eaf.EAFGetNum()

    def EAFGetProductIDs(self) -> tuple[int, ...]:
        """Get the product ID of each focuser."""

        pid_array = (c_int * EAF_ID_MAX)(0)

        pid_array_len = self._eaf.EAFGetProductIDs(byref(pid_array))
        return tuple(pid_array[:pid_array_len])

    def EAFCheck(self, vid: int, pid: int) -> int:
        """Check if the device is EAF. If the device is EAF, return 1, otherwise
        return 0.
        """

        return self._eaf.EAFCheck(c_int(vid), c_int(pid))

    def EAFGetID(self, index: int) -> int:
        """Get ID of focuser."""

        ids = c_int()

        self._eaf.EAFGetID(c_int(index), byref(ids))
        return ids.value

    def EAFOpen(self, ids: int) -> bool:
        """Open focuser."""

        return not self._eaf.EAFOpen(c_int(ids))

    def EAFGetProperty(self, ids: int) -> EAF_INFO:
        """Get property of focuser."""

        info = EAF_INFO()

        self._eaf.EAFGetProperty(c_int(ids), byref(info))
        return info

    def EAFMove(self, ids: int, position: int) -> bool:
        """Move focuser to an absolute position."""

        return not self._eaf.EAFMove(c_int(ids), c_int(position))

    def EAFStop(self, ids: int) -> bool:
        """Stop moving."""

        return not self._eaf.EAFStop(c_int(ids))

    def EAFIsMoving(self, ids: int) -> dict[str, bool]:
        """Check if the focuser is moving."""

        moving = c_bool()
        hand_control = c_bool()

        self._eaf.EAFIsMoving(c_int(ids), byref(moving), byref(hand_control))
        return {"moving": moving.value,
                "hand_control": hand_control.value}

    def EAFGetPosition(self, ids: int) -> int:
        """Get current position."""

        position = c_int()

        self._eaf.EAFGetPosition(c_int(ids), byref(position))
        return position.value

    def EAFResetPostion(self, ids: int, position: int) -> bool:
        """Set as current position."""

        return not self._eaf.EAFResetPostion(c_int(ids), c_int(position))

    def EAFGetTemp(self, ids: int) -> float:
        """Get the value of the temperature detector, if it's moved by handle,
        the temperature value is unreasonable, the value is -273 and return error.
        """

        temperature = c_float()

        self._eaf.EAFGetTemp(c_int(ids), byref(temperature))
        return temperature.value

    def EAFSetBeep(self, ids: int, beep: bool) -> bool:
        """Turn on/off beep, if true the focuser will beep at the moment when it
        begins to move.
        """

        return not self._eaf.EAFSetBeep(c_int(ids), c_bool(beep))

    def EAFGetBeep(self, ids: int) -> bool:
        """Get if beep is turned on."""

        beep = c_bool()

        self._eaf.EAFGetBeep(c_int(ids), byref(beep))
        return beep.value

    def EAFSetMaxStep(self, ids: int, position: int) -> bool:
        """Set the maximum position."""

        return not self._eaf.EAFSetMaxStep(c_int(ids), c_int(position))

    def EAFGetMaxStep(self, ids: int) -> int:
        """Get the maximum position."""

        position = c_int()

        self._eaf.EAFGetMaxStep(c_int(ids), byref(position))
        return position.value

    def EAFStepRange(self, ids: int) -> int:
        """Get the position range."""

        interval = c_int()

        self._eaf.EAFStepRange(c_int(ids), byref(interval))
        return interval.value

    def EAFSetReverse(self, ids: int, direction: bool) -> bool:
        """Set moving direction of focuser."""

        return not self._eaf.EAFSetReverse(c_int(ids), c_bool(direction))

    def EAFGetReverse(self, ids: int) -> bool:
        """Get moving direction of focuser."""

        direction = c_bool()

        self._eaf.EAFGetReverse(c_int(ids), byref(direction))
        return direction.value

    def EAFSetBacklash(self, ids: int, backlash: int) -> bool:
        """Set backlash of focuser."""

        return not self._eaf.EAFSetBacklash(c_int(ids), c_int(backlash))

    def EAFGetBacklash(self, ids: int) -> int:
        """Get backlash of focuser."""

        backlash = c_int()

        self._eaf.EAFGetBacklash(c_int(ids), byref(backlash))
        return backlash.value

    def EAFClose(self, ids: int) -> bool:
        """Close focuser."""

        return not self._eaf.EAFClose(c_int(ids))

    def EAFGetSDKVersion(self) -> str:
        """Get version string."""

        return bytes(self._eaf.EAFGetSDKVersion()).decode("ascii")

    def EAFGetFirmwareVersion(self, ids: int) -> str:
        """Get firmware version of focuser."""

        major = c_ubyte()
        minor = c_ubyte()
        build = c_ubyte()

        self._eaf.EAFGetFirmwareVersion(c_int(ids), byref(major), byref(minor), byref(build))
        return f"{major.value}.{minor.value}.{build.value}"

    def EAFGetSerialNumber(self, ids: int) -> int:
        """Get the serial number from a EAF."""

        serial = EAF_ID()

        self._eaf.EAFGetSerialNumber(c_int(ids), byref(serial))
        return int.from_bytes(serial.id, "big")

    def EAFSetID(self, ids: int, eaf_id: EAF_ID) -> bool:
        """Set the alias to a EAF."""

        return not self._eaf.EAFSetID(c_int(ids), eaf_id)


__all__ = ["Focuser"]
