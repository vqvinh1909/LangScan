# -*- coding: utf-8 -*-
"""
offline_mt.py - Dich ca cau KHONG CAN MANG (du phong khi mat mang).

Dung mo hinh mo cua Argos Translate (OpenNMT, giay phep MIT / CC) chay bang
CTranslate2 + SentencePiece - nhe, khong can PyTorch. Chi co cap truc tiep
Anh -> Viet; Trung / Nhat / Han -> Viet di vong qua tieng Anh nen kem hon
Google ro rang - chi de nam y chinh khi khong co mang.

Mo hinh tai ve data/argos/<nguon>_<dich>/ (~380MB cho ca 4 cap):
    python offline_mt.py download
Thu:
    python offline_mt.py "The server is offline."
"""

import json
import os
import re
import shutil
import sys
import tempfile
import threading
import urllib.request
import zipfile

from paths import DATA_DIR

MODELS_DIR = os.path.join(DATA_DIR, "argos")
INDEX_URL = "https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json"
# Chieu sang tieng Viet: en->vi truc tiep; zh/ja/ko di qua tieng Anh
PAIRS = (("en", "vi"), ("zh", "en"), ("ja", "en"), ("ko", "en"))
HEADERS = {"User-Agent": "Mozilla/5.0 (LangScan)"}

_lock = threading.Lock()
_loaded = {}                    # (nguon, dich) -> (Translator, SentencePiece)


# ---------------------------------------------------------- co san chua ----
def _pair_dir(src, tgt):
    return os.path.join(MODELS_DIR, "{}_{}".format(src, tgt))


def has_pair(src, tgt):
    d = _pair_dir(src, tgt)
    return (os.path.isfile(os.path.join(d, "model", "model.bin"))
            and os.path.isfile(os.path.join(d, "sentencepiece.model")))


def runtime_ready():
    try:
        import ctranslate2  # noqa: F401
        import sentencepiece  # noqa: F401
        return True
    except ImportError:
        return False


def can_translate(src, tgt):
    """Co dich offline duoc src -> tgt khong (truc tiep hoac qua tieng Anh)?"""
    if not runtime_ready() or src == tgt:
        return False
    if has_pair(src, tgt):
        return True
    return src != "en" and tgt != "en" and has_pair(src, "en") and has_pair("en", tgt)


def installed():
    return [p for p in PAIRS if has_pair(*p)]


# ---------------------------------------------------------------- dich ------
def _load(src, tgt):
    with _lock:
        if (src, tgt) not in _loaded:
            import ctranslate2
            import sentencepiece
            d = _pair_dir(src, tgt)
            tr = ctranslate2.Translator(os.path.join(d, "model"), device="cpu",
                                        inter_threads=1, intra_threads=2)
            sp = sentencepiece.SentencePieceProcessor(
                model_file=os.path.join(d, "sentencepiece.model"))
            _loaded[(src, tgt)] = (tr, sp)
        return _loaded[(src, tgt)]


def _sentences(text, src):
    """Cat cau: mo hinh dich tung cau tot hon ca doan dai."""
    if src in ("zh", "ja"):
        parts = re.split(r"(?<=[。！？!?])", text)
    else:
        parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def _translate_pair(text, src, tgt):
    tr, sp = _load(src, tgt)
    out_paras = []
    for para in text.split("\n"):
        sents = _sentences(para, src)
        if not sents:
            continue
        batch = [sp.encode(s, out_type=str) for s in sents]
        res = tr.translate_batch(batch, beam_size=2, max_decoding_length=256)
        # Ghep manh ve chu: '▁' la dau cach cua SentencePiece (sp.decode khong
        # nhan ra manh cua ben dich nen de nguyen '▁' trong chu)
        outs = [re.sub(r"\s+", " ", "".join(r.hypotheses[0]).replace("▁", " "))
                for r in res]
        joiner = "" if tgt in ("zh", "ja") else " "
        out_paras.append(joiner.join(o.strip() for o in outs))
    return "\n".join(out_paras).strip()


def translate(text, src, tgt="vi"):
    """Dich offline. '' neu chua co mo hinh cho cap nay."""
    text = (text or "").strip()
    if not text or not can_translate(src, tgt):
        return ""
    try:
        if has_pair(src, tgt):
            return _translate_pair(text, src, tgt)
        mid = _translate_pair(text, src, "en")          # di vong qua tieng Anh
        return _translate_pair(mid, "en", tgt) if mid else ""
    except Exception as e:
        print("[!] Dich offline loi:", e)
        return ""


# ---------------------------------------------------------- tai mo hinh ----
def _index():
    req = urllib.request.Request(INDEX_URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def _safe_extract(zf, dest):
    """Giai nen .argosmodel (file zip) - chi lay model/ va sentencepiece.model,
    chan duong dan '..' / tuyet doi."""
    names = zf.namelist()
    root = names[0].split("/")[0] + "/" if names else ""
    for name in names:
        rel = name[len(root):] if name.startswith(root) else name
        if not rel or rel.endswith("/"):
            continue
        if not (rel.startswith("model/") or rel == "sentencepiece.model"):
            continue
        target = os.path.normpath(os.path.join(dest, rel))
        if not target.startswith(os.path.normpath(dest) + os.sep):
            raise RuntimeError("duong dan la trong goi mo hinh: " + name)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with zf.open(name) as src, open(target, "wb") as out:
            shutil.copyfileobj(src, out, length=1024 * 1024)


def download(progress=print, pairs=PAIRS):
    """Tai cac mo hinh con thieu. progress(chuoi) de bao tien do.
    -> (so cap da co, loi hoac '')."""
    try:
        index = {(p.get("from_code"), p.get("to_code")): p for p in _index()}
    except Exception as e:
        return len(installed()), "khong tai duoc danh sach mo hinh: {}".format(e)
    os.makedirs(MODELS_DIR, exist_ok=True)
    for src, tgt in pairs:
        if has_pair(src, tgt):
            continue
        pkg = index.get((src, tgt))
        if not pkg or not pkg.get("links"):
            progress("Khong co mo hinh {} -> {}".format(src, tgt))
            continue
        url = pkg["links"][0]
        tmpdir = tempfile.mkdtemp(prefix="argos_")
        try:
            path = os.path.join(tmpdir, "model.zip")
            progress("Dang tai {} -> {} ...".format(src, tgt))
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=600) as r, open(path, "wb") as f:
                total = int(r.headers.get("Content-Length") or 0)
                done = 0
                while True:
                    chunk = r.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
                    done += len(chunk)
                    if total and done % (10 * 1024 * 1024) < 1024 * 1024:
                        progress("  {} -> {}: {:.0f}%".format(src, tgt, done * 100.0 / total))
            dest = _pair_dir(src, tgt)
            part = dest + ".part"
            shutil.rmtree(part, ignore_errors=True)
            with zipfile.ZipFile(path) as zf:
                _safe_extract(zf, part)
            shutil.rmtree(dest, ignore_errors=True)
            os.replace(part, dest)
            progress("  xong {} -> {}".format(src, tgt))
        except Exception as e:
            return len(installed()), "tai {} -> {} that bai: {}".format(src, tgt, e)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
    return len(installed()), ""


def main(argv):
    if len(argv) > 1 and argv[1] == "download":
        n, err = download()
        print("Da co {}/{} cap mo hinh. {}".format(n, len(PAIRS), err))
        return 1 if err else 0
    print("Mo hinh co san:", installed())
    text = " ".join(argv[1:]) or "The server is offline."
    for src in ("en", "zh", "ja", "ko"):
        out = translate(text, src, "vi")
        if out:
            print("[{} -> vi] {}".format(src, out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
