import hashlib

from datatype.chararray import chararray
from datatype.uint32 import uint32
from datatype.uint64 import uint64
from utils.BinaryManager import BinaryReader
from utils.Utils import get_table_padding_count


class IDX:

    def __init__(self):
        self.ENDIANNESS = self._ENDIANNESS()
        self.PACKHEDR_LIST = self.PACKHEDR_LIST()
        self.PACKTOC = self._PACKTOC()
        self.PACKFSLS = self._PACKFSLS()
        self.GENESTRT = self._GENESTRT()
        self.GENEEOF = self._GENEEOF()

    def to_bytearray(self) -> bytearray:
        return (
                    self.ENDIANNESS.to_bytearray() +
                    self.PACKHEDR_LIST.to_bytearray() +
                    self.PACKTOC.to_bytearray() +
                    self.PACKFSLS.to_bytearray() +
                    self.GENESTRT.to_bytearray() +
                    self.GENEEOF.to_bytearray()
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
            self.NAME_IDX: uint32 = uint32()
            self.FILE_LIST_OFFSET: uint32 = uint32(0)
            self.ARCHIVE_PADDING_TYPE: uint32 = uint32(0)
            self.HASH: bytearray = bytearray()

            self.SIGNATURE_ofs: int = 0
            self.TABLE_SIZE_ofs: int = 0
            self.unknown_1_ofs: int = 0
            self.NAME_IDX_ofs: int = 0
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

            self.unknown_1 = src[16:20]
            self.unknown_1_ofs = ofs + 16

            self.NAME_IDX = uint32(src[20:24])
            self.NAME_IDX_ofs = ofs + 20

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
                        self.NAME_IDX.to_bytearray() +
                        self.FILE_LIST_OFFSET.to_bytearray() +
                        self.ARCHIVE_PADDING_TYPE.to_bytearray() +
                        self.HASH
                    )

    class PACKHEDR_LIST:
        def __init__(self):
            self.PACKHEDR_LIST: list[IDX._PACKHEDR] = list()
            self.PADDING: bytearray = bytearray()

            self.PADDING_ofs: int = 0

        def add_from_bytearray(self, ofs: int, src: bytearray):
            packhedr = IDX._PACKHEDR()
            packhedr.from_bytearray(ofs, src)
            self.PACKHEDR_LIST.append(packhedr)

        def to_bytearray(self) -> bytearray:
            result = bytearray()

            for packhedr in self.PACKHEDR_LIST:
                result += packhedr.to_bytearray()

            return result

    class _PACKTOC:
        def __init__(self):
            self.SIGNATURE: chararray = chararray(size=8)
            self.TABLE_SIZE: uint64 = uint64(0)
            self.TOC_SEG_SIZE: uint32 = uint32(0)
            self.TOC_SEG_COUNT: uint32 = uint32(0)
            self.unknown_1: bytearray = bytearray()
            self.TOC_SEGMENT_LIST: list[IDX._PACKTOC._TOC_SEGMENT] = []
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
                if int(self.IDENTIFIER) == 1:
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
            self.ARCHIVE_SEGMENT_LIST: list[IDX._PACKFSLS._ARCHIVE_SEGMENT] = list()
            self.PADDING: bytearray = bytearray()

            self.SIGNATURE_ofs: int = 0
            self.TABLE_SIZE_ofs: int = 0
            self.ARCHIVE_SEG_COUNT_ofs: int = 0
            self.ARCHIVE_SEG_SIZE_ofs: int = 0
            self.unknown_1_ofs: int = 0
            self.ARCHIVE_SEGMENT_LIST_ofs: int = 0
            self.PADDING_ofs: int = 0

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

            self.SIGNATURE_ofs: int = 0
            self.TABLE_SIZE_ofs: int = 0

        def from_bytearray(self, ofs: int, src: bytearray):
            self.SIGNATURE.from_bytearray(src[:8])
            self.SIGNATURE_ofs = ofs
            if str(self.SIGNATURE) != "GENEEOF ":
                raise TableException(self, f"SIGNATURE must be 'GENEEOF '.  this={str(self.SIGNATURE)}")

            self.TABLE_SIZE.from_bytearray(src[8:16])
            self.TABLE_SIZE_ofs = ofs + 8
            if int(self.TABLE_SIZE) != 0:
                raise TableException(self, f"TABLE_SIZE must be 0.  this={int(self.TABLE_SIZE)}")

        def to_bytearray(self) -> bytearray:
            return (
                        self.SIGNATURE.to_bytearray() +
                        self.TABLE_SIZE.to_bytearray()
                    )


class IDXReader:
    def __init__(self, INPUT_IDX_PATH: str):
        self.__INPUT_IDX_PATH = INPUT_IDX_PATH
        self.__IDX = IDX()
        self.__original_md5 = None
    
    def read(self):
        with open(self.__INPUT_IDX_PATH, "rb") as f:
            reader = BinaryReader(bytearray(f.read()))
            reader.seek(0)

        self.__original_md5 = hashlib.md5(reader.get_raw()).hexdigest()

        print("Reading ENDIANNESS table...")
        self.__IDX.ENDIANNESS.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=16))

        print("Reading PACKHEDR table...")
        while True:
            tmp = reader.tell()
            if reader.get_bytes(8).decode("ascii") != "PACKHEDR":
                reader.seek(tmp)
                break
            reader.seek(tmp)
            self.__IDX.PACKHEDR_LIST.add_from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=48))

        print("Reading PACKTOC table...")
        tmp = reader.tell()
        reader.skip(8)
        size = int(uint64(reader.get_bytes(8))) + 16
        reader.seek(tmp)
        self.__IDX.PACKTOC.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=size))

        print("Reading PACKFSLS table...")
        tmp = reader.tell()
        reader.skip(8)
        size = int(uint64(reader.get_bytes(8))) + 16
        reader.seek(tmp)
        self.__IDX.PACKFSLS.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=size))

        print("Reading GENESTRT table...")
        tmp = reader.tell()
        reader.skip(8)
        size = int(uint64(reader.get_bytes(8))) + 16
        reader.seek(tmp)
        self.__IDX.GENESTRT.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=size))

        print("Reading GENEEOF table...")
        self.__IDX.GENEEOF.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=16))

    def get_apk(self) -> IDX:
        return self.__IDX

    def get_original_md5(self) -> str:
        return self.__original_md5


class TableException(Exception):
    def __init__(self, table: object, message: str):
        table_name = table.__class__.__name__
        self.message = f"table {table_name}: {message}"
        super().__init__(self.message)
