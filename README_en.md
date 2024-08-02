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
The apk file is an archive format file that contains various key data necessary for games. It is a format that has nothing to do with the apk, which is an Android application installation file.

![apk_01](img/apk_01.jpg)
Basically, it has the same structure as above. Files are listed at the end of the file, and if there is additional archive, the archive is also listed at the end of the file.
Each archive has its own file data.

The file was arbitrarily named in this paper because the structure was not officially disclosed and the exact name of each area was unknown.

## File Header
|Name|Type|Size (byte)|Description|
|:---:|:---:|:---:|:---|
|ENDIANESS|string|8|Endian of file. <br> **ENDILTLE**: little endian <br> **ENDIBIGE**: big endian|
|PADDING|bytes|8|Padding to fill the space|

## PACKHEDR
|Name|Type|Size (byte)|Description|
|:---:|:---:|:---:|:---|
|PACKHEDR|string|8|Table Signature|
|HEADER SIZE|uint64|8|Table Size|
|unknown_1|?|8||
|FILE LIST OFFSET|int|4|File area start point offset for ROOT ARCHIVE based on file start|
|unknown_2|?|4||
|unknown_3|?|16||
Most tables in apk files start with signature 8 bytes + table content size 8 bytes.
The table content size refers to the size of the rest of the parts except for this 16 bytes.

That is, when looking at the table above, it can be seen that HEADER_SIZE is 8+4+4+16=32 bytes.

## PACKTOC
|Name|Type|Size (byte)|Description|
|:---:|:---:|:---:|:---|
|PACKTOC|string|8|Table Signature. The last character is blank.|
|HEADER SIZE|uint64|8|Table Size|
|TOC SEG SIZE|int|4|Size of one TOC SEGMENT|
|TOC SEG COUNT|int|4|the number of TOC SEGMENT's|
|unknown_1|?|4||
|ZERO|bytes|4|Padding|
|TOC_SEGMENT_LIST|TOC_SEG[]|TOC_SEG_SIZE * <br>TOC_SEG_COUNT|List of TOC SEGMENT|
|TABLE PADDING|||Padding so that the size of the table is divided by 16|

Tables PACKTOC, PACKFSLS, and GENESTRT have TABLE PADDING.
If the table size is not a multiple of 16, this value fills the remaining space with 0s to make it a multiple of 16.

### TOC SEGMENT
|Name|Type|Size (byte)|Description|
|:---:|:---:|:---:|:---|
|IDENTIFIER|int|4|File identifier|
|NAME IDX|int|4|Index of the filename in the string list present in the GENESTRT table|
|ZERO|bytes|8|Padding?|
|FILE OFFSET|uint64|8|Offsetting the start point of a file based on the beginning of the file|
|SIZE|uint64|8|uncompressed size of file(byte)|
|ZSIZE|uint64|8|compressed size of file(byte)|

File compression uses zlib by default.

#### IDENTIFIER
|Value|hex|Meaning|
|:---:|:---:|:---|
|0|0x0000|Uncompressed data|
|1|0x0001|Estimated as a folder, not a file that is actually extracted. Estimated to be no problem ignoring it when extracting|
|512|0x0200|compressed data|

## PACKFSLS
|Name|Type|Size (byte)|Description|
|:---:|:---:|:---:|:---|
|PACKFSLS|string|8|Table Signature|
|HEADER SIZE|uint64|8|Table Size|
|ARCHIVE COUNT|int|4|Number of additional archives|
|ARCHIVE SEG SIZE|int|4|Size of one ARCHIVE SEGMENT|
|unknown_1||4||
|unknown_2||4||
|ARCHIVE SEG LIST|ARCHIVE_SEG[]|List of ARCHIVE_COUNT * <br> ARCHIVE_SEG_SIZE|ARCHIVE SEGMENT|
|TABLE PADDING|||Padding so that the size of the table is divided by 16|
The apk file may or may not contain more than one archive. If included, the archives are listed from the very end of the file, and each archive has its own file information.

If an archive exists, each archive becomes a folder, and the files in each archive are located within that folder.
For Nisekoi Yomeiri, all.apk does not have such an archive, and fs.apk has an archive and files are stored in the folder.

### ARCHIVE SEGMENT
|Name|Type|Size (byte)|Description|
|:---:|:---:|:---:|:---|
|NAME IDX|int|4|Index of the filename in the string list present in the GENESTRT table|
|ZERO|int|4|패딩|
|ARCHIVE OFFSET|uint64|8|Starting point offset for archive based on file beginning|
|SIZE|uint8|8|Size of archive|
|unknown_1||16||

## GENESTRT
|Name|Type|Size (byte)|Description|
|:---:|:---:|:---:|:---|
|GENESTRT|string|8|Table Signature|
|GENESTRT SIZE|uint64|8|Table Size|
|STR OFFSET COUNT|int|4|Number of string offsets|
|unknown_1||4||
|HEADER SIZE +<br>STR OFFSET LIST SIZE|int|4|Sum of header size and offset list size|
|GENESTRT SIZE|int|4|Table Size|
|STR OFFSET LIST|int[]||List of string offsets|
|PAD|bytes|4|Padding|
|STRING LIST|string[]||String list|
|TABLE PADDING|bytes||Padding so that the size of the table is divided by 16|

