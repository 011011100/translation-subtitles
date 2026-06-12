from __future__ import annotations

from pathlib import Path
from typing import Callable

from .srt_utils import Subtitle, compose_srt, seconds_to_srt_timestamp


ProgressCallback = Callable[[str], None]


def transcribe_audio_to_srt(
    audio_path: Path,
    output_path: Path,
    model_name: str = "small",
    device: str = "auto",
    compute_type: str = "auto",
    language: str | None = None,
    progress: ProgressCallback | None = None,
) -> list[Subtitle]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "缺少 faster-whisper。请先安装依赖：pip install -e ."
        ) from exc

    if progress:
        progress(f"正在加载 Whisper 模型：{model_name}")
    model = WhisperModel(model_name, device=device, compute_type=compute_type)

    if progress:
        progress("正在识别语音，这一步可能需要一些时间")
    segments, _info = model.transcribe(
        str(audio_path),
        language=language,
        vad_filter=True,
        beam_size=5,
    )

    subtitles: list[Subtitle] = []
    for index, segment in enumerate(segments, start=1):
        text = segment.text.strip()
        if not text:
            continue
        subtitles.append(
            Subtitle(
                index=index,
                start=seconds_to_srt_timestamp(segment.start),
                end=seconds_to_srt_timestamp(segment.end),
                text=text,
            )
        )

    output_path.write_text(compose_srt(subtitles), encoding="utf-8")
    return subtitles
