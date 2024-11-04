from utils.BinaryManager import BinaryReader
from parser.apk import APK


class DumpApk:
    def __init__(self, i: str, o: str, t: str, q: bool):
        self.INPUT_APK_PATH: str = i
        self.OUTPUT_DUMP_PATH: str = o
        self.DUMP_TYPE: str = "table" if t == "table" else "json"
        self.IS_QUIET: bool = q
        self.APK = APK()

    def dump(self):
        with open(self.INPUT_APK_PATH, "rb") as f:
            reader = BinaryReader(bytearray(f.read()))
            reader.seek(0)

        self.APK.ENDIANNESS.from_bytearray(reader.get_bytes(size=16))

        self.dump_table()

    def dump_table(self):
        # TODO
        pass


