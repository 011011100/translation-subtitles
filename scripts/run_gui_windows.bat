@echo off
setlocal

if not exist .venv (
  python -m venv .venv
)

.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\translation-subtitles-gui.exe
