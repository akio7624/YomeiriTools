* English(this)
* [Korean(this)](README.md)

# Outline
Basically, these are scripts made for the game <Nisekoi Yomeiri!?> Korean patch, but they may be available for other games that use the same format. Other games are not tested enough to cause errors, but at least they will help with the analysis.

This README has been translated through a translator.


# Script Help
```
python main.py [-h] < DUMP_APK    <options...>
                      | DUMP_IDX
                      | UNPACK_APK
                      | PACK_ALL_APK
                      | PACK_FS_APK  >
-------------------------------------------------------
-h                      print this guide
SCRIPT_NAME             select the script name you want to run (required)


:: Script Usage ::
python main.py DUMP_APK -i <input_apk_path> [-o <dump_output_path>] [-t <table|json>] [-q]

-i P    path P of the apk file to dump
-o P    save the dump result as a file in path P
        if you omit this option, it will only print to the terminal
-t T    specifies the type of dump. the default is "table"
        "table" only print important information about the included file
        "json" analyzes all areas of the apk file and print them in json format
-q      does not print dump results with or without option -o

python main.py DUMP_IDX -i <input_apk_path> [-o <dump_output_path>] [-t <table|json>] [-q]

-i P    path P of the idx file to dump
-o P    save the dump result as a file in path P
        if you omit this option, it will only print to the terminal
-t T    specifies the type of dump. the default is "table"
        "table" only print important information about the included file
        "json" analyzes all areas of the apk file and print them in json format
-q      does not print dump results with or without option -o


python main.py UNPACK_APK -i <input_apk_path> -o <dump_output_path> [-e <overwrite|skip>] [-d]

-i P    path P of the apk file to unpack
-o P    save the unpacked file in path P
-e T    specifies how the file to be extracted is handled when it already exists in the folder
        "overwrite" overwrites existing files
        "skip" leaves the existing file intact and skips
        the default is "overwrite"
-d      print debug information

python main.py PACK_APK -i <input_apk_path> <directory_for_pack> [-x <input_idx_path>] -o <output_dir_path> [-d]

-i P Q  path P of the apk file to use for packing
        it is recommended to always use the original apk file.
        this file does not change.
        path Q of the directory to use for packing
        the structure of the directory must remain the same as the apk
        for faster speeds, I recommend that you keep only the changed files
-x P    path P of the idx file to which you want to patch changes in apk file
-o P    save the packed apk file in path P
        if you use -x option for idx file, the idx file is saved in path P
-d      print debug information
```

# APK file structure analysis
Moved to [https://github.com/akio7624/ApkIdxTemplate](https://github.com/akio7624/ApkIdxTemplate)