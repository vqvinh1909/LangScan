# -*- coding: utf-8 -*-
"""
LangScan - Boi den chu Trung / Nhat / Han / Anh o bat ky dau tren Windows,
           bam Ctrl+Alt+D -> popup hien phien am, nghia tieng Viet,
           cap do (HSK / JLPT / CEFR).

Chay:  python langscan.py        (co console)
       pythonw langscan.py       (chay ngam)
Thoat: Ctrl+Alt+Q
"""

import os
import queue
import re
import sys
import threading
import time
import tkinter as tk
import unicodedata

import autostart
import langs
import reverse as reverse_mod
import translate as tr

# ------------------------------------------------------------ cau hinh ------
HOTKEY_LOOKUP = "ctrl+alt+d"        # tu nhan dien ngon ngu
HOTKEY_ZH = "ctrl+alt+c"            # ep tra tieng Trung
HOTKEY_JA = "ctrl+alt+j"            # ep tra tieng Nhat
HOTKEY_KO = "ctrl+alt+k"            # ep tra tieng Han
HOTKEY_EN = "ctrl+alt+e"            # ep tra tieng Anh
# Mo cua so tra tu bang cach NHAN DUP CTRL (nhu Google Dich tren may tinh).
# Doi thanh False neu thay no hay nhay nham khi ban dung Ctrl+C, Ctrl+V.
DOUBLE_CTRL_SEARCH = True
DOUBLE_TAP_GAP = 0.4                # hai lan nhan cach nhau toi da bao nhieu giay
HOTKEY_SNIP = "ctrl+alt+x"          # chup mot vung man hinh roi doc chu (OCR)
HOTKEY_SNIP_AGAIN = "ctrl+alt+z"    # chup lai DUNG vung vua khoanh (phu de, game...)
HOTKEY_QUIT = "ctrl+alt+q"

MAX_WORDS = 25          # so tu toi da hien trong 1 lan tra
SHOW_ENGLISH = True     # hien them dong nghia tieng Anh
TRANSLATE_VI = True     # dich Viet qua mang cho Nhat/Han va tu tieng Anh la
                        # (co cache, tra roi thi lan sau khong can mang)
# True = bam ra ngoai popup thi popup tu dong dong
CLOSE_ON_FOCUS_OUT = os.environ.get("SCAN_KEEP_OPEN") != "1"
POPUP_WIDTH = 470       # co mac dinh; keo goc ◢ cua popup de doi, app nho lai
POPUP_MAX_HEIGHT = 600
POPUP_MIN_SIZE = (340, 160)
CEFR_BADGES = ("A1", "A2", "B1", "B2", "C1", "C2", "IT")   # tu tieng Anh pho bien

# Giao dien popup: "sang" (nen trang nga, xanh tre hop logo) hoac "toi" (ban cu)
THEME = "sang"

if THEME == "toi":
    BG = "#1c1f26"
    BG_ALT = "#242833"
    FG = "#e8eaf0"
    FG_DIM = "#9aa2b1"
    ACCENT = "#f0b429"
    BORDER = "#3a4152"
    # Mau theo thanh dieu tieng Trung (kieu Pleco/Hanping)
    TONE_COLORS = {1: "#e5534b", 2: "#e2953a", 3: "#4aa96c", 4: "#4d8ee8", 5: "#8b93a3"}
else:
    BG = "#fcfbf7"           # trang nga - do choi hon trang tinh
    BG_ALT = "#eaf2ec"       # xanh tre rat nhat cho thanh tren / duoi
    FG = "#1e2a23"
    FG_DIM = "#5d6b63"
    ACCENT = "#1f7a55"       # xanh tre cua logo
    BORDER = "#c9dacf"
    # Thanh dieu: dam hon ban toi de doc ro tren nen sang
    TONE_COLORS = {1: "#d0342c", 2: "#c96f12", 3: "#23854a", 4: "#2563c9", 5: "#6f7782"}

from paths import APP_DIR, DATA_DIR
AUDIO_DIR = os.path.join(DATA_DIR, "audio")
LOG_PATH = os.path.join(DATA_DIR, "langscan.log")
POPUP_PREFS = os.path.join(DATA_DIR, "popup.json")   # kich thuoc popup da keo
SNIP_PREFS = os.path.join(DATA_DIR, "snip.json")     # vung chup lan truoc
LOCK_PORT = 50521       # cong cuc bo dung de chan chay 2 ban cung luc

# Tkinter chi duoc dung tu luong chinh. Luong phu (dich online, tra nguoc)
# day ham vao day, luong giao dien lay ra chay.
UI_QUEUE = queue.Queue()
_ui_pump_on = [False]


def ui_call(fn):
    """Nho luong giao dien chay ham nay (goi duoc tu bat ky luong nao)."""
    UI_QUEUE.put(fn)


def start_ui_pump(root):
    """Bat vong lap rut hang doi giao dien - goi tu luong chinh, mot lan."""
    if _ui_pump_on[0]:
        return
    _ui_pump_on[0] = True

    def pump():
        try:
            while True:
                fn = UI_QUEUE.get_nowait()
                try:
                    fn()
                except Exception as e:
                    print("[!] Loi khi cap nhat giao dien:", e)
        except queue.Empty:
            pass
        root.after(60, pump)

    root.after(60, pump)


# --------------------------------------------------- chay ngam (pythonw) ----
def setup_logging():
    """Chay bang pythonw thi khong co console -> print() se loi. Ghi ra file log."""
    if sys.stdout is not None and sys.stderr is not None:
        return
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        f = open(LOG_PATH, "a", encoding="utf-8", buffering=1)
    except Exception:
        f = open(os.devnull, "w")
    sys.stdout = sys.stderr = f
    print("\n===== {} khoi dong =====".format(time.strftime("%Y-%m-%d %H:%M:%S")))


