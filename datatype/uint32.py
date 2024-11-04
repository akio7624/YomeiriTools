import struct
from typing import Final


class uint32:
    MIN_VALUE: Final[int] = 0
    MAX_VALUE: Final[int] = 4_294_967_295

    def __init__(self, value: int | bytearray = None, endian: str = "<"):
        self.__value: int = 0

        if value is not None:
            self.from_value(value, endian)

    def __int__(self):
        return self.__value

    def from_int(self, value: int):
        if value < self.MIN_VALUE or value > self.MAX_VALUE:
            raise Uint32Exception(f"Value must be between {self.MIN_VALUE} and {self.MAX_VALUE}.")

        self.__value = value

    def from_bytearray(self, value: bytearray, endian: str = "<"):
        if len(value) != 4:
            raise Uint32Exception(f"Size must be a 4 bytes.  size={len(value)}")

        self.__value = struct.unpack(f"{endian}I", value)[0]

    def from_value(self, value: bytearray | int, endian: str = "<"):
        if isinstance(value, bytearray):
            self.from_bytearray(value, endian)
        elif isinstance(value, int):
            self.from_int(value)
        else:
            raise Uint32Exception(f"Value must be bytearray or int.  this={type(value)}")

    def to_int(self) -> int:
        return self.__int__()

    def to_bytearray(self, endian: str = "<") -> bytearray:
        return bytearray(struct.pack(f"{endian}I", self.__value))


class Uint32Exception(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)