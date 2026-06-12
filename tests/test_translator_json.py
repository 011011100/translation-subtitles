from translation_subtitles.translator import _load_json_array


def test_load_json_array_from_markdown_block() -> None:
    content = """```json
[{"id": 1, "translated": "你好"}]
```"""
    assert _load_json_array(content) == [{"id": 1, "translated": "你好"}]


def test_load_json_array_from_surrounding_text() -> None:
    content = '结果如下：[{"id": 2, "translated": "世界"}]'
    assert _load_json_array(content) == [{"id": 2, "translated": "世界"}]
