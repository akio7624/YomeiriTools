import hashlib
import os
from io import StringIO

from prettytable import PrettyTable

from datatype.uint64 import uint64
from utils.BinaryManager import BinaryReader
from parser.idx import IDX, IDXReader
from utils.ProgramInfo import *
from utils.Utils import *


class DumpIdx:
    def __init__(self, i: str, o: str, t: str, q: bool):
        self.INPUT_IDX_PATH: str = i
        self.OUTPUT_DUMP_PATH: str = o
        self.DUMP_TYPE: str = "table" if t == "table" else "json"
        self.IS_QUIET: bool = q
        self.IDX = IDX()
        self.file_size = 0

        self.__original_md5 = None
        self.__dumped_md5 = None

    def dump(self, debug_no_dump: bool = False):
        idx_reader = IDXReader(self.INPUT_IDX_PATH)
        idx_reader.read()
        self.IDX = idx_reader.get_apk()

        self.__original_md5 = idx_reader.get_original_md5()
        self.__dumped_md5 = hashlib.md5(self.IDX.to_bytearray()).hexdigest()

        if self.__original_md5 != self.__dumped_md5:
            print("Warning! The original file and the dumped file do not match. The dump results may be inaccurate.")
            print(f"{self.__original_md5} != {self.__dumped_md5}")

        if debug_no_dump:
            return

        if self.DUMP_TYPE == "table":
            self.dump_table()
        elif self.DUMP_TYPE == "json":
            print(f"JSON dumps are not supported yet.")
            pass  # TODO self.dump_json()

    def dump_table(self):
        print("Start dumping...")

        result = StringIO()
        result.write(f"# File Name: {self.INPUT_IDX_PATH}\n")
        result.write(f"# Dump Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        result.write(f"# Dump Tools: {TOOL_NAME} v{TOOL_VERSION} dump_apk\n")
        result.write(f"# File Size: {self.file_size} bytes\n")
        result.write(f"# File Format: APK\n")
        result.write(f"# File Endian: Little-endian\n")
        result.write("\n\n\n")

        table = PrettyTable()
        table.field_names = ["Name", "Type", "Size", "Value", "Value(hex)", "Offset", "Description"]
        table.align["Description"] = "l"
        table.align["Value"] = "l"
        table.align["Value(hex)"] = "l"

        print("Dumping ENDIANNESS table...")
        result.write("* ENDIANNESS table\n")
        table.add_row(["SIGNATURE", "char[]", 8, str(self.IDX.ENDIANNESS.SIGNATURE), bytes2hex(self.IDX.ENDIANNESS.SIGNATURE.to_bytearray()), hexoffset(self.IDX.ENDIANNESS.SIGNATURE_ofs), "-"])
        table.add_row(["TABLE SIZE", "uint64", 8, int(self.IDX.ENDIANNESS.TABLE_SIZE), bytes2hex(self.IDX.ENDIANNESS.TABLE_SIZE.to_bytearray()), hexoffset(self.IDX.ENDIANNESS.TABLE_SIZE_ofs), "-"])
        result.write(str(table))
        table.clear_rows()

        result.write("\n\n\n")

        print("Dumping PACKHEDR table...")
        for idx, packhedr in enumerate(self.IDX.PACKHEDR_LIST.PACKHEDR_LIST):
            result.write(f"* PACKHEDR table #{idx}\n")
            table.add_row(["SIGNATURE", "char[]", 8, str(packhedr.SIGNATURE), bytes2hex(packhedr.SIGNATURE.to_bytearray()), hexoffset(packhedr.SIGNATURE_ofs), "-"])
            table.add_row(["TABLE SIZE", "uint64", 8, int(packhedr.TABLE_SIZE), bytes2hex(packhedr.TABLE_SIZE.to_bytearray()), hexoffset(packhedr.TABLE_SIZE_ofs), "-"])
            table.add_row(["unknown 1", "-", 8, "-", bytes2hex(packhedr.unknown_1), hexoffset(packhedr.unknown_1_ofs), "-"])
            table.add_row(["FILE LIST OFFSET", "uint32", 4, int(packhedr.FILE_LIST_OFFSET), bytes2hex(packhedr.FILE_LIST_OFFSET.to_bytearray()), hexoffset(packhedr.FILE_LIST_OFFSET_ofs), "-"])
            table.add_row(["ARCHIVE PADDING TYPE", "uint32", 4, int(packhedr.ARCHIVE_PADDING_TYPE), bytes2hex(packhedr.ARCHIVE_PADDING_TYPE.to_bytearray()), hexoffset(packhedr.ARCHIVE_PADDING_TYPE_ofs), archive_padding_type2desc(int(packhedr.ARCHIVE_PADDING_TYPE))])
            table.add_row(["HASH", "byte[]", 16, "-", bytes2hex(packhedr.HASH), hexoffset(packhedr.HASH_ofs), "-"])
            result.write(str(table))
            table.clear_rows()
            result.write("\n\n")

        result.write("\n\n\n")

        print("Dumping PACKTOC table...")
        result.write("* PACKTOC table\n")
        table.add_row(["SIGNATURE", "char[]", 8, str(self.IDX.PACKTOC.SIGNATURE), bytes2hex(self.IDX.PACKTOC.SIGNATURE.to_bytearray()), hexoffset(self.IDX.PACKTOC.SIGNATURE_ofs), "-"])
        table.add_row(["TABLE SIZE", "uint64", 8, int(self.IDX.PACKTOC.TABLE_SIZE), bytes2hex(self.IDX.PACKTOC.TABLE_SIZE.to_bytearray()), hexoffset(self.IDX.PACKTOC.TABLE_SIZE_ofs), "-"])
        table.add_row(["TOC SEG SIZE", "uint32", 4, int(self.IDX.PACKTOC.TOC_SEG_SIZE), bytes2hex(self.IDX.PACKTOC.TOC_SEG_SIZE.to_bytearray()), hexoffset(self.IDX.PACKTOC.TOC_SEG_SIZE_ofs), "-"])
        table.add_row(["TOC SEG COUNT", "uint32", 4, int(self.IDX.PACKTOC.TOC_SEG_COUNT), bytes2hex(self.IDX.PACKTOC.TOC_SEG_COUNT.to_bytearray()), hexoffset(self.IDX.PACKTOC.TOC_SEG_COUNT_ofs), "-"])
        table.add_row(["unknown 1", "-", 8, "-", bytes2hex(self.IDX.PACKTOC.unknown_1), hexoffset(self.IDX.PACKTOC.unknown_1_ofs), "-"])
        table.add_row(["TOC SEG LIST", "TOC_SEGMENT[]", int(self.IDX.PACKTOC.TOC_SEG_SIZE) * int(self.IDX.PACKTOC.TOC_SEG_COUNT), "-", "-", hexoffset(self.IDX.PACKTOC.TOC_SEGMENT_LIST_ofs), "-"])
        table.add_row(["PADDING", "byte[]", len(self.IDX.PACKTOC.PADDING), "-", bytes2hex(self.IDX.PACKTOC.PADDING), hexoffset(self.IDX.PACKTOC.PADDING_ofs), "-"])
        result.write(str(table))
        table.clear_rows()

        result.write("\n\n")

        print("Dumping TOC SEGMENT...")
        if int(self.IDX.PACKTOC.TOC_SEG_COUNT) != 0:
            result.write("    * TOC SEGMENT list\n")
            for i in range(int(self.IDX.PACKTOC.TOC_SEG_COUNT)):
                seg = self.IDX.PACKTOC.TOC_SEGMENT_LIST[i]

                result.write(f"    [{i}]\n")
                table.add_row(["IDENTIFIER", "uint32", 4, int(seg.IDENTIFIER), bytes2hex(seg.IDENTIFIER.to_bytearray()), hexoffset(seg.IDENTIFIER_ofs), identifier2desc(int(seg.IDENTIFIER))])
                table.add_row(["NAME IDX", "uint32", 4, int(seg.NAME_IDX), bytes2hex(seg.NAME_IDX.to_bytearray()), hexoffset(seg.NAME_IDX_ofs), "-"])
                table.add_row(["ZERO", "byte[]", len(seg.ZERO), 8, bytes2hex(seg.ZERO), hexoffset(seg.ZERO_ofs), "-"])
                if int(seg.IDENTIFIER) == 1:  # if directory
                    table.add_row(["ENTRY INDEX", "uint32", 4, int(seg.ENTRY_INDEX), bytes2hex(seg.ENTRY_INDEX.to_bytearray()), hexoffset(seg.ENTRY_INDEX_ofs), "-"])
                    table.add_row(["ENTRY COUNT", "uint32", 4, int(seg.ENTRY_COUNT), bytes2hex(seg.ENTRY_COUNT.to_bytearray()), hexoffset(seg.ENTRY_COUNT_ofs), "-"])
                else:  # if file
                    table.add_row(["FILE OFFSET", "uint64", 8, int(seg.FILE_OFFSET), bytes2hex(seg.FILE_OFFSET.to_bytearray()), hexoffset(seg.FILE_OFFSET_ofs), "-"])
                table.add_row(["FILE SIZE", "uint64", 8, int(seg.FILE_SIZE), bytes2hex(seg.FILE_SIZE.to_bytearray()), hexoffset(seg.FILE_SIZE_ofs), "-"])
                table.add_row(["FILE ZSIZE", "uint64", 8, int(seg.FILE_ZSIZE), bytes2hex(seg.FILE_ZSIZE.to_bytearray()), hexoffset(seg.FILE_ZSIZE_ofs), "-"])
                result.write("\n".join(["    " + line for line in str(table).splitlines()]))
                result.write("\n\n")
                table.clear_rows()
                # if i > 20:
                #     break  # for test

        result.write("\n\n\n")

        print("Dumping PACKFSLS table...")
        result.write("* PACKFSLS table\n")
        table.add_row(["SIGNATURE", "char[]", 8, str(self.IDX.PACKFSLS.SIGNATURE), bytes2hex(self.IDX.PACKFSLS.SIGNATURE.to_bytearray()), hexoffset(self.IDX.PACKFSLS.SIGNATURE_ofs), "-"])
        table.add_row(["TABLE SIZE", "uint64", 8, int(self.IDX.PACKFSLS.TABLE_SIZE), bytes2hex(self.IDX.PACKFSLS.TABLE_SIZE.to_bytearray()), hexoffset(self.IDX.PACKFSLS.TABLE_SIZE_ofs), "-"])
        table.add_row(["ARCHIVE SEG COUNT", "uint32", 4, int(self.IDX.PACKFSLS.ARCHIVE_SEG_COUNT), bytes2hex(self.IDX.PACKFSLS.ARCHIVE_SEG_COUNT.to_bytearray()), hexoffset(self.IDX.PACKFSLS.ARCHIVE_SEG_COUNT_ofs), "-"])
        table.add_row(["ARCHIVE SEG SIZE", "uint32", 4, int(self.IDX.PACKFSLS.ARCHIVE_SEG_SIZE), bytes2hex(self.IDX.PACKFSLS.ARCHIVE_SEG_SIZE.to_bytearray()), hexoffset(self.IDX.PACKFSLS.ARCHIVE_SEG_SIZE_ofs), "-"])
        table.add_row(["unknown 1", "-", 8, "-", bytes2hex(self.IDX.PACKFSLS.unknown_1), hexoffset(self.IDX.PACKFSLS.unknown_1_ofs), "-"])
        table.add_row(["ARCHIVE SEGMENT LIST", "ARCHIVE_SEGMENT[]", int(self.IDX.PACKFSLS.ARCHIVE_SEG_SIZE) * int(self.IDX.PACKFSLS.ARCHIVE_SEG_COUNT), "-", "-", hexoffset(self.IDX.PACKFSLS.ARCHIVE_SEGMENT_LIST_ofs), "-"])
        table.add_row(["PADDING", "byte[]", len(self.IDX.PACKFSLS.PADDING), "-", bytes2hex(self.IDX.PACKFSLS.PADDING), hexoffset(self.IDX.PACKFSLS.PADDING_ofs), "-"])
        result.write(str(table))
        table.clear_rows()

        result.write("\n\n")

        if int(self.IDX.PACKFSLS.ARCHIVE_SEG_COUNT) != 0:
            print("Dumping ARCHIVE SEGMENT...")
            result.write("    * ARCHIVE SEGMENT list\n")
            for i in range(int(self.IDX.PACKFSLS.ARCHIVE_SEG_COUNT)):
                seg = self.IDX.PACKFSLS.ARCHIVE_SEGMENT_LIST[i]

                result.write(f"    [{i}]\n")
                table.add_row(["NAME IDX", "uint32", 4, int(seg.NAME_IDX), bytes2hex(seg.NAME_IDX.to_bytearray()), hexoffset(seg.NAME_IDX_ofs), "-"])
                table.add_row(["ZERO", "byte[]", len(seg.ZERO), "-", bytes2hex(seg.ZERO), hexoffset(seg.ZERO_ofs), "-"])
                table.add_row(["ARCHIVE OFFSET", "uint64", 8, int(seg.ARCHIVE_OFFSET), bytes2hex(seg.ARCHIVE_OFFSET.to_bytearray()), hexoffset(seg.ARCHIVE_OFFSET_ofs), "-"])
                table.add_row(["ARCHIVE SIZE", "uint64", 8, int(seg.ARCHIVE_SIZE), bytes2hex(seg.ARCHIVE_SIZE.to_bytearray()), hexoffset(seg.ARCHIVE_SIZE_ofs), "-"])
                table.add_row(["HASH", "byte[]", 16, "-", bytes2hex(seg.HASH), hexoffset(seg.HASH_ofs), "-"])
                result.write("\n".join(["    " + line for line in str(table).splitlines()]))
                result.write("\n\n")
                table.clear_rows()

        result.write("\n\n\n")

        print("Dumping GENESTRT table...")
        result.write("* GENESTRT table\n")
        table.add_row(["SIGNATURE", "char[]", 8, str(self.IDX.GENESTRT.SIGNATURE), bytes2hex(self.IDX.GENESTRT.SIGNATURE.to_bytearray()), hexoffset(self.IDX.GENESTRT.SIGNATURE_ofs), "-"])
        table.add_row(["TABLE SIZE 1", "uint64", 8, int(self.IDX.GENESTRT.TABLE_SIZE_1), bytes2hex(self.IDX.GENESTRT.TABLE_SIZE_1.to_bytearray()), hexoffset(self.IDX.GENESTRT.TABLE_SIZE_1_ofs), "-"])
        table.add_row(["FILENAME COUNT", "uint32", 8, int(self.IDX.GENESTRT.FILENAME_COUNT), bytes2hex(self.IDX.GENESTRT.FILENAME_COUNT.to_bytearray()), hexoffset(self.IDX.GENESTRT.FILENAME_COUNT_ofs), "-"])
        table.add_row(["unknown 1", "-", 4, "-", bytes2hex(self.IDX.GENESTRT.unknown_1), hexoffset(self.IDX.GENESTRT.unknown_1_ofs), "-"])
        table.add_row(["FILE NAMES OFFSET", "uint32", 4, int(self.IDX.GENESTRT.FILE_NAMES_OFFSET), bytes2hex(self.IDX.GENESTRT.FILE_NAMES_OFFSET.to_bytearray()), hexoffset(self.IDX.GENESTRT.FILE_NAMES_OFFSET_ofs), "-"])
        table.add_row(["TABLE SIZE 2", "uint32", 4, int(self.IDX.GENESTRT.TABLE_SIZE_2), bytes2hex(self.IDX.GENESTRT.TABLE_SIZE_2.to_bytearray()), hexoffset(self.IDX.GENESTRT.TABLE_SIZE_2_ofs), "-"])
        table.add_row(["FILENAME OFFSET LIST", "uint32[]", len(self.IDX.GENESTRT.FILENAME_OFFSET_LIST) * 4, "-", "-", hexoffset(self.IDX.GENESTRT.FILENAME_OFFSET_LIST_ofs), "-"])
        table.add_row(["FILENAME OFFSET LIST PADDING", "byte[]", len(self.IDX.GENESTRT.FILENAME_OFFSET_LIST_PADDING), "-", bytes2hex(self.IDX.GENESTRT.FILENAME_OFFSET_LIST_PADDING), hexoffset(self.IDX.GENESTRT.FILENAME_OFFSET_LIST_PADDING_ofs), "-"])
        table.add_row(["FILE_NAMES", "string[]", self.IDX.GENESTRT.FILE_NAMES_SIZE, "-", "-", hexoffset(self.IDX.GENESTRT.FILE_NAMES_ofs), "-"])
        table.add_row(["PADDING", "byte[]", len(self.IDX.GENESTRT.PADDING), "-", bytes2hex(self.IDX.GENESTRT.PADDING), hexoffset(self.IDX.GENESTRT.PADDING_ofs), "-"])
        result.write(str(table))
        table.clear_rows()

        result.write("\n\n")

        result.write("    * FILENAME OFFSET and FILENAME (Trailing null character removed)\n")
        file_names_table = PrettyTable()
        file_names_table.field_names = ["INDEX", "FILENAME OFFSET", "FILENAME"]
        file_names_table.align["FILENAME"] = "l"
        for i in range(int(self.IDX.GENESTRT.FILENAME_COUNT)):
            file_names_table.add_row([i, int(self.IDX.GENESTRT.FILENAME_OFFSET_LIST[i]), self.IDX.GENESTRT.FILE_NAMES[i][:-1]])

        for line in str(file_names_table).splitlines():
            result.write("    " + line + "\n")

        result.write("\n\n\n")

        print("Dumping GENEEOF table...")
        result.write("* GENEEOF table\n")
        table.add_row(["SIGNATURE", "char[]", 8, str(self.IDX.GENEEOF.SIGNATURE), bytes2hex(self.IDX.GENEEOF.SIGNATURE.to_bytearray()), hexoffset(self.IDX.GENEEOF.SIGNATURE_ofs), "-"])
        table.add_row(["TABLE SIZE", "uint64", 8, int(self.IDX.GENEEOF.TABLE_SIZE), bytes2hex(self.IDX.GENEEOF.TABLE_SIZE.to_bytearray()), hexoffset(self.IDX.GENEEOF.TABLE_SIZE_ofs), "-"])
        result.write(str(table))
        table.clear_rows()

        os.makedirs(os.path.dirname(self.OUTPUT_DUMP_PATH), exist_ok=True)
        with open(self.OUTPUT_DUMP_PATH, "w") as f:
            f.write(result.getvalue())

        if not self.IS_QUIET:
            print(result.getvalue())
