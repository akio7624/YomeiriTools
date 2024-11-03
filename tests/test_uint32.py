import unittest
from datatype.uint32 import uint32, Uint32Exception


class TestCharArray(unittest.TestCase):
    def setUp(self):
        self.num = uint32()

    def test_create_instance(self):
        self.assertEqual(int(self.num), 0)

        with self.assertRaises(Uint32Exception):
            uint32(-10)

        with self.assertRaises(Uint32Exception):
            uint32(9999999999)

        with self.assertRaises(Uint32Exception):
            uint32("123")

    def test_from_int(self):
        with self.assertRaises(Uint32Exception):
            uint32().from_int(-10)

        with self.assertRaises(Uint32Exception):
            uint32().from_int(9999999999)

        self.num.from_int(123)
        self.assertEqual(int(self.num), 123)

    def test_from_bytearray(self):
        arr_big = bytearray(b"\x07\x5B\xCD\x15")  # 123456789 big endian
        arr_little = bytearray(b"\x15\xCD\x5B\x07")  # 123456789 little endian

        self.num.from_bytearray(arr_big, endian=">")
        self.assertEqual(int(self.num), 123456789)

        self.num.from_bytearray(arr_little, endian="<")
        self.assertEqual(int(self.num), 123456789)

        self.num.from_bytearray(arr_little)
        self.assertEqual(int(self.num), 123456789)

    def test_to_int(self):
        self.num.from_int(123)
        self.assertEqual(self.num.to_int(), 123)

    def test_to_bytearray(self):
        arr_little = bytearray(b"\x15\xCD\x5B\x07")  # 123456789 little endian
        self.num.from_bytearray(arr_little)
        self.assertEqual(self.num.to_bytearray(), arr_little)

        arr_big = bytearray(b"\x07\x5B\xCD\x15")  # 123456789 big endian
        self.num.from_bytearray(arr_big, endian=">")
        self.assertEqual(self.num.to_bytearray(endian=">"), arr_big)

        self.assertNotEqual(self.num.to_bytearray(endian=">"), arr_little)
        self.assertNotEqual(self.num.to_bytearray(endian="<"), arr_big)


if __name__ == "__main__":
    unittest.main()

