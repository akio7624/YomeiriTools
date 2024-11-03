import unittest
from datatype.chararray import chararray, CharArrayException


class TestCharArray(unittest.TestCase):
    def setUp(self):
        self.chararray = chararray(size=5)

    def test_create_instance(self):
        with self.assertRaises(CharArrayException):
            chararray(size=-1)

        with self.assertRaises(CharArrayException):
            chararray(size=0)

        with self.assertRaises(CharArrayException):
            chararray(size=5, value=99)

    def test_set_from_str(self):
        with self.assertRaises(CharArrayException):
            self.chararray.from_str("abcdefghij")

        with self.assertRaises(CharArrayException):
            self.chararray.from_str("가나다")

        self.chararray.from_str("abcde")
        self.assertEqual(str(self.chararray), "abcde")

        self.chararray.from_str("abc")
        self.assertEqual(str(self.chararray), "abc\0\0")

    def test_set_from_bytearray(self):
        with self.assertRaises(CharArrayException):
            self.chararray.from_bytearray(bytearray("abcdefghij", "ascii"))

        # with self.assertRaises(CharArrayException):
        #     self.chararray.set_from_bytearray(bytearray("가나다", "ascii"))

        self.chararray.from_bytearray(bytearray("abcde", "ascii"))
        self.assertEqual(str(self.chararray), "abcde")

        self.chararray.from_bytearray(bytearray("abc", "ascii"))
        self.assertEqual(str(self.chararray), "abc\0\0")

    def test_to_bytearray(self):
        self.chararray.from_str("abcde")
        self.assertEqual(self.chararray.to_bytearray(), bytearray("abcde", "ascii"))

        self.chararray.from_str("abc\0\0")
        self.assertEqual(self.chararray.to_bytearray(), bytearray("abc\0\0", "ascii"))

        self.chararray.from_str("abc")
        self.assertEqual(self.chararray.to_bytearray(), bytearray("abc\0\0", "ascii"))

    def test_to_str(self):
        self.chararray.from_str("abcde")
        self.assertEqual(self.chararray.to_str(), "abcde")

        self.chararray.from_str("abc\0\0")
        self.assertEqual(self.chararray.to_str(), "abc\0\0")

        self.chararray.from_str("abc")
        self.assertEqual(self.chararray.to_str(), "abc\0\0")


if __name__ == "__main__":
    unittest.main()

