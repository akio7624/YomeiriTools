HELP_CMD = """
=================================================================
     The collection of tools for modding <Nisekoi Yomeiri!?>     
    It supports dumps, extractions, and patches of apk files.
                   (Not an Android apk file)
           This tool is experimental and not perfect.       
            It's basically made for a specific game,
           but it can also be useful for other games.
=================================================================

ymtools v1.0.0 Released on 2024.08.02

:: Simple Usage ::
python main.py [-h] < DUMP_APK         <options...>
                      | DUMP_IDX
                      | UNPACK_APK
                      | PACK_APK >
-------------------------------------------------------
-h\t\t\tprint this guide
SCRIPT_NAME\t\tselect the script name you want to run


:: Script Usage ::
If you use exe file, replace "python main.py" to "ymtools.exe"

"""

HELP_DUMP_APK = """
python main.py DUMP_APK -i <input_apk_path> [-o <dump_output_path>] [-t <table|json>] [-q]

-i P\tpath P of the apk file to dump
-o P\tsave the dump result as a file in path P
    \tif you omit this option, it will only print to the terminal
-t T\tspecifies the type of dump. the default is "table"
    \t"table" only print important information about the included file
    \t"json" analyzes all areas of the apk file and print them in json format
-q\tdoes not print dump results with or without option -o
"""

HELP_DUMP_IDX = """
python main.py DUMP_IDX -i <input_apk_path> [-o <dump_output_path>] [-t <table|json>] [-q]

-i P\tpath P of the idx file to dump
-o P\tsave the dump result as a file in path P
    \tif you omit this option, it will only print to the terminal
-t T\tspecifies the type of dump. the default is "table"
    \t"table" only print important information about the included file
    \t"json" analyzes all areas of the apk file and print them in json format
-q\tdoes not print dump results with or without option -o
"""

HELP_UNPACK_APK = """

python main.py UNPACK_APK -i <input_apk_path> -o <dump_output_path> [-e <overwrite|skip>] [-d]

-i P\tpath P of the apk file to unpack
-o P\tsave the unpacked file in path P
-e T\tspecifies how the file to be extracted is handled when it already exists in the folder
    \t"overwrite" overwrites existing files
    \t"skip" leaves the existing file intact and skips
    \tthe default is "overwrite"
-d\tprint debug information
"""

HELP_PACK_APK = """
python main.py PACK_APK -i <input_apk_path> <directory_for_pack> [-x <input_idx_path>] -o <output_dir_path> [-d]

-i P Q\tpath P of the apk file to use for packing
      \tit is recommended to always use the original apk file.
      \tthis file does not change.
      \tpath Q of the directory to use for packing
      \tthe structure of the directory must remain the same as the apk
      \tfor faster speeds, I recommend that you keep only the changed files
-x P  \tpath P of the idx file to which you want to patch changes in apk file
-o P  \tsave the packed apk file in path P
      \tif you use -x option for idx file, the idx file is saved in path P
-d    \tprint debug information
"""

HELP_ALL = HELP_CMD + HELP_DUMP_APK + HELP_DUMP_IDX + HELP_UNPACK_APK + HELP_PACK_APK
