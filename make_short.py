import csv
import random
import re
import subprocess
from pathlib import Path


# 이 파일이 있는 폴더를 프로젝트 기준 폴더로 사용합니다.
# 예: maple-shorts/make_short.py 를 실행하면 maple-shorts 폴더가 BASE_DIR 입니다.
BASE_DIR = Path(__file__).resolve().parent
RAW_VIDEO_DIR = BASE_DIR / "raw_video"
OUTPUT_DIR = BASE_DIR / "output"
RECORDS_DIR = BASE_DIR / "records"
ASSETS_DIR = BASE_DIR / "assets"
RECORDS_CSV = RECORDS_DIR / "records.csv"

# assets/font.ttf 가 없을 때 사용할 Windows 기본 한글 폰트입니다.
DEFAULT_KOREAN_FONT = Path(r"C:\Windows\Fonts\malgun.ttf")

# 최종 쇼츠 구성:
# - 앞 5초: 원본 영상의 마지막 5초를 제외한 구간 중 랜덤으로 선택
# - 뒤 5초: 원본 영상의 마지막 5초
RANDOM_CLIP_SECONDS = 5.0
ENDING_CLIP_SECONDS = 5.0

# 처음 records.csv 를 만들 때 사용할 기본 컬럼입니다.
# 나중에 start_time, duration 컬럼을 CSV에 직접 추가해도 코드가 읽을 수 있습니다.
CSV_COLUMNS = [
    "day",
    "date",
    "map",
    "time",
    "end_meso",
    "drops",
    "memo",
    "video_file",
]

SAMPLE_RECORD = {
    "day": "1",
    "date": "2026-06-18",
    "map": "도원경",
    "time": "2시간",
    "end_meso": "550000000",
    "drops": "조각 18개",
    "memo": "첫 재획",
    "video_file": "test.mp4",
}


def ensure_project_folders():
    """프로그램 실행에 필요한 폴더를 자동 생성합니다."""
    for folder in [RAW_VIDEO_DIR, OUTPUT_DIR, RECORDS_DIR, ASSETS_DIR]:
        folder.mkdir(parents=True, exist_ok=True)


