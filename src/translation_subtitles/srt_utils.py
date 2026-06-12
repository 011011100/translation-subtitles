from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import re


TIMESTAMP_RE = re.compile(
    r"(?P<h>\d{2}):(?P<m>\d{2}):(?P<s>\d{2}),(?P<ms>\d{3})"
)


@dataclass
class Subtitle:
    index: int
    start: str
    end: str
    text: str


def parse_srt(content: str) -> list[Subtitle]:
    normalized = content.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []

    subtitles: list[Subtitle] = []
    for block in re.split(r"\n{2,}", normalized):
        lines = block.splitlines()
        if len(lines) < 3:
            continue

        try:
            index = int(lines[0].strip())
        except ValueError:
            continue

        if "-->" not in lines[1]:
            continue
        start, end = [part.strip() for part in lines[1].split("-->", 1)]
        text = "\n".join(lines[2:]).strip()
        subtitles.append(Subtitle(index=index, start=start, end=end, text=text))

    return subtitles


def compose_srt(subtitles: list[Subtitle]) -> str:
    blocks = []
    for new_index, subtitle in enumerate(subtitles, start=1):
        blocks.append(
            "\n".join(
                [
                    str(new_index),
                    f"{subtitle.start} --> {subtitle.end}",
                    subtitle.text.strip(),
                ]
            )
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def seconds_to_srt_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    delta = timedelta(seconds=seconds)
    total_ms = int(delta.total_seconds() * 1000)
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def replace_texts(subtitles: list[Subtitle], texts: list[str]) -> list[Subtitle]:
    if len(subtitles) != len(texts):
        raise ValueError("Subtitle count and translated text count do not match.")
    return [
        Subtitle(
            index=subtitle.index,
            start=subtitle.start,
            end=subtitle.end,
            text=text.strip(),
        )
        for subtitle, text in zip(subtitles, texts, strict=True)
    ]
