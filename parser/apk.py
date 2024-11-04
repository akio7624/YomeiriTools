from datatype.chararray import chararray
from datatype.uint64 import uint64


class APK:

    def __init__(self):
        self.ENDIANNESS = self.__ENDIANNESS()

    class __ENDIANNESS:
        def __init__(self):
            self.ENDIANNESS: chararray = chararray(size=8)
            self.TABLE_SIZE: uint64 = uint64(0)

        def from_bytearray(self, src: bytearray):
            if len(src) != 16:
                raise TableException(self, f"The table size must be 16.  this={len(src)}")

            self.ENDIANNESS.from_bytearray(src[:8])
            if str(self.ENDIANNESS) != "ENDILTLE":
                raise TableException(self, f"ENDIANNESS must be 'ENDILTLE'.  this={str(self.ENDIANNESS)}")

            self.TABLE_SIZE.from_bytearray(src[8:])
            if int(self.TABLE_SIZE) != 0:
                raise TableException(self, f"TABLE_SIZE must be 0.  this={int(self.TABLE_SIZE)}")

        def to_bytearray(self) -> bytearray:
            # TODO
            pass


class TableException(Exception):
    def __init__(self, table: object, message: str):
        table_name = table.__class__.__name__
        self.message = f"table {table_name}: {message}"
        super().__init__(self.message)

