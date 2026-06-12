from translation_subtitles.srt_utils import compose_srt, parse_srt, seconds_to_srt_timestamp


def test_parse_and_compose_srt_round_trip() -> None:
    content = """1
00:00:01,000 --> 00:00:03,000
Hello

2
00:00:03,500 --> 00:00:05,000
World
"""
    subtitles = parse_srt(content)
    assert len(subtitles) == 2
    assert subtitles[0].text == "Hello"
    assert compose_srt(subtitles) == content


def test_seconds_to_srt_timestamp() -> None:
    assert seconds_to_srt_timestamp(65.432) == "00:01:05,432"
