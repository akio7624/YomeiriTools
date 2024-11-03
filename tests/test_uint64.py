import unittest
from datatype.uint64 import uint64, Uint64Exception


class TestCharArray(unittest.TestCase):
    def setUp(self):
        self.num = uint64()
        self.arr_big = bytearray(b"\x11\x22\x10\xF4\x7D\xE9\x81\x15")  # 1234567890123456789 big endian
        self.arr_little = bytearray(b"\x15\x81\xE9\x7D\xF4\x10\x22\x11")  # 1234567890123456789 little endian

    def test_create_instance(self):
        self.assertEqual(int(self.num), 0)

        with self.assertRaises(Uint64Exception):
            uint64(-10)

        with self.assertRaises(Uint64Exception):
            uint64(uint64.MAX_VALUE + 1)

        with self.assertRaises(Uint64Exception):
            uint64("123")

    def test_from_int(self):
        with self.assertRaises(Uint64Exception):
            uint64().from_int(-10)

        with self.assertRaises(Uint64Exception):
            uint64().from_int(uint64.MAX_VALUE + 1)

        self.num.from_int(123)
        self.assertEqual(int(self.num), 123)

    def test_from_bytearray(self):
        self.num.from_bytearray(self.arr_big, endian=">")
        self.assertEqual(int(self.num), 1234567890123456789)

        self.num.from_bytearray(self.arr_little, endian="<")
        self.assertEqual(int(self.num), 1234567890123456789)

        self.num.from_bytearray(self.arr_little)
        self.assertEqual(int(self.num), 1234567890123456789)

    def test_to_int(self):
        self.num.from_int(123)
        self.assertEqual(self.num.to_int(), 123)

    def test_to_bytearray(self):
        self.num.from_bytearray(self.arr_little)
        self.assertEqual(self.num.to_bytearray(), self.arr_little)

        self.num.from_bytearray(self.arr_big, endian=">")
        self.assertEqual(self.num.to_bytearray(endian=">"), self.arr_big)

        self.assertNotEqual(self.num.to_bytearray(endian=">"), self.arr_little)
        self.assertNotEqual(self.num.to_bytearray(endian="<"), self.arr_big)


if __name__ == "__main__":
    unittest.main()

