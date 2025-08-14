# focus_stopwatch_style.py  （アイコン対応）
import tkinter as tk
import customtkinter as ctk
from datetime import datetime, timedelta
from PIL import Image
import os, sys

# ---- PyInstallerでも動くリソースパス ----
def resource_path(rel: str) -> str:
    try:
        base = sys._MEIPASS  # pyinstaller
    except Exception:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, rel)

# ---- 表示フォーマット（00:00:00.00） ----
def fmt_hhmmss_cc(delta: timedelta) -> str:
    total_ms = int(delta.total_seconds() * 100)  # センチ秒
    cs = total_ms % 100
    total_sec = total_ms // 100
    h = total_sec // 3600
    m = (total_sec % 3600) // 60
    s = total_sec % 60
    return f"{h:02d}:{m:02d}:{s:02d}.{cs:02d}"

class Stopwatch:
    def __init__(self):
        self.running = False
        self.start_at: datetime | None = None
        self.paused_total = timedelta(0)
        self.pause_started: datetime | None = None
    def reset(self):
        self.running = False
        self.start_at = None
        self.paused_total = timedelta(0)
        self.pause_started = None
    def start(self):
        if self.running: return
        now = datetime.now()
        if self.start_at is None:
            self.start_at = now
        elif self.pause_started:
            self.paused_total += (now - self.pause_started)
            self.pause_started = None
        self.running = True
    def pause(self):
        if not self.running: return
        self.running = False
        self.pause_started = datetime.now()
    def elapsed(self) -> timedelta:
        if self.start_at is None: return timedelta(0)
        now = datetime.now()
        paused = self.paused_total
        if not self.running and self.pause_started:
            paused += (now - self.pause_started)
        return (now - self.start_at) - paused

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title("ストップウォッチ（フォーカス）")
        self.configure(fg_color="#0E141B")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(0, self._maximize)

        self.sw = Stopwatch()

        # ---- 中央コンテナ ----
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(expand=True)

        # ---- 大きい数字 ----
        self.time_lbl = ctk.CTkLabel(
            wrap, text="00:00:00.00",
            font=("Segoe UI", 120, "bold"),
            text_color="#DDE5EE",
        )
        self.time_lbl.pack(pady=(0, 12))

        # ---- 画像読み込み（PNG→CTkImage）----
        self.img_play  = self._load_img("icon/764.png", (36,36))   # ▶
        self.img_pause = self._load_img("icon/804.png", (36,36))   # ⏸
        self.img_reset = self._load_img("icon/495.png", (28,28))   # ↺
        self.img_save  = self._load_img("icon/4436.png", (28,28))   # ← 追加（保存）

        # ---- ボタン行 ----
        btns = ctk.CTkFrame(wrap, fg_color="transparent")
        btns.pack(pady=24)

        self.play_btn = ctk.CTkButton(
            btns,
            image=self.img_play, text="",
            width=68, 
            height=68,
            corner_radius=34,
            fg_color="#FFD54F", 
            hover_color="#FFC107",
            border_width=0,
            command=self._toggle_play
        )
        self.play_btn.pack(side="left", padx=12, pady=12)

        self.reset_btn = ctk.CTkButton(
            btns,
            image=self.img_reset, text="",
            width=68, 
            height=68,
            corner_radius=34,
            fg_color="#FFD54F",
            hover_color="#FFC107",
            border_width=0,
            state="disabled",
            command=self._reset
        )
        self.reset_btn.pack(side="left", padx=12)

        self.save_btn = ctk.CTkButton(
            btns, 
            image=self.img_save, 
            text="", 
            width=68, 
            height=68,
            corner_radius=34, 
            fg_color="#FFD54F", 
            hover_color="#FFC107",
            state="disabled", 
            command=self._save
        )
        self.save_btn.pack(side="left", padx=12)

        # ---- キー操作 ----
        self.bind("<space>", lambda e: self._toggle_play())
        self.bind("<r>",     lambda e: self._reset())
        self.bind("<Escape>", lambda e: self._on_close())
        self.bind("<F11>",   self._toggle_fullscreen)

        # ---- ループ ----
        self._tick()
        self.attributes("-alpha", 0.95)

    # ---------- helpers ----------
    def _load_img(self, rel_path, size):
        path = resource_path(rel_path)
        try:
            img = Image.open(path)
            return ctk.CTkImage(light_image=img, dark_image=img, size=size)
        except Exception as e:
            print(f"[WARN] cannot load image: {path} ({e})")
            return None  # 画像が無くても動くように

    def _maximize(self):
        try: self.state("zoomed")
        except tk.TclError: pass
        try: self.attributes("-zoomed", True)
        except tk.TclError: pass
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{sw}x{sh}+0+0")

    def _toggle_fullscreen(self, _evt=None):
        self.attributes("-fullscreen", not self.attributes("-fullscreen"))

    def _toggle_play(self):
        if not self.sw.running:
            self.sw.start()
            if self.img_pause: self.play_btn.configure(image=self.img_pause, text="")
            else:              self.play_btn.configure(text="⏸")
            self.reset_btn.configure(state="normal")
            self.save_btn.configure(state="disabled")   # ← 計測中は保存不可
        else:
            self.sw.pause()
            if self.img_play: self.play_btn.configure(image=self.img_play, text="")
            else:             self.play_btn.configure(text="▶")
            self.save_btn.configure(state="normal")     # ← 停止中は保存可

    def _reset(self):
        if self.sw.running: return
        self.sw.reset()
        self.time_lbl.configure(text="00:00:00.00")
        if self.img_play: self.play_btn.configure(image=self.img_play, text="")
        else:             self.play_btn.configure(text="▶")
        self.reset_btn.configure(state="disabled")
        self.save_btn.configure(state="disabled")       # ← 追加

    def _save(self):
    # 計測中は保存させない（仮仕様）
        if self.sw.running:
            tk.messagebox.showwarning("保存できません", "計測中は保存できません。いったん停止してください。（仮）")
            return
        elapsed = self.sw.elapsed()
        if elapsed.total_seconds() <= 0:
            tk.messagebox.showinfo("保存（仮）", "保存対象がありません。")
            return
        tk.messagebox.showinfo(
            "保存（仮）",
            f"{fmt_hhmmss_cc(elapsed)} を保存しました（DB未接続のダミー動作）。"
        )

    def _on_close(self):
        if self.sw.running:
            if not tk.messagebox.askyesno("確認", "計測中です。終了せずにアプリを閉じますか？"):
                return
        self.destroy()

    def _tick(self):
        self.time_lbl.configure(text=fmt_hhmmss_cc(self.sw.elapsed()))
        self.after(10, self._tick)

if __name__ == "__main__":
    app = App()
    app.mainloop()