def create_sample_csv(csv_path):
    """records.csv가 없을 때 초보자가 바로 참고할 수 있는 예시 파일을 만듭니다."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerow(SAMPLE_RECORD)


def read_records(csv_path):
    """
    records.csv를 읽어서 각 행을 dict 형태로 반환합니다.

    기본은 UTF-8 BOM(utf-8-sig)으로 읽습니다.
    다만 Windows에서 엑셀/메모장으로 저장하면 CP949(ANSI)로 저장되는 경우가 있어
    UTF-8 읽기에 실패하면 Windows 한글 인코딩으로 다시 시도합니다.
    """
    encodings = ["utf-8-sig", "cp949", "euc-kr"]
    last_error = None

    for encoding in encodings:
        try:
            with csv_path.open("r", encoding=encoding, newline="") as file:
                return list(csv.DictReader(file))
        except UnicodeDecodeError as error:
            last_error = error

    raise UnicodeDecodeError(
        last_error.encoding,
        last_error.object,
        last_error.start,
        last_error.end,
        "records.csv 인코딩을 읽을 수 없습니다. UTF-8 또는 ANSI(CP949)로 저장해주세요.",
    )


def parse_meso(value):
    """CSV에 적힌 메소 숫자를 int로 바꿉니다. 쉼표가 있어도 읽을 수 있습니다."""
    try:
        return int(str(value).replace(",", "").strip() or "0")
    except ValueError:
        return 0


def get_profit_meso(row):
    """
    수익 메소를 계산합니다.

    새 CSV 형식:
    - 시작 메소를 0으로 보고 end_meso만 적습니다.
    - end_meso가 곧 수익입니다.

    예전 CSV 호환:
    - profit 컬럼이 있으면 그 값을 우선 사용합니다.
    - profit이 없고 start_meso/end_meso가 있으면 end_meso - start_meso로 계산합니다.
    """
    profit_text = (row.get("profit") or "").strip()
    if profit_text:
        return parse_meso(profit_text)

    end_meso = parse_meso(row.get("end_meso"))
    start_meso = parse_meso(row.get("start_meso"))
    profit_meso = end_meso - start_meso
    return max(profit_meso, 0)


def format_meso(value):
    """
    숫자로 저장된 메소 수익을 사람이 보기 좋은 한국식 단위로 바꿉니다.

    예:
    - 550000000  -> 5.5억 메소
    - 1200000000 -> 12억 메소
    - 95000000   -> 9500만 메소
    """
    meso = parse_meso(value)

    if meso >= 100_000_000:
        eok = meso / 100_000_000
        text = f"{eok:.1f}".rstrip("0").rstrip(".")
        return f"{text}억 메소"

    if meso >= 10_000:
        man = meso / 10_000
        text = f"{man:.1f}".rstrip("0").rstrip(".")
        return f"{text}만 메소"

    return f"{meso} 메소"


def get_clip_timing(row):
    """
    CSV에 start_time, duration 컬럼이 있으면 그 값을 사용합니다.
    없거나 빈칸이면 기본값인 0초부터 30초까지를 사용합니다.
    """
    start_time = (row.get("start_time") or "0").strip()
    duration = (row.get("duration") or "30").strip()
    return start_time, duration


def get_video_duration(input_path):
    """
    ffprobe로 원본 영상 길이를 초 단위로 읽습니다.

    새 편집 방식은 "중간 랜덤 5초 + 마지막 5초"라서,
    마지막 5초가 어디서 시작하는지 계산하려면 전체 길이가 필요합니다.
    """
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(input_path),
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return float(result.stdout.strip())


def plan_clip_segments(video_duration, rng=None):
    """
    최종 쇼츠에 넣을 시간 구간을 계산합니다.

    기본 목표는 총 10초입니다.
    - 첫 구간: 마지막 5초 이전에서 랜덤 5초
    - 두 번째 구간: 영상의 마지막 5초

    영상이 10초보다 짧으면 가능한 만큼만 사용합니다.
    예를 들어 8초짜리 영상은 0초부터 8초까지 한 구간만 사용합니다.
    """
    duration = max(float(video_duration), 0.0)
    rng = rng or random

    if duration <= 0:
        return []

    if duration <= ENDING_CLIP_SECONDS:
        return [{"start": 0.0, "duration": duration}]

    ending_start = max(duration - ENDING_CLIP_SECONDS, 0.0)
    random_duration = min(RANDOM_CLIP_SECONDS, ending_start)

    if random_duration <= 0:
        return [{"start": ending_start, "duration": ENDING_CLIP_SECONDS}]

    latest_random_start = max(ending_start - random_duration, 0.0)
    random_start = rng.uniform(0.0, latest_random_start)

    return [
        {"start": random_start, "duration": random_duration},
        {"start": ending_start, "duration": ENDING_CLIP_SECONDS},
    ]


def choose_font_path(assets_dir):
    """
    한글 자막용 폰트 경로를 고릅니다.
    assets/font.ttf 를 넣으면 그 폰트를 우선 사용하고, 없으면 맑은 고딕을 사용합니다.
    """
    custom_font = assets_dir / "font.ttf"
    if custom_font.exists():
        return custom_font
    return DEFAULT_KOREAN_FONT


def choose_bgm_path(assets_dir):
    """
    BGM 파일 경로를 고릅니다.

    기본은 assets/bgm.mp3 입니다.
    다만 Windows에서 확장자 숨김 상태로 이름을 바꾸면 bgm.mp3.mp3처럼 저장되는 경우가 있어,
    정확한 bgm.mp3가 없어도 assets 폴더에 mp3가 하나뿐이면 그 파일을 BGM으로 사용합니다.
    """
    exact_bgm = assets_dir / "bgm.mp3"
    if exact_bgm.exists():
        return exact_bgm

    mp3_files = sorted(assets_dir.glob("*.mp3"))
    if len(mp3_files) == 1:
        return mp3_files[0]

    return None


def ffmpeg_filter_path(path):
    """
    FFmpeg drawtext의 fontfile 옵션에 넣을 경로를 안전하게 바꿉니다.

    Windows 경로 C:\\Windows\\Fonts\\malgun.ttf 는 FFmpeg 필터 안에서
    C\\:/Windows/Fonts/malgun.ttf 처럼 드라이브 콜론을 이스케이프해야 합니다.
    """
    normalized = str(path).replace("\\", "/")
    return normalized.replace(":", r"\:")


def escape_drawtext(text):
    """
    FFmpeg drawtext 필터에서 특수한 의미를 갖는 문자를 이스케이프합니다.

    drawtext는 옵션을 콜론(:)으로 나누고, 작은따옴표(')로 text를 감싸기 때문에
    사용자가 메모에 이런 문자를 적어도 필터가 깨지지 않도록 처리합니다.
    """
    value = str(text or "").replace("\r", " ").replace("\n", " ")
    value = value.replace("\\", r"\\")
    value = value.replace("'", r"\'")
    value = value.replace(":", r"\:")
    value = value.replace(",", r"\,")
    value = value.replace("%", r"\%")
    return value


def drawtext_filter(text, font_path, x, y, fontsize, fontcolor="white", box=True):
    """자막 한 줄을 그리는 drawtext 필터 문자열을 만듭니다."""
    box_options = ""
    if box:
        box_options = ":box=1:boxcolor=black@0.55:boxborderw=18"

    return (
        "drawtext="
        f"fontfile='{ffmpeg_filter_path(font_path)}'"
        f":text='{escape_drawtext(text)}'"
        f":x={x}:y={y}"
        f":fontsize={fontsize}:fontcolor={fontcolor}"
        f"{box_options}"
    )


def build_video_filter(row, font_path):
    """
    1920x1080 가로 영상을 쇼츠용 1080x1920 세로 영상으로 바꾸고 자막을 올립니다.

    crop 설명:
    - 원본이 16:9 가로 영상이라고 보고, 높이(ih)는 그대로 씁니다.
    - 세로 쇼츠는 9:16 이므로 crop 폭은 ih * 9 / 16 입니다.
    - x 위치는 (전체 폭 - crop 폭) / 2 로 잡아 가운데 부분을 자릅니다.

    scale 설명:
    - crop으로 세로 비율을 만든 뒤 최종 해상도 1080x1920으로 확대합니다.
    """
    title = f"메이플 재획 {row.get('day', '').strip() or '?'}일차"
    info_lines = [
        f"사냥터: {row.get('map', '').strip()}",
        f"시간: {row.get('time', '').strip()}",
        f"수익: {format_meso(get_profit_meso(row))}",
        f"드랍: {row.get('drops', '').strip()}",
        f"메모: {row.get('memo', '').strip()}",
    ]
    info_lines = [line for line in info_lines if not line.endswith(": ")]

    filters = [
        # 가운데 세로 영역을 잘라낸 뒤 쇼츠 표준 해상도로 맞춥니다.
        "crop=ih*9/16:ih:(iw-ih*9/16)/2:0",
        "scale=1080:1920",
        # 상단 제목입니다.
        drawtext_filter(
            text=title,
            font_path=font_path,
            x="(w-text_w)/2",
            y="120",
            fontsize="72",
            fontcolor="white",
        ),
    ]
    # 정보 텍스트는 한 줄짜리 긴 문장보다 여러 줄이 쇼츠 화면에서 읽기 쉽습니다.
    for index, line in enumerate(info_lines):
        filters.append(
            drawtext_filter(
                text=line,
                font_path=font_path,
                x="70",
                y=f"h-620+{index}*78",
                fontsize="48",
                fontcolor="white",
            )
        )

    return ",".join(filters)


def safe_filename_part(text):
    """Windows 파일명에 쓸 수 없는 문자를 제거합니다."""
    cleaned = re.sub(r'[<>:"/\\|?*\s]+', "", str(text))
    return cleaned or "result"


def format_ffmpeg_seconds(value):
    """FFmpeg 필터에 넣을 초 단위 값을 소수점 3자리 문자열로 만듭니다."""
    return f"{float(value):.3f}"


def build_output_path(row):
    """예: output/jaehwak_day1_5.5억메소.mp4"""
    day = safe_filename_part(row.get("day", "unknown"))
    profit = safe_filename_part(format_meso(get_profit_meso(row)))
    return OUTPUT_DIR / f"jaehwak_day{day}_{profit}.mp4"


def build_ffmpeg_command(
    input_path,
    output_path,
    row,
    font_path,
    bgm_path=None,
    clip_segments=None,
    start_time="0",
    duration="30",
):
    """
    FFmpeg 실행 명령어를 리스트 형태로 만듭니다.

    PowerShell에서 직접 문자열 명령어를 만들면 따옴표와 한글 경로 때문에 실수하기 쉽습니다.
    그래서 subprocess.run(command) 에 넘길 수 있도록 인자를 리스트로 분리합니다.
    """
    video_filter = build_video_filter(row, font_path)

    # clip_segments가 없으면 예전 start_time/duration 방식처럼 한 구간만 사용합니다.
    # process_records에서는 기본으로 plan_clip_segments() 결과를 넘깁니다.
    if clip_segments is None:
        clip_segments = [
            {
                "start": float(start_time),
                "duration": float(duration),
            }
        ]

    filter_parts = []
    video_labels = []
    audio_labels = []

    for index, segment in enumerate(clip_segments):
        start = format_ffmpeg_seconds(segment["start"])
        clip_duration = format_ffmpeg_seconds(segment["duration"])
        video_label = f"v{index}"
        audio_label = f"a{index}"

        # 영상 구간 자르기:
        # trim=start=...:duration=... 로 원하는 시간 구간만 뽑고,
        # setpts=PTS-STARTPTS 로 붙일 때 시간이 0부터 다시 시작되게 합니다.
        filter_parts.append(
            f"[0:v]trim=start={start}:duration={clip_duration},"
            f"setpts=PTS-STARTPTS[{video_label}]"
        )

        # 오디오도 영상과 같은 시간 구간으로 잘라야 화면과 소리가 맞습니다.
        filter_parts.append(
            f"[0:a]atrim=start={start}:duration={clip_duration},"
            f"asetpts=PTS-STARTPTS[{audio_label}]"
        )

        video_labels.append(f"[{video_label}]")
        audio_labels.append(f"[{audio_label}]")

    segment_count = len(clip_segments)
    total_duration = sum(float(segment["duration"]) for segment in clip_segments)

    # 여러 영상 구간을 순서대로 이어붙입니다.
    filter_parts.append(
        f"{''.join(video_labels)}concat=n={segment_count}:v=1:a=0[vcat]"
    )
    filter_parts.append(
        f"{''.join(audio_labels)}concat=n={segment_count}:v=0:a=1[acat]"
    )

    # 이어붙인 영상에 세로 crop/scale과 자막을 적용합니다.
    filter_parts.append(f"[vcat]{video_filter}[v]")

    if bgm_path:
        # BGM이 있으면 원본 오디오를 살리고, BGM은 작게 깔아 섞습니다.
        filter_parts.append("[acat]volume=1.0[aorig]")
        filter_parts.append(
            f"[1:a]atrim=duration={format_ffmpeg_seconds(total_duration)},"
            "asetpts=PTS-STARTPTS,volume=0.25[abgm]"
        )
        filter_parts.append(
            "[aorig][abgm]amix=inputs=2:duration=first:dropout_transition=2[a]"
        )
    else:
        filter_parts.append("[acat]volume=1.0[a]")

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
    ]

    if bgm_path:
        # BGM이 짧아도 쇼츠 구간 전체에 깔릴 수 있게 반복 입력합니다.
        command.extend(["-stream_loop", "-1", "-i", str(bgm_path)])

    command.extend(
        [
            "-filter_complex",
            ";".join(filter_parts),
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-pix_fmt",
            "yuv420p",
            "-shortest",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
    )
    return command


def run_ffmpeg(command, video_file):
    """FFmpeg를 실행하고, 실패하면 어떤 파일에서 실패했는지 알 수 있게 출력합니다."""
    print(f"[실행] {video_file} 변환을 시작합니다.")
    try:
        subprocess.run(command, check=True)
    except FileNotFoundError:
        print("[오류] ffmpeg를 찾을 수 없습니다. FFmpeg를 설치하고 PATH에 추가해주세요.")
        return False
    except subprocess.CalledProcessError as error:
        print(f"[오류] {video_file} 처리 중 FFmpeg 오류가 발생했습니다.")
        print(f"       종료 코드: {error.returncode}")
        return False

    print(f"[완료] {video_file} 변환이 끝났습니다.")
    return True


def process_records():
    """records.csv의 각 행을 읽어 쇼츠 영상을 생성합니다."""
    ensure_project_folders()

    if not RECORDS_CSV.exists():
        create_sample_csv(RECORDS_CSV)
        print(f"[안내] records.csv가 없어 예시 파일을 만들었습니다: {RECORDS_CSV}")
        print("[안내] raw_video 폴더에 test.mp4 같은 원본 영상을 넣고 records.csv를 수정한 뒤 다시 실행하세요.")
        return

    font_path = choose_font_path(ASSETS_DIR)
    bgm_path = choose_bgm_path(ASSETS_DIR)

    if bgm_path:
        print(f"[안내] BGM 사용: {bgm_path.name}")
    else:
        print("[안내] BGM 없음: 원본 영상 소리만 사용합니다.")

    records = read_records(RECORDS_CSV)
    if not records:
        print(f"[경고] records.csv에 처리할 행이 없습니다: {RECORDS_CSV}")
        return

    success_count = 0
    skip_count = 0
    fail_count = 0

    for row_number, row in enumerate(records, start=2):
        video_file = (row.get("video_file") or "").strip()
        if not video_file:
            print(f"[경고] {row_number}행: video_file 값이 비어 있어 건너뜁니다.")
            skip_count += 1
            continue

        input_path = RAW_VIDEO_DIR / video_file
        if not input_path.exists():
            print(f"[경고] 원본 영상이 없어 건너뜁니다: {input_path}")
            skip_count += 1
            continue

        output_path = build_output_path(row)
        try:
            video_duration = get_video_duration(input_path)
        except FileNotFoundError:
            print("[오류] ffprobe를 찾을 수 없습니다. FFmpeg 설치 폴더가 PATH에 있는지 확인해주세요.")
            fail_count += 1
            continue
        except (subprocess.CalledProcessError, ValueError) as error:
            print(f"[오류] {video_file} 영상 길이를 읽지 못했습니다.")
            print(f"       상세: {error}")
            fail_count += 1
            continue

        clip_segments = plan_clip_segments(video_duration)
        if not clip_segments:
            print(f"[경고] {video_file} 영상 길이가 0초라 건너뜁니다.")
            skip_count += 1
            continue

        segment_text = " + ".join(
            f"{segment['start']:.1f}초부터 {segment['duration']:.1f}초"
            for segment in clip_segments
        )
        print(f"[구간] {video_file}: {segment_text}")

        command = build_ffmpeg_command(
            input_path=input_path,
            output_path=output_path,
            row=row,
            font_path=font_path,
            bgm_path=bgm_path,
            clip_segments=clip_segments,
        )

        if run_ffmpeg(command, video_file):
            print(f"       저장 위치: {output_path}")
            success_count += 1
        else:
            fail_count += 1

    print()
    print("[요약]")
    print(f"- 성공: {success_count}개")
    print(f"- 건너뜀: {skip_count}개")
    print(f"- 실패: {fail_count}개")


if __name__ == "__main__":
    process_records()
