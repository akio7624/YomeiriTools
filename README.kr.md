[![en](https://img.shields.io/badge/lang-en-red.svg)](README.md)
[![kr](https://img.shields.io/badge/lang-kr-green.svg)](README.kr.md)

---

# 개요
기본적으로 게임 <니세코이 요메이리!?> 한글 패치를 위해 만들어진 스크립트들이지만 동일한 파일 포맷을 사용하는 다른 게임에 대해서도 사용할 수 있다.
다른 게임에 대해서는 테스트가 충분히 되지 않아서 오류가 날 수 있지만 적어도 분석에 도움은 될것이다.

# 스크립트 도움말
```
ymtools.exe [-h] <SCRIPT_NAME> <옵션 ...>

-------------------------------------------------------
-h           도움말 출력.
SCRIPT_NAME  실행할 스크립트 이름 선택.


ymtools.exe DUMP_APK -i <input_apk_path> [-o <dump_output_path>] [-t <table|json>] [-q]

-i P       덤프할 APK 파일의 경로 P
-o P       덤프 결과를 경로 P의 파일로 저장한다.
           이 옵션을 생략하면 표준 출력으로만 출력된다.
-t T       덤프의 유형을 지정한다. 기본값은 "table"이다.
           "table"은 포함된 파일에 대한 중요한 정보만 출력한다.
           "json"은 APK 파일의 모든 영역을 분석하여 JSON 형식으로 출력한다.
-q         덤프 결과를 출력하지 않는다. -o 옵션이 있든 없든 상관없다.

ymtools.exe DUMP_IDX -i <input_idx_path> [-o <dump_output_path>] [-t <table|json>] [-q]

-i P       덤프할 APK 파일의 경로 P
-o P       덤프 결과를 경로 P의 파일로 저장한다.
           이 옵션을 생략하면 표준 출력으로만 출력된다.
-t T       덤프의 유형을 지정한다. 기본값은 "table"이다.
           "table"은 포함된 파일에 대한 중요한 정보만 출력한다.
           "json"은 APK 파일의 모든 영역을 분석하여 JSON 형식으로 출력한다.
-q         덤프 결과를 출력하지 않는다. -o 옵션이 있든 없든 상관없다.

ymtools.exe UNPACK_APK -i <input_apk_path> -o <output_directory_path> [-e <overwrite|skip>]

-i P       압축을 풀 APK 파일의 경로 P
-o P       압축 해제된 파일을 경로 P에 저장한다.
-e T       폴더에 이미 존재하는 경우 추출된 파일의 처리 방법을 지정한다.
           "overwrite"는 기존 파일을 덮어쓴다.
           "skip"은 기존 파일을 그대로 두고 건너뛴다.
           기본값은 "overwrite"다.

ymtools.exe PATCH_APK -i <input_apk_path> <directory_for_pack> -o <output_path>

-i P Q     패킹에 사용할 APK 파일의 경로 P
           원본 APK 파일을 항상 사용하는 것이 좋다.
           이 파일은 변경되지 않는다.
           패킹에 사용할 디렉토리의 경로 Q
           디렉토리 구조는 APK와 동일하게 유지되어야 한다.
           빠른 속도를 원한다면 변경된 파일만 유지하는 것이 좋다.
-o P       패킹된 APK 파일을 경로 P에 저장한다.

'PATCH' 방식은 이미 존재하는 APK 파일에서 변경된 파일의 정보만 수정한다.
따라서 기본 APK 파일이 필요하며, 이 파일의 사본에 변경 사항을 적용한다.
이 방법은 APK 파일 내의 파일을 수정할 때 일반적으로 권장된다.


ymtools.exe PACK_APK -i <directory_for_pack> -o <output_path>

-i P       IDX 파일 생성을 위해 사용할 APK 파일 경로의 나열이다.
-o P       패킹된 APK 파일을 경로 P에 저장한다.

'PACK' 방식은 -i 옵션으로 지정된 디렉토리의 모든 파일을 사용하여 새로운 APK 파일을 생성한다.
따라서 기본 APK 파일이 필요 없지만, 파일이 많을 경우 시간이 오래 걸릴 수 있다.


ymtools.exe PACK_APK -i <input_apk_path ...> -o <output_path>

-i P       패킹에 사용할 APK 파일의 경로 P
           이 파일은 변경되지 않는다.
-o P       IDX 파일을 경로 P에 저장한다.

공백으로 구분된 APK 파일들로부터 IDX 파일을 생성한다.
```

# APK 파일 구조 분석
[https://github.com/akio7624/ApkIdxTemplate](https://github.com/akio7624/ApkIdxTemplate)로 이동함. 