from __future__ import annotations

from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from dotenv import load_dotenv

from .config import AppConfig, DEFAULT_BASE_URL, DEFAULT_MODEL, load_config, save_config
from .pipeline import process_video


class SubtitleApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("中文字幕助手")
        self.geometry("680x520")
        self.minsize(620, 480)

        self.messages: queue.Queue[tuple[str, str]] = queue.Queue()
        self.worker: threading.Thread | None = None
        self.config_data = load_config()

        self.video_var = tk.StringVar()
        self.output_var = tk.StringVar(value=str(Path.cwd() / "output"))
        self.api_key_var = tk.StringVar(value=self.config_data.api_key)
        self.model_var = tk.StringVar(value=self.config_data.model or DEFAULT_MODEL)
        self.whisper_model_var = tk.StringVar(value=self.config_data.whisper_model)
        self.device_var = tk.StringVar(value=self.config_data.device)
        self.compute_type_var = tk.StringVar(value=self.config_data.compute_type)
        self.burn_var = tk.BooleanVar(value=self.config_data.burn_subtitles)

        self._build_ui()
        self.after(200, self._poll_messages)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.pack(fill=tk.BOTH, expand=True)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(9, weight=1)

        title = ttk.Label(root, text="中文字幕助手", font=("Microsoft YaHei UI", 18, "bold"))
        title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 14))

        self._entry_row(root, 1, "视频文件", self.video_var, self._choose_video)
        self._entry_row(root, 2, "输出目录", self.output_var, self._choose_output)
        self._entry_row(root, 3, "百炼 Key", self.api_key_var, None, show="*")

        ttk.Label(root, text="翻译模型").grid(row=4, column=0, sticky="w", pady=6)
        ttk.Entry(root, textvariable=self.model_var).grid(row=4, column=1, sticky="ew", pady=6)
        ttk.Label(root, text="默认 qwen-plus").grid(row=4, column=2, sticky="w", padx=(8, 0))

        ttk.Label(root, text="Whisper").grid(row=5, column=0, sticky="w", pady=6)
        ttk.Combobox(
            root,
            textvariable=self.whisper_model_var,
            values=("tiny", "base", "small", "medium", "large-v3"),
            state="readonly",
            width=16,
        ).grid(row=5, column=1, sticky="w", pady=6)

        ttk.Label(root, text="设备").grid(row=6, column=0, sticky="w", pady=6)
        device_frame = ttk.Frame(root)
        device_frame.grid(row=6, column=1, sticky="w", pady=6)
        ttk.Combobox(
            device_frame,
            textvariable=self.device_var,
            values=("auto", "cpu", "cuda"),
            state="readonly",
            width=10,
        ).pack(side=tk.LEFT)
        ttk.Label(device_frame, text="  计算精度").pack(side=tk.LEFT)
        ttk.Combobox(
            device_frame,
            textvariable=self.compute_type_var,
            values=("auto", "int8", "float16", "float32"),
            state="readonly",
            width=10,
        ).pack(side=tk.LEFT)

        ttk.Checkbutton(
            root,
            text="同时生成烧录中文字幕的视频",
            variable=self.burn_var,
        ).grid(row=7, column=1, sticky="w", pady=8)

        self.start_button = ttk.Button(root, text="开始生成", command=self._start)
        self.start_button.grid(row=8, column=1, sticky="w", pady=(10, 12))

        self.log_box = tk.Text(root, height=12, wrap=tk.WORD)
        self.log_box.grid(row=9, column=0, columnspan=3, sticky="nsew")
        self.log_box.configure(state=tk.DISABLED)

    def _entry_row(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        command,
        show: str | None = None,
    ) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=6)
        ttk.Entry(parent, textvariable=variable, show=show).grid(
            row=row,
            column=1,
            sticky="ew",
            pady=6,
        )
        if command is not None:
            ttk.Button(parent, text="选择", command=command).grid(
                row=row,
                column=2,
                sticky="ew",
                padx=(8, 0),
                pady=6,
            )

    def _choose_video(self) -> None:
        path = filedialog.askopenfilename(
            title="选择视频",
            filetypes=[
                ("Video files", "*.mp4 *.mkv *.mov *.avi *.webm"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.video_var.set(path)
            default_output = str(Path(path).with_suffix("").parent / "output")
            self.output_var.set(default_output)

    def _choose_output(self) -> None:
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            self.output_var.set(path)

    def _start(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        video = self.video_var.get().strip()
        api_key = self.api_key_var.get().strip()
        output = self.output_var.get().strip()
        if not video:
            messagebox.showwarning("缺少视频", "请先选择一个视频文件。")
            return
        if not api_key:
            messagebox.showwarning("缺少 Key", "请填写阿里云百炼 API Key。")
            return

        config = AppConfig(
            api_key=api_key,
            model=self.model_var.get().strip() or DEFAULT_MODEL,
            base_url=DEFAULT_BASE_URL,
            whisper_model=self.whisper_model_var.get(),
            device=self.device_var.get(),
            compute_type=self.compute_type_var.get(),
            burn_subtitles=self.burn_var.get(),
        )
        save_config(config)
        self.start_button.configure(state=tk.DISABLED)
        self._clear_log()
        self._log("任务已开始")

        self.worker = threading.Thread(
            target=self._run_pipeline,
            args=(Path(video), Path(output), config),
            daemon=True,
        )
        self.worker.start()

    def _run_pipeline(self, video: Path, output: Path, config: AppConfig) -> None:
        try:
            result = process_video(
                video_path=video,
                output_dir=output,
                config=config,
                progress=lambda message: self.messages.put(("log", message)),
            )
            message = f"完成！中文字幕：{result.translated_srt_path}"
            if result.burned_video_path:
                message += f"\n成片视频：{result.burned_video_path}"
            self.messages.put(("done", message))
        except Exception as exc:  # noqa: BLE001 - GUI should show user-friendly errors.
            self.messages.put(("error", str(exc)))

    def _poll_messages(self) -> None:
        try:
            while True:
                kind, message = self.messages.get_nowait()
                if kind == "log":
                    self._log(message)
                elif kind == "done":
                    self._log(message)
                    self.start_button.configure(state=tk.NORMAL)
                    messagebox.showinfo("处理完成", message)
                elif kind == "error":
                    self._log(f"失败：{message}")
                    self.start_button.configure(state=tk.NORMAL)
                    messagebox.showerror("处理失败", message)
        except queue.Empty:
            pass
        self.after(200, self._poll_messages)

    def _log(self, message: str) -> None:
        self.log_box.configure(state=tk.NORMAL)
        self.log_box.insert(tk.END, f"{message}\n")
        self.log_box.see(tk.END)
        self.log_box.configure(state=tk.DISABLED)

    def _clear_log(self) -> None:
        self.log_box.configure(state=tk.NORMAL)
        self.log_box.delete("1.0", tk.END)
        self.log_box.configure(state=tk.DISABLED)


def main() -> None:
    load_dotenv()
    app = SubtitleApp()
    app.mainloop()


if __name__ == "__main__":
    main()
