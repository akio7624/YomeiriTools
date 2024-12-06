import copy
import hashlib
import json
import os.path
import zlib

from datatype.uint64 import uint64
from parser.apk import APKReader
from utils.Utils import get_changed_file_path, make_tree, get_root_file_padding_cnt, get_archive_file_padding_cnt


class PatchApk:
    def __init__(self, i: list, o: str):
        self.INPUT_APK_PATH: str = i[0]
        self.INPUT_DIR_PATH: str = i[1]
        self.OUTPUT_PATCHED_PATH: str = o
        self.APK = None
        self.TREE: dict = dict()

        self.__original_md5 = None
        self.__dumped_md5 = None

    def patch(self):
        apk_reader = APKReader(self.INPUT_APK_PATH)
        apk_reader.read()
        self.APK = apk_reader.get_apk()
        self.TREE = make_tree(self.APK)

        self.__original_md5 = apk_reader.get_original_md5()
        self.__dumped_md5 = hashlib.md5(self.APK.to_bytearray()).hexdigest()

        if self.__original_md5 != self.__dumped_md5:
            print("Warning! The original file and the dumped file do not match. The dump result may be inaccurate.")
            print(f"{self.__original_md5} != {self.__dumped_md5}")

        changed_files = get_changed_file_path(self.INPUT_DIR_PATH)

        for changed_file in changed_files:
            with open(os.path.join(self.INPUT_DIR_PATH, changed_file), 'rb') as f:
                data = f.read()

                if changed_file.startswith("__ARCHIVE__"):
                    archive_name = changed_file.split("/")[1]
                    file_path = "/".join(changed_file.split("/")[2:])
                    seg = self.TREE["ARCHIVE"][archive_name][file_path]
                    _zip = int(seg.ZIP)

                    if _zip == 0:
                        seg.FILE_SIZE = uint64(len(data))
                        seg.FILE_ZSIZE = uint64(0)
                    elif _zip == 2:
                        seg.FILE_SIZE = uint64(len(data))
                        data = zlib.compress(data, level=9)
                        seg.FILE_ZSIZE = uint64(len(data))
                    else:
                        raise Exception(f"unknown ZIP {_zip}")

                    file = self.APK.PACKFSLS.NAME_ARCHIVE_MAP[archive_name].FILES.FILE_LIST[seg.file_index]
                    file.DATA = copy.deepcopy(data)
                    padding_cnt = get_archive_file_padding_cnt(len(file.DATA))
                    file.PADDING = copy.deepcopy(bytearray(padding_cnt))
                else:
                    seg = self.TREE["ROOT"][changed_file]
                    identifier = int(seg.IDENTIFIER)

                    if identifier == 0:
                        seg.FILE_SIZE = uint64(len(data))
                        seg.FILE_ZSIZE = uint64(0)
                    elif identifier == 512:
                        seg.FILE_SIZE = uint64(len(data))
                        data = zlib.compress(data, level=9)
                        seg.FILE_ZSIZE = uint64(len(data))
                    else:
                        raise Exception(f"unknown identifier {identifier}")

                    file = self.APK.ROOT_FILES.FILE_LIST[seg.file_index]
                    file.DATA = copy.deepcopy(data)
                    padding_cnt = get_root_file_padding_cnt(len(file.DATA))
                    file.PADDING = copy.deepcopy(bytearray(padding_cnt))

        apk_reader.update_offsets()
        self.APK = apk_reader.get_apk()

        with open(self.OUTPUT_PATCHED_PATH, "wb") as f:
            f.write(self.APK.to_bytearray())

        print("Validating patched apk...")
        temp = APKReader(self.OUTPUT_PATCHED_PATH)
        temp.read()

        print("OK.")
