# Made with reference to https://aluigi.altervista.org/bms/dragon_ball_z_boz.bms
import json
from json import JSONEncoder
from typing import Literal

from prettytable import PrettyTable

from scripts.BinaryManager import BinaryReader
from scripts.ByteSegment import ByteSegment


class DumpApk:
    INPUT_APK_PATH: str = None
    OUTPUT_DUMP_PATH: str = None
    DUMP_TYPE: Literal["table", "json"] = None
    IS_QUIET = False

    def __init__(self, i: str, o: str, t: str, q: bool):
        self.INPUT_APK_PATH = i
        self.OUTPUT_DUMP_PATH = o
        self.DUMP_TYPE = "table" if t == "table" else "json"
        self.IS_QUIET = q

        print("Start dump fs.apk!")

    def get_file_seg_size(self, size: int) -> int:
        if size % 512 == 0:
            return size
        n = int(size / 512)
        while True:
            block_size = (n * 512 - 1)
            if size <= block_size:
                return block_size
            n += 1

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

        for i in range(DUMP["PACKFSLS"]["ARCHIVE_COUNT"].get_int()):
            PT = PrettyTable(align="l")
            PT.field_names = ["FNAME", "REAL_OFFSET", "OFFSET", "ZSIZE", "SIZE"]
            result += f"\n\nARCHIVE #{i}\n"
            ARCHIVE = DUMP["FILE_AREA"][f"ARCHIVE #{i}"]

            for FILE_SEG in ARCHIVE["PACKFSHD"]["FILE_SEG_LIST"]:
                FNAME = str(ARCHIVE["GENESTRT"]["STRING_LIST"][FILE_SEG["NAME_IDX"].get_int()])
                ARCHIVE_OFFSET = DUMP["PACKFSLS"]["ARCHIVE_SEGMENT_LIST"][i]["ARCHIVE_OFFSET"].get_int()
                real_offset = ARCHIVE_OFFSET + FILE_SEG["OFFSET"].get_int()
                PT.add_row([FNAME[:-1],
                            "0x" + (f"{real_offset:#x}"[2:]).zfill(8).upper(),
                            str(FILE_SEG["OFFSET"]),
                            FILE_SEG["ZSIZE"].get_int(),
                            FILE_SEG["SIZE"].get_int()
                            ])
            result += str(PT)

        return result

    def dump(self):
        DUMP: dict = {
            "ENDI": dict(),
            "PACKHEDR": dict(),
            "PACKTOC": dict(),
            "PACKFSLS": dict(),
            "GENESTRT": dict(),
            "GENEEOF": dict(),
            "FILE_AREA": dict()
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

        print("parsing PACKHEDR...")
        PACKHEDR = reader.read_string_bytes(8)
        DUMP["PACKHEDR"]["PACKHEDR"] = ByteSegment("str", PACKHEDR)
        HEADER_SIZE = reader.read_u64()
        DUMP["PACKHEDR"]["HEADER_SIZE"] = ByteSegment("int", HEADER_SIZE)
        UNKNOWN = reader.get_buffer(8)
        DUMP["PACKHEDR"]["UNKNOWN_1"] = ByteSegment("raw", UNKNOWN)
        FILE_LIST_OFFSET = reader.read_u32()
        DUMP["PACKHEDR"]["FILE_LIST_OFFSET"] = ByteSegment("offset", FILE_LIST_OFFSET)
        UNKNOWN = reader.get_buffer(4)
        DUMP["PACKHEDR"]["UNKNOWN_2"] = ByteSegment("raw", UNKNOWN)
        UNKNOWN = reader.get_buffer(16)
        DUMP["PACKHEDR"]["UNKNOWN_3"] = ByteSegment("raw", UNKNOWN)

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
            FILE_OFFSET = reader.read_u64()
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
        pad_cnt = (genestrt_start_offset + DUMP["GENESTRT"]["HEADER_SIZE+STR_OFFSET_LIST_SIZE"].get_int()) - reader.get_position()
        DUMP["GENESTRT"]["PAD"] = ByteSegment("raw", reader.get_buffer(pad_cnt))

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

        print("parsing file area...")
        DUMP["FILE_AREA"]["ROOT_ARCHIVE"] = dict()
        for i in range(TOC_SEG_COUNT):
            TOC_SEG = DUMP["PACKTOC"]["TOC_SEGMENT_LIST"][i]
            reader.seek(TOC_SEG["FILE_OFFSET"].get_int())
            real_size = TOC_SEG["SIZE"].get_int() if TOC_SEG["ZSIZE"].get_int() == 0 else TOC_SEG["ZSIZE"].get_int()
            if real_size == 0:
                print("TOC_SEGMENT was skipped because size 0. It may not be a file.")
                print(f"    FNAME: {str(DUMP['GENESTRT']['STRING_LIST'][TOC_SEG['NAME_IDX'].get_int()])[:-1]}    OFFSET: {TOC_SEG['FILE_OFFSET']}")
                continue
            file_seg_size = self.get_file_seg_size(real_size)
            FILE = reader.get_buffer(real_size)
            PAD = reader.get_buffer(file_seg_size - real_size)
            DUMP["FILE_AREA"]["ROOT_ARCHIVE"][TOC_SEG["NAME_IDX"].get_int()] = {
                "FILE": ByteSegment("raw", FILE),
                "PAD": ByteSegment("raw", PAD)
            }

        for i in range(ARCHIVE_COUNT):
            key = f"ARCHIVE #{i}"
            DUMP["FILE_AREA"][key] = {
                "ENDIANESS": dict(),
                "PACKFSHD": dict(),
                "GENESTRT": dict()
            }
            print(f"parsing ARCHIVE #{i}")

            NAME_IDX = DUMP["PACKFSLS"]["ARCHIVE_SEGMENT_LIST"][i]["NAME_IDX"].get_int()
            ARCHIVE_OFFSET = DUMP["PACKFSLS"]["ARCHIVE_SEGMENT_LIST"][i]["ARCHIVE_OFFSET"].get_int()
            SIZE = DUMP["PACKFSLS"]["ARCHIVE_SEGMENT_LIST"][i]["SIZE"].get_int()
            ARCHIVE_NAME = DUMP["GENESTRT"]["STRING_LIST"][NAME_IDX]

            reader.seek(ARCHIVE_OFFSET)
            ENDIANESS = reader.read_string_bytes(8)
            DUMP["FILE_AREA"][key]["ENDIANESS"]["ENDIANESS"] = ByteSegment("str", ENDIANESS)
            PADDING = reader.get_buffer(8)
            DUMP["FILE_AREA"][key]["ENDIANESS"]["PADDING"] = ByteSegment("raw", PADDING)
            PACKFSHD = reader.read_string_bytes(8)
            DUMP["FILE_AREA"][key]["PACKFSHD"]["PACKFSHD"] = ByteSegment("str", PACKFSHD)
            HEADER_SIZE = reader.read_u64()
            DUMP["FILE_AREA"][key]["PACKFSHD"]["HEADER_SIZE"] = ByteSegment("int", HEADER_SIZE)
            DUMMY = reader.get_buffer(4)
            DUMP["FILE_AREA"][key]["PACKFSHD"]["UNKNOWN_1"] = ByteSegment("raw", DUMMY)
            FILE_SEG_SIZE = reader.read_u32()
            DUMP["FILE_AREA"][key]["PACKFSHD"]["FILE_SEG_SIZE?"] = ByteSegment("int", FILE_SEG_SIZE)
            FILE_SEG_COUNT = reader.read_u32()
            DUMP["FILE_AREA"][key]["PACKFSHD"]["FILE_SEG_COUNT"] = ByteSegment("int", FILE_SEG_COUNT)
            SEG_COUNT = reader.read_u32()
            DUMP["FILE_AREA"][key]["PACKFSHD"]["UNKNOWN_2"] = ByteSegment("int", SEG_COUNT)
            DUMMY = reader.get_buffer(16)
            DUMP["FILE_AREA"][key]["PACKFSHD"]["UNKNOWN_3"] = ByteSegment("raw", DUMMY)

            DUMP["FILE_AREA"][key]["PACKFSHD"]["FILE_SEG_LIST"] = list()

            for i in range(FILE_SEG_COUNT):
                NAME_IDX = reader.read_u32()
                ZIP = reader.read_u32()
                OFFSET = reader.read_u64()
                SIZE = reader.read_u64()
                ZSIZE = reader.read_u64()
                # REAL_OFFSET = OFFSET + ARCHIVE_OFFSET
                DUMP["FILE_AREA"][key]["PACKFSHD"]["FILE_SEG_LIST"].append({
                    "NAME_IDX": ByteSegment("int", NAME_IDX),
                    "ZIP": ByteSegment("int", ZIP),
                    "OFFSET": ByteSegment("offset", OFFSET),
                    "SIZE": ByteSegment("int", SIZE),
                    "ZSIZE": ByteSegment("int", ZSIZE)
                })

            print("    parsing GENESTRT...")
            GENESTRT = reader.read_string_bytes(8)
            DUMP["FILE_AREA"][key]["GENESTRT"]["GENESTRT"] = ByteSegment("str", GENESTRT)
            GENESTRT_SIZE = reader.read_u64()
            DUMP["FILE_AREA"][key]["GENESTRT"]["GENESTRT_SIZE_1"] = ByteSegment("int", GENESTRT_SIZE)  # header + string_offset + string_area
            genestrt_start_offset = reader.get_position()
            STR_OFFSET_COUNT = reader.read_u32()
            DUMP["FILE_AREA"][key]["GENESTRT"]["STR_OFFSET_COUNT"] = ByteSegment("int", STR_OFFSET_COUNT)
            UNKNOWN = reader.get_buffer(4)
            DUMP["FILE_AREA"][key]["GENESTRT"]["UNKNOWN_1"] = ByteSegment("raw", UNKNOWN)
            GENESTRT_SIZE = reader.read_u32()
            DUMP["FILE_AREA"][key]["GENESTRT"]["HEADER_SIZE+STR_OFFSET_LIST_SIZE"] = ByteSegment("int", GENESTRT_SIZE)
            GENESTRT_SIZE = reader.read_u32()
            DUMP["FILE_AREA"][key]["GENESTRT"]["GENESTRT_SIZE_2"] = ByteSegment("int", GENESTRT_SIZE)

            DUMP["FILE_AREA"][key]["GENESTRT"]["STR_OFFSET_LIST"] = list()

            for i in range(STR_OFFSET_COUNT):
                DUMP["FILE_AREA"][key]["GENESTRT"]["STR_OFFSET_LIST"].append(ByteSegment("int", reader.read_u32()))
            pad_cnt = (genestrt_start_offset + DUMP["FILE_AREA"][key]["GENESTRT"]["HEADER_SIZE+STR_OFFSET_LIST_SIZE"].get_int()) - reader.get_position()
            DUMP["FILE_AREA"][key]["GENESTRT"]["PAD"] = ByteSegment("raw", reader.get_buffer(pad_cnt))

            DUMP["FILE_AREA"][key]["GENESTRT"]["STRING_LIST"] = list()

            for i in range(STR_OFFSET_COUNT):
                DUMP["FILE_AREA"][key]["GENESTRT"]["STRING_LIST"].append(ByteSegment("str", reader.read_string_utf8()))

            pad_cnt = (genestrt_start_offset + GENESTRT_SIZE) - reader.get_position()
            DUMP["FILE_AREA"][key]["GENESTRT"]["TABLE_PADDING"] = ByteSegment("raw", reader.get_buffer(pad_cnt))

            DUMP["FILE_AREA"][key]["FILE_AREA"] = dict()

            for i in range(FILE_SEG_COUNT):
                FILE_SEG = DUMP["FILE_AREA"][key]["PACKFSHD"]["FILE_SEG_LIST"][i]
                OFFSET = FILE_SEG["OFFSET"].get_int()
                ZSIZE = FILE_SEG["ZSIZE"].get_int()
                SIZE = FILE_SEG["SIZE"].get_int()
                NAME_IDX = FILE_SEG["NAME_IDX"].get_int()
                FNAME = str(DUMP["FILE_AREA"][key]["GENESTRT"]["STRING_LIST"][NAME_IDX])

                reader.seek(ARCHIVE_OFFSET + OFFSET)
                real_size = SIZE if ZSIZE == 0 else ZSIZE
                if real_size == 0:
                    print("FILE_SEGMENT was skipped because size 0. It may not be a file.")
                    print(f"    FNAME: {FNAME[:-1]}    OFFSET: {OFFSET}")
                    continue
                FILE = reader.get_buffer(real_size)
                x = reader.get_position()
                y = 16 - (x % 16)
                PAD = reader.get_buffer(y)
                if PAD == 16:  # no padding
                    PAD = 0
                DUMP["FILE_AREA"][key]["FILE_AREA"][FNAME] = {
                    "FILE": ByteSegment("raw", FILE),
                    "PAD": ByteSegment("raw", PAD)
                }

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
if __name__ == "__main__":
    DumpApk(r"C:\Users\admin\Desktop\testt\patched\all.apk",
               r"C:\Users\admin\Desktop\testt\patched\extract_all",
               "table",
               True).dump()
