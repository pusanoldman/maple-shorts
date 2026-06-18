# Maple Shorts

OBS로 녹화한 메이플스토리 재획 영상을 유튜브 쇼츠용 세로 영상으로 자동 편집하는 Python + FFmpeg 프로그램입니다.

이 프로그램은 게임 조작 자동화나 매크로가 아닙니다. 직접 플레이하고 OBS로 녹화한 영상 파일을 편집하는 용도입니다.

## 무엇을 해주나요?

- 가로 영상인 OBS 녹화본을 1080x1920 세로 쇼츠 영상으로 변환합니다.
- 원본 영상의 가운데 부분을 세로 비율로 잘라냅니다.
- 쇼츠 길이는 기본 약 10초입니다.
- 앞 5초는 원본 영상 중 랜덤 구간을 사용합니다.
- 뒤 5초는 원본 영상의 마지막 5초를 사용합니다.
- 영상 위에 재획 일차, 사냥터, 재획 시간, 수익, 드랍, 메모를 자막으로 넣습니다.
- 끝 메소만 입력하면 `5.5억 메소` 같은 형식으로 자동 표시합니다.
- BGM과 폰트는 선택사항입니다.

## 완성 결과 예시

원본:

```text
raw_video/2026-06-18 19-51-00.mp4
```

실행 후 결과:

```text
output/jaehwak_day1_5.5억메소.mp4
```

## 준비물

처음 한 번만 준비하면 됩니다.

### 1. Python 설치

Python 3가 필요합니다.

설치 여부 확인:

```powershell
python --version
```

버전이 나오면 설치되어 있는 것입니다.

### 2. FFmpeg 설치

FFmpeg가 필요합니다. PowerShell에서 아래 명령어가 실행되어야 합니다.

```powershell
ffmpeg -version
ffprobe -version
```

둘 다 버전이 나오면 준비 완료입니다.

Windows에서는 `winget`으로 설치할 수 있습니다.

```powershell
winget install --id Gyan.FFmpeg
```

설치 후 PowerShell을 껐다가 다시 열고 `ffmpeg -version`을 확인하세요.

## 다운로드 방법

GitHub 페이지에서 초록색 `Code` 버튼을 누른 뒤 `Download ZIP`을 선택합니다.

압축을 풀면 `maple-shorts` 폴더가 생깁니다.

## 폴더 구조

```text
maple-shorts/
├─ make_short.py
├─ records.example.csv
├─ raw_video/
│  └─ 원본 영상을 넣는 폴더
├─ output/
│  └─ 완성된 쇼츠가 저장되는 폴더
├─ records/
│  └─ records.csv
└─ assets/
   ├─ bgm.mp3
   └─ font.ttf
```

`raw_video`, `output`, `records`, `assets` 폴더가 없어도 괜찮습니다. 프로그램을 실행하면 자동으로 만들어집니다.

## 가장 쉬운 사용 순서

### 1. PowerShell 열기

Windows 시작 메뉴에서 `PowerShell`을 검색해서 실행합니다.

### 2. 프로그램 폴더로 이동

예를 들어 바탕화면에 압축을 풀었다면:

```powershell
cd "C:\Users\사용자이름\Desktop\maple-shorts"
```

현재 이 프로젝트를 만든 사람의 경로 예시는 다음과 같습니다.

```powershell
cd "C:\Users\sjs11\OneDrive\Desktop\maple-shorts"
```

각자 컴퓨터에서는 경로가 다를 수 있습니다.

### 3. 원본 영상 넣기

OBS로 녹화한 영상을 `raw_video` 폴더에 넣습니다.

예:

```text
raw_video/2026-06-18 19-51-00.mp4
```

영상 파일 이름은 꼭 `test.mp4`일 필요가 없습니다. 대신 CSV의 `video_file` 값과 실제 파일명이 같아야 합니다.

### 4. records.csv 만들기

`records` 폴더 안에 `records.csv` 파일을 만듭니다.

처음에는 `records.example.csv`를 복사해서 `records/records.csv`로 이름을 바꾸면 편합니다.

예시:

```csv
day,date,map,time,end_meso,drops,memo,video_file
1,2026-06-18,도원경,2시간,550000000,조각 18개,첫 재획,2026-06-18 19-51-00.mp4
```

### 5. 실행하기

```powershell
python make_short.py
```

### 6. 결과 확인하기

완성된 쇼츠 영상은 `output` 폴더에 저장됩니다.

```text
output/
```

## CSV 작성법

CSV는 쉼표로 구분된 표 파일입니다. 엑셀이나 메모장으로 수정할 수 있습니다.