Table that stores the string.

The string information consists of the offset value of the string and the actual string. A string starts at the starting point offset of the STRING LIST plus the offset value of the string and ends in null.

## GENEEOF
|Name|Type|Size (byte)|Description|
|:---:|:---:|:---:|:---|
|GENEEOF|string|8|Table Signature|
|ZERO|bytes|8|Padding|
|TABLE PADDING|bytes||Padding to 0 before file list starts|
The last part of the table, after which the file list of the root archive and the list of archives will appear if the archive exists.

The size of TABLE PADDING is determined by the number of FILE LIST OFFSETs from PACKHEDR minus the starting offset of TABLE PADDING.

## FILE LIST
From now on, files will be listed. It's not just listed. You can think of a file as being in a single block.
The sizes of these blocks are fixed. A block has the smallest size to hold a file, and the rest is padded to zero.

These blocks are listed.

The size of the block is determined as follows.
* File size is a multiple of 512
  * The size of the file is the size of the block.
  * The file is saved without padding.
* in other cases
  * Among the values of 512*n - 1, the minimum size to hold a file is the size of the block.
  * The rest of the space is padded to zero.

Let me give you an example.
Let's say the file size is 23,552 bytes, which is a multiple of 512, so the files will be listed without any additional action.

Suppose the file size is 2752 bytes.
* (512*5)-1 = 2559, which is small to hold a file.
* (512*6)-1 = 3071, which can hold a file.
* (512*7)-1 = 3583. You can hold the file, but there is a smaller value of 3071, so you don't need to calculate it anymore.

The size of the padding will then be 3071 - 2752 = 319 bytes.
After this file is added, it will be padded to zero by 319 bytes, and then the next file will be listed.

## ARCHIVE LIST
If the ARCHIVE COUNT in the PACKFSLS table was not 0, the archive will be listed. Let's look at the structure of the archive.

### ENDIANESS
|Name|Type|Size (byte)|Description|
|:---:|:---:|:---:|:---|
|ENDIANESS|string|8|Endian of archive <br> **ENDILTLE**: little endian <br> **ENDIBIGE**: big endian|
|PADDING|bytes|8|Padding|

### PACKFSHD
|Name|Type|Size (byte)|Description|
|:---:|:---:|:---:|:---|
|PACKFSHD|string|8|Table Signature|
|HEADER SIZE|uint64|8|Table Size|
|unknown_1||4||
|FILE SEG SIZE?|int|4|Estimate the size of a file segment|
|FILE SEG COUNT|int|4|Number of file segments|
|unknown_2|int|4|Same value as FIEL_SEG_SIZE. Why it is duplicated is unknown|
|unknown_3||4||
|FILE SEG LIST|FILE_SEG[]|FILE_SEG_SIZE*<br>FILE_SEG_COUNT|List of FILE SEGMENT|

#### FILE_SEGMENT
|Name|Type|Size (byte)|Description|
|:---:|:---:|:---:|:---|
|NAME_IDX|int|4|Index of the filename in the string list present in the GENESTRT table|
|ZIP|int|4|File compression.<br>**0**: uncompressed<br>**2**: zlib compressed|
|OFFSET|uint64|8|File start point offset based on ARCHIVE OFFSET|
|SIZE|uint64|8|Size of uncompressed file|
|ZSIZE|uint64|8|Size of compressed file. If ZIP is 0, ZSIZE is also 0|

### GENESTRT
|Name|Type|Size (byte)|Description|
|:---:|:---:|:---:|:---|
|GENESTRT|string|8|Table Signature|
|GENESTRT SIZE|uint64|8|Table Size|
|STR OFFSET COUNT|int|4|Number of string offset values|
|unknown_1||4||
|HEADER SIZE +<br>STR OFFSET LIST SIZE|int|4|Sum of header size and offset list size|
|GENESTRT SIZE|int|4|Table Size|
|STR OFFSET LIST|int[]||List of string offsets|
|PAD|bytes|4|Padding|
|STRING LIST|string[]||String list|
|TABLE PADDING|bytes||Padding so that the size of the table is divided by 16|

### FILE LIST
Files in the archive are padded differently than the root archive.
The number of file padding in the root archive was used by calculating the block size as (512*n)-1, but the archive file is padded so that the file size is divided by 16 as in table padding.

This means that the padding size of the archive file is from a minimum of 0 to a maximum of 15.

# Analyzing IDX Files
![idx_01](img/idx_01.jpg)

The idx file is very similar to the apk file. As you can see from the extension, it stores the index for the files in the apk file.
* The idx file copies and lists the PACKHEDR of the apk files.
* The idx file does not have actual file data.
* The idx file does not have an archive. (maybe)

Only data such as the offset, size, and name of the files included in the files are stored, and the rest are the same as the apk file.

However, there is something that has not been achieved yet, but in the case of Nisekoi Yomeiri!?, the files stored in fs.apk in folder format do not exist in pack.idx.
Of course, the file itself is the same as that of all.apk, so it may not matter.

I don't know exactly how the pack.idx file generates indexes from both files because I don't know why fs.apk exists yet.

The current pack.idx file appears to be simply a collection of indexes of all.apk.