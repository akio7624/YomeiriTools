def bytes2hex(v: bytearray) -> str:
    if len(v) == 0:
        return "-"

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


def get_root_file_padding_cnt(size: int) -> int:
    if size % 512 == 0:
        return 0

    n = int(size / 512)

    while True:
        block_size = (n * 512)
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


def archive_padding_type2desc(v: int) -> str:
    if v == 1:
        return "Padded archive to be divisible by 2048"
    elif v == 2:
        return "Padded archive to be divisible by 512"
