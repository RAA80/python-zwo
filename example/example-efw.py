#! /usr/bin/env python3

"""Пример использования библиотеки."""

from zwo.efw import FilterWheel

if __name__ == "__main__":
    wheel = FilterWheel()

    print(f"EFWGetNum = {wheel.EFWGetNum()}")

    ids = wheel.EFWGetID(0)
    print(f"EFWGetID = {ids}")

    print(f"EFWOpen = {wheel.EFWOpen(ids)}")

    info = wheel.EFWGetProperty(ids)
    print(f"EFWGetProperty = {info}")
    print(f"    ID = {info.ID}")
    print(f"    Name = {info.Name}")
    print(f"    slotNum = {info.slotNum}")

    print(f"EFWGetPosition = {wheel.EFWGetPosition(ids)}")
    print(f"EFWSetPosition = {wheel.EFWSetPosition(ids, 0)}")

    # print(f"EFWGetProductIDs = {wheel.EFWGetProductIDs()}")
    # print(f"EFWSetDirection = {wheel.EFWSetDirection(ids, False)}")
    # print(f"EFWGetDirection = {wheel.EFWGetDirection(ids)}")
    # print(f"EFWCalibrate = {wheel.EFWCalibrate(ids)}")
    # print(f"EFWGetSDKVersion = {wheel.EFWGetSDKVersion()}")
    # print(f"EFWGetHWErrorCode = {wheel.EFWGetHWErrorCode(ids)}")
    # print(f"EFWGetFirmwareVersion = {wheel.EFWGetFirmwareVersion(ids)}")
    # print(f"EFWGetSerialNumber = {wheel.EFWGetSerialNumber(ids)}")

    print(f"EFWClose = {wheel.EFWClose(ids)}")
