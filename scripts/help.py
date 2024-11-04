from utils.ProgramInfo import *

HELP_CMD = f"""
==================================================================
   This is a tool for APK and IDX files found in certain games.
==================================================================

{TOOL_NAME} v{TOOL_VERSION} Released on {TOOL_UPDATE_DATE.strftime('%Y.%m.%d')}

:: Simple Usage ::
ymtools.exe [-h] <SCRIPT_NAME> <options ...>

-------------------------------------------------------
-h\t\t\tprint this guide
SCRIPT_NAME\t\tselect the script name you want to run


"""

HELP_DUMP_APK = """
ymtools.exe DUMP_APK -i <input_apk_path> [-o <dump_output_path>] [-t <table|json>] [-q]

-i P\tpath P of the apk file to dump
-o P\tsave the dump result as a file in path P
    \tif you omit this option, it will only print to the terminal
-t T\tspecifies the type of dump. the default is "table"
    \t"table" only print important information about the included file
    \t"json" analyzes all areas of the apk file and print them in json format
-q\tdoes not print dump results with or without option -o
"""

HELP_DUMP_IDX = """
ymtools.exe DUMP_IDX -i <input_idx_path> [-o <dump_output_path>] [-t <table|json>] [-q]

-i P\tpath P of the idx file to dump
-o P\tsave the dump result as a file in path P
    \tif you omit this option, it will only print to the terminal
-t T\tspecifies the type of dump. the default is "table"
    \t"table" only print important information about the included file
    \t"json" analyzes all areas of the apk file and print them in json format
-q\tdoes not print dump results with or without option -o
"""

HELP_UNPACK_APK = """
ymtools.exe UNPACK_APK -i <input_apk_path> -o <output_directory_path> [-e <overwrite|skip>]

-i P\tpath P of the apk file to unpack
-o P\tsave the unpacked file in path P
-e T\tspecifies how the file to be extracted is handled when it already exists in the folder
    \t"overwrite" overwrites existing files
    \t"skip" leaves the existing file intact and skips
    \tthe default is "overwrite"
"""

HELP_PATCH_APK = """
ymtools.exe PATCH_APK -i <input_apk_path> <directory_for_pack> -o <output_path>

-i P Q\tpath P of the apk file to use for packing
      \tit is recommended to always use the original apk file.
      \tthis file does not change.
      \tpath Q of the directory to use for packing
      \tthe structure of the directory must remain the same as the apk
      \tfor faster speeds, I recommend that you keep only the changed files
-o P  \tsave the packed apk file in path P

The 'PATCH' method only modifies information for files that have changed within an existing APK file.
Therefore, a base APK file is required, and changes are applied to a copy of this file.
This method is generally recommended when modifying files within an APK file.

"""

HELP_PACK_APK = """
ymtools.exe PACK_APK -i <directory_for_pack> -o <output_path>

-i P  \tpath P of the directory to use for packing
-o P  \tsave the packed apk file in path P

The 'PACK' method creates a new APK file using all files in the directory specified by the -i option.
Therefore, a base APK file is not required, but this process may take longer if there are many files.

"""

HELP_MAKE_IDX = """
ymtools.exe PACK_APK -i <input_apk_path ...> -o <output_path>

-i P  \tA listing of APK file paths to be used for generating the IDX file.
-o P  \tsave the idx file in path P
      
Generate IDX files from APK files separated by spaces.

"""

HELP_ALL = HELP_CMD + HELP_DUMP_APK + HELP_DUMP_IDX + HELP_UNPACK_APK + HELP_PATCH_APK + HELP_PACK_APK + HELP_MAKE_IDX
