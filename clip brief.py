import os
import re
import time
import threading
import json
from datetime import datetime

import pyperclip
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageGrab


# =========================
# 可调参数（尽量少）
# =========================
POLL_INTERVAL_SEC = 1.2

MIN_TEXT_LEN = 8  # 少于这个长度的文本不记录（去噪核心之一）

# 典型噪音：纯数字/纯符号/短路径/很短的单行片段等
RE_PURE_DIGITS = re.compile(r"^\d+$")
RE_PURE_SYMBOLS = re.compile(r"^[\W_]+$", re.UNICODE)
RE_WIN_PATH = re.compile(r"^[a-zA-Z]:\\")         # C:\xxx
RE_UNIX_PATH = re.compile(r"^/")                  # /xxx
RE_URL = re.compile(r"^https?://", re.IGNORECASE) # 如果你想保留短链接也能放行

APP_CONFIG_FILE = "clip_inbox_config.json"


def config_path() -> str:
    # Use a stable per-user location so config persists in onefile EXE mode.
    appdata = os.getenv("APPDATA")
    if appdata:
        cfg_dir = os.path.join(appdata, "ClipboardInbox")
    else:
        cfg_dir = os.path.join(os.path.expanduser("~"), ".clipboard_inbox")
    os.makedirs(cfg_dir, exist_ok=True)
    return os.path.join(cfg_dir, APP_CONFIG_FILE)


def load_last_base_dir() -> str:
    cfg = config_path()
    if not os.path.exists(cfg):
        return ""
    try:
        with open(cfg, "r", encoding="utf-8") as f:
            data = json.load(f)
        d = data.get("base_dir", "")
        return d.strip() if isinstance(d, str) else ""
    except Exception:
        return ""


