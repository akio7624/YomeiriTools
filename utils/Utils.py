def bytes2hex(v: bytearray) -> str:
    result = ""

    for i in range(0, len(v), 8):
        result += " ".join(f"{b:02X}" for b in v[i:i+8]).zfill(8)
        result += "\n"

    return result.strip()


def hexoffset(v: int) -> str:
    return f"0x{v:08X}"
