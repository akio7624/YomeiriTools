import hashlib
import os
from io import StringIO

from prettytable import PrettyTable

from datatype.uint64 import uint64
from utils.BinaryManager import BinaryReader
from parser.apk import APK, TableException
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

        self.__original_md5 = None
        self.__dumped_md5 = None

    def dump(self, debug_no_dump: bool = False):
        self.read()
        self.__dumped_md5 = hashlib.md5(self.APK.to_bytearray()).hexdigest()

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

    def read(self):
        with open(self.INPUT_APK_PATH, "rb") as f:
            reader = BinaryReader(bytearray(f.read()))
            reader.seek(0)
            self.file_size = reader.size()

        self.__original_md5 = hashlib.md5(reader.get_raw()).hexdigest()

        print("Reading ENDIANNESS table...")
        self.APK.ENDIANNESS.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=16))

        print("Reading PACKHEDR table...")
        self.APK.PACKHEDR.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=48))

        print("Reading PACKTOC table...")
        tmp = reader.tell()
        reader.skip(8)
        size = int(uint64(reader.get_bytes(8))) + 16
        reader.seek(tmp)
        self.APK.PACKTOC.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=size))

        print("Reading PACKFSLS table...")
        tmp = reader.tell()
        reader.skip(8)
        size = int(uint64(reader.get_bytes(8))) + 16
        reader.seek(tmp)
        self.APK.PACKFSLS.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=size))

        print("Reading GENESTRT table...")
        tmp = reader.tell()
        reader.skip(8)
        size = int(uint64(reader.get_bytes(8))) + 16
        reader.seek(tmp)
        self.APK.GENESTRT.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=size))

        print("Reading GENEEOF table...")
        size = get_table_end_padding_count(reader.tell() + 16) + 16
        self.APK.GENEEOF.from_bytearray(ofs=reader.tell(), src=reader.get_bytes(size=size))

        print("Reading ROOT files...")
        tmp = reader.tell()
        root_files_size = 0
        if len(self.APK.PACKTOC.TOC_SEGMENT_LIST) > 0:
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
                block_size = filesize + get_root_file_padding_cnt(filesize)
                root_files_size += block_size

                self.APK.ROOT_FILES.add_from_bytearray(ofs=int(seg.FILE_OFFSET), size=filesize, src=reader.get_bytes(block_size))

            self.APK.ROOT_FILES.sort()

        reader.seek(tmp + root_files_size)
        if reader.EOF():
            return

        self.APK.ROOT_FILES.PADDING_ofs = reader.tell()
        self.APK.ROOT_FILES.PADDING = reader.get_bytes(get_root_files_padding_count(root_files_size))

        if reader.EOF():
            raise TableException(self, f"If ROOT_FILES_PADDING exists, EOF cannot appear")

        for idx, seg in enumerate(self.APK.PACKFSLS.ARCHIVE_SEGMENT_LIST):
            print(f"Reading archive {idx+1}/{len(self.APK.PACKFSLS.ARCHIVE_SEGMENT_LIST)}...")
            archive = self.APK.ARCHIVE()
            ARCHIVE_OFFSET = int(seg.ARCHIVE_OFFSET)
            ARCHIVE_SIZE = int(seg.ARCHIVE_SIZE)

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

                    archive.FILES.add_from_bytearray(ofs=real_file_offset, size=filesize, src=reader.get_bytes(block_size))

                archive.FILES.sort()

            reader.seek(tmp + archive_files_size)

            if not reader.EOF():
                size = get_archive_padding_count(int(self.APK.PACKHEDR.ARCHIVE_PADDING_TYPE), ARCHIVE_SIZE)
                archive.PADDING_ofs = reader.tell()
                archive.PADDING = reader.get_bytes(size=size)

            self.APK.ARCHIVES.add_from_object(archive)

        self.APK.ARCHIVES.sort()

    def dump_table(self):
        print("Start dumping...")

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

        print("Dumping ENDIANNESS table...")
        result.write("* ENDIANNESS table\n")
        table.add_row(["SIGNATURE", "char[]", 8, str(self.APK.ENDIANNESS.SIGNATURE), bytes2hex(self.APK.ENDIANNESS.SIGNATURE.to_bytearray()), hexoffset(self.APK.ENDIANNESS.SIGNATURE_ofs), "-"])
        table.add_row(["TABLE SIZE", "uint64", 8, int(self.APK.ENDIANNESS.TABLE_SIZE), bytes2hex(self.APK.ENDIANNESS.TABLE_SIZE.to_bytearray()), hexoffset(self.APK.ENDIANNESS.TABLE_SIZE_ofs), "-"])
        result.write(str(table))
        table.clear_rows()

        result.write("\n\n\n")

        print("Dumping PACKHEDR table...")
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

        print("Dumping PACKTOC table...")
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

        print("Dumping TOC SEGMENT...")
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
                # if i > 20:
                #     break  # for test

        result.write("\n\n\n")

        print("Dumping PACKFSLS table...")
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
            print("Dumping ARCHIVE SEGMENT...")
            result.write("    * ARCHIVE SEGMENT list\n")
            for i in range(int(self.APK.PACKFSLS.ARCHIVE_SEG_COUNT)):
                seg = self.APK.PACKFSLS.ARCHIVE_SEGMENT_LIST[i]

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

        print("Dumping GENEEOF table...")
        result.write("* GENEEOF table\n")
        table.add_row(["SIGNATURE", "char[]", 8, str(self.APK.GENEEOF.SIGNATURE), bytes2hex(self.APK.GENEEOF.SIGNATURE.to_bytearray()), hexoffset(self.APK.GENEEOF.SIGNATURE_ofs), "-"])
        table.add_row(["TABLE SIZE", "uint64", 8, int(self.APK.GENEEOF.TABLE_SIZE), bytes2hex(self.APK.GENEEOF.TABLE_SIZE.to_bytearray()), hexoffset(self.APK.GENEEOF.TABLE_SIZE_ofs), "-"])
        table.add_row(["TABLE END PADDING", "byte[]", len(self.APK.GENEEOF.TABLE_END_PADDING), "-", bytes2hex(self.APK.GENEEOF.TABLE_END_PADDING), hexoffset(self.APK.GENEEOF.TABLE_END_PADDING_ofs), "-"])
        result.write(str(table))
        table.clear_rows()

        result.write("\n\n\n")

        if len(self.APK.ROOT_FILES.FILE_LIST) > 0:
            print("Dumping ROOT files...")
            result.write("* ROOT FILES (sorted by offset)\n")

            for file in self.APK.ROOT_FILES.FILE_LIST:
                table.add_row(["FILE", "byte[]", len(file.DATA), "-", bytes2hex(file.DATA[:32]) + "\n...", hexoffset(file.DATA_ofs), "-"])
                table.add_row(["PADDING", "byte[]", len(file.PADDING), "-", bytes2hex(file.PADDING[:32]) + "\n...", hexoffset(file.PADDING_ofs), "-"])
                result.write(str(table))
                result.write("\n\n")
                table.clear_rows()

            if len(self.APK.ROOT_FILES.PADDING) > 0:
                table.add_row(["PADDING", "byte[]", len(self.APK.ROOT_FILES.PADDING), "-", bytes2hex(self.APK.ROOT_FILES.PADDING), hexoffset(self.APK.ROOT_FILES.PADDING_ofs), "-"])
                result.write(str(table))
                result.write("\n\n\n")
                table.clear_rows()

        if int(self.APK.PACKFSLS.ARCHIVE_SEG_COUNT) > 0:
            result.write("* ARCHIVE LIST (sorted by offset)\n\n")

            for i, archive in enumerate(self.APK.ARCHIVES.ARCHIVE_LIST):
                print(f"Dumping ARCHIVE {i+1}/{len(self.APK.ARCHIVES.ARCHIVE_LIST)}...")
                result.write(f"ARCHIVE #{i}\n")

                print("    Dumping ENDIANNESS table...")
                result.write("* ENDIANNESS table\n")
                table.add_row(["SIGNATURE", "char[]", 8, str(archive.ENDIANNESS.SIGNATURE), bytes2hex(archive.ENDIANNESS.SIGNATURE.to_bytearray()), hexoffset(archive.ENDIANNESS.SIGNATURE_ofs), "-"])
                table.add_row(["TABLE SIZE", "uint64", 8, int(archive.ENDIANNESS.TABLE_SIZE), bytes2hex(archive.ENDIANNESS.TABLE_SIZE.to_bytearray()), hexoffset(archive.ENDIANNESS.TABLE_SIZE_ofs), "-"])
                result.write(str(table))
                table.clear_rows()

                result.write("\n\n")

                print("    Dumping PACKFSHD table...")
                result.write("* PACKFSHD table\n")
                table.add_row(["SIGNATURE", "char[]", 8, str(archive.PACKFSHD.SIGNATURE), bytes2hex(archive.PACKFSHD.SIGNATURE.to_bytearray()), hexoffset(archive.PACKFSHD.SIGNATURE_ofs), "-"])
                table.add_row(["TABLE SIZE", "uint64", 8, int(archive.PACKFSHD.TABLE_SIZE), bytes2hex(archive.PACKFSHD.TABLE_SIZE.to_bytearray()), hexoffset(archive.PACKFSHD.TABLE_SIZE_ofs), "-"])
                table.add_row(["unknown 1", "byte[]", 4, "-", bytes2hex(archive.PACKFSHD.unknown_1), hexoffset(archive.PACKFSHD.unknown_1_ofs), "-"])
                table.add_row(["FILE SEG SIZE 1", "uint32", 4, int(archive.PACKFSHD.FILE_SEG_SIZE_1), bytes2hex(archive.PACKFSHD.FILE_SEG_SIZE_1.to_bytearray()), hexoffset(archive.PACKFSHD.FILE_SEG_SIZE_1_ofs), "-"])
                table.add_row(["FILE SEG COUNT", "uint32", 4, int(archive.PACKFSHD.FILE_SEG_COUNT), bytes2hex(archive.PACKFSHD.FILE_SEG_COUNT.to_bytearray()), hexoffset(archive.PACKFSHD.FILE_SEG_COUNT_ofs), "-"])
                table.add_row(["FILE SEG SIZE 2", "uint32", 4, int(archive.PACKFSHD.FILE_SEG_SIZE_2), bytes2hex(archive.PACKFSHD.FILE_SEG_SIZE_2.to_bytearray()), hexoffset(archive.PACKFSHD.FILE_SEG_SIZE_2_ofs), "-"])
                table.add_row(["unknown 2", "byte[]", 4, "-", bytes2hex(archive.PACKFSHD.unknown_2), hexoffset(archive.PACKFSHD.unknown_2_ofs), "-"])
                table.add_row(["unknown 3", "byte[]", 4, "-", bytes2hex(archive.PACKFSHD.unknown_3), hexoffset(archive.PACKFSHD.unknown_3_ofs), "-"])
                table.add_row(["FILE SEGMENT LIST", "ARCHIVE_FILE_SEGMENT[]", int(archive.PACKFSHD.FILE_SEG_SIZE_1) * int(archive.PACKFSHD.FILE_SEG_COUNT), "-", "-", hexoffset(archive.PACKFSHD.FILE_SEGMENT_LIST_ofs), "-"])
                table.add_row(["PADDING", "byte[]", len(archive.PACKFSHD.PADDING), "-", bytes2hex(archive.PACKFSHD.PADDING), hexoffset(archive.PACKFSHD.PADDING_ofs), "-"])
                result.write(str(table))
                table.clear_rows()

                result.write("\n\n")

                if int(archive.PACKFSHD.FILE_SEG_COUNT) != 0:
                    result.write("    * FILE SEGMENT list\n")
                    for j in range(int(archive.PACKFSHD.FILE_SEG_COUNT)):
                        seg = archive.PACKFSHD.FILE_SEGMENT_LIST[j]

                        result.write(f"    [{j}]\n")
                        table.add_row(["NAME IDX", "uint32", 4, int(seg.NAME_IDX), bytes2hex(seg.NAME_IDX.to_bytearray()), hexoffset(seg.NAME_IDX_ofs), "-"])
                        table.add_row(["ZIP", "uint32", 4, int(seg.ZIP), bytes2hex(seg.ZIP.to_bytearray()), hexoffset(seg.ZIP_ofs), zip2desc(int(seg.ZIP))])
                        table.add_row(["FILE OFFSET", "uint64", 8, int(seg.FILE_OFFSET), bytes2hex(seg.FILE_OFFSET.to_bytearray()), hexoffset(seg.FILE_OFFSET_ofs), "-"])
                        table.add_row(["FILE SIZE", "uint64", 8, int(seg.FILE_SIZE), bytes2hex(seg.FILE_SIZE.to_bytearray()), hexoffset(seg.FILE_SIZE_ofs), "-"])
                        table.add_row(["FILE ZSIZE", "uint64", 8, int(seg.FILE_ZSIZE), bytes2hex(seg.FILE_ZSIZE.to_bytearray()), hexoffset(seg.FILE_ZSIZE_ofs), "-"])
                        result.write("\n".join(["    " + line for line in str(table).splitlines()]))
                        result.write("\n\n")
                        table.clear_rows()

                result.write("\n\n\n")

                print("    Dumping GENESTRT table...")
                result.write("* GENESTRT table\n")
                table.add_row(["SIGNATURE", "char[]", 8, str(archive.GENESTRT.SIGNATURE), bytes2hex(archive.GENESTRT.SIGNATURE.to_bytearray()), hexoffset(archive.GENESTRT.SIGNATURE_ofs), "-"])
                table.add_row(["TABLE SIZE 1", "uint64", 8, int(archive.GENESTRT.TABLE_SIZE_1), bytes2hex(archive.GENESTRT.TABLE_SIZE_1.to_bytearray()), hexoffset(archive.GENESTRT.TABLE_SIZE_1_ofs), "-"])
                table.add_row(["FILENAME COUNT", "uint32", 8, int(archive.GENESTRT.FILENAME_COUNT), bytes2hex(archive.GENESTRT.FILENAME_COUNT.to_bytearray()), hexoffset(archive.GENESTRT.FILENAME_COUNT_ofs), "-"])
                table.add_row(["unknown 1", "-", 4, "-", bytes2hex(archive.GENESTRT.unknown_1), hexoffset(archive.GENESTRT.unknown_1_ofs), "-"])
                table.add_row(["FILE NAMES OFFSET", "uint32", 4, int(archive.GENESTRT.FILE_NAMES_OFFSET), bytes2hex(archive.GENESTRT.FILE_NAMES_OFFSET.to_bytearray()), hexoffset(archive.GENESTRT.FILE_NAMES_OFFSET_ofs), "-"])
                table.add_row(["TABLE SIZE 2", "uint32", 4, int(archive.GENESTRT.TABLE_SIZE_2), bytes2hex(archive.GENESTRT.TABLE_SIZE_2.to_bytearray()), hexoffset(archive.GENESTRT.TABLE_SIZE_2_ofs), "-"])
                table.add_row(["FILENAME OFFSET LIST", "uint32[]", len(archive.GENESTRT.FILENAME_OFFSET_LIST) * 4, "-", "-", hexoffset(archive.GENESTRT.FILENAME_OFFSET_LIST_ofs), "-"])
                table.add_row(["FILENAME OFFSET LIST PADDING", "byte[]", len(archive.GENESTRT.FILENAME_OFFSET_LIST_PADDING), "-", bytes2hex(archive.GENESTRT.FILENAME_OFFSET_LIST_PADDING), hexoffset(archive.GENESTRT.FILENAME_OFFSET_LIST_PADDING_ofs), "-"])
                table.add_row(["FILE_NAMES", "string[]", archive.GENESTRT.FILE_NAMES_SIZE, "-", "-", hexoffset(archive.GENESTRT.FILE_NAMES_ofs), "-"])
                table.add_row(["PADDING", "byte[]", len(archive.GENESTRT.PADDING), "-", bytes2hex(archive.GENESTRT.PADDING), hexoffset(archive.GENESTRT.PADDING_ofs), "-"])
                result.write(str(table))
                table.clear_rows()
        
                result.write("\n\n")
        
                result.write("    * FILENAME OFFSET and FILENAME (Trailing null character removed)\n")
                file_names_table = PrettyTable()
                file_names_table.field_names = ["INDEX", "FILENAME OFFSET", "FILENAME"]
                file_names_table.align["FILENAME"] = "l"
                for j in range(int(archive.GENESTRT.FILENAME_COUNT)):
                    file_names_table.add_row([j, int(archive.GENESTRT.FILENAME_OFFSET_LIST[j]), archive.GENESTRT.FILE_NAMES[j][:-1]])
        
                for line in str(file_names_table).splitlines():
                    result.write("    " + line + "\n")
        
                result.write("\n\n\n")

                print("    Dumping GENEEOF table...")
                result.write("* GENEEOF table\n")
                table.add_row(["SIGNATURE", "char[]", 8, str(archive.GENEEOF.SIGNATURE), bytes2hex(archive.GENEEOF.SIGNATURE.to_bytearray()), hexoffset(archive.GENEEOF.SIGNATURE_ofs), "-"])
                table.add_row(["TABLE SIZE", "uint64", 8, int(archive.GENEEOF.TABLE_SIZE), bytes2hex(archive.GENEEOF.TABLE_SIZE.to_bytearray()), hexoffset(archive.GENEEOF.TABLE_SIZE_ofs), "-"])
                result.write(str(table))
                table.clear_rows()
        
                result.write("\n\n\n")

                if len(archive.PACKFSHD.FILE_SEGMENT_LIST) > 0:
                    print("    Dumping files...")
                    result.write("* ARCHIVE FILES (sorted by offset)\n")

                    for file in archive.FILES.FILE_LIST:
                        table.add_row(["FILE", "byte[]", len(file.DATA), "-", bytes2hex(file.DATA[:32]) + "\n...", hexoffset(file.DATA_ofs), "-"])
                        table.add_row(["PADDING", "byte[]", len(file.PADDING), "-", bytes2hex(file.PADDING), hexoffset(file.PADDING_ofs), "-"])
                        result.write(str(table))
                        result.write("\n\n")
                        table.clear_rows()

                result.write("\n\n\n")

                if len(archive.PADDING) > 0:
                    table.add_row(["ARCHIVE PADDING", "byte[]", len(archive.PADDING), "-", bytes2hex(archive.PADDING), hexoffset(archive.PADDING_ofs), "-"])
                    result.write(str(table))
                    result.write("\n\n\n")

        os.makedirs(os.path.dirname(self.OUTPUT_DUMP_PATH), exist_ok=True)
        with open(self.OUTPUT_DUMP_PATH, "w") as f:
            f.write(result.getvalue())
        
        if not self.IS_QUIET:
            print(result.getvalue())