def save_last_base_dir(base_dir: str) -> None:
    cfg = config_path()
    data = {"base_dir": base_dir.strip()}
    try:
        with open(cfg, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def now_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def now_time() -> str:
    return datetime.now().strftime("%H:%M:%S")


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def daily_md_path(base_dir: str) -> str:
    """
    收件箱：按日单文件
    base_dir/
      inbox/
        2026-03-04.md
      assets/
        2026-03-04/
          image_xxx.png
    """
    inbox_dir = os.path.join(base_dir, "inbox")
    ensure_dir(inbox_dir)
    return os.path.join(inbox_dir, f"{now_date()}.md")


def daily_assets_dir(base_dir: str) -> str:
    assets_dir = os.path.join(base_dir, "assets", now_date())
    ensure_dir(assets_dir)
    return assets_dir


def should_ignore_text(s: str) -> bool:
    if not s:
        return True

    t = s.strip()
    if not t:
        return True

    # 统一压缩多余空白（避免“看起来不同但本质相同”的噪音）
    t_compact = re.sub(r"[ \t]+", " ", t)

    # 太短：不记
    if len(t_compact) < MIN_TEXT_LEN:
        return True

    # 纯数字（常见验证码/序号等）：不记（如你希望保留长数字，可改为 len<=10 才过滤）
    if RE_PURE_DIGITS.fullmatch(t_compact):
        return True

    # 纯符号：不记
    if RE_PURE_SYMBOLS.fullmatch(t_compact):
        return True

    # 很短的路径/文件名：不记（避免复制文件路径带来一堆垃圾）
    if (RE_WIN_PATH.match(t_compact) or RE_UNIX_PATH.match(t_compact)) and len(t_compact) < 40:
        return True

    return False


def write_md_header_if_needed(md_path: str) -> None:
    if not os.path.exists(md_path):
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# Inbox - {now_date()}\n\n")


def append_text(md_path: str, content: str) -> None:
    write_md_header_if_needed(md_path)
    t = content.strip()
    with open(md_path, "a", encoding="utf-8") as f:
        f.write(f"## {now_time()}\n\n")
        f.write(f"{t}\n\n")
        f.write("---\n\n")


def save_clipboard_image(base_dir: str, image_obj: Image.Image) -> str:
    """
    保存图片到 assets/YYYY-MM-DD/ 下，并返回相对于 base_dir 的相对路径（用于写入 md）
    """
    assets_dir = daily_assets_dir(base_dir)
    ts = datetime.now().strftime("%H%M%S")
    ms = int(time.time() * 1000)
    filename = f"image_{ts}_{ms}.png"
    abs_path = os.path.join(assets_dir, filename)
    image_obj.save(abs_path, "PNG")

    # 写 md 用相对路径，便于移动整个文件夹
    rel_path = os.path.relpath(abs_path, start=base_dir)
    return rel_path.replace("\\", "/")  # 让 md 链接更统一


def append_image(md_path: str, rel_image_path: str) -> None:
    write_md_header_if_needed(md_path)
    with open(md_path, "a", encoding="utf-8") as f:
        f.write(f"## {now_time()}\n\n")
        f.write(f"![image]({rel_image_path})\n\n")
        f.write("---\n\n")


class ClipboardInbox:
    def __init__(self):
        self.base_dir = ""
        self.is_listening = False
        self.thread = None

        self.last_text = ""
        self.last_image_bytes = None

    def set_base_dir(self, base_dir: str):
        self.base_dir = base_dir

    def _snapshot_clipboard_as_baseline(self):
        # 启动时读一次，避免把“启动前已存在的剪贴板内容”写进去
        try:
            t = pyperclip.paste()
            self.last_text = t if isinstance(t, str) else ""
        except Exception:
            self.last_text = ""

        try:
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                self.last_image_bytes = img.tobytes()
            else:
                self.last_image_bytes = None
        except Exception:
            self.last_image_bytes = None

    def start(self):
        if self.is_listening:
            return

        if not self.base_dir:
            raise RuntimeError("保存路径无效，请先选择一个文件夹。")

        ensure_dir(self.base_dir)
        self._snapshot_clipboard_as_baseline()

        self.is_listening = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_listening = False

    def _loop(self):
        while self.is_listening:
            try:
                md_path = daily_md_path(self.base_dir)

                # 1) 先看图片（避免图片被当作空文本跳过）
                img = ImageGrab.grabclipboard()
                if isinstance(img, Image.Image):
                    b = img.tobytes()
                    if self.last_image_bytes is None or b != self.last_image_bytes:
                        rel = save_clipboard_image(self.base_dir, img)
                        append_image(md_path, rel)
                        self.last_image_bytes = b
                        self.last_text = ""  # 防止同一操作带来的文本残留重复
                    time.sleep(POLL_INTERVAL_SEC)
                    continue

                # 2) 再看文本
                txt = pyperclip.paste()
                if isinstance(txt, str):
                    if txt.strip() and txt != self.last_text and not should_ignore_text(txt):
                        append_text(md_path, txt)
                        self.last_text = txt
                        self.last_image_bytes = None

            except Exception:
                # 极简：吞掉异常，避免卡死（需要排查时可改成 print(e)）
                pass

            time.sleep(POLL_INTERVAL_SEC)


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Clipboard Inbox")
        self.root.geometry("520x200")
        self.root.resizable(False, False)

        self.inbox = ClipboardInbox()

        self.path_var = tk.StringVar(value=load_last_base_dir())
        self.status_var = tk.StringVar(value="状态：未监听")

        if self.path_var.get().strip():
            self.inbox.set_base_dir(self.path_var.get().strip())

        self._build()

    def _build(self):
        frm = tk.Frame(self.root, padx=12, pady=12)
        frm.pack(fill="both", expand=True)

        tk.Label(frm, text="保存文件夹：").grid(row=0, column=0, sticky="w")

        entry = tk.Entry(frm, textvariable=self.path_var, width=48)
        entry.grid(row=0, column=1, padx=(6, 6), sticky="w")

        btn_browse = tk.Button(frm, text="选择...", command=self.choose_dir, width=10)
        btn_browse.grid(row=0, column=2, sticky="w")

        tk.Label(frm, textvariable=self.status_var).grid(row=1, column=0, columnspan=3, pady=(10, 6), sticky="w")

        btn_frame = tk.Frame(frm)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=(8, 0), sticky="w")

        tk.Button(btn_frame, text="开始", width=12, command=self.start).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="停止", width=12, command=self.stop).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="退出", width=12, command=self.quit).pack(side="left")

        hint = (
            "输出结构：\n"
            "  <保存文件夹>/inbox/YYYY-MM-DD.md\n"
            "  <保存文件夹>/assets/YYYY-MM-DD/image_*.png\n"
            f"过滤规则：文本长度<{MIN_TEXT_LEN}、纯数字、纯符号、短路径等不记录"
        )
        tk.Label(frm, text=hint, justify="left", fg="#444").grid(row=3, column=0, columnspan=3, pady=(12, 0), sticky="w")

    def choose_dir(self):
        d = filedialog.askdirectory(title="选择保存文件夹")
        if d:
            self.path_var.set(d)
            self.inbox.set_base_dir(d)
            save_last_base_dir(d)

    def start(self):
        try:
            base_dir = self.path_var.get().strip()
            if not base_dir:
                messagebox.showwarning("提示", "请先选择保存文件夹。")
                return
            self.inbox.set_base_dir(base_dir)
            save_last_base_dir(base_dir)
            self.inbox.start()
            self.status_var.set("状态：监听中（写入每日 inbox）")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def stop(self):
        self.inbox.stop()
        self.status_var.set("状态：已停止")

    def quit(self):
        self.inbox.stop()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
