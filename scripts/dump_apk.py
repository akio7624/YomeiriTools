import os
from io import StringIO

from prettytable import PrettyTable

from datatype.uint64 import uint64
from utils.BinaryManager import BinaryReader
from parser.apk import APK
from utils.ProgramInfo import *
from utils.Utils import *


class DumpApk:
    def __init__(self, i: str, o: str, t: str, q: bool):
        self.INPUT_APK_PATH: str = i
        self.OUTPUT_DUMP_PATH: str = o
        self.DUMP_TYPE: str = "table" if t == "table" else "json"
        self.IS_QUIET: bool = q
        self.APK = APK()
        self.file_size = 0

    def dump(self):
        with open(self.INPUT_APK_PATH, "rb") as f:
            reader = BinaryReader(bytearray(f.read()))
            reader.seek(0)
            self.file_size = reader.size()

        self.APK.ENDIANNESS.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=16))
        self.APK.PACKHEDR.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=48))

        tmp = reader.tell()
        reader.skip(8)
        size = int(uint64(reader.get_bytes(8))) + 16
        reader.seek(tmp)
        self.APK.PACKTOC.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=size))

        tmp = reader.tell()
        reader.skip(8)
        size = int(uint64(reader.get_bytes(8))) + 16
        reader.seek(tmp)
        self.APK.PACKFSLS.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=size))

        tmp = reader.tell()
        reader.skip(8)
        size = int(uint64(reader.get_bytes(8))) + 16
        reader.seek(tmp)
        self.APK.GENESTRT.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=size))

        size = get_table_end_padding_count(reader.tell() + 16) + 16
        self.APK.GENEEOF.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=size))

        if int(self.APK.PACKTOC.TOC_SEG_COUNT) > 0:
            for seg in self.APK.PACKTOC.TOC_SEGMENT_LIST:
                if int(seg.IDENTIFIER) == 1:
                    continue
                reader.seek(int(seg.FILE_OFFSET))
                if int(seg.IDENTIFIER) == 0:  # raw file
                    filesize = int(seg.FILE_SIZE)
                elif int(seg.IDENTIFIER) == 512:  # zlib compressed file
                    filesize = int(seg.FILE_ZSIZE)
                else:
                    filesize = None

                self.APK.ROOT_FILES.add_from_bytearray(ofs=int(seg.FILE_OFFSET), size=filesize, src=reader.get_bytes(filesize + get_root_file_padding_cnt(filesize)))

        self.APK.ROOT_FILES.sort()

        self.dump_table()

    def dump_table(self):
        result = StringIO()
        result.write(f"# File Name: {self.INPUT_APK_PATH}\n")
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

        result.write("* ENDIANNESS table\n")
        table.add_row(["SIGNATURE", "char[]", 8, str(self.APK.ENDIANNESS.SIGNATURE), bytes2hex(self.APK.ENDIANNESS.SIGNATURE.to_bytearray()), hexoffset(self.APK.ENDIANNESS.SIGNATURE_ofs), "-"])
        table.add_row(["TABLE SIZE", "uint64", 8, int(self.APK.ENDIANNESS.TABLE_SIZE), bytes2hex(self.APK.ENDIANNESS.TABLE_SIZE.to_bytearray()), hexoffset(self.APK.ENDIANNESS.TABLE_SIZE_ofs), "-"])
        result.write(str(table))
        table.clear_rows()

        result.write("\n\n\n")

        result.write("* PACKHEDR table\n")
        table.add_row(["SIGNATURE", "char[]", 8, str(self.APK.PACKHEDR.SIGNATURE), bytes2hex(self.APK.PACKHEDR.SIGNATURE.to_bytearray()), hexoffset(self.APK.PACKHEDR.SIGNATURE_ofs), "-"])
        table.add_row(["TABLE SIZE", "uint64", 8, int(self.APK.PACKHEDR.TABLE_SIZE), bytes2hex(self.APK.PACKHEDR.TABLE_SIZE.to_bytearray()), hexoffset(self.APK.PACKHEDR.TABLE_SIZE_ofs), "-"])
        table.add_row(["unknown 1", "-", 8, "-", bytes2hex(self.APK.PACKHEDR.unknown_1), hexoffset(self.APK.PACKHEDR.unknown_1_ofs), "-"])
        table.add_row(["FILE LIST OFFSET", "uint32", 4, int(self.APK.PACKHEDR.FILE_LIST_OFFSET), bytes2hex(self.APK.PACKHEDR.FILE_LIST_OFFSET.to_bytearray()), hexoffset(self.APK.PACKHEDR.FILE_LIST_OFFSET_ofs), "-"])
        table.add_row(["ARCHIVE PADDING TYPE", "uint32", 4, int(self.APK.PACKHEDR.ARCHIVE_PADDING_TYPE), bytes2hex(self.APK.PACKHEDR.ARCHIVE_PADDING_TYPE.to_bytearray()), hexoffset(self.APK.PACKHEDR.ARCHIVE_PADDING_TYPE_ofs), archive_padding_type2desc(int(self.APK.PACKHEDR.ARCHIVE_PADDING_TYPE))])
        table.add_row(["HASH", "byte[]", 16, "-", bytes2hex(self.APK.PACKHEDR.HASH), hexoffset(self.APK.PACKHEDR.HASH_ofs), "-"])
        result.write(str(table))
        table.clear_rows()

        result.write("\n\n\n")

        result.write("* PACKTOC table\n")
        table.add_row(["SIGNATURE", "char[]", 8, str(self.APK.PACKTOC.SIGNATURE), bytes2hex(self.APK.PACKTOC.SIGNATURE.to_bytearray()), hexoffset(self.APK.PACKTOC.SIGNATURE_ofs), "-"])
        table.add_row(["TABLE SIZE", "uint64", 8, int(self.APK.PACKTOC.TABLE_SIZE), bytes2hex(self.APK.PACKTOC.TABLE_SIZE.to_bytearray()), hexoffset(self.APK.PACKTOC.TABLE_SIZE_ofs), "-"])
        table.add_row(["TOC SEG SIZE", "uint32", 4, int(self.APK.PACKTOC.TOC_SEG_SIZE), bytes2hex(self.APK.PACKTOC.TOC_SEG_SIZE.to_bytearray()), hexoffset(self.APK.PACKTOC.TOC_SEG_SIZE_ofs), "-"])
        table.add_row(["TOC SEG COUNT", "uint32", 4, int(self.APK.PACKTOC.TOC_SEG_COUNT), bytes2hex(self.APK.PACKTOC.TOC_SEG_COUNT.to_bytearray()), hexoffset(self.APK.PACKTOC.TOC_SEG_COUNT_ofs), "-"])
        table.add_row(["unknown 1", "-", 8, "-", bytes2hex(self.APK.PACKTOC.unknown_1), hexoffset(self.APK.PACKTOC.unknown_1_ofs), "-"])
        table.add_row(["TOC SEG LIST", "TOC_SEGMENT[]", int(self.APK.PACKTOC.TOC_SEG_SIZE) * int(self.APK.PACKTOC.TOC_SEG_COUNT), "-", "-", hexoffset(self.APK.PACKTOC.TOC_SEGMENT_LIST_ofs), "-"])
        table.add_row(["PADDING", "byte[]", len(self.APK.PACKTOC.PADDING), "-", bytes2hex(self.APK.PACKTOC.PADDING), hexoffset(self.APK.PACKTOC.PADDING_ofs), "-"])
        result.write(str(table))
        table.clear_rows()

        result.write("\n\n")

        if int(self.APK.PACKTOC.TOC_SEG_COUNT) != 0:
            result.write("    * TOC SEGMENT list\n")
            for i in range(int(self.APK.PACKTOC.TOC_SEG_COUNT)):
                seg = self.APK.PACKTOC.TOC_SEGMENT_LIST[i]

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
                if i > 20:
                    break  # TODO for test

        result.write("\n\n\n")

        result.write("* PACKFSLS table\n")
        table.add_row(["SIGNATURE", "char[]", 8, str(self.APK.PACKFSLS.SIGNATURE), bytes2hex(self.APK.PACKFSLS.SIGNATURE.to_bytearray()), hexoffset(self.APK.PACKFSLS.SIGNATURE_ofs), "-"])
        table.add_row(["TABLE SIZE", "uint64", 8, int(self.APK.PACKFSLS.TABLE_SIZE), bytes2hex(self.APK.PACKFSLS.TABLE_SIZE.to_bytearray()), hexoffset(self.APK.PACKFSLS.TABLE_SIZE_ofs), "-"])
        table.add_row(["ARCHIVE SEG COUNT", "uint32", 4, int(self.APK.PACKFSLS.ARCHIVE_SEG_COUNT), bytes2hex(self.APK.PACKFSLS.ARCHIVE_SEG_COUNT.to_bytearray()), hexoffset(self.APK.PACKFSLS.ARCHIVE_SEG_COUNT_ofs), "-"])
        table.add_row(["ARCHIVE SEG SIZE", "uint32", 4, int(self.APK.PACKFSLS.ARCHIVE_SEG_SIZE), bytes2hex(self.APK.PACKFSLS.ARCHIVE_SEG_SIZE.to_bytearray()), hexoffset(self.APK.PACKFSLS.ARCHIVE_SEG_SIZE_ofs), "-"])
        table.add_row(["unknown 1", "-", 8, "-", bytes2hex(self.APK.PACKFSLS.unknown_1), hexoffset(self.APK.PACKFSLS.unknown_1_ofs), "-"])
        table.add_row(["ARCHIVE SEGMENT LIST", "ARCHIVE_SEGMENT[]", int(self.APK.PACKFSLS.ARCHIVE_SEG_SIZE) * int(self.APK.PACKFSLS.ARCHIVE_SEG_COUNT), "-", "-", hexoffset(self.APK.PACKFSLS.ARCHIVE_SEGMENT_LIST_ofs), "-"])
        table.add_row(["PADDING", "byte[]", len(self.APK.PACKFSLS.PADDING), "-", bytes2hex(self.APK.PACKFSLS.PADDING), hexoffset(self.APK.PACKFSLS.PADDING_ofs), "-"])
        result.write(str(table))
        table.clear_rows()

        result.write("\n\n")

        if int(self.APK.PACKFSLS.ARCHIVE_SEG_COUNT) != 0:
            result.write("    * ARCHIVE SEGMENT list\n")
            for i in range(int(self.APK.PACKFSLS.ARCHIVE_SEG_COUNT)):
                seg = self.APK.PACKFSLS.ARCHIVE_SEGMENT_LIST[i]

                result.write(f"    [{i}]\n")
                table.add_row(["NAME IDX", "uint32", 4, int(seg.NAME_IDX), bytes2hex(seg.NAME_IDX.to_bytearray()), hexoffset(seg.NAME_IDX_ofs), "-"])
                table.add_row(["ZERO", "byte[]", len(seg.ZERO), 8, bytes2hex(seg.ZERO), hexoffset(seg.ZERO_ofs), "-"])
                table.add_row(["ARCHIVE OFFSET", "uint64", 8, int(seg.ARCHIVE_OFFSET), bytes2hex(seg.ARCHIVE_OFFSET.to_bytearray()), hexoffset(seg.ARCHIVE_OFFSET_ofs), "-"])
                table.add_row(["ARCHIVE SIZE", "uint64", 8, int(seg.ARCHIVE_SIZE), bytes2hex(seg.ARCHIVE_SIZE.to_bytearray()), hexoffset(seg.ARCHIVE_SIZE_ofs), "-"])
                table.add_row(["HASH", "byte[]", 16, "-", bytes2hex(seg.HASH), hexoffset(seg.HASH_ofs), "-"])
                result.write("\n".join(["    " + line for line in str(table).splitlines()]))
                result.write("\n\n")
                table.clear_rows()

        result.write("\n\n\n")

        result.write("* GENESTRT table\n")
        table.add_row(["SIGNATURE", "char[]", 8, str(self.APK.GENESTRT.SIGNATURE), bytes2hex(self.APK.GENESTRT.SIGNATURE.to_bytearray()), hexoffset(self.APK.GENESTRT.SIGNATURE_ofs), "-"])
        table.add_row(["TABLE SIZE 1", "uint64", 8, int(self.APK.GENESTRT.TABLE_SIZE_1), bytes2hex(self.APK.GENESTRT.TABLE_SIZE_1.to_bytearray()), hexoffset(self.APK.GENESTRT.TABLE_SIZE_1_ofs), "-"])
        table.add_row(["FILENAME COUNT", "uint32", 8, int(self.APK.GENESTRT.FILENAME_COUNT), bytes2hex(self.APK.GENESTRT.FILENAME_COUNT.to_bytearray()), hexoffset(self.APK.GENESTRT.FILENAME_COUNT_ofs), "-"])
        table.add_row(["unknown 1", "-", 4, "-", bytes2hex(self.APK.GENESTRT.unknown_1), hexoffset(self.APK.GENESTRT.unknown_1_ofs), "-"])
        table.add_row(["FILE NAMES OFFSET", "uint32", 4, int(self.APK.GENESTRT.FILE_NAMES_OFFSET), bytes2hex(self.APK.GENESTRT.FILE_NAMES_OFFSET.to_bytearray()), hexoffset(self.APK.GENESTRT.FILE_NAMES_OFFSET_ofs), "-"])
        table.add_row(["TABLE SIZE 2", "uint32", 4, int(self.APK.GENESTRT.TABLE_SIZE_2), bytes2hex(self.APK.GENESTRT.TABLE_SIZE_2.to_bytearray()), hexoffset(self.APK.GENESTRT.TABLE_SIZE_2_ofs), "-"])
        table.add_row(["FILENAME OFFSET LIST", "uint32[]", len(self.APK.GENESTRT.FILENAME_OFFSET_LIST) * 4, "-", "-", hexoffset(self.APK.GENESTRT.FILENAME_OFFSET_LIST_ofs), "-"])
        table.add_row(["FILENAME OFFSET LIST PADDING", "byte[]", len(self.APK.GENESTRT.FILENAME_OFFSET_LIST_PADDING), "-", bytes2hex(self.APK.GENESTRT.FILENAME_OFFSET_LIST_PADDING), hexoffset(self.APK.GENESTRT.FILENAME_OFFSET_LIST_PADDING_ofs), "-"])
        table.add_row(["FILE_NAMES", "string[]", self.APK.GENESTRT.FILE_NAMES_SIZE, "-", "-", hexoffset(self.APK.GENESTRT.FILE_NAMES_ofs), "-"])
        table.add_row(["PADDING", "byte[]", len(self.APK.GENESTRT.PADDING), "-", bytes2hex(self.APK.GENESTRT.PADDING), hexoffset(self.APK.GENESTRT.PADDING_ofs), "-"])
        result.write(str(table))
        table.clear_rows()

        result.write("\n\n")

        result.write("    * FILENAME OFFSET and FILENAME (Trailing null character removed)\n")
        file_names_table = PrettyTable()
        file_names_table.field_names = ["INDEX", "FILENAME OFFSET", "FILENAME"]
        file_names_table.align["FILENAME"] = "l"
        for i in range(int(self.APK.GENESTRT.FILENAME_COUNT)):
            file_names_table.add_row([i, int(self.APK.GENESTRT.FILENAME_OFFSET_LIST[i]), self.APK.GENESTRT.FILE_NAMES[i][:-1]])

        for line in str(file_names_table).splitlines():
            result.write("    " + line + "\n")

        result.write("\n\n\n")

        result.write("* GENEEOF table\n")
        table.add_row(["SIGNATURE", "char[]", 8, str(self.APK.GENEEOF.SIGNATURE), bytes2hex(self.APK.GENEEOF.SIGNATURE.to_bytearray()), hexoffset(self.APK.GENEEOF.SIGNATURE_ofs), "-"])
        table.add_row(["TABLE SIZE", "uint64", 8, int(self.APK.GENEEOF.TABLE_SIZE), bytes2hex(self.APK.GENEEOF.TABLE_SIZE.to_bytearray()), hexoffset(self.APK.GENEEOF.TABLE_SIZE_ofs), "-"])
        table.add_row(["TABLE END PADDING", "byte[]", len(self.APK.GENEEOF.TABLE_END_PADDING), "-", bytes2hex(self.APK.GENEEOF.TABLE_END_PADDING), hexoffset(self.APK.GENEEOF.TABLE_END_PADDING_ofs), "-"])
        result.write(str(table))
        table.clear_rows()

        result.write("\n\n\n")

        result.write("* ROOT FILES (sorted by offset)\n")

        for file in self.APK.ROOT_FILES.FILE_LIST:
            table.add_row(["FILE", "byte[]", len(file.DATA), "-", bytes2hex(file.DATA[:32]) + "\n...", hexoffset(file.DATA_ofs), "-"])
            table.add_row(["PADDING", "byte[]", len(file.PADDING), "-", bytes2hex(file.PADDING[:32]) + "\n...", hexoffset(file.PADDING_ofs), "-"])
            result.write(str(table))
            result.write("\n\n")
            table.clear_rows()

        os.makedirs(os.path.dirname(self.OUTPUT_DUMP_PATH), exist_ok=True)
        with open(self.OUTPUT_DUMP_PATH, "w") as f:
            f.write(result.getvalue())


