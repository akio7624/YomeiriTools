import copy
import hashlib

from datatype.chararray import chararray
from datatype.uint32 import uint32
from datatype.uint64 import uint64
from utils.BinaryManager import BinaryReader
from utils.Utils import *


class APK:

    def __init__(self):
        self.ENDIANNESS = self._ENDIANNESS()
        self.PACKHEDR = self._PACKHEDR()
        self.PACKTOC = self._PACKTOC()
        self.PACKFSLS = self._PACKFSLS()
        self.GENESTRT = self._GENESTRT()
        self.GENEEOF = self._GENEEOF()
        self.ROOT_FILES = self._ROOT_FILES()
        self.ARCHIVES = self._ARCHIVES()

    def to_bytearray(self) -> bytearray:
        return (
                    self.ENDIANNESS.to_bytearray() +
                    self.PACKHEDR.to_bytearray() +
                    self.PACKTOC.to_bytearray() +
                    self.PACKFSLS.to_bytearray() +
                    self.GENESTRT.to_bytearray() +
                    self.GENEEOF.to_bytearray() +
                    self.ROOT_FILES.to_bytearray() +
                    self.ARCHIVES.to_bytearray()
                )

    class _ENDIANNESS:
        def __init__(self):
            self.SIGNATURE: chararray = chararray(size=8)
            self.TABLE_SIZE: uint64 = uint64(0)

            self.SIGNATURE_ofs: int = 0
            self.TABLE_SIZE_ofs: int = 0

        def from_bytearray(self, ofs: int, src: bytearray):
            if len(src) != 16:
                raise TableException(self, f"The table size must be 16.  this={len(src)}")

            self.SIGNATURE.from_bytearray(src[:8])
            self.SIGNATURE_ofs = ofs
            if str(self.SIGNATURE) != "ENDILTLE":
                raise TableException(self, f"SIGNATURE must be 'ENDILTLE'.  this={str(self.SIGNATURE)}")

            self.TABLE_SIZE.from_bytearray(src[8:])
            self.TABLE_SIZE_ofs = ofs + 8
            if int(self.TABLE_SIZE) != 0:
                raise TableException(self, f"TABLE_SIZE must be 0.  this={int(self.TABLE_SIZE)}")

        def to_bytearray(self) -> bytearray:
            return self.SIGNATURE.to_bytearray() + self.TABLE_SIZE.to_bytearray()

    class _PACKHEDR:
        def __init__(self):
            self.SIGNATURE: chararray = chararray(size=8)
            self.TABLE_SIZE: uint64 = uint64(0)
            self.unknown_1: bytearray = bytearray()
            self.FILE_LIST_OFFSET: uint32 = uint32(0)
            self.ARCHIVE_PADDING_TYPE: uint32 = uint32(0)
            self.HASH: bytearray = bytearray()

            self.SIGNATURE_ofs: int = 0
            self.TABLE_SIZE_ofs: int = 0
            self.unknown_1_ofs: int = 0
            self.FILE_LIST_OFFSET_ofs: int = 0
            self.ARCHIVE_PADDING_TYPE_ofs: int = 0
            self.HASH_ofs: int = 0

        def from_bytearray(self, ofs: int, src: bytearray):
            self.SIGNATURE.from_bytearray(src[:8])
            self.SIGNATURE_ofs = ofs
            if str(self.SIGNATURE) != "PACKHEDR":
                raise TableException(self, f"SIGNATURE must be 'PACKHEDR'.  this={str(self.SIGNATURE)}")

            self.TABLE_SIZE.from_bytearray(src[8:16])
            self.TABLE_SIZE_ofs = ofs + 8

            if len(src) != int(self.TABLE_SIZE) + 16:
                raise TableException(self, f"The table size mismatch.  this={len(src)} expected={int(self.TABLE_SIZE) + 16}")

            self.unknown_1 = src[16:24]
            self.unknown_1_ofs = ofs + 16

            self.FILE_LIST_OFFSET.from_bytearray(src[24:28])
            self.FILE_LIST_OFFSET_ofs = ofs + 24

            self.ARCHIVE_PADDING_TYPE.from_bytearray(src[28:32])
            self.ARCHIVE_PADDING_TYPE_ofs = ofs + 28
            if int(self.ARCHIVE_PADDING_TYPE) not in [1, 2]:
                raise TableException(self, f"The ARCHIVE PADDING TYPE must be 1 or 2.  this={int(self.ARCHIVE_PADDING_TYPE)}")

            self.HASH = src[32:]
            self.HASH_ofs = ofs + 32

        def to_bytearray(self) -> bytearray:
            return (
                        self.SIGNATURE.to_bytearray() +
                        self.TABLE_SIZE.to_bytearray() +
                        self.unknown_1 +
                        self.FILE_LIST_OFFSET.to_bytearray() +
                        self.ARCHIVE_PADDING_TYPE.to_bytearray() +
                        self.HASH
                    )

    class _PACKTOC:
        def __init__(self):
            self.SIGNATURE: chararray = chararray(size=8)
            self.TABLE_SIZE: uint64 = uint64(0)
            self.TOC_SEG_SIZE: uint32 = uint32(0)
            self.TOC_SEG_COUNT: uint32 = uint32(0)
            self.unknown_1: bytearray = bytearray()
            self.TOC_SEGMENT_LIST: list[APK._PACKTOC._TOC_SEGMENT] = []
            self.PADDING: bytearray = bytearray()

            self.SIGNATURE_ofs: int = 0
            self.TABLE_SIZE_ofs: int = 0
            self.TOC_SEG_SIZE_ofs: int = 0
            self.TOC_SEG_COUNT_ofs: int = 0
            self.unknown_1_ofs: int = 0
            self.TOC_SEGMENT_LIST_ofs: int = 0
            self.PADDING_ofs: int = 0

        def from_bytearray(self, ofs: int, src: bytearray):
            self.SIGNATURE.from_bytearray(src[:8])
            self.SIGNATURE_ofs = ofs
            if str(self.SIGNATURE) != "PACKTOC ":
                raise TableException(self, f"SIGNATURE must be 'PACKTOC '.  this='{str(self.SIGNATURE)}'")

            self.TABLE_SIZE.from_bytearray(src[8:16])
            self.TABLE_SIZE_ofs = ofs + 8
            if len(src) != int(self.TABLE_SIZE) + 16:
                raise TableException(self, f"The table size mismatch.  this={len(src)} expected={int(self.TABLE_SIZE) + 16}")

            self.TOC_SEG_SIZE.from_bytearray(src[16:20])
            self.TOC_SEG_SIZE_ofs = ofs + 16
            if int(self.TOC_SEG_SIZE) != 40:
                raise TableException(self, f"The TOC_SEG_SIZE mismatch.  this={int(self.TOC_SEG_SIZE)}, expected=40")

            self.TOC_SEG_COUNT.from_bytearray(src[20:24])
            self.TOC_SEG_COUNT_ofs = ofs + 20

            self.unknown_1 = src[24:32]
            self.unknown_1_ofs = ofs + 24

            seg_ofs = 32
            self.TOC_SEGMENT_LIST_ofs = ofs + 32
            for i in range(int(self.TOC_SEG_COUNT)):
                seg = self._TOC_SEGMENT()
                seg.from_bytearray(ofs=ofs + seg_ofs, src=src[seg_ofs:seg_ofs + int(self.TOC_SEG_SIZE)])
                self.TOC_SEGMENT_LIST.append(seg)
                seg_ofs += int(self.TOC_SEG_SIZE)

            self.PADDING = src[seg_ofs:seg_ofs + get_table_padding_count(seg_ofs)]
            self.PADDING_ofs = ofs + seg_ofs

        def to_bytearray(self) -> bytearray:
            part_A: bytearray = (
                        self.SIGNATURE.to_bytearray() +
                        self.TABLE_SIZE.to_bytearray() +
                        self.TOC_SEG_SIZE.to_bytearray() +
                        self.TOC_SEG_COUNT.to_bytearray() +
                        self.unknown_1
                    )

            part_B = bytearray()
            for seg in self.TOC_SEGMENT_LIST:
                part_B += seg.to_bytearray()

            part_C: bytearray = self.PADDING

            return part_A + part_B + part_C

        class _TOC_SEGMENT:
            def __init__(self):
                self.IDENTIFIER: uint32 = uint32(0)
                self.NAME_IDX: uint32 = uint32(0)
                self.ZERO: bytearray = bytearray()
                self.FILE_OFFSET: uint64 = uint64(0)  # for file
                self.ENTRY_INDEX: uint32 = uint32(0)  # for directory
                self.ENTRY_COUNT: uint32 = uint32(0)  # for directory
                self.FILE_SIZE: uint64 = uint64(0)
                self.FILE_ZSIZE: uint64 = uint64(0)

                self.IDENTIFIER_ofs: int = 0
                self.NAME_IDX_ofs: int = 0
                self.ZERO_ofs: int = 0
                self.FILE_OFFSET_ofs: int = 0
                self.ENTRY_INDEX_ofs: int = 0
                self.ENTRY_COUNT_ofs: int = 0
                self.FILE_SIZE_ofs: int = 0
                self.FILE_ZSIZE_ofs: int = 0

                self.file_index: int = -1

            def from_bytearray(self, ofs: int, src: bytearray):
                self.IDENTIFIER.from_bytearray(src[:4])
                self.IDENTIFIER_ofs = ofs
                if int(self.IDENTIFIER) not in [0, 1, 512]:
                    raise TableException(self, f"IDENTIFIER must be 0 or 1 or 512    this={int(self.IDENTIFIER)}")

                self.NAME_IDX.from_bytearray(src[4:8])
                self.NAME_IDX_ofs = ofs + 4

                self.ZERO = src[8:16]
                self.ZERO_ofs = ofs + 8

                if int(self.IDENTIFIER) == 1:  # if directory
                    self.ENTRY_INDEX.from_bytearray(src[16:20])
                    self.ENTRY_INDEX_ofs = ofs + 16
                    self.ENTRY_COUNT.from_bytearray(src[20:24])
                    self.ENTRY_COUNT_ofs = ofs + 20
                else:  # if file
                    self.FILE_OFFSET.from_bytearray(src[16:24])
                    self.FILE_OFFSET_ofs = ofs + 16

                self.FILE_SIZE.from_bytearray(src[24:32])
                self.FILE_SIZE_ofs = ofs + 24

                self.FILE_ZSIZE.from_bytearray(src[32:40])
                self.FILE_ZSIZE_ofs = ofs + 32

            def to_bytearray(self) -> bytearray:
                if int(self.IDENTIFIER) == 1:  # if directory
                    return (
                            self.IDENTIFIER.to_bytearray() +
                            self.NAME_IDX.to_bytearray() +
                            self.ZERO +
                            self.ENTRY_INDEX.to_bytearray() +
                            self.ENTRY_COUNT.to_bytearray() +
                            self.FILE_SIZE.to_bytearray() +
                            self.FILE_ZSIZE.to_bytearray()
                    )
                else:
                    return (
                        self.IDENTIFIER.to_bytearray() +
                        self.NAME_IDX.to_bytearray() +
                        self.ZERO +
                        self.FILE_OFFSET.to_bytearray() +
                        self.FILE_SIZE.to_bytearray() +
                        self.FILE_ZSIZE.to_bytearray()
                    )

    class _PACKFSLS:
        def __init__(self):
            self.SIGNATURE: chararray = chararray(size=8)
            self.TABLE_SIZE: uint64 = uint64(0)
            self.ARCHIVE_SEG_COUNT: uint32 = uint32(0)
            self.ARCHIVE_SEG_SIZE: uint32 = uint32(0)
            self.unknown_1: bytearray = bytearray()
            self.ARCHIVE_SEGMENT_LIST: list[APK._PACKFSLS._ARCHIVE_SEGMENT] = list()
            self.PADDING: bytearray = bytearray()

            self.SIGNATURE_ofs: int = 0
            self.TABLE_SIZE_ofs: int = 0
            self.ARCHIVE_SEG_COUNT_ofs: int = 0
            self.ARCHIVE_SEG_SIZE_ofs: int = 0
            self.unknown_1_ofs: int = 0
            self.ARCHIVE_SEGMENT_LIST_ofs: int = 0
            self.PADDING_ofs: int = 0

            self.temp_name_idx_list = []
            self.NAME_ARCHIVE_MAP = dict()

        def from_bytearray(self, ofs: int, src: bytearray):
            self.SIGNATURE.from_bytearray(src[:8])
            self.SIGNATURE_ofs = ofs
            if str(self.SIGNATURE) != "PACKFSLS":
                raise TableException(self, f"SIGNATURE must be 'PACKFSLS'.  this='{str(self.SIGNATURE)}'")

            self.TABLE_SIZE.from_bytearray(src[8:16])
            self.TABLE_SIZE_ofs = ofs + 8
            if len(src) != int(self.TABLE_SIZE) + 16:
                raise TableException(self, f"The table size mismatch.  this={len(src)} expected={int(self.TABLE_SIZE) + 16}")

            self.ARCHIVE_SEG_COUNT.from_bytearray(src[16:20])
            self.ARCHIVE_SEG_COUNT_ofs = ofs + 16

            self.ARCHIVE_SEG_SIZE.from_bytearray(src[20:24])
            self.ARCHIVE_SEG_SIZE_ofs = ofs + 20
            if int(self.ARCHIVE_SEG_SIZE) != 40:
                raise TableException(self, f"The ARCHIVE_SEG_SIZE mismatch.  this={int(self.ARCHIVE_SEG_SIZE)}, expected=40")

            self.unknown_1 = src[24:32]
            self.unknown_1_ofs = ofs + 24

            seg_ofs = 32
            self.ARCHIVE_SEGMENT_LIST_ofs = ofs + 32
            for i in range(int(self.ARCHIVE_SEG_COUNT)):
                seg = self._ARCHIVE_SEGMENT()
                seg.from_bytearray(ofs=ofs + seg_ofs, src=src[seg_ofs:seg_ofs + int(self.ARCHIVE_SEG_SIZE)])
                self.ARCHIVE_SEGMENT_LIST.append(seg)
                seg_ofs += int(self.ARCHIVE_SEG_SIZE)

                self.temp_name_idx_list.append(int(seg.NAME_IDX))

            self.PADDING = src[seg_ofs:seg_ofs + get_table_padding_count(seg_ofs)]
            self.PADDING_ofs = ofs + seg_ofs

        def to_bytearray(self) -> bytearray:
            part_A: bytearray = (
                        self.SIGNATURE.to_bytearray() +
                        self.TABLE_SIZE.to_bytearray() +
                        self.ARCHIVE_SEG_COUNT.to_bytearray() +
                        self.ARCHIVE_SEG_SIZE.to_bytearray() +
                        self.unknown_1
                    )

            part_B = bytearray()
            for seg in self.ARCHIVE_SEGMENT_LIST:
                part_B += seg.to_bytearray()

            part_C: bytearray = self.PADDING

            return part_A + part_B + part_C

        class _ARCHIVE_SEGMENT:
            def __init__(self):
                self.NAME_IDX: uint32 = uint32(0)
                self.ZERO: bytearray = bytearray()
                self.ARCHIVE_OFFSET: uint64 = uint64(0)
                self.ARCHIVE_SIZE: uint64 = uint64(0)
                self.HASH: bytearray = bytearray()

                self.NAME_IDX_ofs: int = 0
                self.ZERO_ofs: int = 0
                self.ARCHIVE_OFFSET_ofs: int = 0
                self.ARCHIVE_SIZE_ofs: int = 0
                self.HASH_ofs: int = 0

            def from_bytearray(self, ofs: int, src: bytearray):
                self.NAME_IDX.from_bytearray(src[:4])
                self.NAME_IDX_ofs = ofs

                self.ZERO = src[4:8]
                self.ZERO_ofs = ofs + 4

                self.ARCHIVE_OFFSET.from_bytearray(src[8:16])
                self.ARCHIVE_OFFSET_ofs = ofs + 8

                self.ARCHIVE_SIZE.from_bytearray(src[16:24])
                self.ARCHIVE_SIZE_ofs = ofs + 16

                self.HASH = src[24:40]
                self.HASH_ofs = ofs + 24

            def to_bytearray(self) -> bytearray:
                return (
                    self.NAME_IDX.to_bytearray() +
                    self.ZERO +
                    self.ARCHIVE_OFFSET.to_bytearray() +
                    self.ARCHIVE_SIZE.to_bytearray() +
                    self.HASH
                )

    class _GENESTRT:
        def __init__(self):
            self.SIGNATURE: chararray = chararray(size=8)
            self.TABLE_SIZE_1: uint64 = uint64(0)
            self.FILENAME_COUNT: uint32 = uint32(0)
            self.unknown_1: bytearray = bytearray()
            self.FILE_NAMES_OFFSET: uint32 = uint32(0)
            self.TABLE_SIZE_2: uint32 = uint32(0)
            self.FILENAME_OFFSET_LIST: list[uint32] = list()
            self.FILENAME_OFFSET_LIST_PADDING: bytearray = bytearray()
            self.FILE_NAMES: list[str] = list()
            self.PADDING: bytearray = bytearray()

            self.SIGNATURE_ofs: int = 0
            self.TABLE_SIZE_1_ofs: int = 0
            self.FILENAME_COUNT_ofs: int = 0
            self.unknown_1_ofs: int = 0
            self.FILE_NAMES_OFFSET_ofs: int = 0
            self.TABLE_SIZE_2_ofs: int = 0
            self.FILENAME_OFFSET_LIST_ofs: int = 0
            self.FILENAME_OFFSET_LIST_PADDING_ofs: int = 0
            self.FILE_NAMES_ofs: int = 0
            self.PADDING_ofs: int = 0

            self.FILE_NAMES_SIZE: int = 0

        def from_bytearray(self, ofs: int, src: bytearray):
            self.SIGNATURE.from_bytearray(src[:8])
            self.SIGNATURE_ofs = ofs
            if str(self.SIGNATURE) != "GENESTRT":
                raise TableException(self, f"SIGNATURE must be 'GENESTRT'.  this={str(self.SIGNATURE)}")

            self.TABLE_SIZE_1.from_bytearray(src[8:16])
            self.TABLE_SIZE_1_ofs = ofs + 8
            if len(src) != int(self.TABLE_SIZE_1) + 16:
                raise TableException(self, f"The table size mismatch.  this={len(src)} expected={int(self.TABLE_SIZE_1) + 16}")

            self.FILENAME_COUNT.from_bytearray(src[16:20])
            self.FILENAME_COUNT_ofs = ofs + 16

            self.unknown_1 = src[20:24]
            self.unknown_1_ofs = ofs + 20

            self.FILE_NAMES_OFFSET.from_bytearray(src[24:28])
            self.FILE_NAMES_OFFSET_ofs = ofs + 24

            self.TABLE_SIZE_2.from_bytearray(src[28:32])
            self.TABLE_SIZE_2_ofs = ofs + 28
            if int(self.TABLE_SIZE_1) != int(self.TABLE_SIZE_2):
                raise TableException(self, f"The TABLE_SIZE_2 mismatch.  this={int(self.TABLE_SIZE_2)} expected={int(self.TABLE_SIZE_1)}")

            seg_ofs = 32
            self.FILENAME_OFFSET_LIST_ofs = ofs + 32
            for i in range(int(self.FILENAME_COUNT)):
                self.FILENAME_OFFSET_LIST.append(uint32(src[seg_ofs:seg_ofs + 4]))
                seg_ofs += 4

            self.FILENAME_OFFSET_LIST_PADDING = src[seg_ofs:seg_ofs + get_table_padding_count(seg_ofs)]
            self.FILENAME_OFFSET_LIST_PADDING_ofs = ofs + seg_ofs

            seg_ofs += len(self.FILENAME_OFFSET_LIST_PADDING)
            self.FILE_NAMES_ofs = ofs + seg_ofs
            for i in range(int(self.FILENAME_COUNT)):
                filename: bytearray = bytearray()
                while True:
                    filename += src[seg_ofs:seg_ofs + 1]
                    self.FILE_NAMES_SIZE += len(filename)
                    seg_ofs += 1
                    if filename[-1] == 0:
                        break
                self.FILE_NAMES.append(filename.decode("ascii"))

            self.PADDING = src[seg_ofs:seg_ofs + get_table_padding_count(seg_ofs)]
            self.PADDING_ofs = ofs + seg_ofs

        def to_bytearray(self) -> bytearray:
            partA = (
                        self.SIGNATURE.to_bytearray() +
                        self.TABLE_SIZE_1.to_bytearray() +
                        self.FILENAME_COUNT.to_bytearray() +
                        self.unknown_1 +
                        self.FILE_NAMES_OFFSET.to_bytearray() +
                        self.TABLE_SIZE_2.to_bytearray()
                    )

            partB = bytearray()
            for o in self.FILENAME_OFFSET_LIST:
                partB += o.to_bytearray()

            partC = self.FILENAME_OFFSET_LIST_PADDING

            partD = bytearray()
            for s in self.FILE_NAMES:
                partD += bytearray(s.encode("ascii"))

            partE = self.PADDING

            return partA + partB + partC + partD + partE

    class _GENEEOF:
        def __init__(self):
            self.SIGNATURE: chararray = chararray(size=8)
            self.TABLE_SIZE: uint64 = uint64(0)
            self.TABLE_END_PADDING: bytearray = bytearray()

            self.SIGNATURE_ofs: int = 0
            self.TABLE_SIZE_ofs: int = 0
            self.TABLE_END_PADDING_ofs: int = 0

        def from_bytearray(self, ofs: int, src: bytearray):
            self.SIGNATURE.from_bytearray(src[:8])
            self.SIGNATURE_ofs = ofs
            if str(self.SIGNATURE) != "GENEEOF ":
                raise TableException(self, f"SIGNATURE must be 'GENEEOF '.  this={str(self.SIGNATURE)}")

            self.TABLE_SIZE.from_bytearray(src[8:16])
            self.TABLE_SIZE_ofs = ofs + 8
            if int(self.TABLE_SIZE) != 0:
                raise TableException(self, f"TABLE_SIZE must be 0.  this={int(self.TABLE_SIZE)}")

            self.TABLE_END_PADDING = src[16:]
            self.TABLE_END_PADDING_ofs = ofs + 16

        def to_bytearray(self) -> bytearray:
            return (
                        self.SIGNATURE.to_bytearray() +
                        self.TABLE_SIZE.to_bytearray() +
                        self.TABLE_END_PADDING
                    )

    class _FILE:
        def __init__(self):
            self.DATA: bytearray = bytearray()
            self.PADDING: bytearray = bytearray()

            self.DATA_ofs: int = 0
            self.PADDING_ofs: int = 0

        def from_bytearray(self, ofs: int, size: int, src: bytearray):
            self.DATA = src[:size]
            self.DATA_ofs = ofs

            self.PADDING = src[size:]
            self.PADDING_ofs = ofs + size

        def to_bytearray(self) -> bytearray:
            return self.DATA + self.PADDING

    class _ROOT_FILES:
        def __init__(self):
            self.FILE_LIST: list[APK._FILE] = list()
            self.PADDING: bytearray = bytearray()

            self.PADDING_ofs: int = 0

        def add_from_bytearray(self, ofs: int, size: int, src: bytearray):
            file = APK._FILE()
            file.from_bytearray(ofs, size, src)
            self.FILE_LIST.append(file)

        def to_bytearray(self) -> bytearray:
            result = bytearray()

            for file in self.FILE_LIST:
                result += file.to_bytearray()

            result += self.PADDING

            return result

        def sort(self):
            self.FILE_LIST.sort(key=lambda x: x.DATA_ofs)

    class _ARCHIVE_FILES:
        def __init__(self):
            self.FILE_LIST: list[APK._FILE] = list()
            self.PADDING: bytearray = bytearray()

            self.PADDING_ofs: int = 0

        def add_from_bytearray(self, ofs: int, size: int, src: bytearray, seg):
            file = APK._FILE()
            file.from_bytearray(ofs, size, src)
            self.FILE_LIST.append(file)

        def to_bytearray(self) -> bytearray:
            result = bytearray()

            for file in self.FILE_LIST:
                result += file.to_bytearray()

            return result

        def sort(self):
            self.FILE_LIST.sort(key=lambda x: x.DATA_ofs)

    class _PACKFSHD:
        def __init__(self):
            self.SIGNATURE: chararray = chararray(size=8)
            self.TABLE_SIZE: uint64 = uint64(0)
            self.unknown_1: bytearray = bytearray()
            self.FILE_SEG_SIZE_1: uint32 = uint32(0)
            self.FILE_SEG_COUNT: uint32 = uint32(0)
            self.FILE_SEG_SIZE_2: uint32 = uint32(0)
            self.unknown_2: bytearray = bytearray()
            self.unknown_3: bytearray = bytearray()
            self.FILE_SEGMENT_LIST: list[APK._PACKFSHD.ARCHIVE_FILE_SEGMENT] = []
            self.PADDING: bytearray = bytearray()

            self.SIGNATURE_ofs: int = 0
            self.TABLE_SIZE_ofs: int = 0
            self.unknown_1_ofs: int = 0
            self.FILE_SEG_SIZE_1_ofs: int = 0
            self.FILE_SEG_COUNT_ofs: int = 0
            self.FILE_SEG_SIZE_2_ofs: int = 0
            self.unknown_2_ofs: int = 0
            self.unknown_3_ofs: int = 0
            self.FILE_SEGMENT_LIST_ofs: int = 0
            self.PADDING_ofs: int = 0

        def from_bytearray(self, ofs: int, src: bytearray):
            self.SIGNATURE.from_bytearray(src[:8])
            self.SIGNATURE_ofs = ofs
            if str(self.SIGNATURE) != "PACKFSHD":
                raise TableException(self, f"SIGNATURE must be 'PACKFSHD'.  this='{str(self.SIGNATURE)}'")

            self.TABLE_SIZE.from_bytearray(src[8:16])
            self.TABLE_SIZE_ofs = ofs + 8
            if len(src) != int(self.TABLE_SIZE) + 16:
                raise TableException(self, f"The table size mismatch.  this={len(src)} expected={int(self.TABLE_SIZE) + 16}")

            self.unknown_1 = src[16:20]
            self.unknown_1_ofs = ofs + 16

            self.FILE_SEG_SIZE_1.from_bytearray(src[20:24])
            self.FILE_SEG_SIZE_1_ofs = ofs + 20
            if int(self.FILE_SEG_SIZE_1) != 32:
                raise TableException(self, f"The FILE_SEG_SIZE_1 mismatch.  this={int(self.FILE_SEG_SIZE_1)}, expected=32")

            self.FILE_SEG_COUNT.from_bytearray(src[24:28])
            self.FILE_SEG_COUNT_ofs = ofs + 24

            self.FILE_SEG_SIZE_2.from_bytearray(src[28:32])
            self.FILE_SEG_SIZE_2_ofs = ofs + 28
            if int(self.FILE_SEG_SIZE_1) != int(self.FILE_SEG_SIZE_2):
                raise TableException(self, f"The FILE_SEG_SIZE_2 mismatch with FILE_SEG_SIZE_1.  this={int(self.FILE_SEG_SIZE_2)}, expected={int(self.FILE_SEG_SIZE_1)}")

            self.unknown_2 = src[32:36]
            self.unknown_2_ofs = ofs + 32

            self.unknown_3 = src[36:48]
            self.unknown_3_ofs = ofs + 36

            seg_ofs = 48
            self.FILE_SEGMENT_LIST_ofs = ofs + 48
            for i in range(int(self.FILE_SEG_COUNT)):
                seg = self.ARCHIVE_FILE_SEGMENT()
                seg.from_bytearray(ofs=ofs + seg_ofs, src=src[seg_ofs:seg_ofs + int(self.FILE_SEG_SIZE_1)])
                self.FILE_SEGMENT_LIST.append(seg)
                seg_ofs += int(self.FILE_SEG_SIZE_1)

            self.PADDING = src[seg_ofs:seg_ofs + get_table_padding_count(seg_ofs)]
            self.PADDING_ofs = ofs + seg_ofs

        def to_bytearray(self) -> bytearray:
            part_A: bytearray = (
                    self.SIGNATURE.to_bytearray() +
                    self.TABLE_SIZE.to_bytearray() +
                    self.unknown_1 +
                    self.FILE_SEG_SIZE_1.to_bytearray() +
                    self.FILE_SEG_COUNT.to_bytearray() +
                    self.FILE_SEG_SIZE_2.to_bytearray() +
                    self.unknown_2 +
                    self.unknown_3
            )

            part_B = bytearray()
            for seg in self.FILE_SEGMENT_LIST:
                part_B += seg.to_bytearray()

            part_C: bytearray = self.PADDING

            return part_A + part_B + part_C

        class ARCHIVE_FILE_SEGMENT:
            def __init__(self):
                self.NAME_IDX: uint32 = uint32(0)
                self.ZIP: uint32 = uint32(0)
                self.FILE_OFFSET: uint64 = uint64(0)  # for file
                self.FILE_SIZE: uint64 = uint64(0)
                self.FILE_ZSIZE: uint64 = uint64(0)

                self.NAME_IDX_ofs: int = 0
                self.ZIP_ofs: int = 0
                self.FILE_OFFSET_ofs: int = 0
                self.FILE_SIZE_ofs: int = 0
                self.FILE_ZSIZE_ofs: int = 0

                self.file_index = -1

            def from_bytearray(self, ofs: int, src: bytearray):
                self.NAME_IDX.from_bytearray(src[:4])
                self.NAME_IDX_ofs = ofs

                self.ZIP.from_bytearray(src[4:8])
                self.ZIP_ofs = ofs + 4

                self.FILE_OFFSET.from_bytearray(src[8:16])
                self.FILE_OFFSET_ofs = ofs + 8

                self.FILE_SIZE.from_bytearray(src[16:24])
                self.FILE_SIZE_ofs = ofs + 16

                self.FILE_ZSIZE.from_bytearray(src[24:32])
                self.FILE_ZSIZE_ofs = ofs + 24

            def to_bytearray(self) -> bytearray:
                return (
                        self.NAME_IDX.to_bytearray() +
                        self.ZIP.to_bytearray() +
                        self.FILE_OFFSET.to_bytearray() +
                        self.FILE_SIZE.to_bytearray() +
                        self.FILE_ZSIZE.to_bytearray()
                )

    class ARCHIVE:
        def __init__(self):
            self.ENDIANNESS = APK._ENDIANNESS()
            self.PACKFSHD = APK._PACKFSHD()
            self.GENESTRT = APK._GENESTRT()
            self.GENEEOF = APK._GENEEOF()
            self.FILES = APK._ARCHIVE_FILES()
            self.PADDING: bytearray = bytearray()

            self.ARCHIVE_ofs: int = 0
            self.PADDING_ofs: int = 0

            self.name_idx: int = -1

        def to_bytearray(self) -> bytearray:
            return (
                        self.ENDIANNESS.to_bytearray() +
                        self.PACKFSHD.to_bytearray() +
                        self.GENESTRT.to_bytearray() +
                        self.GENEEOF.to_bytearray() +
                        self.FILES.to_bytearray() +
                        self.PADDING
                    )

    class _ARCHIVES:
        def __init__(self):
            self.ARCHIVE_LIST: list[APK.ARCHIVE] = list()
            self.PADDING: bytearray = bytearray()

            self.PADDING_ofs: int = 0

        def add_from_object(self, archive: object):
            if not isinstance(archive, APK.ARCHIVE):
                raise TableException(self, f"parameter archive must be instance of APK._ARCHIVE.  this={archive.__class__.__name__}")

            self.ARCHIVE_LIST.append(archive)

        def to_bytearray(self) -> bytearray:
            result = bytearray()

            for archive in self.ARCHIVE_LIST:
                result += archive.to_bytearray()

            return result

        def sort(self):
            self.ARCHIVE_LIST.sort(key=lambda x: x.ARCHIVE_ofs)


