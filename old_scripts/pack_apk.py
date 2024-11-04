import json
import os
import shutil
import sys
import zlib
from typing import List

from scripts.BinaryManager import BinaryReader


class PackApk:
    INPUT_APK_PATH: str = None
    INPUT_DIR_PATH: str = None
    INPUT_IDX_PATH: str = None
    OUTPUT_DIR_PATH: str = None
    IS_DEBUG: bool = False

    def __init__(self, i: List[str], x: str, o: str, d: bool):
        self.INPUT_APK_PATH = i[0]
        self.INPUT_DIR_PATH = i[1]
        self.INPUT_IDX_PATH = x
        self.OUTPUT_DIR_PATH = o
        self.IS_DEBUG = d
        
    def print_d(self, s: str):
        if not self.IS_DEBUG:
            return
        print(s)

    def make_ofs_name(self, name: str, ofs: int):
        basename = name.split(".")
        basename = basename[0] + f"__OFS_{ofs}." + basename[1]
        return basename

    def get_file_seg_size(self, size: int) -> int:
        if size % 512 == 0:
            return size
        n = int(size / 512)
        while True:
            block_size = (n * 512 - 1)
            if size <= block_size:
                return block_size
            n += 1

    def hex(self, v: int):
        return "0x" + (f"{v:#x}"[2:]).zfill(8).upper()

    def pack(self):
        mod_file_list = []
        for root, dirs, files in os.walk(self.INPUT_DIR_PATH):
            for file in files:
                mfn = os.path.join(os.path.relpath(root, self.INPUT_DIR_PATH), file).replace("\\", "/")
                if mfn.startswith("./"):
                    mfn = mfn[2:]
                mod_file_list.append(mfn)

        manual_offset = dict()
        for file in mod_file_list:
            if "__OFS_" in file:
                tmp = file.split("__OFS_")[1]
                ofs = int(tmp.split(".")[0])
                fname = file.replace(f"__OFS_{ofs}", "")
                manual_offset.setdefault(fname, list())
                manual_offset[fname].append(ofs)

        DUMP = ParseApk(self.INPUT_APK_PATH).parse()
        # print_d(json.dumps(DUMP, indent=4))
        INCREASE = 0

        os.makedirs(self.OUTPUT_DIR_PATH, exist_ok=True)
        NEW_APK_PATH = os.path.join(self.OUTPUT_DIR_PATH, os.path.basename(self.INPUT_APK_PATH))
        shutil.copyfile(self.INPUT_APK_PATH, NEW_APK_PATH)

        with open(NEW_APK_PATH, "rb") as f:
            reader = BinaryReader(bytearray(f.read()))
            reader.seek(0)

        DIFF = dict()
        INSERT_FILE = list()

        ROOT_FILES = sorted(DUMP["ROOT"], key=lambda d: d['OFFSET'])
        for FILE in ROOT_FILES:
            IDENTIFIER = FILE["IDENTIFIER"]
            OFFSET_OFFSET = FILE["OFFSET_OFFSET"]
            OFFSET = FILE["OFFSET"]
            SIZE_OFFSET = FILE["SIZE_OFFSET"]
            SIZE = FILE["SIZE"]
            ZSIZE_OFFSET = FILE["ZSIZE_OFFSET"]
            ZSIZE = FILE["ZSIZE"]
            FNAME = FILE["FNAME"]

            if IDENTIFIER == 1:
                continue

            # 수정된 파일이거나, 동일 이름 파일인데, 오프셋으로 찾았을 때 수정된 파일이면
            if FNAME in mod_file_list or (FNAME in manual_offset and OFFSET in manual_offset[FNAME]):
                mod_fp = os.path.join(self.INPUT_DIR_PATH, FNAME)
                if FNAME in manual_offset and OFFSET in manual_offset[FNAME]:
                    mod_fp = os.path.join(self.INPUT_DIR_PATH, self.make_ofs_name(FNAME, OFFSET))

                with open(mod_fp, "rb") as f:
                    FILE_RAW = f.read()
                MOD_SIZE = len(FILE_RAW)
                MOD_ZSIZE = 0

                if ZSIZE != 0:
                    FILE_RAW = zlib.compress(FILE_RAW, level=9)
                    MOD_ZSIZE = len(FILE_RAW)

                NEW_OFFSET = OFFSET + INCREASE
                NEW_SIZE = MOD_SIZE
                NEW_ZSIZE = MOD_ZSIZE

                if OFFSET != NEW_OFFSET:
                    reader.replace_bytes(bytearray(NEW_OFFSET.to_bytes(8, 'little')), OFFSET_OFFSET)
                    self.print_d(f"{FNAME}    OFFSET: {self.hex(OFFSET)}  ->  {self.hex(NEW_OFFSET)}")
                else:
                    self.print_d(f"{FNAME}    OFFSET: {self.hex(OFFSET)}  ==  {self.hex(NEW_OFFSET)}")
                if SIZE != NEW_SIZE:
                    reader.replace_bytes(bytearray(NEW_SIZE.to_bytes(8, 'little')), SIZE_OFFSET)
                    self.print_d(f"{FNAME}    SIZE: {SIZE}  ->  {NEW_SIZE}")
                else:
                    self.print_d(f"{FNAME}    SIZE: {SIZE}  ==  {NEW_SIZE}")
                if ZSIZE != NEW_ZSIZE:
                    reader.replace_bytes(bytearray(NEW_ZSIZE.to_bytes(8, 'little')), ZSIZE_OFFSET)
                    self.print_d(f"{FNAME}    ZSIZE: {ZSIZE}  ->  {NEW_ZSIZE}")
                else:
                    self.print_d(f"{FNAME}    ZSIZE: {ZSIZE}  ==  {NEW_ZSIZE}")

                OLD_BLOCK_SIZE = self.get_file_seg_size(SIZE if ZSIZE == 0 else ZSIZE)
                NEW_BLOCK_SIZE = self.get_file_seg_size(MOD_SIZE if ZSIZE == 0 else MOD_ZSIZE)

                if OLD_BLOCK_SIZE < NEW_BLOCK_SIZE:
                    x = NEW_BLOCK_SIZE - OLD_BLOCK_SIZE
                    INCREASE += x
                    self.print_d(f"INCREASE: +{x}  ->  {INCREASE}")
                elif OLD_BLOCK_SIZE > NEW_BLOCK_SIZE:
                    x = OLD_BLOCK_SIZE - NEW_BLOCK_SIZE
                    INCREASE -= x
                    self.print_d(f"INCREASE: -{x}  ->  {INCREASE}")

                DIFF.setdefault(FNAME, list())
                DIFF[FNAME].append({
                    "OLD_FOFSET": OFFSET,
                    "NEW_OFFSET": NEW_OFFSET,
                    "NEW_SIZE": NEW_SIZE,
                    "NEW_ZSIZE": NEW_ZSIZE
                })

                INSERT_FILE.append({
                    "OFFSET": OFFSET,
                    "FILE": bytearray(FILE_RAW),
                    "OLD_BLOCK_SIZE": OLD_BLOCK_SIZE,
                    "NEW_BLOCK_SIZE": NEW_BLOCK_SIZE
                })
            else:  # 수정된 파일이 아니거나, 동일 이름 파일이지만 수정 목록에 현재 오프셋의 파일은 없을 때
                NEW_OFFSET = OFFSET + INCREASE
                if OFFSET != NEW_OFFSET:
                    reader.replace_bytes(bytearray(NEW_OFFSET.to_bytes(8, 'little')), OFFSET_OFFSET)
                    self.print_d(f"{FNAME}    OFFSET: {self.hex(OFFSET)}  ->  {self.hex(NEW_OFFSET)}")

                    DIFF.setdefault(FNAME, list())
                    DIFF[FNAME].append({
                        "NEW_OFFSET": NEW_OFFSET,
                        "NEW_SIZE": None,
                        "NEW_ZSIZE": None
                    })
                else:
                    self.print_d(f"{FNAME}    OFFSET: {self.hex(OFFSET)}  ==  {self.hex(NEW_OFFSET)}")

        INSERT_FILE.reverse()
        for FILE in INSERT_FILE:
            old_block_size = FILE["OLD_BLOCK_SIZE"]
            new_block_size = FILE["NEW_BLOCK_SIZE"]

            reader.delete_bytes_range(FILE["OFFSET"], old_block_size)
            new_block = FILE["FILE"]
            if len(FILE["FILE"]) < new_block_size:
                new_block += bytearray(new_block_size - len(FILE["FILE"]))
            reader.insert_bytes(FILE["OFFSET"], new_block)

        with open(os.path.join(self.OUTPUT_DIR_PATH, os.path.basename(self.INPUT_APK_PATH)), "wb") as f:
            f.write(reader.get_buffer_all())

        print(f"Total INCREASE: {INCREASE}")

        # print_d(json.dumps(DIFF, indent=4))

        if self.INPUT_IDX_PATH is None:
            sys.exit(0)

        # ##################  Patch pack.idx  ##################
        with open(self.INPUT_IDX_PATH, "rb") as f:
            reader = BinaryReader(bytearray(f.read()))
            reader.seek(0)

        reader.seek(reader.findloc("GENESTRT") - 1)
        reader.skip(17)
        object_count = reader.read_u32()
        reader.skip(12)
        STRING_LIST = []
        for i in range(object_count):
            STRING_LIST.append(reader.read_u32())
        NAMES_OFFSET = reader.get_position()
        for i in range(object_count):
            reader.seek(NAMES_OFFSET + STRING_LIST[i])
            STRING_LIST[i] = reader.read_string_utf8()[:-1]  # remove null

        reader.seek(0)
        reader.seek(reader.findloc("PACKTOC")-1)
        reader.skip(21)
        object_count = reader.read_u32()
        reader.skip(8)

        for i in range(object_count):
            IDENTIFIER = reader.read_u32()
            NAME_IDX = reader.read_u32()
            ZERO = reader.read_u32()
            ZERO = reader.read_u32()
            OFFSET_OFFSET = reader.get_position()
            OFFSET = reader.read_u64()
            SIZE_OFFSET = reader.get_position()
            SIZE = reader.read_u64()
            ZSIZE_OFFSET = reader.get_position()
            ZSIZE = reader.read_u64()
            FNAME = STRING_LIST[NAME_IDX]

            diff_obj = DIFF.get(FNAME)
            if diff_obj is None:
                continue
            if len(diff_obj) == 0:
                continue

            diff_obj = diff_obj[0]
            NEW_OFFSET = diff_obj["NEW_OFFSET"]
            NEW_SIZE = diff_obj["NEW_SIZE"]
            NEW_ZSIZE = diff_obj["NEW_ZSIZE"]

            if OFFSET != NEW_OFFSET:
                reader.replace_bytes(bytearray(NEW_OFFSET.to_bytes(8, 'little')), OFFSET_OFFSET)
                self.print_d(f"idx: {FNAME}    OFFSET: {self.hex(OFFSET)}  ->  {self.hex(NEW_OFFSET)}")
            else:
                self.print_d(f"idx: {FNAME}    OFFSET: {self.hex(OFFSET)}  ==  {self.hex(NEW_OFFSET)}")
            if NEW_SIZE is not None:
                if SIZE != NEW_SIZE:
                    reader.replace_bytes(bytearray(NEW_SIZE.to_bytes(8, 'little')), SIZE_OFFSET)
                    self.print_d(f"idx: {FNAME}    SIZE: {self.hex(SIZE)}  ->  {self.hex(NEW_SIZE)}")
                else:
                    self.print_d(f"idx: {FNAME}    SIZE: {self.hex(SIZE)}  ==  {self.hex(NEW_SIZE)}")
                if ZSIZE != NEW_ZSIZE:
                    reader.replace_bytes(bytearray(NEW_ZSIZE.to_bytes(8, 'little')), ZSIZE_OFFSET)
                    self.print_d(f"idx: {FNAME}    ZSIZE: {self.hex(ZSIZE)}  ->  {self.hex(NEW_ZSIZE)}")
                else:
                    self.print_d(f"idx: {FNAME}    ZSIZE: {self.hex(ZSIZE)}  ==  {self.hex(NEW_ZSIZE)}")

            del DIFF.get(FNAME)[0]

        NEW_IDX_PATH = os.path.join(self.OUTPUT_DIR_PATH, "pack.idx")
        with open(NEW_IDX_PATH, "wb") as f:
            f.write(reader.get_buffer_all())



