from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .config import AppConfig
from .media import burn_subtitles, extract_audio
from .srt_utils import compose_srt, replace_texts
from .transcriber import transcribe_audio_to_srt
from .translator import BailianTranslator


ProgressCallback = Callable[[str], None]


@dataclass
class PipelineResult:
    output_dir: Path
    audio_path: Path
    source_srt_path: Path
    translated_srt_path: Path
    burned_video_path: Path | None


def process_video(
    video_path: Path,
    output_dir: Path,
    config: AppConfig,
    progress: ProgressCallback | None = None,
) -> PipelineResult:
    video_path = video_path.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    stem = video_path.stem
    audio_path = output_dir / f"{stem}.wav"
    source_srt_path = output_dir / f"{stem}.source.srt"
    translated_srt_path = output_dir / f"{stem}.zh.srt"
    burned_video_path = output_dir / f"{stem}.zh.mp4"

    if progress:
        progress(f"开始处理：{video_path.name}")

    extract_audio(video_path, audio_path, progress)

    subtitles = transcribe_audio_to_srt(
        audio_path=audio_path,
        output_path=source_srt_path,
        model_name=config.whisper_model,
        device=config.device,
        compute_type=config.compute_type,
        progress=progress,
    )
    if not subtitles:
        raise RuntimeError("没有识别到可翻译的字幕。")

    translator = BailianTranslator(
        api_key=config.api_key,
        model=config.model,
        base_url=config.base_url,
    )
    translated_texts = translator.translate_subtitles(subtitles, progress)
    translated_subtitles = replace_texts(subtitles, translated_texts)
    translated_srt_path.write_text(
        compose_srt(translated_subtitles),
        encoding="utf-8",
    )

    final_video_path: Path | None = None
    if config.burn_subtitles:
        burn_subtitles(video_path, translated_srt_path, burned_video_path, progress)
        final_video_path = burned_video_path

    if progress:
        progress("处理完成")

    return PipelineResult(
        output_dir=output_dir,
        audio_path=audio_path,
        source_srt_path=source_srt_path,
        translated_srt_path=translated_srt_path,
        burned_video_path=final_video_path,
    )