class APKReader:
    def __init__(self, INPUT_APK_PATH: str):
        self.__INPUT_APK_PATH = INPUT_APK_PATH
        self.__APK = APK()
        self.__original_md5 = None

    def read(self):
        with open(self.__INPUT_APK_PATH, "rb") as f:
            reader = BinaryReader(bytearray(f.read()))
            reader.seek(0)

        self.__original_md5 = hashlib.md5(reader.get_raw()).hexdigest()

        print("Reading ENDIANNESS table...")
        self.__APK.ENDIANNESS.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=16))

        print("Reading PACKHEDR table...")
        self.__APK.PACKHEDR.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=48))

        print("Reading PACKTOC table...")
        tmp = reader.tell()
        reader.skip(8)
        size = int(uint64(reader.get_bytes(8))) + 16
        reader.seek(tmp)
        self.__APK.PACKTOC.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=size))

        print("Reading PACKFSLS table...")
        tmp = reader.tell()
        reader.skip(8)
        size = int(uint64(reader.get_bytes(8))) + 16
        reader.seek(tmp)
        self.__APK.PACKFSLS.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=size))

        print("Reading GENESTRT table...")
        tmp = reader.tell()
        reader.skip(8)
        size = int(uint64(reader.get_bytes(8))) + 16
        reader.seek(tmp)
        self.__APK.GENESTRT.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=size))

        print("Reading GENEEOF table...")
        size = get_table_end_padding_count(reader.tell() + 16) + 16
        self.__APK.GENEEOF.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=size))

        print("Reading ROOT files...")
        tmp = reader.tell()
        root_files_size = 0
        if len(self.__APK.PACKTOC.TOC_SEGMENT_LIST) > 0:
            for seg in self.__APK.PACKTOC.TOC_SEGMENT_LIST:
                if int(seg.IDENTIFIER) == 1:
                    continue
                reader.seek(int(seg.FILE_OFFSET))
                if int(seg.IDENTIFIER) == 0:  # raw file
                    filesize = int(seg.FILE_SIZE)
                elif int(seg.IDENTIFIER) == 512:  # zlib compressed file
                    filesize = int(seg.FILE_ZSIZE)
                else:
                    filesize = None
                block_size = filesize + get_root_file_padding_cnt(filesize)
                root_files_size += block_size

                self.__APK.ROOT_FILES.add_from_bytearray(ofs=int(seg.FILE_OFFSET), size=filesize, src=reader.get_bytes(block_size))

            self.__APK.ROOT_FILES.sort()

            ofs_list = [int(x.DATA_ofs) for x in self.__APK.ROOT_FILES.FILE_LIST]

            for seg in self.__APK.PACKTOC.TOC_SEGMENT_LIST:
                if int(seg.IDENTIFIER) == 1:
                    continue
                seg.file_index = ofs_list.index(int(seg.FILE_OFFSET))

        reader.seek(tmp + root_files_size)
        if reader.EOF():
            return

        self.__APK.ROOT_FILES.PADDING_ofs = reader.tell()
        self.__APK.ROOT_FILES.PADDING = reader.get_bytes(get_root_files_padding_count(root_files_size))

        if reader.EOF():
            raise TableException(self, f"If ROOT_FILES_PADDING exists, EOF cannot appear")

        for idx, seg in enumerate(self.__APK.PACKFSLS.ARCHIVE_SEGMENT_LIST):
            print(f"Reading archive {idx + 1}/{len(self.__APK.PACKFSLS.ARCHIVE_SEGMENT_LIST)}...")
            archive = self.__APK.ARCHIVE()
            archive.name_idx = int(seg.NAME_IDX)
            ARCHIVE_OFFSET = int(seg.ARCHIVE_OFFSET)
            ARCHIVE_SIZE = int(seg.ARCHIVE_SIZE)

            archive.ARCHIVE_ofs = int(seg.ARCHIVE_OFFSET)

            reader.seek(ARCHIVE_OFFSET)

            print(f"    Reading ENDIANNESS table...")
            archive.ENDIANNESS.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=16))

            print(f"    Reading PACKFSHD table...")
            tmp = reader.tell()
            reader.skip(8)
            size = int(uint64(reader.get_bytes(8))) + 16
            reader.seek(tmp)
            archive.PACKFSHD.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=size))

            print(f"    Reading GENESTRT table...")
            tmp = reader.tell()
            reader.skip(8)
            size = int(uint64(reader.get_bytes(8))) + 16
            reader.seek(tmp)
            archive.GENESTRT.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=size))

            print(f"    Reading GENEEOF table...")
            archive.GENEEOF.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=16))

            print(f"    Reading files...")
            tmp = reader.tell()
            archive_files_size = 0
            if len(archive.PACKFSHD.FILE_SEGMENT_LIST) > 0:
                for file_seg in archive.PACKFSHD.FILE_SEGMENT_LIST:
                    real_file_offset = ARCHIVE_OFFSET + int(file_seg.FILE_OFFSET)
                    reader.seek(real_file_offset)

                    if int(file_seg.ZIP) == 0:  # raw file
                        filesize = int(file_seg.FILE_SIZE)
                    elif int(file_seg.ZIP) == 2:  # zlib compressed file
                        filesize = int(file_seg.FILE_ZSIZE)
                    else:
                        filesize = None

                    block_size = filesize + get_archive_file_padding_cnt(filesize)
                    archive_files_size += block_size

                    archive.FILES.add_from_bytearray(ofs=real_file_offset, size=filesize, src=reader.get_bytes(block_size), seg=file_seg)

                archive.FILES.sort()

                ofs_list = [int(x.DATA_ofs) for x in archive.FILES.FILE_LIST]

                for fseg in archive.PACKFSHD.FILE_SEGMENT_LIST:
                    fseg.file_index = ofs_list.index(int(fseg.FILE_OFFSET) + ARCHIVE_OFFSET)

            reader.seek(tmp + archive_files_size)

            if not reader.EOF():
                size = get_archive_padding_count(int(self.__APK.PACKHEDR.ARCHIVE_PADDING_TYPE), ARCHIVE_SIZE)
                archive.PADDING_ofs = reader.tell()
                archive.PADDING = reader.get_bytes(size=size)

            self.__APK.ARCHIVES.add_from_object(archive)

        self.__APK.ARCHIVES.sort()

        for name_idx in self.__APK.PACKFSLS.temp_name_idx_list:
            archive_name = self.__APK.GENESTRT.FILE_NAMES[int(name_idx)][:-1]

            archive = None
            for x in self.__APK.ARCHIVES.ARCHIVE_LIST:
                if x.name_idx == name_idx:
                    archive = x
                    break

            if archive is None:
                raise Exception("archive not found")

            self.__APK.PACKFSLS.NAME_ARCHIVE_MAP[archive_name] = archive

    def get_apk(self) -> APK:
        return self.__APK

    def get_original_md5(self) -> str:
        return self.__original_md5

    def update_offsets(self):
        NEW_OFFSET: int = -1

        if len(self.__APK.PACKTOC.TOC_SEGMENT_LIST) > 0:
            toc_seg_list = sorted(
                [seg for seg in self.__APK.PACKTOC.TOC_SEGMENT_LIST if int(seg.IDENTIFIER) != 1],
                key=lambda seg: int(seg.FILE_OFFSET)
            )

            if len(toc_seg_list) > 0:
                NEW_OFFSET = int(toc_seg_list[0].FILE_OFFSET)

                tmp_seg = toc_seg_list[0]
                file_index = tmp_seg.file_index
                NEW_OFFSET += len(self.__APK.ROOT_FILES.FILE_LIST[file_index].DATA)
                NEW_OFFSET += len(self.__APK.ROOT_FILES.FILE_LIST[file_index].PADDING)

                for seg in toc_seg_list[1:]:  # offset of first file is never change
                    file_index = seg.file_index
                    seg.FILE_OFFSET = uint64(NEW_OFFSET)
                    NEW_OFFSET += len(self.__APK.ROOT_FILES.FILE_LIST[file_index].DATA)
                    NEW_OFFSET += len(self.__APK.ROOT_FILES.FILE_LIST[file_index].PADDING)

        if len(self.__APK.ARCHIVES.ARCHIVE_LIST) > 0:
            for i, archive in enumerate(self.__APK.ARCHIVES.ARCHIVE_LIST):
                print("=======================")
                old_offset = int(archive.ARCHIVE_ofs)
                if NEW_OFFSET == -1:
                    NEW_OFFSET = int(archive.ARCHIVE_ofs)

                archive_seg = [x for x in self.__APK.PACKFSLS.ARCHIVE_SEGMENT_LIST if int(x.ARCHIVE_OFFSET) == old_offset][0]
                archive_seg.ARCHIVE_OFFSET = uint64(NEW_OFFSET)

                seg_list = sorted(
                    [seg for seg in archive.PACKFSHD.FILE_SEGMENT_LIST],
                    key=lambda seg: int(seg.FILE_OFFSET)
                )

                NEW_FILE_OFFSET: int = int(seg_list[0].FILE_OFFSET)

                tmp_seg = seg_list[0]
                file_index = tmp_seg.file_index
                NEW_FILE_OFFSET += len(archive.FILES.FILE_LIST[file_index].DATA)
                NEW_FILE_OFFSET += len(archive.FILES.FILE_LIST[file_index].PADDING)
                print(NEW_FILE_OFFSET)

                for seg in seg_list[1:]:
                    file_index = seg.file_index
                    seg.FILE_OFFSET = uint64(NEW_FILE_OFFSET)
                    NEW_FILE_OFFSET += len(archive.FILES.FILE_LIST[file_index].DATA)
                    NEW_FILE_OFFSET += len(archive.FILES.FILE_LIST[file_index].PADDING)

                if i + 1 < len(self.__APK.ARCHIVES.ARCHIVE_LIST):  # make padding without last archive
                    archive.PADDING = bytearray(0)
                    new_archive_size = len(archive.to_bytearray())
                    archive_seg.ARCHIVE_SIZE = uint64(new_archive_size)

                    new_padding_cnt = get_archive_padding_count(int(self.__APK.PACKHEDR.ARCHIVE_PADDING_TYPE), int(archive_seg.ARCHIVE_SIZE))
                    archive.PADDING = bytearray(new_padding_cnt)
                    NEW_OFFSET += new_archive_size + new_padding_cnt


class TableException(Exception):
    def __init__(self, table: object, message: str):
        table_name = table.__class__.__name__
        self.message = f"table {table_name}: {message}"
        super().__init__(self.message)
