from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

from .config import AppConfig, DEFAULT_BASE_URL, DEFAULT_MODEL
from .pipeline import process_video


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Chinese subtitles for a video.")
    parser.add_argument("video", type=Path, help="Input video path.")
    parser.add_argument("-o", "--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--api-key", default=None, help="Aliyun Bailian/DashScope API key.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Bailian model name.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--whisper-model", default="small")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--compute-type", default="auto")
    parser.add_argument("--no-burn", action="store_true", help="Only write .srt files.")
    return parser


def main() -> None:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()

    from os import getenv

    config = AppConfig(
        api_key=args.api_key or getenv("DASHSCOPE_API_KEY", ""),
        model=args.model,
        base_url=args.base_url,
        whisper_model=args.whisper_model,
        device=args.device,
        compute_type=args.compute_type,
        burn_subtitles=not args.no_burn,
    )

    result = process_video(
        video_path=args.video,
        output_dir=args.output_dir,
        config=config,
        progress=print,
    )
    print(f"中文字幕：{result.translated_srt_path}")
    if result.burned_video_path:
        print(f"成片视频：{result.burned_video_path}")


if __name__ == "__main__":
    main()
