import os

from prettytable import PrettyTable

from utils.BinaryManager import BinaryReader
from parser.apk import APK
from utils.ProgramInfo import *
from utils.Utils import bytes2hex, hexoffset


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

        self.dump_table()

    def dump_table(self):
        result = ""
        result += f"File Name: {self.INPUT_APK_PATH}\n"
        result += f"Dump Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        result += f"Dump Tools: {TOOL_NAME} v{TOOL_VERSION} dump_apk\n"
        result += f"File Size: {self.file_size} bytes\n"
        result += f"File Format: APK\n"
        result += f"File Endian: Little-endian\n"
        result += "\n\n\n"

        table = PrettyTable()
        table.field_names = ["Name", "Type", "Size", "Value", "Value(hex)", "Offset"]
        table.align["Value"] = "l"
        table.align["Value(hex)"] = "l"


        result += "* ENDIANNESS table\n"
        table.add_row(["SIGNATURE", "char[]", 8, str(self.APK.ENDIANNESS.SIGNATURE), bytes2hex(self.APK.ENDIANNESS.SIGNATURE.to_bytearray()), hexoffset(self.APK.ENDIANNESS.SIGNATURE_ofs)])
        table.add_row(["TABLE SIZE", "uint64", 8, int(self.APK.ENDIANNESS.TABLE_SIZE), bytes2hex(self.APK.ENDIANNESS.TABLE_SIZE.to_bytearray()), hexoffset(self.APK.ENDIANNESS.TABLE_SIZE_ofs)])
        result += table.get_string()
        table.clear_rows()

        result += "\n\n\n"

        result += "* PACKHEDR table\n"
        table.add_row(["SIGNATURE", "char[]", 8, str(self.APK.PACKHEDR.SIGNATURE), bytes2hex(self.APK.PACKHEDR.SIGNATURE.to_bytearray()), hexoffset(self.APK.PACKHEDR.SIGNATURE_ofs)])
        table.add_row(["TABLE SIZE", "uint64", 8, int(self.APK.PACKHEDR.TABLE_SIZE), bytes2hex(self.APK.PACKHEDR.TABLE_SIZE.to_bytearray()), hexoffset(self.APK.PACKHEDR.TABLE_SIZE_ofs)])
        table.add_row(["unknown 1", "-", 8, "-", bytes2hex(self.APK.PACKHEDR.unknown_1), hexoffset(self.APK.PACKHEDR.unknown_1_ofs)])
        table.add_row(["FILE LIST OFFSET", "uint32", 4, int(self.APK.PACKHEDR.FILE_LIST_OFFSET), bytes2hex(self.APK.PACKHEDR.ARCHIVE_PADDING_TYPE.to_bytearray()), hexoffset(self.APK.PACKHEDR.ARCHIVE_PADDING_TYPE_ofs)])
        table.add_row(["ARCHIVE PADDING TYPE", "uint32", 4, int(self.APK.PACKHEDR.ARCHIVE_PADDING_TYPE), bytes2hex(self.APK.PACKHEDR.ARCHIVE_PADDING_TYPE.to_bytearray()), hexoffset(self.APK.PACKHEDR.ARCHIVE_PADDING_TYPE_ofs)])
        table.add_row(["HASH", "byte[]", 16, "-", bytes2hex(self.APK.PACKHEDR.HASH), hexoffset(self.APK.PACKHEDR.HASH_ofs)])
        result += table.get_string()

        os.makedirs(os.path.dirname(self.OUTPUT_DUMP_PATH), exist_ok=True)
        with open(self.OUTPUT_DUMP_PATH, "w") as f:
            f.write(result)


