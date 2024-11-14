import hashlib
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

    def test_is_dump_same_with_original(self):
        self.parser = DumpIdx(self.pack_idx_path, os.path.join(self.samples_path, "dump_result", "test__dump_apk__all.apk__.txt"), "table", True)
        self.parser.dump(debug_no_dump=True)

        with open(self.pack_idx_path, "rb") as f:
            data = f.read()
            original_md5 = hashlib.md5(data).hexdigest()
            original_size = len(data)

        with open("../samples/temp.idx", "wb") as f:
            f.write(self.parser.IDX.to_bytearray())

        dumped_md5 = hashlib.md5(self.parser.IDX.to_bytearray()).hexdigest()
        dumped_size = len(self.parser.IDX.to_bytearray())

        self.assertEqual(original_size, dumped_size)
        self.assertEqual(original_md5, dumped_md5)

if __name__ == '__main__':
    unittest.main()
