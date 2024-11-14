[![en](https://img.shields.io/badge/lang-en-red.svg)](README.md)
[![kr](https://img.shields.io/badge/lang-kr-green.svg)](README.kr.md)

---

# Outline
Basically, these are scripts made for the game <Nisekoi Yomeiri!?> Korean patch, but they may be available for other games that use the same format. Other games are not tested enough to cause errors, but at least they will help with the analysis.

This README has been translated through a translator.


# Script Help
```
ymtools.exe [-h] <SCRIPT_NAME> <options ...>

-------------------------------------------------------
-h			print this guide
SCRIPT_NAME		select the script name you want to run


ymtools.exe DUMP_APK -i <input_apk_path> [-o <dump_output_path>] [-t <table>] [-q]

-i P	path P of the apk file to dump
-o P	save the dump result as a file in path P
    	if you omit this option, it will only print to the terminal
-t T	specifies the type of dump. the default is "table"
    	"table" only print important information about the included file
-q	does not print dump results with or without option -o

ymtools.exe DUMP_IDX -i <input_idx_path> [-o <dump_output_path>] [-t <table>] [-q]

-i P	path P of the idx file to dump
-o P	save the dump result as a file in path P
    	if you omit this option, it will only print to the terminal
-t T	specifies the type of dump. the default is "table"
    	"table" only print important information about the included file
-q	does not print dump results with or without option -o

ymtools.exe UNPACK_APK -i <input_apk_path> -o <output_directory_path> [-e <overwrite|skip>]

-i P	path P of the apk file to unpack
-o P	save the unpacked file in path P
-e T	specifies how the file to be extracted is handled when it already exists in the folder
    	"overwrite" overwrites existing files
    	"skip" leaves the existing file intact and skips
    	the default is "overwrite"

ymtools.exe PATCH_APK -i <input_apk_path> <directory_for_pack> -o <output_path>

-i P Q	path P of the apk file to use for packing
      	it is recommended to always use the original apk file.
      	this file does not change.
      	path Q of the directory to use for packing
      	the structure of the directory must remain the same as the apk
      	for faster speeds, I recommend that you keep only the changed files
-o P  	save the packed apk file in path P

The 'PATCH' method only modifies information for files that have changed within an existing APK file.
Therefore, a base APK file is required, and changes are applied to a copy of this file.
This method is generally recommended when modifying files within an APK file.


ymtools.exe PACK_APK -i <directory_for_pack> -o <output_path>

-i P  	path P of the directory to use for packing
-o P  	save the packed apk file in path P

The 'PACK' method creates a new APK file using all files in the directory specified by the -i option.
Therefore, a base APK file is not required, but this process may take longer if there are many files.


ymtools.exe PACK_APK -i <input_apk_path ...> -o <output_path>

-i P  	A listing of APK file paths to be used for generating the IDX file.
-o P  	save the idx file in path P
      
Generate IDX files from APK files separated by spaces.
```

# APK file structure analysis
Moved to [https://github.com/akio7624/ApkIdxTemplate](https://github.com/akio7624/ApkIdxTemplate)