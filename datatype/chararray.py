# support only ASCII

class chararray:
    def __init__(self, size: int, value: str | bytearray = None):
        if size < 1:
            raise CharArrayException(f"Size must be a positive integer.  size={size}")

        self.__size = size
        self.__value: list[str] = ["\0" for _ in range(size)]

        if value is not None:
            self.from_value(value)

    def __str__(self):
        return "".join(self.__value)

    def from_str(self, value: str):
        if self.__size < len(value):
            raise CharArrayException(f"The value is larger than the size. size={self.__size}  len(value)={len(value)}")
        if not all(ord(c) < 128 for c in value):
            raise CharArrayException(f"chararray supports only ASCII characters.")

        self.__value = list(value) + ["\0" for _ in range(self.__size - len(value))]

    def from_bytearray(self, value: bytearray):
        if self.__size < len(value):
            raise CharArrayException(f"The value is larger than the size. size={self.__size}  len(value)={len(value)}")
        if not all(c < 128 for c in value):
            raise CharArrayException(f"chararray supports only ASCII characters.")

        self.__value = list(value.decode("ascii")) + ["\0" for _ in range(self.__size - len(value))]

    def from_value(self, value: str | bytearray):
        if isinstance(value, bytearray):
            self.from_bytearray(value)
        elif isinstance(value, str):
            self.from_str(value)
        else:
            raise CharArrayException(f"Value must be bytearray or str.  this={type(value)}")

    def to_str(self) -> str:
        return self.__str__()

    def to_bytearray(self) -> bytearray:
        return bytearray([ord(c) for c in self.__value])


class CharArrayException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
