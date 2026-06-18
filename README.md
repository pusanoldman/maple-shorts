# Maple Shorts

OBS로 녹화한 메이플스토리 재획 영상을 유튜브 쇼츠용 세로 영상으로 자동 편집하는 Python + FFmpeg 도구입니다.

이 프로그램은 게임 조작 자동화나 매크로가 아닙니다. 직접 플레이하고 OBS로 녹화한 영상 파일을 편집하는 용도입니다.

## 주요 기능

- OBS 녹화본을 1080x1920 세로 쇼츠 영상으로 변환
- 원본 영상 가운데 영역을 세로 비율로 crop 후 scale
- 기본 쇼츠 구성: 랜덤 5초 + 영상 마지막 5초, 총 약 10초
- 상단 제목과 재획 정보 자막 자동 삽입
- 끝 메소만 입력하면 수익 자동 표시
- `assets/font.ttf`가 있으면 사용자 폰트 사용
- `assets/bgm.mp3`가 있으면 BGM 자동 믹스
- CSV가 UTF-8 또는 Windows ANSI/CP949로 저장돼도 읽기 지원

## 폴더 구조

```text
maple-shorts/
├─ make_short.py
├─ raw_video/
│  └─ 원본 OBS 녹화 영상
├─ output/
│  └─ 완성된 쇼츠 영상
├─ records/
│  └─ records.csv
├─ assets/
│  ├─ bgm.mp3
│  └─ font.ttf
└─ records.example.csv
```

`raw_video`, `output`, `records`, `assets` 폴더는 실행 시 자동 생성됩니다.

## 준비물

1. Python 3
2. FFmpeg
3. OBS로 녹화한 메이플스토리 영상

FFmpeg는 `ffmpeg`와 `ffprobe` 명령을 PowerShell에서 실행할 수 있도록 PATH에 등록되어 있어야 합니다.

## 사용 방법

1. 이 폴더로 이동합니다.

```powershell
cd "C:\Users\sjs11\OneDrive\Desktop\maple-shorts"
```

2. 원본 영상을 `raw_video` 폴더에 넣습니다.

예:

```text
raw_video/2026-06-18 19-51-00.mp4
```

3. `records/records.csv`를 작성합니다.

예:

```csv
day,date,map,time,end_meso,drops,memo,video_file
1,2026-06-18,도원경,2시간,550000000,조각 18개,첫 재획,2026-06-18 19-51-00.mp4
```

중요한 점은 `video_file` 값이 `raw_video` 폴더 안의 실제 파일명과 정확히 같아야 한다는 것입니다.

4. 실행합니다.

```powershell
python make_short.py
```

5. 결과 영상을 확인합니다.

```text
output/
```

결과 파일명 예:

```text
jaehwak_day1_5.5억메소.mp4
```

## CSV 컬럼

| 컬럼 | 설명 |
| --- | --- |
| `day` | 재획 N일차 |
| `date` | 날짜 |
| `map` | 사냥터 |
| `time` | 재획 시간 |
| `end_meso` | 끝 메소. 시작 메소는 0으로 봅니다. |
| `drops` | 드랍템 |
| `memo` | 메모 |
| `video_file` | `raw_video` 폴더 안의 영상 파일명 |

## BGM과 폰트

BGM을 넣고 싶으면 다음 파일을 추가합니다.

```text
assets/bgm.mp3
```

한글 폰트를 직접 지정하고 싶으면 다음 파일을 추가합니다.

```text
assets/font.ttf
```

`assets/font.ttf`가 없으면 Windows 기본 한글 폰트인 맑은 고딕을 사용합니다.

## 편집 방식

현재 기본 편집 방식은 총 약 10초입니다.

```text
앞 5초: 원본 영상 중 랜덤 구간
뒤 5초: 원본 영상의 마지막 5초
```

원본 영상이 짧으면 가능한 범위 안에서 자동으로 조정합니다.

## GitHub에 올리지 않는 파일

원본 영상과 결과 영상은 용량이 크고 개인 정보나 게임 닉네임이 포함될 수 있으므로 GitHub에 올리지 않습니다.

```text
raw_video/*
output/*
records/records.csv
assets/bgm.mp3
```

예시 CSV는 `records.example.csv`를 참고하세요.
