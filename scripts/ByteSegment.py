import binascii
from typing import Literal
import copy

class ByteSegment:
    endian: Literal["little", "big"] = None
    t: str = None
    raw: bytearray = None
    str_v: str = None
    int_v: int = None
    offset_v: str = None

    def __init__(self, t: Literal["int", "str", "raw", "offset"], v: str | int | bytearray, endian: Literal["little", "big"] = "little"):
        self.endian = endian
        self.t = t
        if t == "raw":
            self.raw = copy.deepcopy(v)
        elif t == "str":
            self.str_v = v
            self.raw = bytearray(v.encode("utf-8"))
        elif t == "int":
            self.int_v = v
            self.raw = bytearray(v.to_bytes(length=8, byteorder=endian))
        elif t == "offset":
            self.int_v = v
            self.offset_v = "0x" + (f"{v:#x}"[2:]).zfill(8).upper()
            self.raw = bytearray(v.to_bytes(length=8, byteorder=endian))

    def __str__(self):
        if self.t == "raw":
            size = len(self.raw)
            if 16 < size:
                return self.raw2hex(self.raw[:8]) + " ... " + self.raw2hex(self.raw[-8:]) + f" (total {size} byte)"
            else:
                return self.raw.hex(" ") + f" (total {size} byte)"
        elif self.t == "int":
            return str(self.int_v)
        elif self.t == "str":
            return self.str_v
        elif self.t == "offset":
            return self.offset_v

    def get_int(self) -> int:
        return self.int_v

    def raw2hex(self, r: bytearray):
        return r.hex(" ")