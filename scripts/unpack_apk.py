import json
import os.path
import zlib
from json import JSONEncoder
from pathlib import Path
from typing import Literal

from scripts.BinaryManager import BinaryReader
from scripts.ByteSegment import ByteSegment


class UnpackApk:
    INPUT_APK_PATH: str = None
    OUTPUT_DIR_PATH: str = None
    FILE_EXISTS: Literal["overwrite", "skip"] = None
    IS_DEBUG: bool = False

    def __init__(self, i: str, o: str, e: Literal["overwrite", "skip"], d: bool):
        self.INPUT_APK_PATH = i
        self.OUTPUT_DIR_PATH = o
        self.FILE_EXISTS = e
        self.IS_DEBUG = d

    def print_d(self, s: str):
        if not self.IS_DEBUG:
            return
        print(s)

    def extract_file(self, out_path: str, file: bytearray, offset: int, is_same_name: bool, is_zip: bool):
        if is_zip:
            file = zlib.decompress(file)
        parent_dir = Path(out_path).parent.absolute()
        os.makedirs(parent_dir, exist_ok=True)

        if is_same_name:
            basename = os.path.basename(out_path).split(".")
            basename = basename[0] + f"__OFS_{offset}." + basename[1]
            out_path = os.path.join(parent_dir, basename)

        if os.path.isfile(out_path):
            if self.FILE_EXISTS == "skip":
                return

        with open(out_path, "wb") as f:
            f.write(file)
        print(f"Extract File: {out_path}")

    def extract(self):
        os.makedirs(self.OUTPUT_DIR_PATH, exist_ok=True)

        with open(self.INPUT_APK_PATH, "rb") as f:
            reader = BinaryReader(bytearray(f.read()))
            reader.seek(0)
            print(f"Read file from {self.INPUT_APK_PATH}")
            print(f"File Size: {reader.size()} byte")

        DUMP: dict = {
            "PACKTOC": dict(),
            "PACKFSLS": dict(),
            "GENESTRT": dict(),
            "FILE_AREA": dict()
        }
        FILE_LIST = dict()

        print("parsing file header...")
        ENDIANESS = reader.read_string_bytes(8)
        ZERO = reader.get_buffer(8)

        print("parsing PACKHEDR...")
        PACKHEDR = reader.read_string_bytes(8)
        HEADER_SIZE = reader.read_u64()
        UNKNOWN = reader.get_buffer(8)
        FILE_LIST_OFFSET = reader.read_u32()
        UNKNOWN = reader.get_buffer(4)
        UNKNOWN = reader.get_buffer(16)

        print("parsing PACKTOC...")
        PACKTOC = reader.read_string_bytes(8)
        HEADER_SIZE = reader.read_u64()
        packtoc_start_offset = reader.get_position()
        TOC_SEG_SIZE = reader.read_u32()
        TOC_SEG_COUNT = reader.read_u32()
        UNKNOWN = reader.read_u32()
        ZERO = reader.get_buffer(4)

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
                "FILE_OFFSET": ByteSegment("offset", FILE_OFFSET),
                "SIZE": ByteSegment("int", SIZE),
                "ZSIZE": ByteSegment("int", ZSIZE)
            })

        pad_cnt = (packtoc_start_offset + HEADER_SIZE) - reader.get_position()
        ZERO = reader.get_buffer(pad_cnt)

        print("parsing PACKFSLS...")
        PACKFSLS = reader.read_string_bytes(8)
        HEADER_SIZE = reader.read_u64()
        packfsls_start_offset = reader.get_position()
        ARCHIVE_COUNT = reader.read_u32()
        ARCHIVE_SEG_SIZE = reader.read_u32()
        UNKNOWN = reader.get_buffer(4)
        UNKNOWN = reader.get_buffer(4)

        DUMP["PACKFSLS"]["ARCHIVE_SEGMENT_LIST"] = list()

        for ARCHIVE in range(ARCHIVE_COUNT):
            NAME_IDX = reader.read_u32()
            ZERO = reader.get_buffer(4)
            ARCHIVE_OFFSET = reader.read_u64()
            SIZE = reader.read_u64()
            DUMMY = reader.get_buffer(16)
            DUMP["PACKFSLS"]["ARCHIVE_SEGMENT_LIST"].append({
                "NAME_IDX": ByteSegment("int", NAME_IDX),
                "ARCHIVE_OFFSET": ByteSegment("offset", ARCHIVE_OFFSET),
                "SIZE": ByteSegment("int", SIZE)
            })

        pad_cnt = (packfsls_start_offset + HEADER_SIZE) - reader.get_position()
        ZERO = reader.get_buffer(pad_cnt)

        print("parsing GENESTRT...")
        GENESTRT = reader.read_string_bytes(8)
        GENESTRT_SIZE = reader.read_u64()
        genestrt_start_offset = reader.get_position()
        STR_OFFSET_COUNT = reader.read_u32()
        DUMP["GENESTRT"]["STR_OFFSET_COUNT"] = ByteSegment("int", STR_OFFSET_COUNT)
        UNKNOWN = reader.get_buffer(4)
        GENESTRT_SIZE = reader.read_u32()
        DUMP["GENESTRT"]["HEADER_SIZE+STR_OFFSET_LIST_SIZE"] = ByteSegment("int", GENESTRT_SIZE)
        GENESTRT_SIZE = reader.read_u32()

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
        ZERO = reader.get_buffer(8)
        TABLE_PADDING = reader.get_buffer(FILE_LIST_OFFSET - reader.get_position())

        print("parsing file area...")
        DUMP["FILE_AREA"]["ROOT_ARCHIVE"] = dict()
        for i in range(TOC_SEG_COUNT):
            TOC_SEG = DUMP["PACKTOC"]["TOC_SEGMENT_LIST"][i]
            FNAME = str(DUMP["GENESTRT"]["STRING_LIST"][TOC_SEG["NAME_IDX"].get_int()])[:-1]
            IDENTIFIER = TOC_SEG["IDENTIFIER"].get_int()
            FILE_OFFSET = TOC_SEG["FILE_OFFSET"].get_int()
            SIZE = TOC_SEG["SIZE"].get_int()
            ZSIZE = TOC_SEG["ZSIZE"].get_int()

            reader.seek(FILE_OFFSET)
            real_size = SIZE if ZSIZE == 0 else ZSIZE
            if IDENTIFIER == 1:
                print("File was skipped because IDENTIFIER 0. It may not be a file.")
                continue
            if real_size == 0:
                print("File was skipped because size 0. It may not be a file.")
                self.print_d(f"    FNAME: {str(DUMP['GENESTRT']['STRING_LIST'][TOC_SEG['NAME_IDX'].get_int()])[:-1]}    OFFSET: {TOC_SEG['FILE_OFFSET']}")
                continue

            FILE = reader.get_buffer(real_size)
            out_path = os.path.join(self.OUTPUT_DIR_PATH, FNAME)
            FILE_LIST.setdefault(FNAME, list())
            FILE_LIST[FNAME].append({
                "out_path": out_path,
                "file": FILE,
                "offset": FILE_OFFSET,
                "zsize": ZSIZE,
                "fname": FNAME
            })

        for i in range(ARCHIVE_COUNT):
            key = f"ARCHIVE #{i}"
            DUMP["FILE_AREA"][key] = {
                "PACKFSHD": dict(),
                "GENESTRT": dict()
            }
            print(f"parsing ARCHIVE #{i}")

            NAME_IDX = DUMP["PACKFSLS"]["ARCHIVE_SEGMENT_LIST"][i]["NAME_IDX"].get_int()
            ARCHIVE_OFFSET = DUMP["PACKFSLS"]["ARCHIVE_SEGMENT_LIST"][i]["ARCHIVE_OFFSET"].get_int()
            SIZE = DUMP["PACKFSLS"]["ARCHIVE_SEGMENT_LIST"][i]["SIZE"].get_int()
            ARCHIVE_NAME = str(DUMP["GENESTRT"]["STRING_LIST"][NAME_IDX])[:-1]

            reader.seek(ARCHIVE_OFFSET)
            ENDIANESS = reader.read_string_bytes(8)
            PADDING = reader.get_buffer(8)

            PACKFSHD = reader.read_string_bytes(8)
            HEADER_SIZE = reader.read_u64()
            DUMMY = reader.get_buffer(4)
            FILE_SEG_SIZE = reader.read_u32()
            FILE_SEG_COUNT = reader.read_u32()
            SEG_COUNT = reader.read_u32()
            DUMMY = reader.get_buffer(16)

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
            GENESTRT_SIZE = reader.read_u64()
            genestrt_start_offset = reader.get_position()
            STR_OFFSET_COUNT = reader.read_u32()
            UNKNOWN = reader.get_buffer(4)
            GENESTRT_SIZE = reader.read_u32()
            DUMP["FILE_AREA"][key]["GENESTRT"]["HEADER_SIZE+STR_OFFSET_LIST_SIZE"] = ByteSegment("int", GENESTRT_SIZE)
            GENESTRT_SIZE = reader.read_u32()
            DUMP["FILE_AREA"][key]["GENESTRT"]["GENESTRT_SIZE_2"] = ByteSegment("int", GENESTRT_SIZE)

            DUMP["FILE_AREA"][key]["GENESTRT"]["STR_OFFSET_LIST"] = list()

            for i in range(STR_OFFSET_COUNT):
                DUMP["FILE_AREA"][key]["GENESTRT"]["STR_OFFSET_LIST"].append(ByteSegment("int", reader.read_u32()))
            pad_cnt = (genestrt_start_offset + DUMP["FILE_AREA"][key]["GENESTRT"]["HEADER_SIZE+STR_OFFSET_LIST_SIZE"].get_int()) - reader.get_position()
            reader.get_buffer(pad_cnt)

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
                FNAME = str(DUMP["FILE_AREA"][key]["GENESTRT"]["STRING_LIST"][NAME_IDX])[:-1]

                reader.seek(ARCHIVE_OFFSET + OFFSET)
                real_size = SIZE if ZSIZE == 0 else ZSIZE
                if real_size == 0:
                    print("FILE_SEGMENT was skipped because size 0. It may not be a file.")
                    self.print_d(f"    FNAME: {FNAME}    OFFSET: {OFFSET}")
                    continue
                FILE = reader.get_buffer(real_size)
                out_path = os.path.join(self.OUTPUT_DIR_PATH, ARCHIVE_NAME, FNAME)
                FILE_LIST.setdefault(ARCHIVE_NAME + "/" + FNAME, list())
                FILE_LIST[ARCHIVE_NAME + "/" + FNAME].append({
                    "out_path": out_path,
                    "file": FILE,
                    "offset": ARCHIVE_OFFSET + OFFSET,
                    "zsize": ZSIZE,
                    "fname": ARCHIVE_NAME + "/" + FNAME
                })

        for fname, obj_list in FILE_LIST.items():
            is_same_name = 1 < len(obj_list)
            for obj in obj_list:
                out_path = obj["out_path"]
                file = obj["file"]
                offset = obj["offset"]
                zsize = obj["zsize"]
                fname = obj["fname"]
                offset_hex = "0x" + (f"{offset:#x}"[2:]).zfill(8).upper()

                self.print_d(f"File info: FNAME: {fname}    OFFSET: {offset_hex}    ZSIZE: {zsize}    SIZE: {len(file)}")

                if zsize == 0:
                    self.extract_file(out_path, file, offset, is_same_name, False)
                else:
                    self.extract_file(out_path, file, offset, is_same_name, True)

        print("Extract end")


# for test
if __name__ == "__main__":
    UnpackApk(r"C:\Users\admin\Desktop\testt\patched\all.apk",
               r"C:\Users\admin\Desktop\testt\patched\extract_all",
               "overwrite",
               True).extract()
