import csv
import random
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

import make_short


class MapleShortsTests(unittest.TestCase):
    def test_format_meso_uses_korean_eok_units(self):
        self.assertEqual(make_short.format_meso("550000000"), "5.5억 메소")
        self.assertEqual(make_short.format_meso("1200000000"), "12억 메소")
        self.assertEqual(make_short.format_meso("95000000"), "9500만 메소")

    def test_get_clip_timing_defaults_and_allows_csv_override(self):
        self.assertEqual(make_short.get_clip_timing({}), ("0", "30"))
        self.assertEqual(
            make_short.get_clip_timing({"start_time": "15", "duration": "45"}),
            ("15", "45"),
        )

    def test_plan_clip_segments_uses_random_five_seconds_and_last_five_seconds(self):
        rng = random.Random(7)

        segments = make_short.plan_clip_segments(video_duration=65.97, rng=rng)

        self.assertEqual(len(segments), 2)
        self.assertAlmostEqual(segments[0]["duration"], 5.0)
        self.assertAlmostEqual(segments[1]["start"], 60.97)
        self.assertAlmostEqual(segments[1]["duration"], 5.0)
        self.assertGreaterEqual(segments[0]["start"], 0)
        self.assertLessEqual(segments[0]["start"] + segments[0]["duration"], 60.97)

    def test_plan_clip_segments_handles_short_videos_without_negative_times(self):
        rng = random.Random(1)

        segments = make_short.plan_clip_segments(video_duration=8.0, rng=rng)

        self.assertEqual(
            segments,
            [
                {"start": 0.0, "duration": 3.0},
                {"start": 3.0, "duration": 5.0},
            ],
        )

    def test_get_profit_meso_uses_end_meso_when_start_and_profit_are_missing(self):
        self.assertEqual(
            make_short.get_profit_meso({"end_meso": "550000000"}),
            550000000,
        )
        self.assertEqual(
            make_short.get_profit_meso(
                {"start_meso": "1000000000", "end_meso": "1550000000"}
            ),
            550000000,
        )
        self.assertEqual(
            make_short.get_profit_meso({"profit": "123456789", "end_meso": "999"}),
            123456789,
        )

    def test_choose_font_prefers_assets_font_then_malgun(self):
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            assets_dir = base_dir / "assets"
            assets_dir.mkdir()

            self.assertEqual(
                make_short.choose_font_path(assets_dir),
                Path(r"C:\Windows\Fonts\malgun.ttf"),
            )

            custom_font = assets_dir / "font.ttf"
            custom_font.write_bytes(b"fake font")

            self.assertEqual(make_short.choose_font_path(assets_dir), custom_font)

    def test_create_sample_csv_writes_expected_columns_and_example(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "records.csv"

            make_short.create_sample_csv(csv_path)

            with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
                rows = list(csv.DictReader(file))

            self.assertEqual(make_short.CSV_COLUMNS, list(rows[0].keys()))
            self.assertEqual(rows[0]["day"], "1")
            self.assertEqual(rows[0]["map"], "도원경")
            self.assertEqual(rows[0]["end_meso"], "550000000")
            self.assertEqual(rows[0]["video_file"], "test.mp4")
            self.assertNotIn("start_meso", rows[0])
            self.assertNotIn("profit", rows[0])

    def test_read_records_accepts_windows_korean_cp949_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "records.csv"
            csv_path.write_text(
                "day,date,map,time,end_meso,drops,memo,video_file\n"
                "1,2026-06-18,도원경,2시간,550000000,조각 18개,첫 재획,test.mp4\n",
                encoding="cp949",
            )

            rows = make_short.read_records(csv_path)

            self.assertEqual(rows[0]["map"], "도원경")
            self.assertEqual(rows[0]["time"], "2시간")
            self.assertEqual(rows[0]["drops"], "조각 18개")

    def test_build_ffmpeg_command_contains_crop_scale_text_and_audio_choice(self):
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            input_path = base_dir / "raw_video" / "test.mp4"
            output_path = base_dir / "output" / "result.mp4"
            font_path = Path(r"C:\Windows\Fonts\malgun.ttf")
            bgm_path = base_dir / "assets" / "bgm.mp3"
            row = {
                "day": "1",
                "map": "도원경",
                "time": "2시간",
                "end_meso": "550000000",
                "drops": "조각 18개",
                "memo": "첫 재획",
            }

            command = make_short.build_ffmpeg_command(
                input_path=input_path,
                output_path=output_path,
                row=row,
                font_path=font_path,
                bgm_path=bgm_path,
                clip_segments=[
                    {"start": 12.5, "duration": 5.0},
                    {"start": 60.97, "duration": 5.0},
                ],
            )
            joined = " ".join(str(part) for part in command)

            self.assertEqual(command[0], "ffmpeg")
            self.assertIn("trim=start=12.500:duration=5.000", joined)
            self.assertIn("trim=start=60.970:duration=5.000", joined)
            self.assertIn("concat=n=2:v=1:a=0", joined)
            self.assertIn("crop=ih*9/16:ih:(iw-ih*9/16)/2:0", joined)
            self.assertIn("scale=1080:1920", joined)
            self.assertIn("메이플 재획 1일차", joined)
            self.assertIn("5.5억 메소", joined)
            self.assertIn(str(bgm_path), command)
            self.assertIn("amix=inputs=2:duration=first:dropout_transition=2", joined)


if __name__ == "__main__":
    unittest.main()
