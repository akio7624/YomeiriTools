import os
import unittest

from scripts.make_idx import MakeIdx


class TextMakeIdx(unittest.TestCase):
    def setUp(self):
        self.samples_path = os.path.join("..", "samples")
        self.patched_path = os.path.join("..", "patched")
        os.makedirs(self.patched_path, exist_ok=True)

        self.all_apk_path = os.path.join("..", "patched", "all.apk")
        self.fs_apk_path = os.path.join("..", "patched", "fs.apk")

        self.patched_idx_path = os.path.join(self.patched_path, "pack.idx")

    def test_make_idx(self):
        MakeIdx([self.all_apk_path, self.fs_apk_path], self.patched_idx_path).make()


if __name__ == '__main__':
    unittest.main()
