import hashlib
import os.path
import zlib

from parser.apk import APKReader
from utils.Utils import get_name_from_name_idx


class UnpackApk:
    def __init__(self, i: str, o: str, e: str):
        self.INPUT_APK_PATH: str = i
        self.OUTPUT_DUMP_PATH: str = o
        self.IS_OVERWRITE: bool = True if e == "overwrite" else False
        self.APK = None

        self.__ROOT_FILE_OFFSET_INDEX = dict()  # k: root file offset    v: root files index
        self.__ARCHIVE_FILE_OFFSET_INDEX = dict()
        self.__original_md5 = None
        self.__dumped_md5 = None

    def extract(self):
        apk_reader = APKReader(self.INPUT_APK_PATH)
        apk_reader.read()
        self.APK = apk_reader.get_apk()

        for idx, file in enumerate(self.APK.ROOT_FILES.FILE_LIST):
            self.__ROOT_FILE_OFFSET_INDEX[int(file.DATA_ofs)] = idx

        self.__original_md5 = apk_reader.get_original_md5()
        self.__dumped_md5 = hashlib.md5(self.APK.to_bytearray()).hexdigest()

        if self.__original_md5 != self.__dumped_md5:
            print("Warning! The original file and the dumped file do not match. The extract results may be inaccurate.")
            print(f"{self.__original_md5} != {self.__dumped_md5}")

        if len(self.APK.PACKTOC.TOC_SEGMENT_LIST) > 0:
            toc_segment = self.APK.PACKTOC.TOC_SEGMENT_LIST[0]
            if int(toc_segment.IDENTIFIER) == 1:  # If folders are present, they are expected to start with an empty string directory.
                self.extract_directory(int(toc_segment.ENTRY_INDEX), int(toc_segment.ENTRY_COUNT), "")
            else:  # files for root directory, Only files are expected, without any folders.
                for toc_segment in self.APK.PACKTOC.TOC_SEGMENT_LIST:
                    self.extract_root_file(toc_segment, get_name_from_name_idx(self.APK, int(toc_segment.NAME_IDX)))

        if int(self.APK.PACKFSLS.ARCHIVE_SEG_COUNT) > 0:
            os.makedirs(os.path.join(self.OUTPUT_DUMP_PATH, "__ARCHIVE__"), exist_ok=True)

            archive_offset_index = dict()
            for archive_segment in self.APK.PACKFSLS.ARCHIVE_SEGMENT_LIST:
                archive_name = get_name_from_name_idx(self.APK, int(archive_segment.NAME_IDX))
                archive_dir_path = os.path.join(self.OUTPUT_DUMP_PATH, "__ARCHIVE__", archive_name)
                os.makedirs(archive_dir_path, exist_ok=True)
                archive_offset_index[int(archive_segment.ARCHIVE_OFFSET)] = archive_dir_path

            for archive in self.APK.ARCHIVES.ARCHIVE_LIST:
                archive_dir_path = archive_offset_index[int(archive.ARCHIVE_ofs)]

                self.__ARCHIVE_FILE_OFFSET_INDEX.clear()
                for idx, file in enumerate(archive.FILES.FILE_LIST):
                    self.__ARCHIVE_FILE_OFFSET_INDEX[int(file.DATA_ofs)] = idx

                for file_segment in archive.PACKFSHD.FILE_SEGMENT_LIST:
                    self.extract_archive_file(archive, file_segment, archive_dir_path, get_name_from_name_idx(archive, int(file_segment.NAME_IDX)))

    def extract_directory(self, entry_index: int, entry_count: int, path: str):
        os.makedirs(os.path.join(self.OUTPUT_DUMP_PATH, path), exist_ok=True)

        for i in range(entry_index, entry_index + entry_count):
            toc_segment = self.APK.PACKTOC.TOC_SEGMENT_LIST[i]
            if int(toc_segment.IDENTIFIER) == 1:
                self.extract_directory(int(toc_segment.ENTRY_INDEX), int(toc_segment.ENTRY_COUNT), os.path.join(path, get_name_from_name_idx(self.APK, int(toc_segment.NAME_IDX))))
            else:
                file_path = os.path.join(path, get_name_from_name_idx(self.APK, int(toc_segment.NAME_IDX)))
                self.extract_root_file(toc_segment, file_path)

    def extract_root_file(self, toc_segment, path: str):
        file_path = os.path.join(self.OUTPUT_DUMP_PATH, path)

        if os.path.isfile(file_path) and not self.IS_OVERWRITE:
            return

        file_idx = self.__ROOT_FILE_OFFSET_INDEX[int(toc_segment.FILE_OFFSET)]
        file = self.APK.ROOT_FILES.FILE_LIST[file_idx]
        with open(file_path, "wb") as f:
            if int(toc_segment.IDENTIFIER) == 512:  # zlib file
                f.write(zlib.decompress(file.DATA))
            else:
                f.write(file.DATA)

    def extract_archive_file(self, archive, file_seg, archive_dir_path: str, path: str):
        parents_path = "/".join(path.split("/")[:-1])
        file_path = os.path.join(archive_dir_path, path)
        os.makedirs(os.path.join(archive_dir_path, parents_path), exist_ok=True)

        if os.path.isfile(file_path) and not self.IS_OVERWRITE:
            return

        file_idx = self.__ARCHIVE_FILE_OFFSET_INDEX[archive.ARCHIVE_ofs + int(file_seg.FILE_OFFSET)]
        file = archive.FILES.FILE_LIST[file_idx]
        with open(file_path, "wb") as f:
            if int(file_seg.ZIP) == 2:  # zlib file
                f.write(zlib.decompress(file.DATA))
            else:
                f.write(file.DATA)
