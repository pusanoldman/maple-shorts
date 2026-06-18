# 실행 방법 빠른 안내

이 파일은 Maple Shorts를 바로 실행하기 위한 짧은 안내입니다.

## 1. PowerShell 열기

Windows 시작 메뉴에서 `PowerShell`을 검색해서 실행합니다.

## 2. 프로그램 폴더로 이동

```powershell
cd "C:\Users\sjs11\OneDrive\Desktop\maple-shorts"
```

## 3. 원본 영상 넣기

OBS로 녹화한 영상을 아래 폴더에 넣습니다.

```text
C:\Users\sjs11\OneDrive\Desktop\maple-shorts\raw_video
```

예:

```text
raw_video\2026-06-18 19-51-00.mp4
```

## 4. records.csv 수정

아래 파일을 엽니다.

```text
C:\Users\sjs11\OneDrive\Desktop\maple-shorts\records\records.csv
```

예시:

```csv
day,date,map,time,end_meso,drops,memo,video_file
1,2026-06-18,도원경,2시간,550000000,조각 18개,첫 재획,2026-06-18 19-51-00.mp4
```

중요한 점:

```text
video_file 값 = raw_video 폴더 안의 실제 영상 파일명
```

파일명이 다르면 프로그램이 영상을 찾지 못합니다.

## 5. 실행

PowerShell에서 아래 명령어를 입력합니다.

```powershell
python make_short.py
```

## 6. 결과 확인

완성된 쇼츠 영상은 아래 폴더에 생깁니다.

```text
C:\Users\sjs11\OneDrive\Desktop\maple-shorts\output
```

## BGM 넣기

`assets` 폴더에 오디오 파일을 넣으면 자동으로 BGM이 들어갑니다.

지원 확장자:

```text
.mp3, .wav, .m4a, .aac, .flac, .ogg
```

여러 개가 있으면 랜덤으로 하나가 선택됩니다.

## 자주 나는 문제

### 원본 영상이 없어 건너뜁니다

`records.csv`의 `video_file` 이름과 `raw_video` 폴더 안 실제 파일명이 같은지 확인하세요.

### ffmpeg를 찾을 수 없습니다

FFmpeg가 설치되어 있어야 합니다.

확인:

```powershell
ffmpeg -version
```

설치:

```powershell
winget install --id Gyan.FFmpeg
```
