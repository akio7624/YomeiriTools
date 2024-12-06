import os.path
import unittest

from scripts.patch_apk import PatchApk
from scripts.unpack_apk import UnpackApk


class TestDumpApk(unittest.TestCase):
    def setUp(self):
        self.samples_path = os.path.join("..", "samples")
        self.patched_path = os.path.join("..", "patched")
        os.makedirs(self.patched_path, exist_ok=True)

        self.all_apk_path = os.path.join("..", "samples", "all.apk")
        self.fs_apk_path = os.path.join("..", "samples", "fs.apk")
        self.stage_apk_path = os.path.join("..", "samples", "stage.apk")

        self.all_apk_extracted_path = os.path.join(self.samples_path, "extract", "all")
        self.fs_apk_extracted_path = os.path.join(self.samples_path, "extract", "fs")
        self.stage_apk_extracted_path = os.path.join(self.samples_path, "extract", "stage")

        self.patched_all_apk_path = os.path.join(self.patched_path, "all.apk")
        self.patched_fs_apk_path = os.path.join(self.patched_path, "fs.apk")
        self.patched_stage_apk_path = os.path.join(self.patched_path, "stage.apk")

    def test_patch_all_apk(self):
        PatchApk([self.all_apk_path, self.all_apk_extracted_path], self.patched_all_apk_path).patch()

    def test_patch_fs_apk(self):
        PatchApk([self.fs_apk_path, self.fs_apk_extracted_path], self.patched_fs_apk_path).patch()

    def test_patch_stage_apk(self):
        PatchApk([self.stage_apk_path, self.stage_apk_extracted_path], self.patched_stage_apk_path).patch()


if __name__ == '__main__':
    unittest.main()
