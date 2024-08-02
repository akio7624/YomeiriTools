import struct


class BinaryReader:
    __RAW: bytearray = bytearray()
    __OFFSET: int = 0

    def __init__(self, data: bytearray):
        if type(data) is not bytearray:
            raise BinaryManagerException(f"BinaryReader only accepts type bytearray")
        self.__RAW = data
        self.__OFFSET = -1

    def append(self, value: int):
        self.__RAW.append(value)

    def append_array(self, value: bytearray):
        self.__RAW.extend(value)

    def append_string(self, value: str):
        self.__RAW.extend(value.encode())

    def set_bytes(self, value: int, pos: int):
        self.__RAW[pos] = value

    def replace_bytes(self, arr: bytearray, pos: int):
        self.__RAW[pos:pos+len(arr)] = arr

    def insert_bytes(self, pos: int, arr: bytearray):
        self.__RAW[pos:pos] = arr

    def delete_bytes_range(self, s: int, length: int):
        del self.__RAW[s:s+length]

    def clear(self):
        self.__RAW.clear()
        self.__OFFSET = -1

    def skip(self, n):
        self.__OFFSET += n

    def size(self) -> int:
        return len(self.__RAW)

    def get_1byte(self) -> int:
        if self.__OFFSET + 1 < self.size():
            result = self.__RAW[self.__OFFSET+1]
            self.__OFFSET += 1
            return result
        else:
            print(f"BinaryManager get_1byte() OutOfRange")
            return 0

    def get_1byte_2(self) -> int:
        if self.__OFFSET + 1 < self.size():
            result = self.__RAW[self.__OFFSET+1]
            self.__OFFSET += 1
            return result
        else:
            # print(f"BinaryManager get_1byte() OutOfRange")
            return None

    def get_buffer(self, length: int) -> bytearray:
        if self.__OFFSET + length <= self.size():
            result = bytearray(self.__RAW[self.__OFFSET:self.__OFFSET+length])
            self.__OFFSET += length
            return result
        else:
            print(f"BinaryManager get_buffer() OutOfRange")
            return bytearray()

    def get_buffer_all(self) -> bytearray:
        return bytearray(self.__RAW)

    def seek(self, offset: int):
        self.__OFFSET = offset

    def get_position(self) -> int:
        return self.__OFFSET

    def decode_u32(self, offset: int) -> int:
        try:
            result = struct.unpack("<I", self.__RAW[offset:offset+4])[0]
        except struct.error:
            result = 0
        return result

    def read_u32(self) -> int:
        offset = self.__OFFSET
        try:
            result = struct.unpack("<I", self.__RAW[offset:offset+4])[0]
        except struct.error:
            result = 0
        self.__OFFSET += 4
        return result

    def decode_u64(self, offset: int) -> int:
        try:
            result = struct.unpack("<Q", self.__RAW[offset:offset+8])[0]
        except struct.error:
            result = 0
        return result

    def read_u64(self) -> int:
        offset = self.__OFFSET
        try:
            result = struct.unpack("<Q", self.__RAW[offset:offset+8])[0]
        except struct.error:
            result = 0
        self.__OFFSET += 8
        return result

    def decode_string_utf8(self, offset: int) -> str:
        temp: bytearray = bytearray()
        while offset < self.size():
            b: int = self.__RAW[offset]
            if b == 0:
                temp.append(0)
                break
            temp.append(b)
            offset += 1
        return temp.decode("utf-8")

    def read_string_utf8(self) -> str:
        offset = self.__OFFSET
        temp: bytearray = bytearray()
        while offset < self.size():
            b: int = self.__RAW[offset]
            if b == 0:
                temp.append(0)
                break
            temp.append(b)
            offset += 1
        self.__OFFSET += len(temp)
        return temp.decode("utf-8")

    def read_string_bytes(self, n: int):
        offset = self.__OFFSET
        self.__OFFSET += n
        return self.__RAW[offset:offset+n].decode()


    def remove_last(self):
        self.__RAW = self.__RAW[:self.size()-1]

    def get_raw(self) -> bytearray:
        return self.__RAW

    def __getitem__(self, index: int):
        return self.__RAW[index]

    def findloc(self, target: str):
        return self.__OFFSET + self.__RAW[self.__OFFSET:].index(target.encode())

    def padding(self, size: int):
        tmp = self.__OFFSET % size
        if(tmp):
            self.skip(size - tmp)


class BinaryManagerException(Exception):
    pass
