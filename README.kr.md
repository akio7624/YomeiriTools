[![en](https://img.shields.io/badge/lang-en-red.svg)](README.md)
[![kr](https://img.shields.io/badge/lang-kr-green.svg)](README.kr.md)

---

# 개요
기본적으로 게임 <니세코이 요메이리!?> 한글 패치를 위해 만들어진 스크립트들입니다만, 동일한 포맷을 사용하는 다른 게임에 대해서도 사용할 수 있을지도 모릅니다. 다른 게임에 대해서는 테스트가 충분히 되지 않아서 오류가 날 수 있지만 적어도 분석에 도움은 될겁니다.

# 스크립트 도움말
```
python main.py [-h] < DUMP_APK    <options...>
                      | DUMP_IDX
                      | UNPACK_APK
                      | PACK_ALL_APK
                      | PACK_FS_APK  >
-------------------------------------------------------
-h              이 도움말을 출력합니다
SCRIPT_NAME     실행할 스크립트의 이름을 설정합니다 (필수)


:: 스크립트 사용방법 ::
python main.py DUMP_APK -i <input_apk_path> [-o <dump_output_path>] [-t <table|json>] [-q]

-i P    덤프할 apk 파일의 경로 P
-o P    덤프 결과를 저장할 경로 P
        이 옵션을 지정하지 않으면 파일로 저장되지 않고 터미널에 출력만 합니다.
-t T    덤프 결과의 유형을 선택합니다. 기본값은 table입니다.
        "table"은 파일들의 주요 정보만 출력합니다.
        "json"은 파일의 모든 부분을 분석하고 그 결과를 json으로 출력합니다.
-q      옵션 -o의 여부와 관계없이 덤프 결과를 터미널에 출력하지 않습니다.


python main.py DUMP_IDX -i <input_apk_path> [-o <dump_output_path>] [-t <table|json>] [-q]

-i P    덤프할 idx 파일의 경로 P
-o P    덤프 결과를 저장할 경로 P
        이 옵션을 지정하지 않으면 파일로 저장되지 않고 터미널에 출력만 합니다.
-t T    덤프 결과의 유형을 선택합니다. 기본값은 table입니다.
        "table"은 파일들의 주요 정보만 출력합니다.
        "json"은 파일의 모든 부분을 분석하고 그 결과를 json으로 출력합니다.
-q      옵션 -o의 여부와 관계없이 덤프 결과를 터미널에 출력하지 않습니다.


python main.py UNPACK_APK -i <input_apk_path> -o <dump_output_path> [-e <overwrite|skip>] [-d]

-i P    추출할 apk 파일의 경로 P
-o P    추출된 파일들을 저장할 폴더의 경로 P
-e T    추출하려는 파일이 이미 존재할 때 동작을 선택합니다
        "overwrite"는 기존 파일을 덮어씁니다
        "skip"는 기존 파일을 유지합니다
        기본값은 "overwrite"입니다
-d      디버그 정보를 출력합니다.


python main.py PACK_APK -i <input_apk_path> <directory_for_pack> [-x <input_idx_path>] [-o <output_dir_path>] [-d]

-i P Q  패킹에 사용할 apk 파일의 경로 P입니다.
        항상 원본 apk파일을 사용하는것을 추천합니다.
        이 파일은 변경되지 않습니다.
        패치할 파일이 포함된 폴더의 경로 Q입니다.
        폴더의 구조는 기존 apk 파일의 구조와 동일해야합니다.
        빠른 속도를 위해 실제로 수정되어서 패치할 파일만 남겨두는 것을 추천합니다.
-x P    idx 파일 패치를 원할경우 idx 파일의 경로 P입니다.
-o P    패킹된 apk 파일을 저장할 경로 P입니다.
        만약 -x 옵션으로 idx 파일을 선택했다면 idx 파일도 이곳에 저장됩니다.
-d      디버그 정보를 출력합니다.
```

# APK 파일 구조 분석
[https://github.com/akio7624/ApkIdxTemplate](https://github.com/akio7624/ApkIdxTemplate)로 이동함. 