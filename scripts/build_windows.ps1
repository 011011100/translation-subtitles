$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
  python -m venv .venv
}

.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"

$extraArgs = @()
if (Test-Path "bin\ffmpeg.exe") {
  $extraArgs += "--add-binary"
  $extraArgs += "bin\ffmpeg.exe;bin"
}

.\.venv\Scripts\python.exe -m PyInstaller `
  --name "中文字幕助手" `
  --onefile `
  --windowed `
  --collect-all faster_whisper `
  --collect-all ctranslate2 `
  @extraArgs `
  "run_gui.py"

Write-Host "Done: dist\中文字幕助手.exe"