| 컬럼 | 뜻 | 예시 |
| --- | --- | --- |
| `day` | 재획 N일차 | `1` |
| `date` | 날짜 | `2026-06-18` |
| `map` | 사냥터 | `도원경` |
| `time` | 재획 시간 | `2시간` |
| `end_meso` | 끝 메소 | `550000000` |
| `drops` | 드랍템 | `조각 18개` |
| `memo` | 메모 | `첫 재획` |
| `video_file` | 원본 영상 파일명 | `2026-06-18 19-51-00.mp4` |

시작 메소는 0으로 봅니다. 그래서 `end_meso`만 적으면 됩니다.

예:

```text
end_meso = 550000000
```

영상에는 다음처럼 표시됩니다.

```text
5.5억 메소
```

## 영상 파일명 규칙

`raw_video` 폴더 안의 실제 파일명과 `records.csv`의 `video_file` 값이 정확히 같아야 합니다.

예를 들어 원본 영상이:

```text
raw_video/maple hunt 01.mp4
```

이면 CSV는:

```csv
day,date,map,time,end_meso,drops,memo,video_file
1,2026-06-18,도원경,2시간,550000000,조각 18개,첫 재획,maple hunt 01.mp4
```

띄어쓰기와 확장자 `.mp4`까지 똑같이 적어야 합니다.

## BGM 넣기

BGM을 넣고 싶으면 `assets` 폴더에 오디오 파일을 넣습니다.

```text
assets/bgm1.mp3
assets/bgm2.wav
assets/chill.m4a
```

오디오 파일이 여러 개 있으면 실행할 때마다 그중 하나를 랜덤으로 골라 BGM으로 넣습니다.

지원하는 확장자:

```text
.mp3, .wav, .m4a, .aac, .flac, .ogg
```

`font.ttf` 같은 비오디오 파일은 무시합니다. 오디오 파일이 없으면 원본 영상 소리만 사용합니다.

## 한글 폰트 바꾸기

원하는 한글 폰트를 쓰고 싶으면 `assets` 폴더에 아래 이름으로 넣습니다.

```text
assets/font.ttf
```

없으면 Windows 기본 한글 폰트인 맑은 고딕을 사용합니다.

## 편집 방식

현재 기본 편집 방식은 약 10초 쇼츠입니다.

```text
앞 5초: 원본 영상의 랜덤 구간
뒤 5초: 원본 영상의 마지막 5초
```

예를 들어 원본 영상이 47초라면:

```text
27.2초부터 5초 + 42.0초부터 마지막 5초
```

처럼 자동으로 잘라서 이어 붙입니다.

실행할 때마다 앞 5초 랜덤 구간은 달라질 수 있습니다.

## 자주 나는 오류

### 원본 영상이 없어 건너뜁니다

예:

```text
[경고] 원본 영상이 없어 건너뜁니다: raw_video/test.mp4
```

해결:

- `raw_video` 폴더에 영상이 있는지 확인하세요.
- `records.csv`의 `video_file` 값이 실제 파일명과 같은지 확인하세요.

### ffmpeg를 찾을 수 없습니다

해결:

- FFmpeg를 설치하세요.
- 설치 후 PowerShell을 새로 열어보세요.
- `ffmpeg -version`이 실행되는지 확인하세요.

### CSV 한글이 깨지거나 읽기 오류가 납니다

이 프로그램은 UTF-8과 Windows ANSI/CP949 CSV를 모두 읽을 수 있게 되어 있습니다.

그래도 문제가 나면 `records.csv`를 메모장에서 열고 `다른 이름으로 저장`을 누른 뒤 인코딩을 `UTF-8`로 저장해보세요.

### 결과 영상이 덮어써집니다

같은 `day`와 같은 `end_meso`를 쓰면 결과 파일명이 같아질 수 있습니다.

예:

```text
jaehwak_day1_5.5억메소.mp4
```

기존 파일을 보관하고 싶으면 실행 전에 `output` 폴더의 파일명을 바꾸거나 다른 곳으로 옮기세요.

## GitHub에 올리지 않는 파일

아래 파일은 개인 영상, 결과물, BGM 등이므로 GitHub에 올리지 않도록 `.gitignore`에 등록되어 있습니다.

```text
raw_video/*
output/*
records/records.csv
assets/*.mp3
assets/*.ttf
```

예시 CSV는 `records.example.csv`를 참고하세요.

## 주의

이 프로그램은 OBS로 직접 녹화한 영상을 편집하는 도구입니다.

게임 플레이 자동화, 입력 자동화, 매크로 기능은 포함하지 않습니다.
