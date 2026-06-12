from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable


ProgressCallback = Callable[[str], None]


def find_ffmpeg() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg

    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir:
        bundled = Path(bundle_dir) / "bin" / "ffmpeg.exe"
        if bundled.exists():
            return str(bundled)

    local = Path(__file__).resolve().parents[2] / "bin" / "ffmpeg.exe"
    if local.exists():
        return str(local)
    raise FileNotFoundError(
        "找不到 ffmpeg。请安装 ffmpeg，或把 ffmpeg.exe 放到项目 bin 目录。"
    )


def extract_audio(
    video_path: Path,
    audio_path: Path,
    progress: ProgressCallback | None = None,
) -> None:
    ffmpeg = find_ffmpeg()
    if progress:
        progress("正在从视频提取音频")
    _run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            str(audio_path),
        ]
    )


def burn_subtitles(
    video_path: Path,
    subtitle_path: Path,
    output_path: Path,
    progress: ProgressCallback | None = None,
) -> None:
    ffmpeg = find_ffmpeg()
    if progress:
        progress("正在烧录中文字幕到视频")

    subtitle_filter = _subtitle_filter_arg(subtitle_path)
    style = (
        "FontName=Microsoft YaHei,"
        "FontSize=20,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BorderStyle=1,"
        "Outline=1,"
        "Shadow=0,"
        "MarginV=28"
    )
    _run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(video_path),
            "-vf",
            f"subtitles={subtitle_filter}:force_style='{style}'",
            "-c:a",
            "copy",
            str(output_path),
        ]
    )


def _subtitle_filter_arg(path: Path) -> str:
    value = str(path.resolve()).replace("\\", "/")
    value = value.replace(":", r"\:")
    value = value.replace("'", r"\'")
    return f"'{value}'"


def _run(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(message or f"Command failed: {' '.join(command)}")
