import os.path
import unittest

from scripts.unpack_apk import UnpackApk


class TestDumpApk(unittest.TestCase):
    def setUp(self):
        self.samples_path = os.path.join("..", "samples")
        self.extract_path = os.path.join("..", "samples", "extract")
        self.all_apk_path = os.path.join("..", "samples", "all.apk")
        self.fs_apk_path = os.path.join("..", "samples", "fs.apk")
        self.stage_apk_path = os.path.join("..", "samples", "stage.apk")

    def test_all_apk(self):
        outpath = os.path.join(self.extract_path, "all")
        os.makedirs(outpath, exist_ok=True)
        UnpackApk(self.all_apk_path, outpath, "overwrite").extract()

    def test_fs_apk(self):
        outpath = os.path.join(self.extract_path, "fs")
        os.makedirs(outpath, exist_ok=True)
        UnpackApk(self.fs_apk_path, outpath, "overwrite").extract()

    def test_stage_apk(self):
        outpath = os.path.join(self.extract_path, "stage")
        os.makedirs(outpath, exist_ok=True)
        UnpackApk(self.stage_apk_path, outpath, "overwrite").extract()


if __name__ == '__main__':
    unittest.main()
