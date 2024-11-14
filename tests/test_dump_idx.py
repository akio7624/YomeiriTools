import os.path
import unittest

from scripts.dump_idx import DumpIdx


class TestDumpApk(unittest.TestCase):
    def setUp(self):
        self.samples_path = os.path.join("..", "samples")
        self.pack_idx_path = os.path.join("..", "samples", "pack.idx")

    def test_dump_table_pack_idx(self):
        self.parser = DumpIdx(self.pack_idx_path, os.path.join(self.samples_path, "dump_result", "test__dump_idx__pack.idx__.txt"), "table", True)
        self.parser.dump()


if __name__ == '__main__':
    unittest.main()
