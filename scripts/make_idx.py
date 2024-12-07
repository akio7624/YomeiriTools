import copy
import os

from datatype.chararray import chararray
from datatype.uint32 import uint32
from datatype.uint64 import uint64
from parser.apk import APKReader
from parser.idx import IDX
from utils.Utils import get_table_padding_count, get_archive_file_padding_cnt


class MakeIdx:
    def __init__(self, i: list[str], o: str, d: str):
        self.INPUT_APK_PATH_LIST = i
        self.OUTPUT_IDX_PATH = o
        self.DIR_NAME = d
        self.IDX = IDX()
        self.APK_LIST: list[APKReader] = []

    def make(self):
        self.IDX.ENDIANNESS.SIGNATURE = chararray(size=8, value="ENDILTLE")
        self.IDX.ENDIANNESS.TABLE_SIZE = uint64(0)

        for apk_path in self.INPUT_APK_PATH_LIST:
            print(f"Read apk file: {apk_path}")
            apk_reader = APKReader(apk_path)
            apk_reader.read()

            packhedr = apk_reader.get_apk().PACKHEDR.to_bytearray()
            self.IDX.PACKHEDR_LIST.add_from_bytearray(ofs=16, src=packhedr)
            self.IDX.PACKHEDR_LIST.PACKHEDR_LIST[-1].apk_name = self.DIR_NAME + "/" + os.path.basename(apk_path) + "\0"

            self.APK_LIST.append(apk_reader)

        print("Packing idx file...")

        toc_seg_list = []  # Assume there is no duplicate seg between each apk file
        toc_seg_entry_index_increase = 0
        archive_seg_list = []
        for idx, apk_reader in enumerate(self.APK_LIST):
            for seg in apk_reader.get_apk().PACKTOC.TOC_SEGMENT_LIST:
                if int(seg.IDENTIFIER) == 1:
                    if int(seg.ENTRY_COUNT) == 0:
                        continue
                    seg.ENTRY_INDEX = uint32(int(seg.ENTRY_INDEX) + toc_seg_entry_index_increase)
                toc_seg_list.append(seg)
                seg.filename = apk_reader.get_apk().GENESTRT.FILE_NAMES[int(seg.NAME_IDX)]
            for seg in apk_reader.get_apk().PACKFSLS.ARCHIVE_SEGMENT_LIST:
                archive_seg_list.append(seg)
                seg.filename = apk_reader.get_apk().GENESTRT.FILE_NAMES[int(seg.NAME_IDX)]
                seg.ZERO = uint32(1)

            toc_seg_entry_index_increase += len(apk_reader.get_apk().PACKTOC.TOC_SEGMENT_LIST)

        self.IDX.PACKTOC.SIGNATURE = chararray(size=8, value="PACKTOC ")
        self.IDX.PACKTOC.TOC_SEG_SIZE = uint32(40)
        self.IDX.PACKTOC.TOC_SEG_COUNT = uint32(len(toc_seg_list))
        self.IDX.PACKTOC.unknown_1 = bytearray((16).to_bytes(1, byteorder='little')) + bytearray(7)

        for seg in toc_seg_list:
            self.IDX.PACKTOC.TOC_SEGMENT_LIST.append(copy.deepcopy(seg))

        self.IDX.PACKTOC.TABLE_SIZE = uint64(4+4+8+(len(toc_seg_list) * 40))
        padding_cnt = get_table_padding_count(int(self.IDX.PACKTOC.TABLE_SIZE))
        self.IDX.PACKTOC.PADDING = bytearray(padding_cnt)

        self.IDX.PACKTOC.TABLE_SIZE = uint64(int(self.IDX.PACKTOC.TABLE_SIZE) + padding_cnt)

        self.IDX.PACKFSLS.SIGNATURE = chararray(size=8, value="PACKFSLS")
        self.IDX.PACKFSLS.ARCHIVE_SEG_COUNT = uint32(len(archive_seg_list))
        self.IDX.PACKFSLS.ARCHIVE_SEG_SIZE = uint32(40)
        self.IDX.PACKFSLS.unknown_1 = bytearray((16).to_bytes(1, byteorder='little')) + bytearray(7)

        for seg in archive_seg_list:
            self.IDX.PACKFSLS.ARCHIVE_SEGMENT_LIST.append(copy.deepcopy(seg))

        self.IDX.PACKFSLS.TABLE_SIZE = uint64(4 + 4 + 8 + (len(archive_seg_list) * 40))
        padding_cnt = get_table_padding_count(int(self.IDX.PACKFSLS.TABLE_SIZE))
        self.IDX.PACKFSLS.PADDING = bytearray(padding_cnt)

        self.IDX.PACKFSLS.TABLE_SIZE = uint64(int(self.IDX.PACKFSLS.TABLE_SIZE) + padding_cnt)

        apk_path_list = list()
        string_set = set()
        for apk_reader in self.APK_LIST:
            apk = apk_reader.get_apk()
            for filename in apk.GENESTRT.FILE_NAMES:
                if filename.endswith(".apk\0"):
                    apk_path_list.append(filename)
                else:
                    string_set.add(filename)

        for packhedr in self.IDX.PACKHEDR_LIST.PACKHEDR_LIST:
            packhedr.NAME_IDX = uint32(apk_path_list.index(packhedr.apk_name))

        string_list = apk_path_list + sorted(list(string_set))
        for seg in self.IDX.PACKTOC.TOC_SEGMENT_LIST:
            seg.NAME_IDX = uint32(string_list.index(seg.filename))
        for seg in self.IDX.PACKFSLS.ARCHIVE_SEGMENT_LIST:
            seg.NAME_IDX = uint32(string_list.index(seg.filename))

        self.IDX.GENESTRT.SIGNATURE = chararray(size=8, value="GENESTRT")
        self.IDX.GENESTRT.unknown_1 = bytearray((16).to_bytes(1, byteorder='little')) + bytearray(3)
        self.IDX.GENESTRT.FILE_NAMES = [x for x in string_list]

        self.IDX.GENESTRT.FILENAME_COUNT = uint32(len(string_list))

        ofs_list: list[uint32] = [uint32(0)]
        for fname in string_list[:-1]:
            ofs = int(ofs_list[-1]) + len(fname)
            ofs_list.append(uint32(ofs))
        self.IDX.GENESTRT.FILENAME_OFFSET_LIST = ofs_list

        temp = bytearray()
        for o in self.IDX.GENESTRT.FILENAME_OFFSET_LIST:
            temp += o.to_bytearray()
        padding_cnt = get_table_padding_count(len(temp))
        self.IDX.GENESTRT.FILENAME_OFFSET_LIST_PADDING = bytearray(padding_cnt)

        temp = bytearray()
        for s in string_list:
            temp += bytearray(s.encode("ascii"))

        table_size = 8 + 8 + 4 + 4 + 4 + 4 + (4*len(string_list)) + padding_cnt + len(temp)
        padding_cnt = get_table_padding_count(table_size)
        self.IDX.GENESTRT.PADDING = bytearray(padding_cnt)

        self.IDX.GENESTRT.TABLE_SIZE_1 = uint64(table_size + padding_cnt - 16)
        self.IDX.GENESTRT.TABLE_SIZE_2 = uint32(table_size + padding_cnt - 16)
        self.IDX.GENESTRT.FILE_NAMES_OFFSET = uint32(4 + 4 + 4 + 4 + (4*len(string_list)))

        self.IDX.GENEEOF.SIGNATURE = chararray(size=8, value="GENEEOF ")
        self.IDX.GENEEOF.TABLE_SIZE = uint64(0)

        result = self.IDX.to_bytearray()
        with open(self.OUTPUT_IDX_PATH, 'wb') as f:
            f.write(result)

        print("OK.")