class ParseApk():
    apk_path: str = None

    def __init__(self, apk_path):
        self.apk_path = apk_path

    def parse(self):
        DUMP = {
            "ROOT": [],
            "ARCHIVE": {}
        }

        with open(self.apk_path, "rb") as f:
            reader = BinaryReader(bytearray(f.read()))
            reader.seek(0)

        reader.seek(reader.findloc("GENESTRT"))
        reader.skip(8+8)
        genestrt_start_offset = reader.get_position()
        STR_OFFSET_COUNT = reader.read_u32()
        reader.skip(4)
        SIZE_TMP = reader.read_u32()
        reader.skip(4+4)

        str_offset_list: List[int] = []

        for i in range(STR_OFFSET_COUNT):
            str_offset_list.append(reader.read_u32())

        pad_cnt = (genestrt_start_offset + SIZE_TMP) - reader.get_position()
        reader.get_buffer(pad_cnt)

        root_str_list: List[str] = []

        for i in range(STR_OFFSET_COUNT):
            root_str_list.append(reader.read_string_utf8())

        reader.seek(0)
        reader.seek(reader.findloc("PACKTOC "))
        reader.skip(8+8+4)
        TOC_SEG_COUNT = reader.read_u32()
        reader.skip(4+4)

        for i in range(TOC_SEG_COUNT):
            IDENTIFIER = reader.read_u32()
            NAME_IDX = reader.read_u32()
            ZERO = reader.get_buffer(8)
            OFFSET_OFFSET = reader.get_position()
            OFFSET = reader.read_u64()
            SIZE_OFFSET = reader.get_position()
            SIZE = reader.read_u64()
            ZSIZE_OFFSET = reader.get_position()
            ZSIZE = reader.read_u64()
            FNAME = root_str_list[NAME_IDX][:-1]

            DUMP["ROOT"].append({
                "IDENTIFIER": IDENTIFIER,
                "OFFSET": OFFSET,
                "SIZE": SIZE,
                "ZSIZE": ZSIZE,
                "OFFSET_OFFSET": OFFSET_OFFSET,
                "SIZE_OFFSET": SIZE_OFFSET,
                "ZSIZE_OFFSET": ZSIZE_OFFSET,
                "FNAME": FNAME
            })

        reader.seek(reader.findloc("PACKFSLS"))
        reader.skip(8+8)
        ARCHIVE_COUNT = reader.read_u32()
        reader.skip(4+4+4)

        for i in range(ARCHIVE_COUNT):
            NAME_IDX = reader.read_u32()
            ZERO = reader.get_buffer(4)
            ARCHIVE_OFFSET_OFFSET = reader.get_position()
            ARCHIVE_OFFSET = reader.read_u64()
            SIZE_OFFSET = reader.get_position()
            SIZE = reader.read_u64()
            DUMMY = reader.get_buffer(16)
            ARCHIVE_NAME = root_str_list[NAME_IDX][:-1]

            DUMP["ARCHIVE"][ARCHIVE_NAME] = {
                "ARCHIVE_OFFSET_OFFSET": ARCHIVE_OFFSET_OFFSET,
                "SIZE_OFFSET": SIZE_OFFSET,
                "ARCHIVE_OFFSET": ARCHIVE_OFFSET,
                "SIZE": SIZE,
                "FILES": list()
            }
            tmp = reader.get_position()

            if ARCHIVE_COUNT != 0:
                print("Multiple archive is not support")
                sys.exit()

            reader.seek(ARCHIVE_OFFSET)
            reader.seek(reader.findloc("GENESTRT"))
            reader.skip(8+8)
            genestrt_start_offset = reader.get_position()
            STR_OFFSET_COUNT = reader.read_u32()
            reader.skip(4)
            SIZE_TMP = reader.read_u32()
            reader.skip(4)

            str_offset_list = []

            for i in range(STR_OFFSET_COUNT):
                str_offset_list.append(reader.read_u32())
            pad_cnt = (genestrt_start_offset + SIZE_TMP) - reader.get_position()
            reader.get_buffer(pad_cnt)

            str_list = []

            for i in range(STR_OFFSET_COUNT):
                str_list.append(reader.read_string_utf8())

            reader.seek(ARCHIVE_OFFSET)
            reader.seek(reader.findloc("PACKFSHD"))
            reader.skip(8+8+4+4)
            FILE_SEG_CNT = reader.read_u32()
            reader.skip(4+16)

            for i in range(FILE_SEG_CNT):
                NAME_IDX = reader.read_u32()
                ZIP = reader.read_u32()
                OFFSET_OFFSET = reader.get_position()
                OFFSET = reader.read_u64()
                SIZE_OFFSET = reader.get_position()
                SIZE = reader.read_u64()
                ZSIZE_OFFSET = reader.get_position()
                ZSIZE = reader.read_u64()
                real_offset = ARCHIVE_OFFSET + OFFSET
                FNAME = ARCHIVE_NAME + "/" + str_list[NAME_IDX][:-1]
                DUMP["ARCHIVE"][ARCHIVE_NAME]["FILES"].append({
                    "OFFSET": OFFSET,
                    "REAL_OFFSET": real_offset,
                    "SIZE": SIZE,
                    "ZSIZE": ZSIZE,
                    "OFFSET_OFFSET": OFFSET_OFFSET,
                    "SIZE_OFFSET": SIZE_OFFSET,
                    "ZSIZE_OFFSET": ZSIZE_OFFSET,
                    "ZIP": ZIP,
                    "FNAME": FNAME
                })

            reader.seek(tmp)

        # print_d(json.dumps(DUMP, indent=4, ensure_ascii=False))
        return DUMP


# for test
# if __name__ == "__main__":
#     PackApk([r"C:\Users\admin\Desktop\testt\all.apk",
#                r"C:\Users\admin\Desktop\testt\mod_all\all"],
#                r"C:\Users\admin\Desktop\testt\pack.idx",
#                r"C:\Users\admin\Desktop\testt\patched",
#                True).pack()
