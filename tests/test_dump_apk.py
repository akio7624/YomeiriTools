import hashlib
import os.path
import unittest

from scripts.dump_apk import DumpApk


class TestDumpApk(unittest.TestCase):
    def setUp(self):
        self.samples_path = os.path.join("..", "samples")
        self.all_apk_path = os.path.join("..", "samples", "all.apk")
        self.fs_apk_path = os.path.join("..", "samples", "fs.apk")
        self.stage_apk_path = os.path.join("..", "samples", "stage.apk")

    def test_dump_table_all_apk(self):
        self.parser = DumpApk(self.all_apk_path, os.path.join(self.samples_path, "dump_result", "test__dump_apk__all.apk__.txt"), "table", True)
        self.parser.dump()

    def test_is_dump_same_with_original_all_apk(self):
        self.parser = DumpApk(self.all_apk_path, os.path.join(self.samples_path, "dump_result", "test__dump_apk__all.apk__.txt"), "table", True)
        self.parser.dump(debug_no_dump=True)

        with open(self.all_apk_path, "rb") as f:
            data = f.read()
            original_md5 = hashlib.md5(data).hexdigest()
            original_size = len(data)

        with open("../samples/temp.apk", "wb") as f:
            f.write(self.parser.APK.to_bytearray())

        dumped_md5 = hashlib.md5(self.parser.APK.to_bytearray()).hexdigest()
        dumped_size = len(self.parser.APK.to_bytearray())

        self.assertEqual(original_size, dumped_size)
        self.assertEqual(original_md5, dumped_md5)

    def test_dump_table_fs_apk(self):
        self.parser = DumpApk(self.fs_apk_path, os.path.join(self.samples_path, "dump_result", "test__dump_apk__fs.apk__.txt"), "table", True)
        self.parser.dump()

    def test_is_dump_same_with_original_fs_apk(self):
        self.parser = DumpApk(self.fs_apk_path, os.path.join(self.samples_path, "dump_result", "test__dump_apk__fs.apk__.txt"), "table", True)
        self.parser.dump(debug_no_dump=True)

        with open(self.fs_apk_path, "rb") as f:
            data = f.read()
            original_md5 = hashlib.md5(data).hexdigest()
            original_size = len(data)

        with open("../samples/temp.apk", "wb") as f:
            f.write(self.parser.APK.to_bytearray())

        dumped_md5 = hashlib.md5(self.parser.APK.to_bytearray()).hexdigest()
        dumped_size = len(self.parser.APK.to_bytearray())

        self.assertEqual(original_size, dumped_size)
        self.assertEqual(original_md5, dumped_md5)

    def test_dump_table_stage_apk(self):
        self.parser = DumpApk(self.stage_apk_path, os.path.join(self.samples_path, "dump_result", "test__dump_apk__stage.apk__.txt"), "table", True)
        self.parser.dump()

    def test_is_dump_same_with_original_stage_apk(self):
        self.parser = DumpApk(self.stage_apk_path, os.path.join(self.samples_path, "dump_result", "test__dump_apk__stage.apk__.txt"), "table", True)
        self.parser.dump(debug_no_dump=True)

        with open(self.stage_apk_path, "rb") as f:
            data = f.read()
            original_md5 = hashlib.md5(data).hexdigest()
            original_size = len(data)

        with open("../samples/temp.apk", "wb") as f:
            f.write(self.parser.APK.to_bytearray())

        dumped_md5 = hashlib.md5(self.parser.APK.to_bytearray()).hexdigest()
        dumped_size = len(self.parser.APK.to_bytearray())

        self.assertEqual(original_size, dumped_size)
        self.assertEqual(original_md5, dumped_md5)


if __name__ == '__main__':
    unittest.main()
