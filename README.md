# translation-subtitles

一个给视频自动生成中文字幕的桌面工具原型，适合打包成 Windows `.exe` 发给不熟悉电脑的朋友使用。

当前默认方案：

- 语音识别：本地 `faster-whisper`
- 字幕翻译：阿里云百炼 OpenAI 兼容接口
- 默认模型：`qwen-plus`
- 视频处理：`ffmpeg`
- 界面：Python 内置 `tkinter`

## 功能

- 选择本地视频文件
- 自动提取音频
- 自动识别英文字幕
- 使用百炼 `qwen-plus` 翻译为简体中文
- 输出 `.source.srt` 原文字幕和 `.zh.srt` 中文字幕
- 可选生成烧录中文字幕的 `.mp4`
- API Key 保存在用户本机配置目录，不写死进程序

## 本地开发运行

需要 Python 3.10+ 和 ffmpeg。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

把 `.env` 里的 `DASHSCOPE_API_KEY` 改成你的阿里云百炼 API Key。

启动桌面界面：

```bash
translation-subtitles-gui
```

或用命令行处理一个视频：

```bash
translation-subtitles ./input.mp4 -o ./output
```

只生成字幕、不烧录视频：

```bash
translation-subtitles ./input.mp4 -o ./output --no-burn
```

## Windows 打包

在 Windows 电脑上安装 Python 3.10+，把 `ffmpeg.exe` 放到项目的 `bin/ffmpeg.exe`，然后运行：

```powershell
.\scripts\build_windows.ps1
```

打包成功后会生成：

```text
dist\中文字幕助手.exe
```

发给朋友时建议一起说明：

1. 双击打开软件。
2. 填入他自己的阿里云百炼 API Key。
3. 选择视频。
4. 点“开始生成”。
5. 等输出目录里出现中文字幕和视频。

## 注意

- 第一次运行 `faster-whisper` 会下载模型，速度取决于网络。
- 普通 CPU 电脑也能跑，但长视频会比较慢。
- 如果需要完全离线运行，可以提前把 Whisper 模型缓存和 `ffmpeg.exe` 一起准备好。
- 不要把自己的 API Key 写死到代码或 exe 里，避免别人使用时产生你的费用。
