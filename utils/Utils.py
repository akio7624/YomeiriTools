import os
from pathlib import Path

# from parser.apk import APK


def bytes2hex(v: bytearray) -> str:
    if len(v) == 0:
        return "-"
    elif len(v) == 1:
        return "00"
    elif len(v) == 2:
        return "00 00"

    result = ""

    for i in range(0, len(v), 16):
        result += " ".join(f"{b:02X}" for b in v[i:i+16]).zfill(8)
        result += "\n"

    return result.strip()


def hexoffset(v: int) -> str:
    return f"0x{v:08X}"


def get_table_padding_count(current: int) -> int:
    if current % 16 == 0:
        return 0

    return 16 - (current % 16)


def get_table_end_padding_count(current: int) -> int:
    if current % 2048 == 0:
        return 0

    n = int(current / 2048)

    while True:
        block_size = (n * 2048)
        if current <= block_size:
            return block_size - current
        n += 1


# padding for single root file
def get_root_file_padding_cnt(size: int) -> int:
    if size % 512 == 0:
        return 0

    n = int(size / 512)

    while True:
        block_size = (n * 512)
        if size <= block_size:
            return block_size - size
        n += 1


# padding for all root files
def get_root_files_padding_count(size: int) -> int:
    if size % 2048 == 0:
        return 0

    n = int(size / 2048)

    while True:
        block_size = (n * 2048)
        if size <= block_size:
            return block_size - size
        n += 1


def get_archive_file_padding_cnt(size: int) -> int:
    if size % 16 == 0:
        return 0

    n = int(size / 16)

    while True:
        block_size = (n * 16)
        if size <= block_size:
            return block_size - size
        n += 1


def get_archive_padding_count(pad_type: int, size: int) -> int:
    if pad_type == 1:
        unit = 2048
    elif pad_type == 2:
        unit = 512
    else:
        unit = None

    if size % unit == 0:
        return 0

    n = int(size / unit)

    while True:
        block_size = (n * unit)
        if size <= block_size:
            return block_size - size
        n += 1


def identifier2desc(v: int) -> str:
    if v == 0:
        return "raw file"
    elif v == 1:
        return "directory"
    elif v == 512:
        return "zlib compressed file"


def zip2desc(v: int) -> str:
    if v == 0:
        return "raw file"
    elif v == 2:
        return "zlib compressed file"


def archive_padding_type2desc(v: int) -> str:
    if v == 1:
        return "Padded archive to be divisible by 2048"
    elif v == 2:
        return "Padded archive to be divisible by 512"


def get_name_from_name_idx(apk, name_idx: int) -> str:
    return apk.GENESTRT.FILE_NAMES[name_idx][:-1]  # remove null


def get_changed_file_path(directory):
    result = []

    for dir_path, _, filenames in os.walk(directory):
        for name in filenames:
            full = str(os.path.join(dir_path, name))
            rel = os.path.relpath(full, directory).replace("\\", "/")
            result.append(rel)

    return result


TREE: dict = dict()


def make_tree(apk) -> dict:
    TREE["ROOT"] = dict()
    TREE["ARCHIVE"] = dict()

    if len(apk.PACKTOC.TOC_SEGMENT_LIST) > 0:
        toc_segment = apk.PACKTOC.TOC_SEGMENT_LIST[0]
        if int(toc_segment.IDENTIFIER) == 1:  # If folders are present, they are expected to start with an empty string directory.
            extract_directory(apk, int(toc_segment.ENTRY_INDEX), int(toc_segment.ENTRY_COUNT), "")
        else:  # files for root directory, Only files are expected, without any folders.
            for toc_segment in apk.PACKTOC.TOC_SEGMENT_LIST:
                file_path = get_name_from_name_idx(apk, int(toc_segment.NAME_IDX)).replace("\\", "/")
                TREE["ROOT"][file_path] = toc_segment

    if int(apk.PACKFSLS.ARCHIVE_SEG_COUNT) > 0:
        ofs_name_map = dict()
        for archive_segment in apk.PACKFSLS.ARCHIVE_SEGMENT_LIST:
            archive_name = get_name_from_name_idx(apk, int(archive_segment.NAME_IDX))
            TREE["ARCHIVE"].setdefault(archive_name, {})
            ofs_name_map[int(archive_segment.ARCHIVE_OFFSET)] = archive_name

        for archive in apk.ARCHIVES.ARCHIVE_LIST:
            archive_name = ofs_name_map[archive.ARCHIVE_ofs]
            for file_segment in archive.PACKFSHD.FILE_SEGMENT_LIST:
                file_path = get_name_from_name_idx(archive, int(file_segment.NAME_IDX))
                TREE["ARCHIVE"][archive_name][file_path] = file_segment

    return TREE


def extract_directory(apk, entry_index: int, entry_count: int, path: str):
    for i in range(entry_index, entry_index + entry_count):
        toc_segment = apk.PACKTOC.TOC_SEGMENT_LIST[i]
        if int(toc_segment.IDENTIFIER) == 1:
            extract_directory(apk, int(toc_segment.ENTRY_INDEX), int(toc_segment.ENTRY_COUNT), os.path.join(path, get_name_from_name_idx(apk, int(toc_segment.NAME_IDX))))
        else:
            file_path = os.path.join(path, get_name_from_name_idx(apk, int(toc_segment.NAME_IDX))).replace("\\", "/")
            TREE["ROOT"][file_path] = toc_segment
