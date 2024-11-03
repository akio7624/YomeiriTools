import copy
import struct

from datatype.uint64 import uint64


class BinaryReader:
    def __init__(self, data: bytearray):
        if type(data) is not bytearray:
            raise BinaryManagerException(f"BinaryReader only accepts type bytearray")

        self.__RAW: bytearray = data
        self.__OFFSET: int = -1

    def __getitem__(self, index: int):
        return self.__RAW[index]

    def clear(self):
        self.__RAW.clear()
        self.__OFFSET = -1

    def skip(self, n):
        self.__OFFSET += n

    def size(self) -> int:
        return len(self.__RAW)

    def seek(self, offset: int):
        self.__OFFSET = offset

    def tell(self) -> int:
        return self.__OFFSET

    def get_byte(self) -> int:
        if self.__OFFSET < self.size():
            result = self.__RAW[self.__OFFSET]
            self.__OFFSET += 1
            return result
        else:
            raise BinaryManagerException(f"get_byte() OutOfRange.")

    def get_bytes(self, size: int) -> bytearray:
        if self.__OFFSET + size <= self.size():
            result = self.__RAW[self.__OFFSET:self.__OFFSET + size]
            self.__OFFSET += size
            return result
        else:
            raise BinaryManagerException(f"get_bytes() OutOfRange.")

    def read_ascii_string(self) -> str:
        tmp: bytearray = bytearray()

        while self.tell() < self.size():
            b: int = self.__RAW[self.tell()]
            if b == 0:
                tmp.append(0)
                self.__OFFSET += 1
                break
            tmp.append(b)
            self.__OFFSET += 1

        return tmp.decode("ascii")


class BinaryManagerException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
