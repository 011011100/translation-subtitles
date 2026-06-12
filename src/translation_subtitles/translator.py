from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Callable, Iterable

from .config import DEFAULT_BASE_URL, DEFAULT_MODEL
from .srt_utils import Subtitle


ProgressCallback = Callable[[str], None]


SYSTEM_PROMPT = (
    "你是专业视频字幕翻译。把英文视频字幕翻译成自然、简洁、适合中国观众观看的简体中文。"
    "保持原意、语气、梗和术语的一致性。不要解释，不要添加字幕以外的内容。"
    "如果原文是人名、品牌、专有名词，优先保留常见译名；没有常见译名就保留英文。"
)


@dataclass
class BailianTranslator:
    api_key: str
    model: str = DEFAULT_MODEL
    base_url: str = DEFAULT_BASE_URL
    batch_size: int = 20
    retries: int = 2

    def __post_init__(self) -> None:
        if not self.api_key.strip():
            raise ValueError("Missing DASHSCOPE_API_KEY.")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("缺少 openai。请先安装依赖：pip install -e .") from exc

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def translate_subtitles(
        self,
        subtitles: list[Subtitle],
        progress: ProgressCallback | None = None,
    ) -> list[str]:
        translated: list[str] = []
        total = len(subtitles)

        for start in range(0, total, self.batch_size):
            batch = subtitles[start : start + self.batch_size]
            if progress:
                progress(f"正在翻译字幕 {start + 1}-{start + len(batch)} / {total}")
            translated.extend(self._translate_batch_with_retry(batch))

        return translated

    def _translate_batch_with_retry(self, batch: list[Subtitle]) -> list[str]:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                return self._translate_batch(batch)
            except Exception as exc:  # noqa: BLE001 - surface provider errors after retries.
                last_error = exc
                if attempt < self.retries:
                    time.sleep(1.5 * (attempt + 1))
        assert last_error is not None
        raise last_error

    def _translate_batch(self, batch: list[Subtitle]) -> list[str]:
        payload = [{"id": item.index, "text": item.text} for item in batch]
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "请翻译下面 JSON 数组中的 text 字段，只返回 JSON 数组。"
                        "每个对象必须保留 id，并输出 translated 字段。\n\n"
                        f"{json.dumps(payload, ensure_ascii=False)}"
                    ),
                },
            ],
        )
        content = response.choices[0].message.content or ""
        items = _load_json_array(content)
        translations_by_id = {
            int(item["id"]): str(item["translated"]).strip()
            for item in items
            if "id" in item and "translated" in item
        }
        translations = [translations_by_id.get(item.index, "") for item in batch]
        if any(not text for text in translations):
            raise ValueError("Translator returned incomplete subtitle JSON.")
        return translations


def _load_json_array(content: str) -> list[dict[str, object]]:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\[[\s\S]*\]", content)
        if not match:
            raise
        data = json.loads(match.group(0))

    if not isinstance(data, list):
        raise ValueError("Translator response is not a JSON array.")
    if not all(isinstance(item, dict) for item in data):
        raise ValueError("Translator response contains non-object items.")
    return data


def chunked(items: list[Subtitle], size: int) -> Iterable[list[Subtitle]]:
    for index in range(0, len(items), size):
        yield items[index : index + size]
