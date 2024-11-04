def bytes2hex(v: bytearray) -> str:
    return " ".join(f"{b:02X}" for b in v).zfill(8)


def hexoffset(v: int, size: int = 8) -> str:
    return f"0x{v:08X}"