def already_running():
    """Giu mot socket cuc bo lam 'khoa' - ban thu hai se khong mo duoc."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", LOCK_PORT))
        s.listen(1)
    except OSError:
        return True
    globals()["_LOCK_SOCKET"] = s        # giu tham chieu de khong bi dong
    return False


# --------------------------------------------------------------- audio -----
class Speaker(object):
    """Phat am: gTTS (online, co cache) -> SAPI (offline) -> tat."""

    def __init__(self):
        self.mode = None
        self._mixer = None
        try:
            import pygame
            pygame.mixer.init()
            self._mixer = pygame.mixer
        except Exception:
            self._mixer = None
        try:
            import gtts  # noqa: F401
            if self._mixer is not None:
                self.mode = "gtts"
        except Exception:
            pass
        if self.mode is None:
            try:
                import win32com.client  # noqa: F401
                self.mode = "sapi"
            except Exception:
                self.mode = None
        os.makedirs(AUDIO_DIR, exist_ok=True)

    @property
    def available(self):
        return self.mode is not None

    def say(self, text, lang=langs.ZH):
        if not text or not self.available:
            return
        threading.Thread(target=self._say, args=(text, lang), daemon=True).start()

    def _say(self, text, lang):
        try:
            if self.mode == "gtts":
                import hashlib
                code = langs.TTS_LANG.get(lang, "zh-CN")
                # md5 thay cho hash(): hash() cua Python doi moi lan mo app nen
                # truoc day cache khong bao gio dung lai, lan nao cung tai lai
                key = hashlib.md5(text.encode("utf-8")).hexdigest()[:16]
                path = os.path.join(AUDIO_DIR, "{}_{}.mp3".format(code, key))
                if not os.path.exists(path):
                    from gtts import gTTS
                    gTTS(text=text, lang=code).save(path)
                self._mixer.music.load(path)
                self._mixer.music.play()
            elif self.mode == "sapi":
                import win32com.client
                win32com.client.Dispatch("SAPI.SpVoice").Speak(text)
        except Exception as e:
            print("[!] Khong phat am duoc:", e)


# ----------------------------------------------------------- clipboard -----
def grab_selection():
    """Gia lap Ctrl+C de lay doan dang boi den, roi tra clipboard ve nhu cu."""
    import keyboard
    import pyperclip

    try:
        old = pyperclip.paste()
    except Exception:
        old = ""

    # Nha cac phim dang giu cua to hop hotkey truoc khi gui Ctrl+C
    for k in ("ctrl", "alt", "shift", "d", "c", "j", "k", "e", "s", "x"):
        try:
            keyboard.release(k)
        except Exception:
            pass
    time.sleep(0.05)

    marker = "\x00__scan__\x00"
    try:
        pyperclip.copy(marker)
    except Exception:
        pass

    keyboard.send("ctrl+c")

    text = ""
    for _ in range(20):                      # cho toi da ~1 giay
        time.sleep(0.05)
        try:
            cur = pyperclip.paste()
        except Exception:
            cur = marker
        if cur != marker:
            text = cur
            break

    try:
        pyperclip.copy(old)                  # tra clipboard ve nguyen trang
    except Exception:
        pass
    return text


# --------------------------------------------------------------- popup -----
# Chu co dau / chu d cua tieng Viet -> coi la go tieng Viet
RE_VI = langs.RE_VI
_QUOTES = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'})


class Popup(object):
    def __init__(self, root, analyzer, speaker):
        self.root = root
        self.analyzer = analyzer
        self.speaker = speaker
        self.win = None
        self.src_pref = "auto"      # ngon ngu nguon dang chon trong popup
        self.dst_pref = "vi"        # ngon ngu dich dang chon trong popup
        self._pos = None            # giu vi tri popup khi dich lai
        self._menu_open = False
        self.reverse = None         # chi so tra nguoc (dung lan dau, ~10 giay)
        self._hint_empty = False    # mo o go tay trong: hien huong dan
        # Kich thuoc nguoi dung keo: user_h None = tu co gian theo noi dung
        self.width, self.user_h = POPUP_WIDTH, None
        self._load_size()

    def close(self, _=None):
        if self.win is not None:
            try:
                self.win.destroy()
            except Exception:
                pass
            self.win = None

    # ---- dung khung
    def show(self, raw_text, force_lang=None, keep_pos=False):
        # Vai app dua chu Viet dang to hop (NFD: dau tach rieng): doi ve NFC
        # de nhan dien tieng Viet va tkinter ve dau dung cho
        raw_text = unicodedata.normalize("NFC", raw_text or "")
        # Dau nhay cong (’ “ ”): font chu Han cua o nhap ve rong nhu mot chu
        # Han nen trong nhu thua dau cach ("Saturday’ s") -> doi ve dau thuong
        raw_text = raw_text.translate(_QUOTES)
        self._pos = None
        self._phrase_lbl = None
        if not keep_pos:                # quet / boi den moi -> nguon ve 'Tu dong'
            self.src_pref = "auto"
        if keep_pos and self.win is not None:
            try:
                self._pos = (self.win.winfo_x(), self.win.winfo_y())
            except Exception:
                self._pos = None
        self.close()
        eff_force = force_lang or (self.src_pref if self.src_pref != "auto" else None)
        has_cjk = bool(langs.RE_HAN.search(raw_text) or langs.RE_KANA.search(raw_text)
                       or langs.RE_HANGUL.search(raw_text))
        is_vi = (not force_lang) and (
            self.src_pref == VI or
            (self.src_pref in ("auto", langs.EN) and not has_cjk
             and bool(RE_VI.search(raw_text.lower()))))
        # Tieng Viet go khong dau / chu OCR mat dau ('toi di hoc', 'ngan hang'):
        # truoc day bi coi la tieng Anh roi dich ra cau vo nghia.
        # 'maybe' ('xin chao', 'ni hao'): van tra nhu pinyin, them muc tieng Viet.
        vi_plain = None
        if not is_vi and not force_lang and self.src_pref == "auto" and not has_cjk:
            try:
                vi_plain = self.analyzer.vietnamese_plain(raw_text)
            except Exception:
                vi_plain = None
            is_vi = vi_plain == "vi"
        if is_vi:                       # go tieng Viet: khong tra tu dien ngoai ngu
            lang, cards, err = None, [], ""
            text = " ".join(raw_text.split())
        else:
            lang, cards, err = self.analyzer.analyze(
                raw_text, force_lang=eff_force, max_words=MAX_WORDS)
            text = langs.clean(raw_text, lang) if lang else ""
            if not text and cards and lang in (langs.JA, langs.KO):
                # go phien am: dich ca cau tren chu kana / Hangul da doi lai
                try:
                    text = self.analyzer.romanized_text(raw_text, lang)
                except Exception:
                    text = ""

        win = tk.Toplevel(self.root)
        self.win = win
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg=BORDER)

        outer = tk.Frame(win, bg=BG, bd=0)
        outer.pack(padx=1, pady=1, fill="both", expand=True)

        # ---- thanh tren: o nhap (sua duoc) + nut Tra + dong
        head = tk.Frame(outer, bg=BG_ALT)
        head.pack(fill="x")
        shown = (raw_text or text or "").strip()   # giu nguyen chu goc, ke ca dau va dong
        ent = tk.Text(head, bg=BG, fg=FG, insertbackground=FG, relief="flat",
                      font=("Microsoft YaHei", 12), highlightthickness=1,
                      highlightbackground=BORDER, highlightcolor=ACCENT,
                      wrap="word", height=1, width=10, padx=6, pady=4, undo=True)
        ent.insert("1.0", shown)
        ent.pack(side="left", fill="x", expand=True, padx=(10, 6), pady=8)
        self._entry = ent

        def _get():
            return ent.get("1.0", "end-1c").strip()

        def _lines():
            # Tk dem so CHO XUONG DONG giua dau va cuoi (it hon so dong 1 don
            # vi): 2 dong tra ve 1 -> truoc day o nhap thieu mat dong cuoi
            n = ent.count("1.0", "end-1c", "displaylines")
            n = n[0] if isinstance(n, tuple) else n
            return int(n or 0) + 1

        def _fit(_e=None):
            """O nhap cao vua du so dong chu (toi da 6), dai hon thi cuon."""
            try:
                ent.update_idletasks()
                n = max(1, min(6, _lines()))
                if int(ent.cget("height")) != n:
                    ent.config(height=n)
                    self._regrow()
            except Exception:
                pass

        def _redo(_e=None, _force=force_lang):
            q = _get()
            if q:
                self.root.after(10, lambda: self.show(q, _force, keep_pos=True))
            return "break"

        def _newline(_e=None):
            ent.insert("insert", "\n")
            _fit()
            return "break"

        def _wheel_text(e):
            try:
                if _lines() > int(ent.cget("height")):
                    ent.yview_scroll(int(-e.delta / 120), "units")
                    return "break"
            except Exception:
                pass

        for seq in ("<Return>", "<KP_Enter>"):
            ent.bind(seq, _redo)
        for seq in ("<Shift-Return>", "<Shift-KP_Enter>"):
            ent.bind(seq, _newline)
        ent.bind("<KeyRelease>", _fit)
        ent.bind("<<Paste>>", lambda e: ent.after(20, _fit))
        ent.bind("<MouseWheel>", _wheel_text)
        win.after(40, _fit)
        win.after(250, _fit)
        # Do lai moi khi o nhap duoc ve / doi be rong: sau OCR may dang ban, cua
        # so hien muon hon 250ms nen hai lan do tren dem sai so dong (con 1
        # dong, dong sau bi che). Doi chieu cao xong Tk ve lai -> _fit thay
        # khong doi gi nua nen khong lap vo han.
        ent.bind("<Map>", lambda e: ent.after(10, _fit), add="+")
        ent.bind("<Configure>", lambda e: ent.after(10, _fit), add="+")
        # Nut Tra bam dong dau o nhap (o nhap cao nhieu dong thi khong troi
        # xuong giua); chua cho ben phai cho nut dong o goc.
        tk.Button(head, text="Tra", bg=ACCENT, fg=BG, bd=0, padx=10, pady=2,
                  activebackground=FG, activeforeground=BG, cursor="hand2",
                  font=("Segoe UI", 9, "bold"), command=_redo
                  ).pack(side="left", anchor="n", padx=(0, 34), pady=(10, 8))
        # Nut dong sat goc tren ben phai, sang do khi re chuot (kieu Windows)
        close = tk.Label(head, text="✕", bg=BG_ALT, fg=FG_DIM, cursor="hand2",
                         font=("Segoe UI", 11), width=3, pady=2)
        close.place(relx=1.0, x=0, y=0, anchor="ne")
        close.bind("<Enter>", lambda e: close.config(bg="#c42b1c", fg="white"))
        close.bind("<Leave>", lambda e: close.config(bg=BG_ALT, fg=FG_DIM))
        close.bind("<Button-1>", lambda e: self.close())

        # ---- thanh ngon ngu: nguon -> dich, ngon ngu nhan ra, nut nghe
        bar = tk.Frame(outer, bg=BG_ALT)
        bar.pack(fill="x")
        src_choices = list(SRC_CHOICES)
        src_var = tk.StringVar(value=LABEL.get(self.src_pref, "Tự động"))
        dst_var = tk.StringVar(value=LABEL.get(self.dst_pref, "Việt"))

        def _pick_src(name):
            self.src_pref = next((k for k, n in SRC_CHOICES if n == name), "auto")
            self.root.after(10, lambda: self.show(_get(), None, keep_pos=True))

        def _pick_dst(name):
            self.dst_pref = next((k for k, n in DST_CHOICES if n == name), VI)
            self.root.after(10, lambda: self.show(_get(), None, keep_pos=True))

        tk.Label(bar, text="Nguồn", bg=BG_ALT, fg=FG_DIM,
                 font=("Segoe UI", 8)).pack(side="left", padx=(10, 2), pady=(0, 4))
        self._option(bar, src_var, [n for _, n in src_choices], _pick_src
                     ).pack(side="left", pady=(0, 4))
        def _swap(_lang=lang, _vi=is_vi):
            cur_src = self.src_pref
            if cur_src == "auto":
                cur_src = VI if _vi else (_lang or langs.EN)
            cur_dst = self.dst_pref if not (_vi and self.dst_pref == VI) else langs.EN
            res = getattr(getattr(self, "_phrase_lbl", None), "_result", "")
            q = res or _get()
            self.src_pref, self.dst_pref = cur_dst, cur_src
            self.root.after(10, lambda: self.show(q, None, keep_pos=True))
        tk.Button(bar, text="⇄", bg=BG_ALT, fg=ACCENT, bd=0, cursor="hand2",
                  activebackground=BORDER, activeforeground=ACCENT,
                  font=("Segoe UI", 11, "bold"), command=_swap
                  ).pack(side="left", padx=6, pady=(0, 4))
        tk.Label(bar, text="Đích", bg=BG_ALT, fg=FG_DIM,
                 font=("Segoe UI", 8)).pack(side="left", padx=(0, 2), pady=(0, 4))
        self._option(bar, dst_var, [n for _, n in DST_CHOICES], _pick_dst
                     ).pack(side="left", pady=(0, 4))
        if lang or is_vi:
            tk.Label(bar, text=("Việt" if is_vi else langs.LANG_NAME[lang]),
                     bg=BORDER, fg=ACCENT,
                     font=("Segoe UI", 8, "bold"), padx=6, pady=1
                     ).pack(side="left", padx=(10, 0), pady=(0, 4))
        if text and lang and self.speaker.available:
            tk.Button(bar, text="▶ Nghe", bg=BG_ALT, fg=ACCENT, bd=0,
                      activebackground=BORDER, activeforeground=ACCENT,
                      cursor="hand2", font=("Segoe UI", 9),
                      command=lambda: self.speaker.say(text, lang)
                      ).pack(side="left", padx=6, pady=(0, 4))

        # ---- than: danh sach the tu, cuon duoc
        body = tk.Frame(outer, bg=BG)
        body.pack(fill="both", expand=True)
        canvas = tk.Canvas(body, bg=BG, highlightthickness=0, width=self.width)
        scroll = tk.Scrollbar(body, orient="vertical", command=canvas.yview,
                              bg=BG, troughcolor=BG, bd=0, highlightthickness=0)
        inner = tk.Frame(canvas, bg=BG)
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        inner_id = canvas.create_window((0, 0), window=inner, anchor="nw", width=self.width)
        self._laid_w = self.width
        # Keo goc doi co -> canvas rong/hep ra: noi dung va cac dong chu chay theo
        canvas.bind("<Configure>",
                    lambda e, c=canvas, i=inner_id: self._on_resize(c, i, e.width))
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        def _wheel(e, canvas=canvas):
            try:
                canvas.yview_scroll(int(-e.delta / 120), "units")
            except tk.TclError:           # popup da dong -> go su kien, het loi
                try:
                    canvas.unbind_all("<MouseWheel>")
                except Exception:
                    pass
        canvas.bind_all("<MouseWheel>", _wheel)
        self._canvas, self._inner = canvas, inner

        target = self.dst_pref if self.dst_pref != VI else langs.EN
        # Pinyin lay tu chu GOC: chon nguon 'Trung' thi langs.clean() bo het chu
        # Latinh, 'wo shi' thanh rong va truoc day bao "Khong tra duoc tu nao".
        py_text = text if (text and lang != langs.ZH) else " ".join(raw_text.split())
        want_py = (not is_vi
                   and bool(re.match(r"^[A-Za-zÀ-ǿ1-5 ']{2,}$", py_text))
                   and len(py_text.split()) <= 10
                   and self.src_pref in ("auto", langs.ZH)
                   and lang in (None, langs.EN, langs.ZH)
                   # Tu dong + tu tieng Anh that ('bank'): khong doc them nhu pinyin
                   # (ra toan 半空, 扮酷... thua). Muon doc pinyin thi chon nguon Trung.
                   # Chi tinh tu tieng Anh pho bien (co cap CEFR / thuat ngu IT):
                   # tu dien Anh-Viet co ca muc hiem 'wo', 'shi', 'ni' -> 'wo shi',
                   # 'ni hao' van phai doc nhu pinyin
                   and not (self.src_pref == "auto" and lang == langs.EN and cards
                            and all(c.badge in CEFR_BADGES for c in cards)))
        # Tu dong ma tieng Anh khong ra gi ('taberu', 'annyeong'): thu doc nhu
        # romaji tieng Nhat / phien am tieng Han
        want_rom = (want_py and self.src_pref == "auto" and lang == langs.EN
                    and not any(c.found for c in cards))
        if is_vi:
            # Cum khong dau ngan ('ngan hang'): dich may doan bua ("Ngan cave"),
            # phan tra nguoc ben duoi da ra dung - bo dong dich ca cum
            if not (vi_plain == "vi" and len(text.split()) <= 2):
                self._phrase_line(inner, text, VI, target=target)
        elif not raw_text.strip() and self._hint_empty:
            self._message(inner, "Gõ hoặc dán chữ cần dịch vào ô phía trên rồi nhấn "
                                 "Enter.\nViệt ⇄ Trung / Nhật / Hàn / Anh; gõ pinyin "
                                 "(yinhang, yín háng) cũng được.")
        elif err:
            self._message(inner, err)
        elif lang is None and not want_py:
            self._message(inner, "Vùng bôi đen không có chữ nào tra được.")
        elif not cards:
            if not want_py:                 # pinyin thi phan tra pinyin ben duoi lo
                self._message(inner, "Không tra được từ nào trong đoạn này.")
        else:
            # Dich ca cau (chay ngam, co cache) - huu ich nhat voi cau dai
            # Dich ca cum khi co tu 2 tu tro len, ke ca khi cac tu phu
            # (that/of/you...) bi loc nen chi con 1 the tu.
            multi_word = (lang not in (langs.ZH, langs.JA)
                          and len(text.split()) >= 2)
            if TRANSLATE_VI and (len(cards) > 1 or multi_word or self.dst_pref != VI):
                self._phrase_line(inner, text, lang)
            for i, c in enumerate(cards):
                self._card_block(inner, c, first=(i == 0))

        if is_vi or want_py or vi_plain == "maybe":
            self._extra_lookup(win, inner, py_text if want_py else text,
                               is_vi, target, want_py, want_rom,
                               also_vi=(vi_plain == "maybe"))

        # Gon de khong bi goc bo cat chu; chua le phai cho goc keo ◢
        mods = HOTKEY_ZH.rsplit("+", 1)[0].title()
        footbar = tk.Frame(outer, bg=BG_ALT)
        footbar.pack(fill="x")
        foot = tk.Label(footbar, anchor="w", bg=BG_ALT, fg=FG_DIM, font=("Segoe UI", 8),
                        text="Esc đóng  ·  Enter tra lại  ·  {}+{}/{}/{}/{}: ép Trung/Nhật/Hàn/Anh"
                        .format(mods, HOTKEY_ZH[-1].upper(), HOTKEY_JA[-1].upper(),
                                HOTKEY_KO[-1].upper(), HOTKEY_EN[-1].upper()))
        foot.pack(fill="x", ipady=4, padx=(14, 24))

        # Popup khong co thanh tieu de (overrideredirect) nen tu lam: keo vung
        # trong cua thanh tren / thanh ngon ngu / dong duoi de di chuyen,
        # keo goc ◢ de doi co.
        for w in (head, bar, footbar, foot):
            self._draggable(w, win)
        grip = tk.Label(outer, text="◢", bg=BG_ALT, fg=FG_DIM, cursor="size_nw_se",
                        font=("Segoe UI", 9))
        grip.place(relx=1.0, rely=1.0, x=-6, y=-3, anchor="se")   # tranh goc bo
        grip.bind("<ButtonPress-1>", lambda e, w=win: self._resize_start(e, w))
        grip.bind("<B1-Motion>", lambda e, w=win: self._resize_move(e, w))
        grip.bind("<ButtonRelease-1>", lambda e: self._resize_end())

        self._place(win)
        self._round_corners(win)
        win.bind("<Escape>", self.close)
        if CLOSE_ON_FOCUS_OUT:
            # Chi dong khi focus roi han khoi popup (chuyen giua o nhap, nut,
            # menu chon ngon ngu trong popup thi khong dong)
            def _focus_out(_e=None, _win=win):
                def _check():
                    if self.win is not _win or self._menu_open:
                        return
                    try:
                        w = _win.focus_get()
                    except Exception:
                        w = None
                    if w is not None:
                        try:
                            if isinstance(w, tk.Menu) or w.winfo_toplevel() is _win:
                                return
                        except Exception:
                            return
                    self.close()
                _win.after(200, _check)
            win.bind("<FocusOut>", _focus_out)
        win.focus_force()
        try:
            ent.focus_set()
            ent.tag_add("sel", "1.0", "end-1c")
            ent.mark_set("insert", "end-1c")
        except Exception:
            pass

    def _option(self, parent, var, names, command):
        """O chon (xo xuong) ngon ngu, ve theo mau popup."""
        om = tk.OptionMenu(parent, var, *names, command=command)
        om.config(bg=BG, fg=FG, activebackground=BORDER, activeforeground=FG,
                  bd=0, highlightthickness=0, relief="flat", padx=6, pady=1,
                  font=("Segoe UI", 9), cursor="hand2")
        menu = om["menu"]
        menu.config(bg=BG, fg=FG, activebackground=ACCENT, activeforeground=BG,
                    bd=0, font=("Segoe UI", 9),
                    postcommand=lambda: setattr(self, "_menu_open", True))
        menu.bind("<Unmap>", lambda e: self.root.after(
            300, lambda: setattr(self, "_menu_open", False)))
        return om

    def _message(self, parent, msg):
        tk.Label(parent, text=msg, bg=BG, fg=FG_DIM, font=("Segoe UI", 10),
                 wraplength=self.width - 30, justify="left").pack(
                     anchor="w", padx=14, pady=14)

    # ---- khung dich ca cau (noi bat, co nut Sao chep)
    def _phrase_line(self, parent, text, lang, target=None):
        target = target or self.dst_pref
        if target == lang:              # nguon trung dich -> tu doi sang ngon ngu kia
            target = langs.EN if lang == VI else VI
        box = tk.Frame(parent, bg=BG_ALT)
        box.pack(fill="x", padx=10, pady=(8, 2))
        top = tk.Frame(box, bg=BG_ALT)
        top.pack(fill="x", padx=10, pady=(6, 0))
        tk.Label(top, text="DỊCH  →  {}".format(LABEL.get(target, target).upper()),
                 bg=BG_ALT, fg=ACCENT, font=("Segoe UI", 8, "bold")).pack(side="left")
        lbl = tk.Label(box, text="đang dịch...", bg=BG_ALT, fg=FG_DIM,
                       font=("Microsoft YaHei", 13),
                       wraplength=self.width - 40, justify="left")
        copy_btn = tk.Button(top, text="Sao chép", bg=BG_ALT, fg=ACCENT, bd=0,
                             activebackground=BORDER, activeforeground=ACCENT,
                             cursor="hand2", font=("Segoe UI", 8))
        copy_btn.config(command=lambda: self._copy(lbl, copy_btn))
        copy_btn.pack(side="right")
        if self.speaker.available:
            # Hai nut doc to canh nhau: cau DA DICH (giong ngon ngu dich) va
            # cau GOC can dich (giong ngon ngu nguon). Pack tu phai sang trai.
            def _say(_lbl=lbl, _t=target):
                said = getattr(_lbl, "_result", "")
                if said:
                    self.speaker.say(said, _t)
            for label, cmd in (("▶ Câu dịch", _say),
                               ("▶ Câu gốc", lambda _s=text, _l=lang: self.speaker.say(_s, _l))):
                tk.Button(top, text=label, bg=BG_ALT, fg=ACCENT, bd=0,
                          activebackground=BORDER, activeforeground=ACCENT,
                          cursor="hand2", font=("Segoe UI", 8), command=cmd
                          ).pack(side="right", padx=(0, 8))
        lbl.pack(anchor="w", padx=10, pady=(2, 8))
        self._phrase_lbl = lbl

        # Phien am Latin (pinyin / romaji / RR) cho cau Trung / Nhat / Han:
        # cau goc o tren ban dich, cau dich ra o duoi - de doc duoc ca cau
        cjk = (langs.ZH, langs.JA, langs.KO)

        def roman_label(before):
            return tk.Label(box, text="", bg=BG_ALT, fg=ACCENT, font=("Segoe UI", 10, "italic"),
                            wraplength=self.width - 40, justify="left")

        def fill_roman(rl, sentence, rlang, **pack):
            def work():
                try:
                    r = self.analyzer.romanize_sentence(sentence, rlang)
                except Exception as e:
                    print("[!] Loi phien am:", e)
                    r = ""
                if r:
                    def show():
                        try:
                            if rl.winfo_exists():
                                rl.config(text=r)
                                rl.pack(anchor="w", padx=10, **pack)
                                self._regrow()
                        except tk.TclError:
                            pass
                    ui_call(show)
            threading.Thread(target=work, daemon=True).start()

        if lang in cjk:                  # cau goc tieng Trung/Nhat/Han
            fill_roman(roman_label(lbl), text, lang, before=lbl, pady=(2, 0))
        after = None
        if target in cjk:                # dich ra tieng Trung/Nhat/Han
            out_rl = roman_label(None)
            after = lambda vi: fill_roman(out_rl, vi, target, after=lbl, pady=(0, 8))
        # Lam sach cau truoc khi gui dich may (noi dong / gach noi, dau cau, chu
        # IN HOA...) - o nhap van hien chu goc
        try:
            mt_text = self.analyzer.prepare_for_mt(text, lang)
        except Exception:
            mt_text = text

        # Dich may dich sai thuat ngu ('offline' -> 'ngoai tuyen') thi dich lai
        # voi thuat ngu dung trong bo chuyen nganh
        def fix(out, _src=mt_text, _l=lang, _t=target):
            return self.analyzer.enforce_terms(
                _src, _l, out, _t, lambda s: tr.translate(s, _l, target=_t))
        self._fill_async(lbl, mt_text, lang, prefix="", color=FG, target=target,
                         after=after, fix=fix)

    def _copy(self, lbl, btn=None):
        result = getattr(lbl, "_result", "")
        if not result:
            return
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(result)
            self.root.update()
            if btn is not None:
                btn.config(text="Đã chép ✓")
        except Exception:
            pass

    # ---- mo o go tay (nhan dup Ctrl): popup trong, con tro nam san o o nhap
    def show_empty(self):
        self._hint_empty = True
        try:
            self.show("", None)
        finally:
            self._hint_empty = False

    def _section(self, parent, title):
        tk.Label(parent, text=title.upper(), bg=BG, fg=ACCENT,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=12, pady=(10, 0))

    # ---- keo di chuyen / doi co popup
    @staticmethod
    def _round_corners(win, radius=16):
        """Bo goc popup. Windows 11: nho DWM ve (min, co bong do). Windows 10
        khong co tinh nang do: cat cua so thanh hinh chu nhat bo goc, cat lai
        moi khi doi co."""
        try:
            import ctypes
            win.update_idletasks()
            hwnd = int(win.wm_frame(), 16)
            pref = ctypes.c_int(2)                       # DWMWCP_ROUND
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 33, ctypes.byref(pref), ctypes.sizeof(pref)) == 0:
                return                                   # 33 = DWMWA_WINDOW_CORNER_PREFERENCE
        except Exception:
            return

        def clip(_e=None):
            try:
                w, h = win.winfo_width(), win.winfo_height()
                rgn = ctypes.windll.gdi32.CreateRoundRectRgn(0, 0, w + 1, h + 1,
                                                             radius, radius)
                ctypes.windll.user32.SetWindowRgn(hwnd, rgn, True)
            except Exception:
                pass
        clip()
        win.bind("<Configure>", clip, add="+")

    def _load_size(self):
        try:
            import json
            with open(POPUP_PREFS, encoding="utf-8") as f:
                d = json.load(f)
            self.width = max(POPUP_MIN_SIZE[0], int(d.get("width", POPUP_WIDTH)))
            h = d.get("height")
            self.user_h = max(POPUP_MIN_SIZE[1], int(h)) if h else None
        except Exception:
            pass

    def _save_size(self):
        try:
            import json
            with open(POPUP_PREFS, "w", encoding="utf-8") as f:
                json.dump({"width": self.width, "height": self.user_h}, f)
        except Exception:
            pass

    @staticmethod
    def _draggable(widget, win):
        """Giu chuot trai vao vung trong cua widget roi keo -> di chuyen popup.
        Chi bat su kien tren chinh widget, nen bam nut / o nhap ben trong van binh thuong."""
        def press(e):
            widget._drag = (e.x_root - win.winfo_x(), e.y_root - win.winfo_y())

        def move(e):
            dx, dy = getattr(widget, "_drag", (0, 0))
            win.geometry("+{}+{}".format(e.x_root - dx, e.y_root - dy))
        widget.bind("<ButtonPress-1>", press)
        widget.bind("<B1-Motion>", move)
        widget.configure(cursor="fleur")

    def _resize_start(self, e, win):
        self._rs = (e.x_root, e.y_root, win.winfo_width(), win.winfo_height())
        self._resizing = True

    def _resize_end(self):
        self._resizing = False
        self._save_size()

    def _resize_move(self, e, win):
        x0, y0, w0, h0 = self._rs
        w = max(POPUP_MIN_SIZE[0] + 18, w0 + e.x_root - x0)
        h = max(POPUP_MIN_SIZE[1], h0 + e.y_root - y0)
        self.user_h = h                      # chieu cao toi da tu gio (xem _height)
        win.geometry("{}x{}".format(w, h))

    def _on_resize(self, canvas, item, width):
        """Canvas doi be rong: keo khung noi dung theo va ngat dong lai chu."""
        if width < 50:
            return
        try:
            canvas.itemconfigure(item, width=width)
        except tk.TclError:
            return
        delta = width - self._laid_w
        if not delta:
            return
        self._laid_w = width
        # Chi nho be rong khi nguoi dung dang keo: canvas thuc te lech vai diem
        # anh so voi self.width (thanh cuon, vien), nho moi lan se hep dan
        if getattr(self, "_resizing", False):
            self.width = width

        def walk(w):
            for c in w.winfo_children():
                if isinstance(c, tk.Label):
                    try:
                        wl = int(str(c.cget("wraplength")))
                        if wl > 0:
                            c.configure(wraplength=max(120, wl + delta))
                    except (tk.TclError, ValueError):
                        pass
                walk(c)
        walk(self._inner)

    def _height(self, win):
        """Chieu cao popup: vua noi dung, toi da bang co nguoi dung da keo
        (chua keo thi POPUP_MAX_HEIGHT). It chu thi popup gon lai, nhieu chu
        thi dan toi muc do roi cuon - khong de khoang trang thua."""
        max_h = self.user_h or POPUP_MAX_HEIGHT
        try:
            win.update_idletasks()
            need = self._inner.winfo_reqheight()
            chrome = win.winfo_reqheight() - self._canvas.winfo_reqheight()
            self._canvas.configure(height=max(90, min(need, max_h - chrome)))
            win.update_idletasks()
        except Exception:
            pass
        return min(win.winfo_reqheight(), max_h)

    def _regrow(self):
        """Noi dung vua dai ra (dich xong, tra nguoc xong): gian popup cho vua."""
        win = self.win
        if win is None:
            return
        try:
            h = self._height(win)
            w = self.width + 18
            sh = win.winfo_screenheight()
            x, y = win.winfo_x(), win.winfo_y()
            if y + h > sh - 40:
                y = max(10, sh - h - 40)
            win.geometry("{}x{}+{}+{}".format(w, h, x, y))
        except Exception:
            pass

    # ---- tra nguoc Viet -> ngoai ngu / go pinyin (chay ngam, khong lam treo popup)
    def _extra_lookup(self, win, inner, query, is_vi, target, want_py, want_rom=False,
                      also_vi=False):
        lbl = tk.Label(inner, text="đang tìm từ trong chỉ mục...", bg=BG, fg=FG_DIM,
                       font=("Segoe UI", 9, "italic"))
        lbl.pack(anchor="w", padx=12, pady=(8, 4))

        def work():
            backward, pinyin, phrase, note = [], [], [], ""
            romans = []                 # [(tieu de, danh sach the)]
            if want_rom:
                for rlang, title in ((langs.JA, "Đọc như romaji tiếng Nhật"),
                                     (langs.KO, "Đọc như phiên âm tiếng Hàn")):
                    try:            # chua cai tu dien Nhat thi bo qua, khong bao loi
                        found = [c for c in self.analyzer.romanized(query, rlang) if c.found]
                    except Exception:
                        found = []
                    if found:
                        romans.append((title, found))
            try:
                if self.reverse is None:
                    ui_call(lambda: lbl.winfo_exists() and lbl.config(
                        text="đang dựng chỉ mục tra ngược (chỉ lần đầu, ~10 giây)..."))
                    self.reverse = reverse_mod.Reverse(self.analyzer)
                rv = self.reverse
                if is_vi or also_vi:            # also_vi: 'xin chao' doc ca kieu Viet
                    if target in (langs.JA, langs.KO):
                        backward, _bridge = rv.search_foreign(query, target)
                        if backward:
                            note = "qua Hán tự và tiếng Anh"
                    else:
                        backward = rv.search(
                            query, only=target if target in (langs.ZH, langs.EN) else None)
                    # Thuat ngu chuyen nganh len dau ('bảng cân đối kế toán' -> 资产负债表)
                    tcards = self.analyzer.terms_from_vi(
                        query, target if target in (langs.ZH, langs.JA, langs.KO) else langs.EN)
                    if tcards:
                        seen = {c.word for c in tcards}
                        backward = tcards + [c for c in backward if c.word not in seen]
                if want_py:
                    phrase = rv.pinyin_phrase(query)       # 'wo shi' -> 我 是
                    if len(query.split()) <= 3:
                        pinyin = rv.search_pinyin(query)
            except Exception as e:
                note = str(e)

            def apply_():
                try:
                    if self.win is not win or not lbl.winfo_exists():
                        return
                    if not backward and not pinyin and not phrase and not romans:
                        # Go tu / cum tieng Viet ma khong ra gi: bao ro. Ca cau thi
                        # tra nguoc vo nghia - dong dich ca cau o tren la du.
                        if note or (is_vi and len(query.split()) <= 2):
                            lbl.config(text=note or "không tìm thấy từ nào nghĩa là '{}'"
                                       .format(query))
                        else:                   # thu doc pinyin / romaji khong ra: im lang
                            lbl.destroy()
                        self._regrow()
                        return
                    lbl.destroy()
                    if backward:
                        found = {c.lang for c in backward}
                        title = ("Tiếng Việt → tiếng {}".format(LABEL.get(found.pop(), ""))
                                 if len(found) == 1 else "Tiếng Việt → Trung / Anh")
                        if note:
                            title += "  ({})".format(note)
                        if also_vi and not is_vi:
                            title = "Nếu là tiếng Việt không dấu:  " + title
                        self._section(inner, title)
                        for i, c in enumerate(backward):
                            self._card_block(inner, c, first=(i == 0))
                    for title, rcards in romans:
                        self._section(inner, title)
                        for i, c in enumerate(rcards):
                            self._card_block(inner, c, first=(i == 0))
                    if phrase:
                        self._section(inner, "Câu pinyin:  " + " ".join(c.word for c in phrase))
                        for i, c in enumerate(phrase):
                            self._card_block(inner, c, first=(i == 0))
                    if pinyin:
                        self._section(inner, "Đọc như một từ" if phrase else "Đọc như pinyin")
                        for i, c in enumerate(pinyin):
                            self._card_block(inner, c, first=(i == 0))
                    self._regrow()
                except Exception:
                    pass
            ui_call(apply_)
        threading.Thread(target=work, daemon=True).start()

    # ---- mot the tu
    def _card_block(self, parent, card, first=False, width=None):
        width = width or self.width
        block = tk.Frame(parent, bg=BG)
        block.pack(fill="x", padx=12, pady=(10 if first else 6, 2))

        row = tk.Frame(block, bg=BG)
        row.pack(fill="x")

        color = FG
        if card.lang == langs.ZH and len(card.tones) == 1:
            color = TONE_COLORS.get(card.tones[0], FG)
        tk.Label(row, text=card.word, bg=BG, fg=color,
                 font=("Microsoft YaHei", 20, "bold")).pack(side="left")

        if card.badge:
            known = not card.badge.lower().startswith(("ngoài", "thuần"))
            tk.Label(row, text=card.badge, bg=BORDER if known else BG_ALT,
                     fg=FG if known else FG_DIM, font=("Segoe UI", 8, "bold"),
                     padx=6, pady=1).pack(side="left", padx=6)

        if card.reading:
            tk.Label(row, text="[{}]".format(card.reading), bg=BG, fg=ACCENT,
                     font=("Segoe UI", 12)).pack(side="left", padx=4)

        if self.speaker.available:
            tk.Button(row, text="▶", bg=BG, fg=FG_DIM, bd=0, cursor="hand2",
                      activebackground=BG, activeforeground=ACCENT,
                      font=("Segoe UI", 9),
                      command=lambda: self.speaker.say(card.speak, card.lang)
                      ).pack(side="left")

        if not card.found:
            if TRANSLATE_VI:
                lbl = self._sense(block, "...", FG_DIM, 11, width)
                self._fill_async(lbl, card.speak, card.lang, color=FG)
            else:
                tk.Label(block, text="không có trong từ điển", bg=BG, fg=FG_DIM,
                         font=("Segoe UI", 9)).pack(anchor="w")
            return

        # Tieng Trung: nghia Viet co san offline.
        # Nhat/Han: dich ngam roi dien vao sau.
        if card.vi:
            self._sense(block, "; ".join(card.vi), FG, 11, width)
        elif TRANSLATE_VI and card.lang != langs.ZH:
            lbl = self._sense(block, "...", FG_DIM, 11, width)
            self._fill_async(lbl, card.word, card.lang, prefix="", color=FG)

        if SHOW_ENGLISH and card.en:
            self._sense(block, "; ".join(card.en), FG_DIM, 9, width)
        if card.note:
            self._sense(block, card.note, FG_DIM, 9, width)

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=12, pady=(6, 0))

    def _sense(self, block, text, color, size, width=None):
        lbl = tk.Label(block, text=text, bg=block["bg"], fg=color,
                       font=("Segoe UI", size),
                       wraplength=(width or self.width) - 40,
                       justify="left")
        lbl.pack(anchor="w", pady=(1, 0))
        return lbl

    def _fill_async(self, label, text, lang, prefix="", color=FG, target="vi", after=None,
                    fix=None):
        """Dich o luong khac roi cap nhat nhan - khong lam treo popup.
        fix(ban_dich) -> ban_dich: sua them (o luong nen) truoc khi hien.
        after(ban_dich): goi them (o luong nen) khi dich xong, neu co."""
        source = text

        def done(vi):
            if fix and vi:
                try:
                    vi = fix(vi) or vi
                except Exception as e:
                    print("[!] Loi khi ep thuat ngu:", e)
            if after and vi and vi.strip().lower() != str(source).strip().lower():
                try:
                    after(vi)
                except Exception as e:
                    print("[!] Loi sau khi dich:", e)
            def apply_():
                try:
                    if not label.winfo_exists():
                        return
                    if vi and vi.strip().lower() == str(source).strip().lower():
                        label._result = vi
                        label.config(text="giữ nguyên (tên riêng hoặc thuật ngữ)",
                                     fg=FG_DIM)
                    elif vi:
                        label._result = vi
                        label.config(text=prefix + vi, fg=color)
                    else:
                        label.config(text="(chưa dịch được - có thể đang mất mạng)",
                                     fg=FG_DIM)
                    self._regrow()
                except Exception:
                    pass
            ui_call(apply_)
        tr.translate_async(text, lang, done, target=target)

    # ---- vi tri popup: canh con tro chuot, khong tran ra ngoai man hinh
    def _place(self, win):
        h = self._height(win)
        w = self.width + 18
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        if getattr(self, "_pos", None):          # dich lai: giu nguyen cho cu
            x, y = self._pos
            x = max(0, min(x, sw - w - 10))
            y = max(0, min(y, sh - h - 40))
            win.geometry("{}x{}+{}+{}".format(w, h, x, y))
            return
        x, y = self.root.winfo_pointerxy()
        x = max(10, min(x + 12, sw - w - 10))
        y = y + 16
        if y + h > sh - 40:
            y = max(10, y - h - 32)
        win.geometry("{}x{}+{}+{}".format(w, h, x, y))


# ---------------------------------------------------- nhan dup Ctrl --------
class DoubleTap(object):
    """Bat kieu bam Ctrl hai lan lien tiep.

    Chi tinh khi Ctrl duoc bam MOT MINH: neu giua hai lan co phim khac
    (Ctrl+C, Ctrl+V...) thi bo qua, khong thi cu copy hai lan la no nhay ra.
    """

    def __init__(self, callback, key="ctrl", gap=DOUBLE_TAP_GAP):
        self.callback = callback
        self.key = key
        self.gap = gap
        self.last_release = -1e9      # chua bam lan nao
        self.dirty = False          # da co phim khac bam xen vao chua

    def is_target(self, name):
        return name in (self.key, "left " + self.key, "right " + self.key)

    def feed(self, name, is_down, now):
        """Nap mot su kien phim. Tra ve True neu vua du hai lan bam."""
        if not self.is_target(name):
            if is_down:
                self.dirty = True   # dang giu Ctrl ma bam phim khac
            return False
        if is_down:
            return False
        # Ctrl vua duoc nha ra
        clean, self.dirty = not self.dirty, False
        if clean and (now - self.last_release) <= self.gap:
            self.last_release = -1e9
            return True
        self.last_release = now if clean else -1e9
        return False

    def hook(self, event):
        import keyboard
        try:
            fired = self.feed(event.name or "",
                              event.event_type == keyboard.KEY_DOWN,
                              time.time())
        except Exception:
            return
        if fired:
            self.callback()


# ------------------------------------------------ chup man hinh roi doc chu -
class Snipper(object):
    """Keo chuot chon mot vung man hinh -> OCR -> dua vao popup nhu binh thuong.

    Dung cho cho khong boi den duoc: anh, PDF scan, video, game, phan mem
    ve giao dien bang do hoa.
    """

    def __init__(self, root, on_text):
        self.root = root
        self.on_text = on_text          # goi lai voi doan chu doc duoc
        self.win = None
        self.canvas = None
        self.start = None
        self.rect = None
        self.last_box = self._load_box()  # vung khoanh lan truoc (toa do tkinter)

    @staticmethod
    def _load_box():
        try:
            import json
            with open(SNIP_PREFS, encoding="utf-8") as f:
                box = tuple(int(v) for v in json.load(f)["box"])
            return box if len(box) == 4 else None
        except Exception:
            return None

    def _save_box(self, box):
        self.last_box = box
        try:
            import json
            with open(SNIP_PREFS, "w", encoding="utf-8") as f:
                json.dump({"box": list(box)}, f)
        except Exception:
            pass

    def snip_again(self):
        """Chup lai dung vung lan truoc (chu doi, vi tri khong doi: phu de
        video, game, tai lieu cuon). Chua khoanh lan nao thi cho khoanh."""
        if self.win is not None:
            return
        if not self.last_box:
            self.start_snip()
            return
        self._grab(self.last_box)

    def _flash(self, box):
        """Nhay vien vang quanh vung vua chup ~0.5s de biet no chup cho nao.
        Ve SAU khi da chup xong nen khong lot vao anh."""
        x1, y1, x2, y2 = box
        t = 3
        wins = []
        for gx, gy, gw, gh in ((x1 - t, y1 - t, x2 - x1 + 2 * t, t),
                               (x1 - t, y2, x2 - x1 + 2 * t, t),
                               (x1 - t, y1, t, y2 - y1), (x2, y1, t, y2 - y1)):
            try:
                w = tk.Toplevel(self.root)
                w.overrideredirect(True)
                w.attributes("-topmost", True)
                w.configure(bg=ACCENT)
                w.geometry("{}x{}+{}+{}".format(max(gw, 1), max(gh, 1), gx, gy))
                wins.append(w)
            except Exception:
                pass

        def gone():
            for w in wins:
                try:
                    w.destroy()
                except Exception:
                    pass
        self.root.after(500, gone)

    def start_snip(self):
        if self.win is not None:
            return
        try:
            from PIL import ImageGrab      # noqa: F401
        except ImportError:
            self.on_text("", "thiếu thư viện Pillow - chạy setup.bat (hoặc cài lại LangScan)")
            return

        win = tk.Toplevel(self.root)
        self.win = win
        win.attributes("-fullscreen", True)
        win.attributes("-alpha", 0.25)
        win.attributes("-topmost", True)
        win.configure(bg="black", cursor="crosshair")
        canvas = tk.Canvas(win, bg="black", highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        self.canvas = canvas
        canvas.bind("<Button-1>", self._down)
        canvas.bind("<B1-Motion>", self._move)
        canvas.bind("<ButtonRelease-1>", self._up)
        win.bind("<Escape>", lambda e: self._cancel())
        win.focus_force()

    def _cancel(self):
        if self.win is not None:
            try:
                self.win.destroy()
            except Exception:
                pass
            self.win = None
            self.rect = None

    def _down(self, event):
        self.start = (event.x_root, event.y_root)
        self.rect = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline=ACCENT, width=2)
        self._origin = (event.x, event.y)

    def _move(self, event):
        if self.rect is not None:
            self.canvas.coords(self.rect, self._origin[0], self._origin[1],
                               event.x, event.y)

    def _up(self, event):
        if self.start is None:
            self._cancel()
            return
        x1, y1 = self.start
        x2, y2 = event.x_root, event.y_root
        self.start = None
        self._cancel()
        box = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        if box[2] - box[0] < 8 or box[3] - box[1] < 8:
            self.on_text("", "vùng chọn quá nhỏ")
            return
        self._save_box(box)              # cho Ctrl+Alt+Z chup lai vung nay
        # Cho lop phu bien han roi moi chup, khong thi chup nham chinh no
        self.root.after(120, lambda: self._grab(box))

    def _screen_scale(self):
        """Ti le giua diem anh THAT va toa do tkinter bao.

        Windows dat ty le hien thi 125%/150% thi tkinter van bao toa do theo
        he 100%, con anh chup ra la diem anh that -> khoanh mot dang, chup
        mot neo. Phai nhan lai cho dung.
        """
        if getattr(self, "_scale", None) is None:
            try:
                from PIL import ImageGrab
                phys = ImageGrab.grab().size[0]
                logical = self.root.winfo_screenwidth()
                self._scale = (phys / float(logical)) if logical else 1.0
                if not (0.5 <= self._scale <= 4.0):
                    self._scale = 1.0
                if abs(self._scale - 1.0) > 0.01:
                    print("[*] Ty le man hinh {:.0f}% - da bu lai khi chup".format(
                        self._scale * 100))
            except Exception:
                self._scale = 1.0
        return self._scale

    def _grab(self, box):
        # Do ti le man hinh o LUONG CHINH: no goi Tk (winfo_screenwidth), ma Tk
        # goi tu luong nen khong an toan (co luc loi -> ti le 100%, chup lech)
        scale = self._screen_scale()

        def work():
            try:
                from PIL import ImageGrab
                real = tuple(int(round(v * scale)) for v in box)
                try:
                    img = ImageGrab.grab(bbox=real, all_screens=True)
                except TypeError:          # ban Pillow cu khong co all_screens
                    img = ImageGrab.grab(bbox=real)
                ui_call(lambda: self._flash(box))
                # Chu nho thi phong to len - OCR doc chinh xac hon han
                if img.width < 900:
                    from PIL import Image
                    factor = min(3.0, 900.0 / max(img.width, 1))
                    img = img.resize((int(img.width * factor),
                                      int(img.height * factor)), Image.LANCZOS)
                import ocr
                text, lang = ocr.read_auto(img)
                if not text:
                    ui_call(lambda: self.on_text("", ocr.status_text()))
                else:
                    ui_call(lambda: self.on_text(text, ""))
            except Exception as e:
                ui_call(lambda: self.on_text("", "lỗi khi chụp / đọc chữ: {}".format(e)))
        threading.Thread(target=work, daemon=True).start()


# ------------------------------------------------------ cua so tra tu tay ---
SEARCH_WIDTH = 620
SEARCH_HEIGHT = 620

# Thanh chon ngon ngu kieu Google Dich: Nguon -> Dich.
VI = "vi"
SRC_CHOICES = (("auto", "Tự động"), (VI, "Việt"), (langs.ZH, "Trung"),
               (langs.JA, "Nhật"), (langs.KO, "Hàn"), (langs.EN, "Anh"))
DST_CHOICES = ((VI, "Việt"), (langs.ZH, "Trung"), (langs.EN, "Anh"),
               (langs.JA, "Nhật"), (langs.KO, "Hàn"))
LABEL = dict(SRC_CHOICES)



# ------------------------------------------------------- icon khay he thong -
class Tray(object):
    """Icon o khay he thong (canh dong ho). Khong co pystray thi bo qua."""

    def __init__(self, app):
        self.app = app
        self.icon = None

    def _image(self):
        # Khay he thong chi hien 16-24px: dung ban chu "V" cua logo
        import logo
        return logo.draw(32)

    def _menu(self):
        import pystray
        Item, Menu = pystray.MenuItem, pystray.Menu
        return Menu(
            Item("Tra từ đang bôi đen ({})".format(HOTKEY_LOOKUP.upper()),
                 lambda: self.app.on_hotkey(), default=True),
            Item("Ép tra tiếng Nhật ({})".format(HOTKEY_JA.upper()),
                 lambda: self.app.on_hotkey(langs.JA)),
            Item("Ép tra tiếng Hàn ({})".format(HOTKEY_KO.upper()),
                 lambda: self.app.on_hotkey(langs.KO)),
            Item("Ép tra tiếng Anh ({})".format(HOTKEY_EN.upper()),
                 lambda: self.app.on_hotkey(langs.EN)),
            Menu.SEPARATOR,
            Item("Ô gõ tay để dịch / tra từ ({})".format(
                "nhấn đúp Ctrl"),
                 lambda: self.app.open_search()),
            Item("Chụp màn hình rồi đọc chữ ({})".format(HOTKEY_SNIP.upper()),
                 lambda: self.app.open_snip()),
            Item("Chụp lại vùng cũ ({})".format(HOTKEY_SNIP_AGAIN.upper()),
                 lambda: self.app.open_snip_again()),
            Menu.SEPARATOR,
            Item("Khởi động cùng Windows", lambda: self._toggle_autostart(),
                 checked=lambda item: autostart.is_installed()),
            Item("Mở thư mục cài đặt", lambda: self._open(APP_DIR)),
            Item("Xem nhật ký (log)", lambda: self._open(LOG_PATH)),
            Menu.SEPARATOR,
            Item("Thoát ({})".format(HOTKEY_QUIT.upper()), lambda: self.app.quit()),
        )

    def _open(self, path):
        try:
            os.startfile(path)
        except Exception as e:
            print("[!] Khong mo duoc {}: {}".format(path, e))

    def _toggle_autostart(self):
        def work():
            try:
                autostart.toggle()
            except Exception as e:
                print("[!] Loi bat/tat khoi dong cung Windows:", e)
            if self.icon is not None:
                self.icon.update_menu()
        threading.Thread(target=work, daemon=True).start()

    def start(self):
        try:
            import pystray  # noqa: F401
        except ImportError:
            print("[!] Chua co icon khay (thieu pystray/pillow). Cai: pip install pystray pillow")
            return
        try:
            import pystray
            self.icon = pystray.Icon("LangScan", self._image(),
                                     "LangScan - {} de tra tu".format(
                                         HOTKEY_LOOKUP.upper()), self._menu())
            threading.Thread(target=self.icon.run, daemon=True).start()
        except Exception as e:
            print("[!] Khong tao duoc icon khay:", e)


# ----------------------------------------------------------------- app -----
class App(object):
    def __init__(self):
        self.analyzer = langs.Analyzer()
        self.root = tk.Tk()
        self.root.withdraw()
        self.speaker = Speaker()
        if not self.speaker.available:
            print("[!] Chua phat am duoc (thieu gtts/pygame). Cai:  pip install gtts pygame")
        self.popup = Popup(self.root, self.analyzer, self.speaker)
        self.snipper = Snipper(self.root, self._snip_done)
        self.q = queue.Queue()
        self.tray = Tray(self)

    def open_search(self):
        """Mo cua so go tay - phai chay o luong giao dien."""
        self.q.put(("__search__", None))

    def open_snip(self):
        """Chup mot vung man hinh roi doc chu."""
        self.q.put(("__snip__", None))

    def open_snip_again(self):
        """Chup lai dung vung lan truoc."""
        self.q.put(("__snip_again__", None))

    def _snip_done(self, text, err):
        """OCR xong: co chu thi hien popup, khong thi bao loi."""
        if text:
            import ocr
            text = ocr.tidy_lines(text)      # noi dong bi ngat giua cau (tieu de...)
            print("[*] OCR doc duoc: {}".format(text[:60].replace("\n", " ")))
            self.popup.show(text)
        else:
            fatal_msg = err or "không đọc được chữ nào trong vùng đã chọn"
            print("[!] OCR:", fatal_msg)
            self.popup.show("")
            try:
                self.popup._message(self.popup._inner, fatal_msg)
            except Exception:
                pass

    def on_hotkey(self, force_lang=None):
        # Chay o luong cua thu vien keyboard -> chi day yeu cau vao hang doi
        threading.Thread(target=self._collect, args=(force_lang,), daemon=True).start()

    def _collect(self, force_lang):
        try:
            self.q.put((grab_selection(), force_lang))
        except Exception as e:
            print("[!] Loi khi lay vung boi den:", e)

    def pump(self):
        try:
            while True:
                text, force_lang = self.q.get_nowait()
                if text == "__search__":
                    self.popup.show_empty()
                elif text == "__snip__":
                    self.snipper.start_snip()
                elif text == "__snip_again__":
                    # Dong popup cu truoc: no hay nam de len chinh vung can chup
                    self.popup.close()
                    self.root.after(150, self.snipper.snip_again)
                else:
                    self.popup.show(text, force_lang)
        except queue.Empty:
            pass
        self.root.after(60, self.pump)

    def run(self):
        import keyboard
        keyboard.add_hotkey(HOTKEY_LOOKUP, lambda: self.on_hotkey(None))
        keyboard.add_hotkey(HOTKEY_ZH, lambda: self.on_hotkey(langs.ZH))
        keyboard.add_hotkey(HOTKEY_JA, lambda: self.on_hotkey(langs.JA))
        keyboard.add_hotkey(HOTKEY_KO, lambda: self.on_hotkey(langs.KO))
        keyboard.add_hotkey(HOTKEY_EN, lambda: self.on_hotkey(langs.EN))
        if DOUBLE_CTRL_SEARCH:
            self._double_ctrl = DoubleTap(self.open_search)
            keyboard.hook(self._double_ctrl.hook)
        keyboard.add_hotkey(HOTKEY_SNIP, self.open_snip)
        keyboard.add_hotkey(HOTKEY_SNIP_AGAIN, self.open_snip_again)
        keyboard.add_hotkey(HOTKEY_QUIT, self.quit)
        self.tray.start()
        start_ui_pump(self.root)
        print()
        print("=" * 62)
        print("  LangScan dang chay - Trung / Nhat / Han / Anh")
        print("  {}  tra tu (tu nhan dien ngon ngu)".format(HOTKEY_LOOKUP.upper()))
        print("  {} / {} / {} / {}  ep tra Trung / Nhat / Han / Anh".format(
            HOTKEY_ZH.upper(), HOTKEY_JA.upper(), HOTKEY_KO.upper(), HOTKEY_EN.upper()))
        print("  {}  mo o go tay de dich / tra tu (2 chieu Viet <-> nuoc ngoai)".format(
            "NHAN DUP CTRL" if DOUBLE_CTRL_SEARCH else "(tu icon khay)"))
        print("  {}  chup mot vung man hinh roi doc chu (OCR)".format(
            HOTKEY_SNIP.upper()))
        print("  {}  chup lai dung vung vua khoanh".format(HOTKEY_SNIP_AGAIN.upper()))
        print("  Khoi dong cung Windows: {}".format(
            "DANG BAT" if autostart.is_installed() else "dang tat"))
        print("  Thoat: {} (hoac chuot phai vao icon khay)".format(HOTKEY_QUIT.upper()))
        print("=" * 62)
        self.root.after(60, self.pump)
        self.root.mainloop()

    def quit(self):
        print("[*] Thoat.")
        try:
            if self.tray.icon is not None:
                self.tray.icon.stop()
        except Exception:
            pass
        try:
            self.root.quit()
        finally:
            os._exit(0)


def fatal(msg):
    """Bao loi ra man hinh - vi chay ngam thi khong ai doc duoc console."""
    print("[!]", msg)
    try:
        import tkinter.messagebox as mb
        r = tk.Tk()
        r.withdraw()
        mb.showerror("LangScan", msg)
        r.destroy()
    except Exception:
        pass


def selftest():
    """LangScan.exe --selftest: tra thu 4 thu tieng + OCR, ghi ra data/selftest.txt.

    Ban .exe khong co console va khong chay duoc chandoan.bat, nen day la
    cach kiem tra nhanh sau khi cai (khong mo popup, khong dang ky phim tat)."""
    setup_logging()                 # .exe khong co console: print() ghi vao log
    path = os.path.join(DATA_DIR, "selftest.txt")
    lines, ok = [], True
    a = langs.Analyzer()
    for text, force, want in (("我在银行工作", None, "银行"), ("食べました", None, "食べる"),
                              ("은행에서", None, "은행"), ("studying", None, "study"),
                              ("tabemashita", langs.JA, "食べる"),
                              ("annyeonghaseyo", langs.KO, "안녕하세요")):
        try:
            lang, cards, err = a.analyze(text, force_lang=force)
            words = [c.word for c in cards]
            good = any(want in w for w in words)
            lines.append("[{}] {} -> {} {}".format("OK" if good else "X ", text,
                                                    " ".join(words), err))
        except Exception as e:
            good = False
            lines.append("[X ] {} -> loi {}: {}".format(text, type(e).__name__, e))
        ok = ok and good
    try:
        import ocr
        lines.append("OCR: " + ocr.status_text().replace("\n", " | "))
    except Exception as e:
        lines.append("OCR: loi {}".format(e))
    lines.append("Thu muc app: " + APP_DIR)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return 0 if ok else 1


def main():
    # LangScan.exe --autostart install|uninstall: autostart.py goi lai .exe
    # bang quyen admin de tao/xoa task (ban .py thi goi thang autostart.py)
    if len(sys.argv) > 2 and sys.argv[1] == "--autostart":
        return autostart.main([sys.argv[0], sys.argv[2]])
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        return selftest()
    setup_logging()
    if already_running():
        print("[=] LangScan da chay san roi - thoat ban thu hai.")
        return 0
    for mod in ("keyboard", "pyperclip"):
        try:
            __import__(mod)
        except ImportError:
            fatal("Thiếu thư viện '{}'.\nMở thư mục LangScan và chạy setup.bat "
                  "(hoặc cài lại LangScan).".format(mod))
            return 1
    try:
        App().run()
    except Exception as e:
        import traceback
        traceback.print_exc()
        fatal("Lỗi: {}\nXem chi tiết trong data/langscan.log".format(e))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
