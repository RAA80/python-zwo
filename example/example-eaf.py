#! /usr/bin/env python3

"""Пример использования библиотеки."""

from zwo.eaf import Focuser

if __name__ == "__main__":
    focus = Focuser()

    print(f"EAFGetNum = {focus.EAFGetNum()}")

    ids = focus.EAFGetID(0)
    print(f"EAFGetID = {ids}")

    print(f"EAFOpen = {focus.EAFOpen(ids)}")

    info = focus.EAFGetProperty(ids)
    print(f"EAFGetProperty = {info}")
    print(f"    ID = {info.ID}")
    print(f"    Name = {info.Name}")
    print(f"    MaxStep = {info.MaxStep}")

    print(f"EAFGetPosition = {focus.EAFGetPosition(ids)}")
    print(f"EAFMove = {focus.EAFMove(ids, position=1000)}")

    # print(f"EAFGetTemp = {focus.EAFGetTemp(ids)}")
    # print(f"EAFGetSDKVersion = {focus.EAFGetSDKVersion()}")
    # print(f"EAFGetSerialNumber = {focus.EAFGetSerialNumber(ids)}")

    print(f"EAFClose = {focus.EAFClose(ids)}")
