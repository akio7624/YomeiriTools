import argparse
from scripts import help
from scripts.dump_apk import DumpApk
from scripts.dump_idx import DumpIdx
from scripts.pack_apk import PackApk
from scripts.unpack_apk import UnpackApk


class Main:
    parser = None

    def main(self):
        self.init_argparse()
        args = self.parser.parse_args()

        if args.script is None:
            print(help.HELP_ALL)
        elif args.script == "DUMP_APK":
            DumpApk(args.i, args.o, args.t, args.q).dump()
        elif args.script == "DUMP_IDX":
            DumpIdx(args.i, args.o, args.t, args.q).dump()
        elif args.script == "UNPACK_APK":
            UnpackApk(args.i, args.o, args.e, args.d).extract()
        elif args.script == "PACK_APK":
            PackApk(args.i, args.x, args.o, args.d).pack()

    def init_argparse(self):
        self.parser = argparse.ArgumentParser(description="The collection of tools for modding <Nisekoi Yomeiri!?>", add_help=False)
        # self.parser.add_argument("-h", action="store_true", help="Print information for all command")
        subparser = self.parser.add_subparsers(dest="script")

        parser_dump_all_apk = subparser.add_parser("DUMP_APK", add_help=False)
        parser_dump_all_apk.add_argument("-i", type=str, required=True)
        parser_dump_all_apk.add_argument("-o", type=str)
        parser_dump_all_apk.add_argument("-t", type=str, choices=["table", "json"], default="table")
        parser_dump_all_apk.add_argument("-q", action="store_true")

        parser_dump_idx = subparser.add_parser("DUMP_IDX", add_help=False)
        parser_dump_idx.add_argument("-i", type=str, required=True)
        parser_dump_idx.add_argument("-o", type=str)
        parser_dump_idx.add_argument("-t", type=str, choices=["table", "json"], default="table")
        parser_dump_idx.add_argument("-q", action="store_true")

        parser_unpack_apk = subparser.add_parser("UNPACK_APK", add_help=False)
        parser_unpack_apk.add_argument("-i", type=str, required=True)
        parser_unpack_apk.add_argument("-o", type=str, required=True)
        parser_unpack_apk.add_argument("-e", type=str, choices=["overwrite", "skip"], default="overwrite")
        parser_unpack_apk.add_argument("-d", action="store_true")

        parser_pack_fs_apk = subparser.add_parser("PACK_APK", add_help=False)
        parser_pack_fs_apk.add_argument("-i", type=str, required=True, nargs=2)
        parser_pack_fs_apk.add_argument("-x", type=str)
        parser_pack_fs_apk.add_argument("-o", type=str, required=True)
        parser_pack_fs_apk.add_argument("-d", action="store_true")


if __name__ == "__main__":
    Main().main()
