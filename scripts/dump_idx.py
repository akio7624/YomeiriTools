import json
from json import JSONEncoder
from typing import Literal

from prettytable import PrettyTable

from scripts.BinaryManager import BinaryReader
from scripts.ByteSegment import ByteSegment


class DumpIdx:
    INPUT_APK_PATH: str = None
    OUTPUT_DUMP_PATH: str = None
    DUMP_TYPE: Literal["table", "json"] = None
    IS_QUIET = False

    def __init__(self, i: str, o: str, t: str, q: bool):
        self.INPUT_APK_PATH = i
        self.OUTPUT_DUMP_PATH = o
        self.DUMP_TYPE = "table" if t == "table" else "json"
        self.IS_QUIET = q

    def make_table(self, DUMP: dict) -> str:
        result = ""
        PT = PrettyTable(align="l")
        PT.field_names = ["FNAME", "OFFSET", "ZSIZE", "SIZE", "IDENTIFIER"]

        result += "ROOT ARCHIVE\n"
        for TOC_SEG in DUMP["PACKTOC"]["TOC_SEGMENT_LIST"]:
            PT.add_row([str(DUMP["GENESTRT"]["STRING_LIST"][TOC_SEG["NAME_IDX"].get_int()])[:-1],
                       str(TOC_SEG["FILE_OFFSET"]),
                        TOC_SEG["ZSIZE"].get_int(),
                        TOC_SEG["SIZE"].get_int(),
                        TOC_SEG["IDENTIFIER"]
                       ])
        result += str(PT)

        return result

    def dump(self):
        DUMP: dict = {
            "ENDI": dict(),
            "PACKHEDR": list(),
            "PACKTOC": dict(),
            "PACKFSLS": dict(),
            "GENESTRT": dict(),
            "GENEEOF": dict()
        }

        with open(self.INPUT_APK_PATH, "rb") as f:
            reader = BinaryReader(bytearray(f.read()))
            reader.seek(0)
            print(f"Read file from {self.INPUT_APK_PATH}")
            print(f"File Size: {reader.size()} byte")

        print("parsing file header...")
        ENDIANESS = reader.read_string_bytes(8)
        DUMP["ENDI"]["ENDIANESS"] = ByteSegment("str", ENDIANESS)
        ZERO = reader.get_buffer(8)
        DUMP["ENDI"]["ZERO"] = ByteSegment("raw", ZERO)

        while True:
            print("parsing PACKHEDR...")
            PACKHEDR = reader.read_string_bytes(8)
            print(PACKHEDR)
            HEADER_SIZE = reader.read_u64()
            UNKNOWN_1 = reader.get_buffer(8)
            FILE_LIST_OFFSET = reader.read_u32()
            UNKNOWN_2 = reader.get_buffer(4)
            UNKNOWN_3 = reader.get_buffer(16)

            DUMP["PACKHEDR"].append({
                "PACKHEDR": ByteSegment("str", PACKHEDR),
                "HEADER_SIZE": ByteSegment("int", HEADER_SIZE),
                "UNKNOWN_1": ByteSegment("raw", UNKNOWN_1),
                "FILE_LIST_OFFSET": ByteSegment("offset", FILE_LIST_OFFSET),
                "UNKNOWN_2": ByteSegment("raw", UNKNOWN_2),
                "UNKNOWN_3": ByteSegment("raw", UNKNOWN_3)
            })

            tmp = reader.get_position()
            if reader.read_string_bytes(8) == "PACKTOC ":
                reader.seek(tmp)
                break
            reader.seek(tmp)

        print("parsing PACKTOC...")
        PACKTOC = reader.read_string_bytes(8)
        DUMP["PACKTOC"]["PACKTOC"] = ByteSegment("str", PACKTOC)
        HEADER_SIZE = reader.read_u64()
        DUMP["PACKTOC"]["HEADER_SIZE"] = ByteSegment("int", HEADER_SIZE)
        packtoc_start_offset = reader.get_position()
        TOC_SEG_SIZE = reader.read_u32()
        DUMP["PACKTOC"]["TOC_SEG_SIZE"] = ByteSegment("int", TOC_SEG_SIZE)
        TOC_SEG_COUNT = reader.read_u32()
        DUMP["PACKTOC"]["TOC_SEG_COUNT"] = ByteSegment("int", TOC_SEG_COUNT)
        UNKNOWN = reader.read_u32()
        DUMP["PACKTOC"]["UNKNOWN_1"] = ByteSegment("int", UNKNOWN)
        ZERO = reader.get_buffer(4)
        DUMP["PACKTOC"]["ZERO"] = ByteSegment("raw", ZERO)

        DUMP["PACKTOC"]["TOC_SEGMENT_LIST"] = list()

        for i in range(TOC_SEG_COUNT):
            IDENTIFIER = reader.read_u32()
            NAME_IDX = reader.read_u32()
            ZERO = reader.get_buffer(8)
            FILE_OFFSET = reader.read_u64()  # real file offset = file area offset + file_offset
            SIZE = reader.read_u64()
            ZSIZE = reader.read_u64()
            DUMP["PACKTOC"]["TOC_SEGMENT_LIST"].append({
                "IDENTIFIER": ByteSegment("int", IDENTIFIER),
                "NAME_IDX": ByteSegment("int", NAME_IDX),
                "ZERO": ByteSegment("raw", ZERO),
                "FILE_OFFSET": ByteSegment("offset", FILE_OFFSET),
                "SIZE": ByteSegment("int", SIZE),
                "ZSIZE": ByteSegment("int", ZSIZE)
            })

        pad_cnt = (packtoc_start_offset + HEADER_SIZE) - reader.get_position()
        ZERO = reader.get_buffer(pad_cnt)
        DUMP["PACKTOC"]["TABLE_PADDINGDING"] = ByteSegment("raw", ZERO)

        print("parsing PACKFSLS...")
        PACKFSLS = reader.read_string_bytes(8)
        DUMP["PACKFSLS"]["PACKFSLS"] = ByteSegment("str", PACKFSLS)
        HEADER_SIZE = reader.read_u64()
        packfsls_start_offset = reader.get_position()
        DUMP["PACKFSLS"]["HEADER_SIZE"] = ByteSegment("int", HEADER_SIZE)
        ARCHIVE_COUNT = reader.read_u32()
        DUMP["PACKFSLS"]["ARCHIVE_COUNT"] = ByteSegment("int", ARCHIVE_COUNT)
        ARCHIVE_SEG_SIZE = reader.read_u32()
        DUMP["PACKFSLS"]["ARCHIVE_SEG_SIZE"] = ByteSegment("int", ARCHIVE_SEG_SIZE)
        UNKNOWN = reader.get_buffer(4)
        DUMP["PACKFSLS"]["UNKNOWN_1"] = ByteSegment("raw", UNKNOWN)
        UNKNOWN = reader.get_buffer(4)
        DUMP["PACKFSLS"]["UNKNOWN_2"] = ByteSegment("raw", UNKNOWN)

        DUMP["PACKFSLS"]["ARCHIVE_SEGMENT_LIST"] = list()

        for ARCHIVE in range(ARCHIVE_COUNT):
            NAME_IDX = reader.read_u32()
            ZERO = reader.get_buffer(4)
            ARCHIVE_OFFSET = reader.read_u64()
            SIZE = reader.read_u64()
            DUMMY = reader.get_buffer(16)
            DUMP["PACKFSLS"]["ARCHIVE_SEGMENT_LIST"].append({
                "NAME_IDX": ByteSegment("int", NAME_IDX),
                "ZERO": ByteSegment("raw", ZERO),
                "ARCHIVE_OFFSET": ByteSegment("offset", ARCHIVE_OFFSET),
                "SIZE": ByteSegment("int", SIZE),
                "DUMMY": ByteSegment("raw", DUMMY)
            })

        pad_cnt = (packfsls_start_offset + HEADER_SIZE) - reader.get_position()
        ZERO = reader.get_buffer(pad_cnt)
        DUMP["PACKFSLS"]["TABLE_PADDINGDING"] = ByteSegment("raw", ZERO)

        print("parsing GENESTRT...")
        GENESTRT = reader.read_string_bytes(8)
        DUMP["GENESTRT"]["GENESTRT"] = ByteSegment("str", GENESTRT)
        GENESTRT_SIZE = reader.read_u64()
        DUMP["GENESTRT"]["GENESTRT_SIZE_1"] = ByteSegment("int", GENESTRT_SIZE)  # header + string_offset + string_area
        genestrt_start_offset = reader.get_position()
        STR_OFFSET_COUNT = reader.read_u32()
        DUMP["GENESTRT"]["STR_OFFSET_COUNT"] = ByteSegment("int", STR_OFFSET_COUNT)
        UNKNOWN = reader.get_buffer(4)
        DUMP["GENESTRT"]["UNKNOWN_1"] = ByteSegment("raw", UNKNOWN)
        GENESTRT_SIZE = reader.read_u32()
        DUMP["GENESTRT"]["HEADER_SIZE+STR_OFFSET_LIST_SIZE"] = ByteSegment("int", GENESTRT_SIZE)
        GENESTRT_SIZE = reader.read_u32()
        DUMP["GENESTRT"]["GENESTRT_SIZE_2"] = ByteSegment("int", GENESTRT_SIZE)

        DUMP["GENESTRT"]["STR_OFFSET_LIST"] = list()

        for i in range(STR_OFFSET_COUNT):
            DUMP["GENESTRT"]["STR_OFFSET_LIST"].append(ByteSegment("int", reader.read_u32()))
        pad_cnt = (genestrt_start_offset + DUMP["GENESTRT"][
            "HEADER_SIZE+STR_OFFSET_LIST_SIZE"].get_int()) - reader.get_position()
        DUMP["GENESTRT"]["PAD"] = ByteSegment("raw", reader.get_buffer(4))

        DUMP["GENESTRT"]["STRING_LIST"] = list()

        for i in range(STR_OFFSET_COUNT):
            DUMP["GENESTRT"]["STRING_LIST"].append(ByteSegment("str", reader.read_string_utf8()))

        pad_cnt = (genestrt_start_offset + GENESTRT_SIZE) - reader.get_position()
        DUMP["GENESTRT"]["TABLE_PADDING"] = ByteSegment("raw", reader.get_buffer(pad_cnt))

        print("parsing GENEEOF...")
        GENEEOF = reader.read_string_bytes(8)
        DUMP["GENEEOF"]["GENEEOF"] = ByteSegment("str", GENEEOF)
        ZERO = reader.get_buffer(8)
        DUMP["GENEEOF"]["ZERO"] = ByteSegment("raw", ZERO)
        TABLE_PADDING = reader.get_buffer(FILE_LIST_OFFSET - reader.get_position())
        DUMP["GENEEOF"]["TABLE_PADDING"] = ByteSegment("raw", TABLE_PADDING)

        print("parse success")

        class CustomEncoder(JSONEncoder):
            def default(self, o):
                if isinstance(o, int):
                    return o
                if isinstance(o, ByteSegment) and o.t == "int":
                    return o.get_int()
                return str(o)

        result = json.dumps(DUMP, indent=4, ensure_ascii=False, cls=CustomEncoder)
        if self.DUMP_TYPE == "table":
            result = self.make_table(DUMP)

        if not self.IS_QUIET:
            print(result)

        with open(self.OUTPUT_DUMP_PATH, "w") as f:
            f.write(result)
            print(f"Dump saved on {self.OUTPUT_DUMP_PATH}")


# for test
# if __name__ == "__main__":
#     DumpIdx(r"C:\Users\admin\Desktop\testt\pack.idx",
#                r"C:\Users\admin\Desktop\testt\pack_dump.txt",
#                "table",
#                True).dump()
