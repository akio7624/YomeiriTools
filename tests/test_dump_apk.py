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

    def test_dump_table_fs_apk(self):
        self.parser = DumpApk(self.fs_apk_path, os.path.join(self.samples_path, "dump_result", "test__dump_apk__fs.apk__.txt"), "table", True)
        self.parser.dump()

    def test_dump_table_stage_apk(self):
        self.parser = DumpApk(self.stage_apk_path, os.path.join(self.samples_path, "dump_result", "test__dump_apk__stage.apk__.txt"), "table", True)
        self.parser.dump()


if __name__ == '__main__':
    unittest.main()
