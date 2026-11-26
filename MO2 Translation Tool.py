#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MO2 Translation Tool — v3.0.1-ja.7（日本語化・改造版）
=====================================================

Mod Organizer 2 用の Mod 翻訳プラグイン（LLM / 機械翻訳）。

原作:   InfernoKgn — MO2 Translation Tool 3.0.1
        https://www.nexusmods.com/skyrimspecialedition/mods/197796
改造:   BluishCat（日本語 UI・不具合修正・機能追加）

原作の配布条件（Nexus の Permissions）に従い、原作者を明記して公開しています。
有料配布・Donation Points の対象にすることはできません。
変更点の一覧は同梱の README_ja.md を参照してください。
"""

import json
import mmap
import os
import queue
import re
import shutil
import struct
import sys
import tempfile
import threading
import time
import zipfile
import zlib
import time
import urllib.request
import urllib.parse
import json
from collections import Counter, OrderedDict
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib import request as urlrequest
from urllib import error as urlerror
from urllib.parse import urlencode

# ============================================================================
# Qt: то, что уже загружено в MO2
# ============================================================================
QT_FLAVOR = None
try:
    from PyQt6 import QtWidgets, QtCore, QtGui
    from PyQt6.QtWidgets import *      # noqa: F401,F403
    from PyQt6.QtCore import *         # noqa: F401,F403
    from PyQt6.QtGui import *          # noqa: F401,F403
    try:
        from PyQt6.QtGui import QShortcut, QKeySequence
    except ImportError:
        pass
    QT_FLAVOR = "PyQt6"
except ImportError:
    try:
        from PyQt5 import QtWidgets, QtCore, QtGui
        from PyQt5.QtWidgets import *  # noqa: F401,F403
        from PyQt5.QtCore import *     # noqa: F401,F403
        from PyQt5.QtGui import *      # noqa: F401,F403
        try:
            from PyQt5.QtWidgets import QShortcut
            from PyQt5.QtGui import QKeySequence
        except ImportError:
            pass
        QT_FLAVOR = "PyQt5"
    except ImportError:
        from PySide6 import QtWidgets, QtCore, QtGui
        from PySide6.QtWidgets import *  # noqa: F401,F403
        from PySide6.QtCore import *     # noqa: F401,F403
        from PySide6.QtGui import *      # noqa: F401,F403
        try:
            from PySide6.QtGui import QShortcut, QKeySequence
        except ImportError:
            pass
        QT_FLAVOR = "PySide6"


def _pick(*paths):
    """Ищет Qt-константу по нескольким путям (scoped Qt6 / flat Qt5)."""
    roots = {"Qt": Qt, "QtWidgets": QtWidgets, "QtGui": QtGui, "QtCore": QtCore}
    for path in paths:
        parts = path.split(".")
        cur = roots[parts[0]]
        try:
            for p in parts[1:]:
                cur = getattr(cur, p)
            return cur
        except AttributeError:
            continue
    raise AttributeError(f"Qt-константа не найдена: {paths}")


ALIGN_CENTER = _pick("Qt.AlignmentFlag.AlignCenter", "Qt.AlignCenter")
ALIGN_RIGHT = _pick("Qt.AlignmentFlag.AlignRight", "Qt.AlignRight")
ITEM_EDITABLE = _pick("Qt.ItemFlag.ItemIsEditable", "Qt.ItemIsEditable")
ITEM_ENABLED = _pick("Qt.ItemFlag.ItemIsEnabled", "Qt.ItemIsEnabled")
ITEM_SELECTABLE = _pick("Qt.ItemFlag.ItemIsSelectable", "Qt.ItemIsSelectable")
ITEM_USERCHECK = _pick("Qt.ItemFlag.ItemIsUserCheckable", "Qt.ItemFlag.ItemIsUserCheckable")
ITEM_CHECKED = _pick("Qt.CheckState.Checked", "Qt.Checked")
ITEM_UNCHECKED = _pick("Qt.CheckState.Unchecked", "Qt.Unchecked")
NO_EDIT = _pick("QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers",
                "QtWidgets.QAbstractItemView.NoEditTriggers")
EDIT_DBL = _pick("QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked",
                 "QtWidgets.QAbstractItemView.DoubleClicked")
EDIT_SEL = _pick("QtWidgets.QAbstractItemView.EditTrigger.SelectedClicked",
                 "QtWidgets.QAbstractItemView.SelectedClicked")
SEL_ROWS = _pick("QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows",
                 "QtWidgets.QAbstractItemView.SelectRows")
HDR_STRETCH = _pick("QtWidgets.QHeaderView.ResizeMode.Stretch",
                    "QtWidgets.QHeaderView.Stretch")
HDR_CONTENTS = _pick("QtWidgets.QHeaderView.ResizeMode.ResizeToContents",
                     "QtWidgets.QHeaderView.ResizeToContents")
HDR_FIXED = _pick("QtWidgets.QHeaderView.ResizeMode.Fixed",
                  "QtWidgets.QHeaderView.Fixed")                  
HDR_INTERACTIVE = _pick("QtWidgets.QHeaderView.ResizeMode.Interactive",
                        "QtWidgets.QHeaderView.Interactive")                                    
ECHO_PASSWORD = _pick("QtWidgets.QLineEdit.EchoMode.Password",
                      "QtWidgets.QLineEdit.Password")
CURSOR_END = _pick("QtGui.QTextCursor.MoveOperation.End", "QtGui.QTextCursor.End")
CURSOR_START = _pick("QtGui.QTextCursor.MoveOperation.Start", "QtGui.QTextCursor.Start")
CURSOR_DOWN = _pick("QtGui.QTextCursor.MoveOperation.Down", "QtGui.QTextCursor.Down")
KEEP_ANCHOR = _pick("QtGui.QTextCursor.MoveMode.KeepAnchor", "QtGui.QTextCursor.KeepAnchor")
BTN_YES = _pick("QtWidgets.QMessageBox.StandardButton.Yes", "QtWidgets.QMessageBox.Yes")
BTN_NO = _pick("QtWidgets.QMessageBox.StandardButton.No", "QtWidgets.QMessageBox.No")
TAB_N = _pick("QtWidgets.QTabWidget.TabPosition.North", "QtWidgets.QTabWidget.North")
EV_RESIZE = _pick("QtCore.QEvent.Type.Resize", "QtCore.QEvent.Resize")
ROLE_USER = _pick("Qt.ItemDataRole.UserRole", "Qt.UserRole")
SEL_MULTI = _pick("QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection",
                  "QtWidgets.QAbstractItemView.ExtendedSelection")
CTX_MENU = _pick("QtCore.Qt.ContextMenuPolicy.CustomContextMenu",
                 "QtCore.Qt.CustomContextMenu")
KEY_COPY = _pick("QtGui.QKeySequence.StandardKey.Copy", "QtGui.QKeySequence.Copy")
ST_EDIT = _pick("QtWidgets.QAbstractItemView.State.EditingState",
                "QtWidgets.QAbstractItemView.EditingState")
DLG_ACCEPTED = _pick("QtWidgets.QDialog.DialogCode.Accepted",
                     "QtWidgets.QDialog.Accepted")
BTN_OK = _pick("QtWidgets.QDialogButtonBox.StandardButton.Ok",
               "QtWidgets.QDialogButtonBox.Ok")
BTN_CANCEL = _pick("QtWidgets.QDialogButtonBox.StandardButton.Cancel",
                   "QtWidgets.QDialogButtonBox.Cancel")


def _exec_dialog(d):
    fn = getattr(d, "exec", None)
    if callable(fn):
        return fn()
    return getattr(d, "exec_")()


try:
    import mobase
    HAS_MOBASE = True
except ImportError:
    mobase = None
    HAS_MOBASE = False

_PLUGIN_BASE = mobase.IPluginTool if HAS_MOBASE else object

_ENCODING_BOMS = (
    (b"\xff\xfe\x00\x00", "utf-32-le"), (b"\x00\x00\xfe\xff", "utf-32-be"),
    (b"\xff\xfe", "utf-16-le"), (b"\xfe\xff", "utf-16-be"), (b"\xef\xbb\xbf", "utf-8-sig"),
)

def detect_text_encoding(raw: bytes, fallback: str = "utf-8") -> str:
    for bom, name in _ENCODING_BOMS:
        if raw.startswith(bom): return name
    if b"\x00" in raw[:512]:
        return "utf-16-be" if raw[0:512:2].count(0) > raw[1:512:2].count(0) else "utf-16-le"
    try:
        raw.decode("utf-8"); return "utf-8"
    except UnicodeDecodeError: pass
    for enc in ("cp1251", "cp1252"):
        try:
            raw.decode(enc); return enc
        except UnicodeDecodeError: continue
    return fallback

# Валидатор плейсхолдеров: токены, которые обязаны сохраниться в переводе.
PLACEHOLDER_RE = re.compile(
    r"%(?:\d+\$)?[-+#0]*\d*(?:\.\d+)?[hlL]?[diuxXeEfgGaAcspn%]"   # %d, %s, %f, %1$s, ...
    r"|</?[A-Za-z][A-Za-z0-9_\-.:\"' ]{0,64}/?>"                # <tag>, </b>, <br/>
    r"|\{[^{}\n]{0,48}\}"                                         # {0}, {player.name}
    r"|｟\d+｠"                                                    # оставшийся защитный маркер
)

_TARGET_SCRIPT_RE = {
    "ja": re.compile(r"[\u3040-\u30ff\u4e00-\u9fff\uff66-\uff9f]"),   # かな・漢字（1文字でもあれば日本語化済み扱い）
    "zh": re.compile(r"[\u4e00-\u9fff]"),
    "zh-CN": re.compile(r"[\u4e00-\u9fff]"),
    "zh-TW": re.compile(r"[\u4e00-\u9fff]"),
    "ru": re.compile(r"[А-Яа-яЁё]"),
}


def already_in_target(text, tgt, src="en"):
    """翻訳先の文字（日本語ならかな/漢字）を既に含む行か。
    含んでいれば LLM に送らず原文のまま返す。翻訳専用モデル（PLaMo 等）は
    「既に翻訳先言語なら変更しない」という指示を守らず逆方向に訳してしまうため、
    プロンプトに頼らずコード側で判定する。"""
    rx = _TARGET_SCRIPT_RE.get(tgt)
    if rx is None or tgt == src:
        return False
    return bool(rx.search(PLACEHOLDER_RE.sub("", text or "")))


def manifest_filename(mod_name):
    """記録ファイル名。長い Mod 名は短縮してハッシュを付ける（MO2 内では 260 文字を超えるパスに書けないため）。"""
    import hashlib
    safe = re.sub(r'[<>:"/\\|?*]', "_", mod_name or "").strip().rstrip(".") or "mod"
    if len(safe) > 40:
        safe = safe[:40].rstrip(" ._-") + "_" + hashlib.md5(mod_name.encode("utf-8")).hexdigest()[:8]
    return safe + ".json"


def find_manifest(mod_path, mod_name):
    """記録ファイルの場所（新しい短縮名 → 旧形式の名前 → フォルダ内の json の順に探す）。無ければ新しい名前のパス。"""
    d = os.path.join(mod_path, "MO2TranslationTool")
    new = os.path.join(d, manifest_filename(mod_name))
    if os.path.exists(new):
        return new
    legacy = re.sub(r'[<>:"/\\|?*]', "_", mod_name or "").strip().rstrip(".") or "mod"
    old = os.path.join(d, legacy + ".json")
    if os.path.exists(old):
        return old
    try:
        js = sorted(f for f in os.listdir(d) if f.lower().endswith(".json"))
        if js:
            return os.path.join(d, js[0])
    except OSError:
        pass
    return new


def _file_sig(path):
    try:
        st = os.stat(path)
        return [st.st_size, int(st.st_mtime)]
    except OSError:
        return None


def _esp_has_text(path, max_size=200 * 1024 * 1024):
    """esp/esm/esl に翻訳対象の文字列がありそうか（localized なら .strings 側なので False）。"""
    try:
        size = os.path.getsize(path)
        if size < 24 or size > max_size:
            return size > max_size
        with open(path, "rb") as f:
            head = f.read(24)
            if head[:4] != b"TES4":
                return False
            if struct.unpack_from("<I", head, 8)[0] & FLAG_LOCALIZED:
                return False
            f.seek(0)
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                return mm.find(b"FULL") >= 0 or mm.find(b"DESC") >= 0
    except Exception:
        return False


def _pex_has_display_text(path, tgt="ja", src="en", max_size=8 * 1024 * 1024):
    """状態判定用: .pex に翻訳対象の表示用文字列があるか（関数名を含まないファイルは解析しない）。"""
    try:
        if os.path.getsize(path) > max_size:
            return False
        with open(path, "rb") as f:
            data = f.read()
        if not any(k in data for k in (b"Option", b"InfoText", b"TitleText", b"ShowMessage",
                                        b"Notification", b"MessageBox")):
            return False
        return bool(pex_extract_strings(data, "utf-8", tgt, src))
    except Exception:
        return False


def _translation_key_gaps(mod_path, tgt="ja", src="en"):
    """Interface/Translations のルーズの英語訳ファイルのうち、翻訳先ファイルにキーが足りないもの → [(rel, 件数)]
    （ゲームが読むのは Interface/Translations 直下だけなので、そこだけ見る）"""
    gaps = []
    iface = _find_file_ci(mod_path, "interface")
    tdir = _find_file_ci(iface, "translations") if iface else None
    if not tdir or not os.path.isdir(tdir):
        return gaps
    rel_dir = os.path.relpath(tdir, mod_path).replace("\\", "/")
    for fn in os.listdir(tdir):
        if not fn.lower().endswith(".txt") or not is_source_lang_file(fn, src):
            continue
        gap_path, _t, missing = translation_gap(os.path.join(tdir, fn), tgt)
        if gap_path and missing:
            gaps.append((f"{rel_dir}/{fn}", len(missing)))
    return gaps


def compute_mod_status(mod_path, mod_name, tgt="ja", src="en", dsd_covered=frozenset(), include_pex=False,
                       include_skse_menu=False):
    """Mod の翻訳状態を判定する → (code, detail)。
    code: done=翻訳済み / stale=要再翻訳 / ja=翻訳先言語あり / todo=未翻訳 / none=対象なし"""
    mp = find_manifest(mod_path, mod_name)
    if os.path.exists(mp):
        try:
            with open(mp, encoding="utf-8") as f:
                man = json.load(f)
        except Exception:
            return "stale", "記録ファイルを読めません"
        if "written" not in man or "sources" not in man:
            files = man.get("files", [])
            if not files or not all(os.path.exists(os.path.join(mod_path, r)) for r in files):
                return "stale", "記録が古い形式で、訳ファイルの一部が見つかりません"
            man["written"] = {r: _file_sig(os.path.join(mod_path, r)) for r in files}
            srcs = {}
            src_suf = LANG_SUFFIX.get(src, src)
            for r in files:
                rl = r.replace("\\", "/")
                parts = rl.split("/")
                if "dynamicstringdistributor" in rl.lower() and len(parts) >= 5:
                    cand = parts[3]                       # SKSE/Plugins/DynamicStringDistributor/<esp>/x.json
                    if os.path.exists(os.path.join(mod_path, cand)):
                        srcs[cand] = _file_sig(os.path.join(mod_path, cand))
                elif file_lang(rl) == LANG_SUFFIX.get(tgt, tgt):
                    d = os.path.dirname(rl)
                    stem, ext = os.path.splitext(os.path.basename(rl))
                    want = (_LANG_TAIL_RE.sub("_" + src_suf, stem) + ext).lower()
                    try:
                        for fn in os.listdir(os.path.join(mod_path, d)):
                            if fn.lower() == want:
                                srcs[(d + "/" + fn) if d else fn] = _file_sig(os.path.join(mod_path, d, fn))
                    except OSError:
                        pass
            man["sources"] = srcs
            try:
                with open(mp, "w", encoding="utf-8") as f:
                    json.dump(man, f, ensure_ascii=False, indent=2)
            except OSError:
                pass
            return "done", f"{len(files)} ファイル（旧形式の記録を更新）"
        changed = [r for r, sig in man["written"].items()
                   if _file_sig(os.path.join(mod_path, r)) != sig]
        src_changed = [r for r, sig in man["sources"].items()
                       if _file_sig(os.path.join(mod_path, r)) != sig]
        if changed or src_changed:
            parts = []
            if src_changed:
                parts.append("元ファイルが変更: " + ", ".join(src_changed[:3]))
            if changed:
                parts.append("訳ファイルが変更/消失: " + ", ".join(changed[:3]))
            return "stale", " / ".join(parts)
        if include_pex and not any(r.lower().endswith(".pex") for r in man["written"]):
            sdir = os.path.join(mod_path, "Scripts")
            try:
                pex_todo = [f"Scripts/{fn}" for fn in os.listdir(sdir)
                            if fn.lower().endswith(".pex")
                            and _pex_has_display_text(os.path.join(sdir, fn), tgt, src)]
            except OSError:
                pex_todo = []
            if pex_todo:
                return "todo", "スクリプトが未翻訳: " + ", ".join(pex_todo[:4]) + (" …" if len(pex_todo) > 4 else "")
        gaps = _translation_key_gaps(mod_path, tgt, src)
        if gaps:
            return "todo", "訳ファイルのキー不足: " + ", ".join(f"{r}（{n}）" for r, n in gaps[:3]) + (" …" if len(gaps) > 3 else "")
        if include_skse_menu:
            written_n = {os.path.normcase(os.path.normpath(r)) for r in man["written"]}
            sk_todo, _sk_ja = skse_menu_status(mod_path, tgt, src, written_n)
            if sk_todo:
                return "todo", "SKSE メニューが未翻訳: " + ", ".join(sk_todo[:3]) + (" …" if len(sk_todo) > 3 else "")
        if not man["written"]:
            return "done", "確認済み・出力なし（公式レコードの上書きのみ等）"
        return "done", f"{len(man['written'])} ファイル"

    tsuf = LANG_SUFFIX.get(tgt, tgt).lower()
    ja_hits, todo = [], []
    for dp, dirs, fs in os.walk(mod_path):
        rel_dir = os.path.relpath(dp, mod_path).replace("\\", "/")
        rl = rel_dir.lower()
        if rl.split("/")[0] in ("mo2translationtool", "fomod"):
            dirs[:] = []
            continue
        names = {fn.lower() for fn in fs}
        for fn in fs:
            low = fn.lower()
            ext = os.path.splitext(low)[1]
            rel = fn if rel_dir == "." else f"{rel_dir}/{fn}"
            is_tr_txt = ext == ".txt" and "interface/translations" in rl
            if is_tr_txt or ext in STRING_EXTS:
                lang = file_lang(low)
                if lang == tsuf:
                    ja_hits.append(rel)
                elif not is_source_lang_file(low, src):
                    pass                      # 他言語の訳ファイル（翻訳元にしない）
                elif _localize_name(fn, tgt).lower() in names:
                    if is_tr_txt:             # 対になる翻訳先ファイルがある → 足りないキーがあれば対象
                        gap_path, _t, missing = translation_gap(os.path.join(dp, fn), tgt)
                        if gap_path and missing:
                            todo.append(f"{rel}（キー不足 {len(missing)}）")
                else:
                    todo.append(rel)
            elif low == "config.json" and rl.startswith("mcm/config/"):
                try:
                    if os.path.getsize(os.path.join(dp, fn)) < 2_000_000:
                        with open(os.path.join(dp, fn), "rb") as f:
                            raw = f.read()
                        txt = raw.decode("utf-8", "replace")
                        if already_in_target(txt, tgt, src):
                            ja_hits.append(rel)
                        elif any(not u["warn"] for u in load_json_units(text=txt, rel=rel)):
                            todo.append(rel)      # $KEY 参照だけの config は Translations 側で訳されるので対象外
                except OSError:
                    pass
            elif ext in (".esp", ".esm", ".esl") and rel_dir == ".":
                if low in dsd_covered:
                    ja_hits.append(rel + " (DSD)")
                elif _esp_has_text(os.path.join(dp, fn)):
                    todo.append(rel)
            elif include_pex and ext == ".pex" and rl == "scripts":
                if _pex_has_display_text(os.path.join(dp, fn), tgt, src):
                    todo.append(rel)
    if include_skse_menu:
        sk_todo, sk_ja = skse_menu_status(mod_path, tgt, src)
        todo += sk_todo
        ja_hits += sk_ja
    if todo:
        return "todo", ("一部日本語あり / " if ja_hits else "") + "対象: " + ", ".join(todo[:4]) + (" …" if len(todo) > 4 else "")
    if ja_hits:
        return "ja", ", ".join(ja_hits[:4]) + (" …" if len(ja_hits) > 4 else "")
    return "none", ""


def rollback_inplace(mod_path, mod_name):
    """元の Mod に書き込んだ訳を取り消す: 書いたファイルを削除し、退避した元ファイルを戻し、記録を消す。
    → (削除数, 復元数)。記録に載っていないファイルは触らない。"""
    mp = find_manifest(mod_path, mod_name)
    if not os.path.exists(mp):
        return 0, 0
    with open(mp, encoding="utf-8") as f:
        man = json.load(f)
    removed = restored = 0
    for b in man.get("backups", []):
        bak = os.path.join(mod_path, b)
        orig = re.sub(r"\.bak_[A-Za-z-]+$", "", bak)
        if os.path.exists(bak):
            shutil.copy2(bak, orig)
            os.remove(bak)
            restored += 1
    restored_set = {os.path.normcase(re.sub(r"\.bak_[A-Za-z-]+$", "", os.path.join(mod_path, b)))
                    for b in man.get("backups", [])}
    for r in man.get("files", []):
        full = os.path.join(mod_path, r)
        if os.path.normcase(full) in restored_set:
            continue                    # 元ファイルに戻したもの
        if os.path.exists(full):
            os.remove(full)
            removed += 1
            d = os.path.dirname(full)   # 空になったフォルダ（DSD 用など）を片付ける
            while d and os.path.normcase(d) != os.path.normcase(mod_path):
                try:
                    os.rmdir(d)
                except OSError:
                    break
                d = os.path.dirname(d)
    os.remove(mp)
    try:
        os.rmdir(os.path.dirname(mp))
    except OSError:
        pass
    return removed, restored


def check_placeholders(src, dst):
    """Возвращает (ok, lost). ok=False, если в dst не хватает хотя бы одного
    токена из src; lost — список потерянных токенов (без дублей).
    Сравнение мультимножествами: два %d в исходнике требуют двух %d в переводе."""
    src_tokens = PLACEHOLDER_RE.findall(src or "")
    if not src_tokens:
        return True, []
    dst_counts = Counter(PLACEHOLDER_RE.findall(dst or ""))
    lost = []
    for t in src_tokens:
        if dst_counts.get(t, 0) > 0:
            dst_counts[t] -= 1
        elif t not in lost:
            lost.append(t)
    return (not lost), lost

def has_missing_placeholders(src, dst):
    # Ищем токены вроде %d, <tag>, {0}, ｟1｠
    return not check_placeholders(src, dst)[0]

# ── Валидатор длины строки (MCM / XML / JSON интерфейсы) ───────────────────
LEN_LIMIT_RATIO = 1.4      # перевод длиннее оригинала на 40% и более
LEN_MIN_SRC = 3            # для совсем коротких строк сравнение бессмысленно
UI_LEN_EXTS = (".json", ".xml", ".pex")

def is_ui_length_file(rel):
    """Файл интерфейса (MCM-конфиг, XML-меню), где длина строки критична."""
    return (rel or "").lower().endswith(UI_LEN_EXTS)

def is_too_long(src, dst, ratio=LEN_LIMIT_RATIO):
    """True, если len(dst) > len(src) * ratio — перевод может не влезть в UI."""
    src, dst = src or "", dst or ""
    if len(src) < LEN_MIN_SRC or not dst:
        return False
    return len(dst) > len(src) * ratio

# ── Детектор смешанного языка (английские слова в русском переводе) ────────
_EN_WORD_RE = re.compile(r"[A-Za-z]{3,}")

def has_mixed_language(src, dst, target_lang):
    """True, если в переводе для target_lang == 'ru' остались английские слова.
    Имена собственные ( слова с заглавной буквы, присутствующие в оригинале)
    игнорируются; плейсхолдеры и теги словами не считаются."""
    if target_lang != "ru" or not dst:
        return False
    known = {w.lower() for w in _EN_WORD_RE.findall(src or "") if w[0].isupper()}
    clean = PLACEHOLDER_RE.sub(" ", dst)
    return any(w.lower() not in known for w in _EN_WORD_RE.findall(clean))

# ============================================================================
# Константы
# ============================================================================
APP_NAME = "MO2 Translation Tool"
APP_VERSION = "3.0.1-ja.7"
CONFIG_NAME = "MO2 Translation Tool.config.json"
GLOSSARY_NAME = "MO2 Translation Tool.glossary.json"

TEXT_EXT = (".txt", ".json", ".xml", ".ini", ".csv")
STRING_EXTS = (".strings", ".dlstrings", ".ilstrings")

T = {
    "backend": ("Бэкенд", "Backend"),
    "source": ("Исходный", "Source"),
    "target": ("Целевой", "Target"),
    "encoding": ("Кодировка", "Encoding"),
    "lang_ui": ("Язык интерфейса", "UI language"),
    "show_api": ("Показать настройки API", "Show API Settings"),
    "tr_settings": ("Настройки перевода", "Translation Settings"),
    "convert_units": ("Конвертировать футы в метры", "Convert feet to meters"),
    "delay": ("Задержка (мс)", "Delay (ms)"),
    "threads": ("Потоки", "Threads"),
    "batch": ("Строк за раз", "Lines per batch"),
    "dry_run": ("Пробный прогон", "Dry run"),
    "extract_bsa": ("Извлекать BSA/BA2", "Extract BSA/BA2"),
    "gen_report": ("Создать отчёт", "Generate report"),
    "api_settings": ("Настройки бэкендов", "Backend settings"),
    "openai_url": ("OpenAI-совм. URL", "OpenAI-compat URL"),
    "openai_model": ("Модель", "Model"),
    "openai_key": ("OpenAI/Strata ключ", "OpenAI/Strata key"),
    "ollama_url": ("Ollama URL", "Ollama URL"),
    "lmstudio_url": ("LM Studio URL", "LM Studio URL"),
    "openrouter_key": ("OpenRouter ключ", "OpenRouter key"),
    "deepl_key": ("DeepL ключ", "DeepL API key"),
    "yandex_key": ("Yandex ключ", "Yandex API key"),
    "temperature": ("Температура", "Temperature"),
    "max_tokens": ("Макс. токенов", "Max tokens"),
    "sys_prompt": ("Системный промпт", "System prompt"),
    "reset_default": ("Сбросить", "Reset to default"),
    "search_mods": ("Поиск модов…", "Search mods…"),
    "select_all": ("Выбрать все", "Select all"),
    "select_none": ("Снять выбор", "Select none"),
    "refresh": ("Обновить", "Refresh mods"),
    "add_folders": ("Добавить папки…", "Add folders…"),
    "col_mod": ("Мод", "Mod"),
    "col_plugins": ("Плагины", "Plugins"),
    "col_strings": ("Стр. таблицы", "String tables"),
    "col_trans": ("Переводы", "Translations"),
    "col_json": ("JSON", "JSON"),
    "col_xml": ("XML", "XML"),
    "tab_log": ("Журнал", "Log"),
    "tab_preview": ("Предпросмотр строк", "Strings Preview"),
    "tab_glossary": ("Глоссарий", "Glossary"),
    "col_src": ("Оригинал", "Original"),
    "col_dst": ("Перевод", "Translation"),
    "col_file": ("Файл", "File"),
    "col_status": ("Статус", "Status"),
    "gloss_add": ("Добавить", "Add"),
    "gloss_del": ("Удалить", "Delete"),
    "gloss_hint": ("Термины глоссария вшиваются в промпт как обязательные.",
                   "Glossary terms are injected into the prompt as mandatory."),
    "out_settings": ("Настройки вывода", "Output settings"),
    "folder": ("Папка", "Folder"),
    "browse": ("Обзор…", "Browse…"),
    "mod_name": ("Имя мода", "Mod name"),
    "save_zip": ("Сохранить как .zip", "Save as .zip"),
    "save_dsd": ("Сохранить как DSD (без изменения .esp)", "Save as DSD (without editing .esp)"),
    "btn_translate": ("Перевести", "Translate"),
    "btn_save": ("Сохранить вывод", "Save Output"),
    "btn_cancel": ("Отмена", "Cancel"),
    "btn_open_out": ("Открыть папку вывода", "Open output folder"),
    "btn_close": ("Закрыть", "Close"),
    "btn_open_file": ("Открыть файл…", "Open file…"),
    "btn_load_sst": ("Словари .sst", "SST dictionaries"),
    "tip_load_sst": (
        "Словари xTranslator (.sst, бинарные SSU2/SSU8/SSU9) или текст «оригинал \\t перевод».\n"
        "Точные совпадения переводятся из словаря без обращения к LLM. Пути запоминаются.",
        "xTranslator dictionaries (.sst, binary SSU2/SSU8/SSU9) or text \"original \\t translation\".\n"
        "Exact matches are translated from the dictionary without calling the LLM. Paths are remembered."),
    "sst_loaded": ("Загружено {n} терминов из словаря .sst ({path}). Всего в словаре: {total}",
                   "Loaded {n} terms from .sst dictionary ({path}). Dictionary total: {total}"),
    "sst_no_pairs": ("В файле не найдено пар «оригинал → перевод».",
                     "No \"original → translation\" pairs found in the file."),
    "sst_error": ("Не удалось прочитать словарь .sst:", "Failed to read the .sst dictionary:"),
    "sst_bad_enc": ("Файл не читается ни в одной известной кодировке (UTF-8, UTF-16, cp1251, cp1252).",
                    "The file is not readable in any known encoding (UTF-8, UTF-16, cp1251, cp1252)."),
    "tip_sst": ("Перевод взят из словаря .sst", "Translation taken from the .sst dictionary"),
    "sst_add_files": ("Добавить файлы .sst…", "Add .sst files…"),
    "sst_add_folder": ("Добавить папку со словарями…", "Add dictionary folder…"),
    "sst_reload": ("Перезагрузить словари", "Reload dictionaries"),
    "sst_clear": ("Очистить словари", "Clear dictionaries"),
    "sst_status": ("Загружено: {total} строк из {files} файлов", "Loaded: {total} strings from {files} files"),
    "sst_cleared": ("Словари .sst очищены.", "The .sst dictionaries were cleared."),
    "sst_missing": ("Путь словаря не найден:", "Dictionary path not found:"),
    "sst_unknown_fmt": ("неизвестный формат .sst", "unknown .sst format"),
    "sst_loaded_many": ("Словари .sst: {files} файлов, {n} строк. Всего в словаре: {total}",
                        "SST dictionaries: {files} files, {n} strings. Dictionary total: {total}"),
    "sst_hints": ("Передавать имена из словаря LLM как глоссарий", "Pass dictionary names to the LLM as glossary hints"),
    "tip_sst_hints": ("Короткие имена (люди, места, предметы) из словаря .sst, найденные в строке, передаются LLM как термины.",
                      "Short names (people, places, items) from the .sst dictionaries that appear in a line are given to the LLM as terminology."),
    "sst_hints_on": ("Подсказки терминов из .sst: {n} имён", "SST terminology hints: {n} names"),
    "tip_len_warn": ("⚠️ Перевод слишком длинный, может не поместиться в интерфейсе",
                     "⚠️ The translation is too long — it may not fit in the interface"),
    "tip_len_note": ("Длина: {n} против {m} символов", "Length: {n} vs {m} characters"),
    "tip_mixed": ("В переводе остались английские слова",
                  "English words remain in the translation"),
    "tip_mixed_words": ("Английские слова: {words}", "English words left: {words}"),
    "sum_warnings": ("⚠️ Проверьте превью: {long} строк(и) длиннее оригинала на 40% и более (UI), "
                     "{mixed} перевод(ов) содержат английские слова.",
                     "⚠️ Check the preview: {long} string(s) exceed the original by ≥40% (UI), "
                     "{mixed} translation(s) still contain English words."),

    "msg_no_units": (
        "В выбранных модах не найдено переводимых строк (.strings, .json, .txt).\n\n"
        "Примечание: плагины (.esp/.esm/.esl) не переводятся напрямую.\n"
        "Убедитесь, что у мода есть строковые файлы, или включено извлечение BSA/BA2.",
        "No translatable lines found in the selected mods (.strings, .json, .txt).\n\n"
        "Note: plugins (.esp/.esm/.esl) are not translated directly.\n"
        "Ensure the mod has string files or BSA/BA2 extraction is enabled."),
    "msg_no_text": ("Нет переводимого текста.", "Nothing translatable."),
    "msg_no_folder": ("Не задана папка вывода.", "Output folder is not set."),
    "msg_placeholder_warn": (
        "Внимание! В {n} строках потеряны плейсхолдеры (%d, <tag>, ｟0｠).\n\n"
        "Если сохранить мод в таком виде, игра может вылететь.\n"
        "Вы уверены, что хотите продолжить?",
        "Warning! {n} line(s) lost placeholders (%d, <tag>, {{0}}).\n\n"
        "Saving the mod in this state may crash the game.\n"
        "Are you sure you want to continue?"),
    "msg_save_error": ("Ошибка сохранения:", "Save error:"),
    "msg_zip_overwrite": (
        "Файл уже существует:\n{path}\n\nПерезаписать?",
        "File already exists:\n{path}\n\nOverwrite?"),
    "msg_plugin_only": (
        "Это плагин Mod Organizer 2.\nПоместите файл в <MO2>/plugins/ "
        "и запускайте из тулбара MO2.",
        "This is a Mod Organizer 2 plugin.\nPut the file into <MO2>/plugins/ "
        "and run it from the MO2 toolbar."),
    "btn_replace": ("Заменить…", "Replace…"),
    "filter_all": ("Все строки", "All strings"),
    "filter_pending": ("Только Ожидающие", "Pending only"),
    "filter_errors": ("Только Ошибки (✗)", "Errors only (✗)"),
    "filter_warn": ("Только Технические (⚠️)", "Technical only (⚠️)"),
    "filter_missing": ("Только Пропущенные (🚫)", "Missing only (🚫)"),
    "dlg_replace_title": ("Найти и заменить", "Find & Replace"),
    "dlg_find": ("Найти:", "Find:"),
    "dlg_replace_to": ("Заменить на:", "Replace with:"),
    "dlg_scope_all": ("Везде (Оригинал и Перевод)", "Everywhere (Original & Translation)"),
    "dlg_scope_src": ("Только в Оригинале", "Original only"),
    "dlg_scope_dst": ("Только в Переводе", "Translation only"),
    "dlg_filtered_only": ("Только отфильтрованные строки", "Filtered rows only"),
    "per_mod_save": ("Автосохранение по модам", "Auto-save per mod"),
    "col_state": ("Статус", "State"),
    "st_done": ("Переведено", "Translated"),
    "st_stale": ("Устарело", "Outdated"),
    "st_ja": ("Есть перевод", "Has target lang"),
    "st_todo": ("Не переведено", "Untranslated"),
    "st_none": ("Нечего", "Nothing"),
    "select_todo": ("Выбрать непереведённые", "Select untranslated"),
    "show_states": ("Показать:", "Show:"),
    "notify_done": ("Уведомлять по завершении", "Notify when finished"),
    "in_place": ("Писать в папку исходного мода", "Write into the source mod folder"),
    "tip_in_place": ("Перевод сохраняется прямо в папку каждого мода.",
                     "Translations are written directly into each source mod folder."),
    "tip_per_mod": ("Переводить по одному моду и сохранять каждый в <папка>/<мод>_<язык>.",
                    "Translate one mod at a time and save each to <folder>/<mod>_<lang>."),
    "conn_test": ("Проверить соединение", "Test connection"),
    "allow_risky": ("Рискованные форматы (ini / прочие json / xml / правка .esp)",
                    "Risky formats (ini / other json / xml / direct .esp edit)"),
    "tip_risky": ("ВЫКЛ: только .strings, Interface/Translations, MCM config.json и DSD для .esp.",
                  "OFF: only .strings, Interface/Translations, MCM config.json and DSD for .esp.\n"
                  "ON: also ini / other json / xml and direct .esp editing (may break SPID/KID/FLM, "
                  "SKSE plugin settings, etc.)."),
    "translate_skse_menu": ("Файлы перевода меню SKSE (SKSE Menu Framework и др.)",
                            "SKSE menu translation files (SKSE Menu Framework etc.)"),
    "tip_skse_menu": ("Только проверенные форматы: SKSEMenuFrameworkStrings.json, BFCO NG Language.json, "
                      "MCM Memory Translation.json, dMenu translations.txt, Skyrim Party Sheet, "
                      "SKSE/Plugins/*/Translations/en|english.txt.",
                      "Only verified formats: SKSEMenuFrameworkStrings.json, BFCO NG Language.json, "
                      "MCM Memory Translation.json, dMenu translations.txt, Skyrim Party Sheet, "
                      "SKSE/Plugins/*/Translations/en|english.txt."),
    "translate_pex": ("Строки для показа в скриптах (.pex) — экспериментально",
                      "Display strings in scripts (.pex) — experimental"),
    "tip_pex": ("Переводит только строки, передаваемые в функции показа (MCM AddToggleOption и др., "
                "Debug.Notification / MessageBox). Перевод добавляется в таблицу строк, оригинал остаётся.",
                "Translates only string literals passed to display functions (MCM AddToggleOption etc., "
                "Debug.Notification / MessageBox). Translations are appended; original strings stay intact."),
}

# ── 日本語 UI ─────────────────────────────────────────────────────────────
T["all_files"] = ("Все файлы", "All files")

T_JA = {
    "backend": "バックエンド",
    "source": "翻訳元",
    "target": "翻訳先",
    "encoding": "文字コード",
    "lang_ui": "UI言語",
    "show_api": "API設定を表示",
    "tr_settings": "翻訳設定",
    "convert_units": "フィート→メートル換算",
    "delay": "待機 (ms)",
    "threads": "スレッド数",
    "batch": "1回の行数",
    "dry_run": "ドライラン",
    "extract_bsa": "BSA/BA2 を展開",
    "gen_report": "レポート作成",
    "api_settings": "バックエンド設定",
    "openai_url": "OpenAI互換 URL",
    "openai_model": "モデル",
    "openai_key": "OpenAI/Strata キー",
    "ollama_url": "Ollama URL",
    "lmstudio_url": "LM Studio URL",
    "openrouter_key": "OpenRouter キー",
    "deepl_key": "DeepL APIキー",
    "yandex_key": "Yandex APIキー",
    "temperature": "Temperature",
    "max_tokens": "最大トークン数",
    "sys_prompt": "システムプロンプト",
    "reset_default": "既定に戻す",
    "search_mods": "Mod を検索…",
    "select_all": "すべて選択",
    "select_none": "選択解除",
    "refresh": "Mod一覧を更新",
    "add_folders": "フォルダを追加…",
    "col_mod": "Mod",
    "col_plugins": "プラグイン",
    "col_strings": "Strings",
    "col_trans": "翻訳ファイル",
    "col_json": "JSON",
    "col_xml": "XML",
    "tab_log": "ログ",
    "tab_preview": "文字列プレビュー",
    "tab_glossary": "用語集",
    "col_src": "原文",
    "col_dst": "訳文",
    "col_file": "ファイル",
    "col_status": "状態",
    "gloss_add": "追加",
    "gloss_del": "削除",
    "gloss_hint": "用語集の語句は必須の訳語としてプロンプトに埋め込まれます。",
    "out_settings": "出力設定",
    "folder": "フォルダ",
    "browse": "参照…",
    "mod_name": "Mod名",
    "save_zip": ".zip で保存",
    "save_dsd": "DSD 形式で保存（.esp は変更しない）",
    "btn_translate": "翻訳",
    "btn_save": "出力を保存",
    "btn_cancel": "キャンセル",
    "btn_open_out": "出力フォルダを開く",
    "btn_close": "閉じる",
    "btn_open_file": "ファイルを開く…",
    "btn_load_sst": "SST 辞書",
    "tip_load_sst": (
        "xTranslator の辞書 (.sst、バイナリの SSU2/SSU8/SSU9) か、「原文 \\t 訳文」形式のテキスト。\n"
        "原文と完全に一致する文字列は、LLM を呼ばずに辞書の訳を使います。\n"
        "読み込んだファイル・フォルダは記憶され、次回から自動で読み込まれます。\n"
        "フォルダ（xTranslator の UserDictionaries など）は毎回中身を探し直します。"),
    "sst_loaded": ".sst 辞書から {n} 語を読み込みました ({path})。辞書の合計: {total}",
    "sst_no_pairs": "ファイル内に「原文 → 訳文」のペアが見つかりません。",
    "sst_error": ".sst 辞書を読み込めませんでした:",
    "sst_bad_enc": "既知のどの文字コード (UTF-8, UTF-16, cp1251, cp1252) でも読み込めません。",
    "tip_sst": ".sst 辞書から取得した訳文",
    "sst_add_files": ".sst ファイルを追加…",
    "sst_add_folder": "辞書フォルダを追加…",
    "sst_reload": "辞書を読み込み直す",
    "sst_clear": "辞書をすべて外す",
    "sst_status": "読み込み済み: {files} ファイル、{total} 件",
    "sst_cleared": ".sst 辞書をすべて外しました。",
    "sst_missing": "辞書のパスが見つかりません:",
    "sst_unknown_fmt": "未対応の .sst 形式です",
    "sst_loaded_many": ".sst 辞書: {files} ファイル、{n} 件を読み込みました。辞書の合計: {total}",
    "sst_hints": "辞書の固有名詞を LLM に用語として渡す",
    "tip_sst_hints": ("SST 辞書のうち短い名前（人名・地名・アイテム名など）が文中に出てきたら、"
                      "その訳語を用語集として LLM に渡します。文全体が辞書と一致しない行でも訳語が揃います。"),
    "sst_hints_on": "SST 辞書の用語ヒント: {n} 語",
    "tip_len_warn": "⚠️ 訳文が長すぎます。UI に収まらない可能性があります",
    "tip_len_note": "長さ: {n} 文字（原文 {m} 文字）",
    "tip_mixed": "訳文に英単語が残っています",
    "tip_mixed_words": "残った英単語: {words}",
    "sum_warnings": ("⚠️ プレビューを確認してください: 原文より40%以上長い文字列 {long} 件 (UI)、"
                     "英単語が残った訳文 {mixed} 件。"),
    "msg_no_units": (
        "選択した Mod に翻訳可能な文字列 (.strings, .json, .txt) が見つかりません。\n\n"
        "注意: プラグイン (.esp/.esm/.esl) は直接翻訳されません。\n"
        "Mod に strings ファイルがあるか、BSA/BA2 の展開が有効か確認してください。"),
    "msg_no_text": "翻訳可能なテキストがありません。",
    "msg_no_folder": "出力フォルダが設定されていません。",
    "msg_placeholder_warn": (
        "警告: {n} 行でプレースホルダー (%d, <tag>, {0}) が失われています。\n\n"
        "この状態で保存するとゲームがクラッシュする可能性があります。\n"
        "本当に続行しますか？"),
    "msg_save_error": "保存エラー:",
    "msg_zip_overwrite": "ファイルは既に存在します:\n{path}\n\n上書きしますか？",
    "msg_plugin_only": (
        "これは Mod Organizer 2 のプラグインです。\n<MO2>/plugins/ に置いて "
        "MO2 のツールバーから起動してください。"),
    "btn_replace": "置換…",
    "filter_all": "すべての行",
    "filter_pending": "未処理のみ",
    "filter_errors": "エラーのみ (✗)",
    "filter_warn": "技術的な行のみ (⚠️)",
    "filter_missing": "プレースホルダー欠落のみ (🚫)",
    "dlg_replace_title": "検索と置換",
    "dlg_find": "検索:",
    "dlg_replace_to": "置換後:",
    "dlg_scope_all": "すべて（原文と訳文）",
    "dlg_scope_src": "原文のみ",
    "dlg_scope_dst": "訳文のみ",
    "dlg_filtered_only": "絞り込み表示中の行のみ",
    "all_files": "すべてのファイル",
    "per_mod_save": "Mod ごとに自動保存",
    "col_state": "状態",
    "st_done": "翻訳済み",
    "st_stale": "要再翻訳",
    "st_ja": "日本語あり",
    "st_todo": "未翻訳",
    "st_none": "対象なし",
    "select_todo": "未翻訳と要再翻訳だけ選択",
    "show_states": "表示:",
    "notify_done": "完了したら音とダイアログで知らせる",
    "in_place": "元の Mod フォルダに直接書き込む",
    "tip_in_place": ("オン: 訳を元の Mod フォルダの中に直接書き込みます（MO2 の一覧は増えません）。Mod は1つずつ処理します。\n"
                     "・_japanese.txt / _japanese.strings / DSD 用 json は別名で追加。既に同名のファイルがあれば上書きしません。\n"
                     "・MCM の config.json は英語版を config.json.bak_en に退避してから上書きします。\n"
                     "・.esp は書き換えず DSD 形式のみ。出力フォルダ・Mod名・zip の設定は使いません。\n"
                     "・Mod を更新（再インストール）すると訳も消えるので、訳し直しが必要だと分かります。"),
    "tip_per_mod": ("オン: Mod を1つずつ翻訳し、終わるたびに <フォルダ>/<Mod名>_<言語> へ自動保存して次の Mod に進みます。\n"
                    "Mod 名欄は使いません。プレースホルダーが欠けた行は原文のまま保存します。\n"
                    "オフ: これまでどおり全部翻訳してから「出力を保存」でまとめて保存します。"),
    "conn_test": "接続テスト",
    "allow_risky": "危険な形式も対象にする（ini / MCM以外の json / xml / esp 直接書換）",
    "tip_risky": ("オフ（推奨）: .strings、Interface/Translations の txt、MCM の config.json だけを翻訳し、"
                  ".esp は DSD 形式で出力します。\n"
                  "オン: ini / その他の json / xml も対象にし、.esp を直接書き換えます。"
                  "SPID・KID・FLM の設定や SKSE プラグインの設定値まで翻訳されて壊れるおそれがあります。"),
    "translate_skse_menu": "SKSE メニュー（SKSE Menu Framework など）の訳ファイルも翻訳する",
    "tip_skse_menu": ("オンにすると、メニューの文字列を独自の訳ファイルに持つ SKSE プラグインのうち、形式を確認したものだけを翻訳します。\n"
                      "上書き型（ファイルが 1 つだけ）: SKSE Menu Framework 本体、BFCO NG、MCM Memory、dMenu、Skyrim Party Sheet。"
                      "値だけを訳し、キー・%d などの書式・アイコン文字・コメントはそのまま残します。"
                      "「元の Mod フォルダに直接書き込む」では英語版を .bak_en に退避してから上書きします。\n"
                      "言語ファイル型: SKSE/Plugins/<Mod>/Translations/en.txt・english.txt（Detailed MiniMap、Hotkey Atlas など）。"
                      "ja.txt / japanese.txt を作り、既にあれば足りないキーだけ追記します（元のファイルは .bak_ja に退避）。\n"
                      "DLL に直接書かれた文字列は対象外です。"),
    "translate_pex": "スクリプト（.pex）の表示用の文字列も翻訳する（実験的）",
    "tip_pex": ("オンにすると、Scripts フォルダの .pex のうち、表示用の関数に直接渡される英語だけを翻訳します。\n"
                "対象: MCM の AddToggleOption / AddTextOption / SetInfoText / ShowMessage など、Debug.Notification / MessageBox。\n"
                "訳文は文字列表の末尾に追加し、その呼び出し箇所だけを差し替えます。元の英語は残るので、"
                "同じ文字列を比較やキーに使っている処理には影響しません。\n"
                "ページ名・配列（メニューの選択肢）・変数を経由する文字列は訳しません。BSA 内の .pex も対象外です。\n"
                "「元の Mod フォルダに直接書き込む」では英語版を .pex.bak_en に退避してから上書きします。"),
}

ALL_FILES_LABELS = ("Все файлы", "All files", "すべてのファイル")

# 現在の UI 言語（ダイアログ起動時・切替時に更新。ログ等の固定文言用）
_UI_LANG = ["ja"]


def _tx(ru, ja):
    """ハードコード文言用: UI言語が ja なら日本語、それ以外は元のロシア語。"""
    return ja if _UI_LANG[0] == "ja" else ru


DEFAULT_SYSTEM_PROMPT = """You are a professional translator for video game UI, menus, and dialogue mods.
Translate the provided text from {SRC} to {TGT}.

RULES:
1. Return ONLY the translated text. No explanations, no quotes, no "Here is…".
2. PRESERVE EXACTLY: %d %s %f, \\n \\t, <tags>, ｟0｠ ｟1｠ tokens, file paths, punctuation. NEVER delete or modify these tokens.
3. Do NOT translate: brand names, mod names, plugin names, Form IDs.
4. Keep UI labels short (1-2 words).
5. If the text is already in the target language, return it unchanged.
6. Use the GLOSSARY block (if present) as mandatory terminology."""

LANG_MAP = {"ru": "RUSSIAN", "en": "ENGLISH", "de": "GERMAN", "fr": "FRENCH",
            "es": "SPANISH", "it": "ITALIAN", "pl": "POLISH", "ja": "JAPANESE",
            "zh": "CHINESE", 
            "zh-CN": "SIMPLIFIED CHINESE", 
            "zh-TW": "TRADITIONAL CHINESE",
            "cs": "CZECH"}

LANG_SUFFIX = {"ru": "russian", "en": "english", "de": "german", "fr": "french",
               "es": "spanish", "it": "italian", "pl": "polish",
               "ja": "japanese", "zh": "chinese", 
               "zh-CN": "chineses", 
               "zh-TW": "chineset",
               "cs": "czech"}

LANGS = [("en", "English"), ("ru", "Русский"), ("de", "Deutsch"), ("fr", "Français"),
         ("es", "Español"), ("it", "Italiano"), ("pl", "Polski"), ("ja", "日本語"),
         ("zh-CN", "中文 (简体)"), ("zh-TW", "中文 (繁體)"), 
         ("cs", "Čeština")]
ENCODINGS = ["utf-8", "windows-1251", "cp1252", "utf-16"]
BACKENDS = ["LM Studio", "Ollama", "OpenAI", "OpenRouter", "DeepL", "Yandex", "Google Translate"]

C = {
    "bg": "#14171d", "panel": "#1b2027", "panel2": "#232a35",
    "border": "#2d3644", "field": "#10141a", "text": "#dbe1ea",
    "dim": "#8b95a5", "accent": "#e8a33d", "accent_soft": "#f2c069",
    "teal": "#4fb6a8", "ok": "#79c267", "err": "#e0605f",
    "warn_len": "#e8a33d", "mixed": "#5aa7e0",
    "selected": "#31405a", "sel_text": "#ffffff",
}

STYLESHEET = """
QDialog { background: %(bg)s; }
QWidget { color: %(text)s; font-size: 12px; }
QLabel { background: transparent; }
QLabel#title { color: %(accent)s; font-size: 18px; font-weight: 700; }
QLabel#ver { color: %(dim)s; font-size: 10px; }
QLabel#group { color: %(teal)s; font-weight: 700; font-size: 11px; }
QLabel#hint { color: %(dim)s; font-size: 10px; }
QLabel#statusmsg { color: %(dim)s; font-size: 11px; }
QFrame#panel { background: %(panel)s; border: 1px solid %(border)s; border-radius: 6px; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit {
    background: %(field)s; border: 1px solid %(border)s; border-radius: 4px;
    padding: 4px 7px; selection-background-color: %(accent)s; selection-color: #191307;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QPlainTextEdit:focus { border-color: %(accent)s; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox::down-arrow { image: none; border-left: 4px solid transparent;
    border-right: 4px solid transparent; border-top: 5px solid %(dim)s; margin-right: 6px; }
QComboBox QAbstractItemView { background: %(panel)s; border: 1px solid %(border)s;
    selection-background-color: %(selected)s; selection-color: %(sel_text)s; outline: 0; }
QPushButton {
    background: %(panel2)s; border: 1px solid %(border)s; border-radius: 5px;
    padding: 6px 14px; font-weight: 600; color: %(text)s;
}
QPushButton:hover { background: %(border)s; }
QPushButton:pressed { background: %(selected)s; }
QPushButton:disabled { color: #566073; background: %(panel)s; }
QPushButton#primary { background: %(accent)s; color: #191307; border-color: %(accent)s; }
QPushButton#primary:hover { background: %(accent_soft)s; }
QPushButton#primary:disabled { background: %(panel)s; color: #566073; border-color: %(border)s; }
QPushButton#danger:hover { border-color: %(err)s; color: %(err)s; }
QPushButton#ghost { background: transparent; border: none; color: %(teal)s;
    font-weight: 700; text-align: left; padding: 1px 0; }
QPushButton#ghost:hover { color: %(accent)s; }
QCheckBox { spacing: 5px; }
QCheckBox::indicator { width: 13px; height: 13px; border: 1px solid %(border)s;
    border-radius: 3px; background: %(field)s; }
QCheckBox::indicator:checked { background: %(accent)s; border-color: %(accent)s; }
QTableWidget {
    background: %(panel)s; alternate-background-color: #1e242d;
    border: 1px solid %(border)s; gridline-color: #242c38; outline: 0;
}
QTableWidget::item { padding: 2px 5px; }
QTableWidget::item:selected { background: %(selected)s; color: %(sel_text)s; }
QHeaderView::section {
    background: %(panel2)s; color: %(dim)s; border: none;
    border-right: 1px solid %(border)s; border-bottom: 1px solid %(border)s;
    padding: 5px 7px; font-weight: 700; font-size: 10px;
}
QTabWidget::pane { border: 1px solid %(border)s; border-radius: 4px; background: %(panel)s; }
QTabBar::tab { background: %(panel2)s; color: %(dim)s; padding: 6px 16px;
    border: 1px solid %(border)s; border-bottom: none; border-top-left-radius: 5px;
    border-top-right-radius: 5px; margin-right: 2px; font-weight: 600; }
QTabBar::tab:selected { background: %(panel)s; color: %(accent)s; }
QTabBar::tab:hover:!selected { color: %(text)s; }
QProgressBar {
    background: %(field)s; border: 1px solid %(border)s; border-radius: 4px;
    text-align: center; color: %(text)s; font-size: 10px; height: 15px;
}
QProgressBar::chunk { background: %(accent)s; border-radius: 3px; }
QPlainTextEdit#log, QPlainTextEdit#prompt {
    font-family: Consolas, "DejaVu Sans Mono", monospace; font-size: 11px;
}
QScrollBar:vertical { background: %(bg)s; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: %(border)s; border-radius: 5px; min-height: 22px; }
QScrollBar::handle:vertical:hover { background: %(dim)s; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: %(bg)s; height: 10px; margin: 0; }
QScrollBar::handle:horizontal { background: %(border)s; border-radius: 5px; min-width: 22px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QMenu { background: %(panel)s; border: 1px solid %(border)s; padding: 4px 0; }
QMenu::item { padding: 5px 24px 5px 16px; }
QMenu::item:selected { background: %(selected)s; }
QToolTip { background: %(panel2)s; color: %(text)s; border: 1px solid %(border)s; padding: 4px; }
""" % C


# ============================================================================
# Защита плейсхолдеров
# ============================================================================
TOKEN_RE = re.compile(
    r"%(?:\d+\$)?[-+#0]*\d*(?:\.\d+)?[hlL]?[diouxXeEfgGaAcspn%]"
    r"|\{\{[^{}\n]*\}\}"
    r"|\{[^{}\n]{0,48}\}"
    r"|\\[nrtfb\\\"']"
    r"|</?[A-Za-z][^<>\n]{0,64}/?>"
)


def _sentinel(i):
    return f"｟{i}｠"


CORRUPT_RE = re.compile(
    r"｟\s*(\d+)\s*｠"
    r"|__\s*(?:TAG|PLACEHOLDER|PH|TOKEN|VAR)\s*(\d+)\s*__"
    r"|<<\s*P?\s*(\d+)\s*>>"
    r"|\[\[\s*P?\s*(\d+)\s*\]\]"
    r"|⟦\s*P?\s*(\d+)\s*⟧"
    r"|⟨\s*(\d+)\s*⟩"
    r"|【\s*(\d+)\s*】",
    re.IGNORECASE,
)
RESIDUAL_RE = re.compile(
    r"__\s*(?:TAG|PLACEHOLDER|PH|TOKEN|VAR)\s*\d*\s*__"
    r"|｟[^\n｠]{0,8}｠"
    r"|<<\s*P?\s*\d*\s*>>"
    r"|\[\[\s*P?\s*\d*\s*\]\]"
    r"|⟦\s*P?\s*\d*\s*⟧"
    r"|⟨\s*\d*\s*⟩",
    re.IGNORECASE,
)

QUOTE_PAIRS = {('"', '"'), ("'", "'"), ("«", "»"), ("“", "”"), ("„", "“"),
               ("‘", "’"), ("『", "』"), ("「", "」")}


class PlaceholderProtector:
    def protect(self, text):
        tokens, index = [], {}

        def repl(m):
            t = m.group(0)
            if t not in index:
                index[t] = len(tokens)
                tokens.append(t)
            return _sentinel(index[t])

        # 1. Защита одиночных символов внутри тегов (хоткеи)
        def protect_hotkey(m):
            char = m.group(3)
            if char not in index:
                index[char] = len(tokens)
                tokens.append(char)
            return m.group(1) + m.group(2) + _sentinel(index[char]) + m.group(4) + m.group(5)

        text = re.sub(r"(>)(\s*)([A-Za-z0-9])(\s*)(<)", protect_hotkey, text)

        # 2. Защита стандартных плейсхолдеров (%d, {0}), НО БЕЗ ТЕГОВ!
        PH_ONLY_RE = re.compile(
            r"%(?:\d+\$)?[-+#0]*\d*(?:\.\d+)?[hlL]?[diouxXeEfgGaAcspn%]"
            r"|\{\{[^{}\n]*\}\}"
            r"|\{[^{}\n]{0,48}\}"
            r"|\\[nrtfb\\\"']"
        )
        return PH_ONLY_RE.sub(repl, text), tokens

    def restore(self, text, tokens, repair=True):
        def repl(m):
            num = next((g for g in m.groups() if g is not None), None)
            if num is None:
                return ""
            i = int(num)
            if 0 <= i < len(tokens):
                return tokens[i]
            return ""
        out = CORRUPT_RE.sub(repl, text)
        out = RESIDUAL_RE.sub("", out)
        # Аргумент `repair` оставлен для совместимости, но токены сюда НЕ
        # дописываются в конец строки: тихая «починка» ломает грамматику.
        return out.strip()


# ============================================================================
# Сетевые клиенты
# ============================================================================
class LLMError(Exception):
    pass


def _http_json(url, body, headers, timeout):
    req = urlrequest.Request(url, data=body, headers=headers, method="POST")
    with urlrequest.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _sleep_retry(attempt, cancel):
    delay = min(30.0, 1.6 * (2 ** attempt))
    end = time.time() + delay
    while time.time() < end:
        if cancel.is_set():
            raise LLMError("Отменено")
        time.sleep(0.2)


def normalize_openai_url(text, default):
    """LM Studio 等の URL を補う: "192.168.1.10:1234" → "http://192.168.1.10:1234/v1"。"""
    url = (text or "").strip().rstrip("/")
    if not url:
        return default
    if not re.match(r"^https?://", url, re.I):
        url = "http://" + url
    if not re.search(r"/v\d+$", url):
        url += "/v1"
    return url


def openai_list_models(base, key="", timeout=5):
    """OpenAI 互換サーバーの /models を取得 → モデル ID のリスト。失敗時は LLMError。"""
    base = (base or "").rstrip("/")
    if not base:
        raise LLMError(_tx("Не задан URL", "URL が設定されていません"))
    headers = {"User-Agent": f"{APP_NAME}/{APP_VERSION}"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    try:
        req = urlrequest.Request(base + "/models", headers=headers)
        with urlrequest.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
    except urlerror.HTTPError as e:
        raise LLMError(f"HTTP {e.code} {e.reason} ({base}/models)")
    except (urlerror.URLError, TimeoutError, OSError) as e:
        reason = getattr(e, "reason", None) or e
        raise LLMError(_tx(f"Нет соединения с {base}: {reason}",
                           f"{base} に接続できません: {reason}"))
    except ValueError:
        raise LLMError(_tx(f"Ответ не JSON: {base}/models",
                           f"{base}/models の応答が JSON ではありません（URL が違う可能性）"))
    items = data.get("data") if isinstance(data, dict) else None
    if items is None and isinstance(data, dict):
        items = data.get("models")          # Ollama ネイティブ形式
    return [str(m.get("id") or m.get("name") or "") for m in (items or []) if isinstance(m, dict)]


def _conn_hint(err):
    """接続失敗時のよくある原因。"""
    e = str(err).lower()
    if "10061" in e or "refused" in e or "拒否" in e:
        return _tx("Сервер не запущен или порт неверный.",
                   "サーバーが起動していないか、ポート番号が違います。LM Studio の開発者画面で「Start Server」を確認してください。")
    if "timed out" in e or "timeout" in e or "10060" in e or "タイムアウト" in e:
        return _tx("Нет ответа: проверьте IP, брандмауэр и «Serve on Local Network».",
                   "応答がありません。IP アドレス、相手 PC のファイアウォール（ポート 1234 の受信許可）、"
                   "LM Studio の「Serve on Local Network」がオンか確認してください。")
    if "getaddrinfo" in e or "11001" in e or "name" in e and "resolve" in e:
        return _tx("Имя хоста не найдено.", "ホスト名が見つかりません。IP アドレスで指定してみてください。")
    if "http 404" in e or "json" in e:
        return _tx("Проверьте, что URL оканчивается на /v1.", "URL の末尾が /v1 になっているか確認してください。")
    if "http 401" in e or "http 403" in e:
        return _tx("Неверный API-ключ.", "API キーが正しくありません。")
    return ""


class OpenAIClient:
    """OpenAI-совместимый /chat/completions (OpenAI, OpenRouter, LM Studio, Ollama)."""

    def __init__(self, base, key, model, temperature=0.2, max_tokens=512,
                 timeout=90, retries=3, extra_body=None):
        self.base = (base or "").rstrip("/")
        self.key = key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.retries = retries
        self.extra_body = extra_body or {}

    @staticmethod
    def _extract(data):
        try:
            choice = data["choices"][0]
        except (KeyError, IndexError, TypeError):
            raise LLMError(_tx(f"Некорректный ответ сервера: {str(data)[:150]}", f"サーバーの応答が不正です: {str(data)[:150]}"))
        msg = choice.get("message") or {}
        content = msg.get("content")
        if content is None:
            content = msg.get("text") or ""
        finish = choice.get("finish_reason")
        had_thinking = bool(msg.get("reasoning_content") or msg.get("thinking"))
        return (content or "").strip(), finish, had_thinking

    def chat(self, system, user, cancel):
        if not self.base:
            raise LLMError(_tx("Не задан URL бэкенда", "バックエンドの URL が設定されていません"))
        budget = max(int(self.max_tokens), min(8192, int(len(user) * 1.4) + 512))
        body_dict = {
            "model": self.model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "temperature": self.temperature,
            "max_tokens": budget,
        }
        body_dict.update(self.extra_body)
        body = json.dumps(body_dict, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json",
                   "User-Agent": f"{APP_NAME}/{APP_VERSION}"}
        if self.key:
            headers["Authorization"] = f"Bearer {self.key}"
        last = LLMError(_tx("Неизвестная ошибка", "不明なエラー"))
        for attempt in range(self.retries + 1):
            if cancel.is_set():
                raise LLMError("Отменено")
            try:
                data = _http_json(self.base + "/chat/completions", body,
                                  headers, self.timeout)
                content, finish, had_thinking = self._extract(data)
                if content:
                    return content
                if had_thinking:
                    last = LLMError(
                        _tx("Модель потратила ответ на рассуждения и не выдала текст — "
                        "увеличьте «Макс. токенов» или отключите thinking в настройках модели", "モデルが推論 (thinking) で出力を使い切り、テキストを返しませんでした — 「最大トークン数」を増やすか、モデル設定で thinking を無効にしてください"))
                else:
                    last = LLMError(_tx(f"Пустой ответ модели (finish_reason={finish})", f"モデルの応答が空です (finish_reason={finish})"))
                if attempt >= self.retries:
                    raise last
            except LLMError:
                raise
            except urlerror.HTTPError as e:
                detail = ""
                try:
                    detail = e.read().decode("utf-8", "replace")[:200]
                except Exception:
                    pass
                last = LLMError(f"HTTP {e.code} {detail or e.reason}")
                if e.code not in (408, 429, 500, 502, 503, 504) or attempt >= self.retries:
                    raise last
                _sleep_retry(attempt, cancel)
                continue
            except (urlerror.URLError, TimeoutError, OSError) as e:
                last = LLMError(_tx(f"Сеть: {getattr(e, 'reason', None) or e}", f"ネットワーク: {getattr(e, 'reason', None) or e}"))
                if attempt >= self.retries:
                    raise last
                _sleep_retry(attempt, cancel)
                continue
            except (KeyError, IndexError, ValueError) as e:
                raise LLMError(_tx(f"Некорректный ответ: {e}", f"不正な応答: {e}"))
            _sleep_retry(attempt, cancel)
        raise last


class DeepLClient:
    def __init__(self, key, target="ru", timeout=60):
        self.key = key
        self.target = target.upper()
        # Маппинг для DeepL
        if self.target == "ZH-CN" or self.target == "ZH":
            self.target = "ZH-HANS"
        elif self.target == "ZH-TW":
            self.target = "ZH-HANT"
        self.timeout = timeout

    def translate_lines(self, lines, cancel):
        out = []
        for i in range(0, len(lines), self.BATCH_SIZE):
            chunk = lines[i:i + self.BATCH_SIZE]
            out.extend(self._batch(chunk, cancel))
        return out

    def _batch(self, lines, cancel):
        url = "https://api-free.deepl.com/v2/translate"
        if not self.key.startswith(("f", "[f")) and "-fx" not in self.key:
            url = "https://api.deepl.com/v2/translate"
        params = [("auth_key", self.key), ("target_lang", self.target)]
        for ln in lines:
            params.append(("text", ln))
        body = urlencode(params).encode("utf-8")
        last = LLMError(_tx("DeepL: неизвестная ошибка", "DeepL: 不明なエラー"))
        for attempt in range(self.retries + 1):
            if cancel.is_set():
                raise LLMError("Отменено")
            try:
                data = _http_json(
                    url, body,
                    {"Content-Type": "application/x-www-form-urlencoded"},
                    self.timeout)
                return [t["text"] for t in data["translations"]]
            except urlerror.HTTPError as e:
                last = LLMError(f"DeepL HTTP {e.code}")
                if e.code not in (429, 500, 502, 503, 504) or attempt >= self.retries:
                    raise last
            except (urlerror.URLError, OSError) as e:
                last = LLMError(_tx(f"DeepL сеть: {getattr(e, 'reason', e)}", f"DeepL ネットワーク: {getattr(e, 'reason', e)}"))
                if attempt >= self.retries:
                    raise last
            _sleep_retry(attempt, cancel)
        raise last


class YandexClient:
    BATCH_SIZE = 25

    def __init__(self, key, src="en", tgt="ru", timeout=60, retries=3):
        self.key = key
        self.pair = f"{src}-{tgt}"
        self.timeout = timeout
        self.retries = retries

    def translate_lines(self, lines, cancel):
        out = []
        for i in range(0, len(lines), self.BATCH_SIZE):
            chunk = lines[i:i + self.BATCH_SIZE]
            out.extend(self._batch(chunk, cancel))
        return out

    def _batch(self, lines, cancel):
        params = [("key", self.key), ("lang", self.pair), ("format", "text")]
        for ln in lines:
            params.append(("text", ln))
        url = "https://translate.yandex.net/api/v1.5/tr.json/translate?" + urlencode(params)
        last = LLMError(_tx("Yandex: неизвестная ошибка", "Yandex: 不明なエラー"))
        for attempt in range(self.retries + 1):
            if cancel.is_set():
                raise LLMError("Отменено")
            try:
                req = urlrequest.Request(url)
                with urlrequest.urlopen(req, timeout=self.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                if data.get("code") != 200:
                    raise LLMError(_tx(f"Yandex: {data.get('message', 'ошибка')}", f"Yandex: {data.get('message', 'エラー')}"))
                return data["text"]
            except LLMError:
                raise
            except urlerror.HTTPError as e:
                last = LLMError(f"Yandex HTTP {e.code}")
                if e.code not in (429, 500, 502, 503, 504) or attempt >= self.retries:
                    raise last
            except (urlerror.URLError, OSError) as e:
                last = LLMError(_tx(f"Yandex сеть: {getattr(e, 'reason', e)}", f"Yandex ネットワーク: {getattr(e, 'reason', e)}"))
                if attempt >= self.retries:
                    raise last
            _sleep_retry(attempt, cancel)
        raise last


class GoogleFreeClient:
    def __init__(self, src="en", tgt="ru", timeout=30):
        self.src = src
        self.tgt = tgt
        self.timeout = timeout
        # Расширенные заголовки, чтобы имитировать реальный браузер Chrome
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://translate.google.com/"
        }

    def translate_lines(self, lines, cancel):
        results = []
        for ln in lines:
            if cancel.is_set():
                raise LLMError("Отменено")
            if not ln.strip():
                results.append(ln)
                continue

            params = {
                "client": "gtx",
                "sl": self.src,
                "tl": self.tgt,
                "dt": "t",
                "q": ln
            }
            # Используем домен translate.google.com (он реже блокирует, чем googleapis)
            url = "https://translate.google.com/translate_a/single?" + urlencode(params)
            
            max_retries = 3
            success = False
            
            for attempt in range(max_retries):
                if cancel.is_set():
                    raise LLMError("Отменено")
                try:
                    req = urlrequest.Request(url, headers=self.headers)
                    with urlrequest.urlopen(req, timeout=self.timeout) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                        translated = "".join(seg[0] for seg in data[0] if seg and seg[0])
                        results.append(translated if translated else ln)
                    success = True
                    break # Успех! Выходим из цикла попыток
                except urlerror.HTTPError as e:
                    if e.code == 429:
                        if attempt == max_retries - 1:
                            raise LLMError(_tx("Google Error 429: Превышен лимит запросов. Убедитесь, что Потоки = 1, и увеличьте Задержку до 3000 мс.", "Google Error 429: リクエスト上限を超えました。スレッド数を 1 にし、待機を 3000 ms まで増やしてください。"))
                        # Если 429, ждем 5 секунд и пробуем снова
                        time.sleep(5) 
                    else:
                        raise LLMError(f"Google HTTP error: {e.code}")
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise LLMError(f"Google translate error: {e}")
                    time.sleep(3)
            
            if not success:
                results.append(ln)
                
        return results


# ============================================================================
# Переводчик
# ============================================================================
class Translator:
    MAX_RECURSION = 4

    def __init__(self, client, protector, system_prompt, src, tgt,
                 glossary=None, repair=True, dry_run=False, unit_convert=False,
                 log=None, sst_terms=None):
        self.client = client
        self.protector = protector
        self.system_prompt = system_prompt
        self.src = src
        self.tgt = tgt
        self.glossary = glossary or {}
        self.sst_terms = sst_terms or {}   # SST 辞書の短い名前（原文 → 訳）。用語ヒント用
        self.repair = repair
        self.dry_run = dry_run
        self.unit_convert = unit_convert
        self.log = log or (lambda *_a: None)

    def _glossary_hits(self, lines):
        hits = []
        blob = "\n".join(lines).lower()
        for term, trans in self.glossary.items():
            t = term.strip()
            if not t:
                continue
            needle = t.lower()
            if re.fullmatch(r"[a-zа-яё0-9'\- ]+", needle):
                if re.search(rf"(?<![A-Za-zА-Яа-яё]){re.escape(needle)}(?![A-Za-zА-Яа-яё])", blob):
                    hits.append((term, trans))
            elif needle in blob:
                hits.append((term, trans))
        if self.sst_terms:
            own = {h[0].strip().lower() for h in hits}
            hits += [h for h in sst_term_hits(lines, self.sst_terms) if h[0].lower() not in own]
        return hits

    def _system(self, n, numbered, hits):
        src_name = LANG_MAP.get(self.src, self.src.upper())
        tgt_name = LANG_MAP.get(self.tgt, self.tgt.upper())
        sysp = (self.system_prompt
                .replace("{SRC}", src_name)
                .replace("{TGT}", tgt_name))
        extra = [
            f"INPUT HAS EXACTLY {n} LINES — return EXACTLY {n} lines, same order.",
            "Do not merge, split or add lines. No numbering, no quotes around lines.",
            "Tokens ｟0｠ ｟1｠ … are atomic placeholders — copy them verbatim.",
            "Output the translation DIRECTLY — no reasoning, no thinking, no comments.",
        ]
        if numbered:
            extra.append('Input lines are prefixed "N| ". Keep the "N| " prefix in output.')
        if hits:
            extra.append("GLOSSARY (mandatory terminology):")
            extra += [f'"{a}" → "{b}"' for a, b in hits[:40]]
        return sysp + "\n\n" + "\n".join(extra)

    def _call(self, payload, n, numbered, hits, cancel):
        if self.dry_run:
            return payload
        if isinstance(self.client, (DeepLClient, YandexClient, GoogleFreeClient)):
            return "\n".join(self.client.translate_lines(payload.split("\n"), cancel))
        return self.client.chat(self._system(n, numbered, hits), payload, cancel)

    @staticmethod
    def _strip_fences(text):
        t = text.strip().lstrip("\ufeff")
        t = re.sub(r"^```[a-zA-Z]*\s*\n?", "", t)
        return re.sub(r"\n?```\s*$", "", t)

    def _split(self, text, n, numbered):
        t = self._strip_fences(text)
        if numbered:
            lines = []
            for raw in t.split("\n"):
                m = re.match(r"^\s*(\d+)\s*[|).:]\s?(.*)$", raw)
                if m:
                    lines.append(m.group(2))
        else:
            lines = t.split("\n")
            while lines and not lines[0].strip():
                lines.pop(0)
            while lines and not lines[-1].strip():
                lines.pop()

        if len(lines) == n:
            return lines

        if len(lines) > n:
            # Попытка убрать «вот перевод:»-преамбулу
            while len(lines) > n:
                first = lines[0].strip().lower()
                looks_like_preamble = (
                    first.endswith(":")
                    or any(first.startswith(p) for p in (
                        "here", "sure", "translation", "translated",
                        "the translation", "конечно", "перевод", "вот", "ниже"))
                )
                if looks_like_preamble:
                    lines.pop(0)
                    continue
                break
            if len(lines) > n:
                self.log("warn",
                         _tx(f"Модель вернула {len(lines)} строк вместо {n}, обрезаем до {n}", f"モデルが {n} 行ではなく {len(lines)} 行を返しました。{n} 行に切り詰めます"))
                lines = lines[:n]

        return lines if len(lines) == n else None

    def _post(self, raw, src, tokens):
        s = raw.strip()
        if src.lstrip()[:1] not in ("-", "•", "*", "·"):
            s = re.sub(r"^\s*[-•*·]\s+", "", s)
        if not re.match(r"^\s*\d+\s*[|).:]", src):
            s = re.sub(r"^\s*\d+\s*[|).:]\s+", "", s)
        if len(s) >= 2 and src.lstrip()[:1] != s[0]:
            if (s[0], s[-1]) in QUOTE_PAIRS:
                s = s[1:-1].strip()
        
        s = self.protector.restore(s, tokens, repair=self.repair)
        s = RESIDUAL_RE.sub("", s).strip()
        
        if self.unit_convert:
            s = _convert_units(s)
            
        # --- ДОБАВИТЬ ЭТОТ БЛОК ---
        # Автокоррекция регистра первой буквы
        if s and src.strip():
            src_first = src.strip()[0]
            s_first = s[0]
            if src_first.isupper() and s_first.islower():
                s = s[0].upper() + s[1:]
            elif src_first.islower() and s_first.isupper():
                s = s[0].lower() + s[1:]
        # --------------------------
        
        return s

    # Уточняющие контекстные инструкции; порядок = приоритет (первое совпадение).
    _CTX_RULES = [
        (("mcm", ".json", ".xml", ".pex"),
         "Context: This is a UI menu. Keep the translation as short and concise "
         "as possible. Use standard gaming UI terms."),
        (("info", "qust", "quest"),
         "Context: This is a game dialogue or quest log. Use natural, conversational "
         "language. Keep it in-character."),
        (("book", "desc"),
         "Context: This is a book or item description. Use literary, immersive language."),
    ]

    @classmethod
    def _context_instructions(cls, context):
        """Инструкция по типу файла. Точное правило (диалог/квест, MCM/меню,
        книга/описание) перекрывает базовую подсказку по расширению."""
        cl = (context or "").lower()
        if not cl:
            return []
        for keys, instr in cls._CTX_RULES:
            if any(k in cl for k in keys):
                return [instr]
        if cl.endswith((".esp", ".esm", ".esl")):
            return ["Context: This text is from a game plugin (NPC names, items, or dialogue)."]
        if cl.endswith(".txt"):
            return ["Context: This text is from a book or interface file."]
        return []

    def translate_lines(self, lines, cancel, _depth=0):
        protected, maps = [], []
        for ln in lines:
            p, toks = self.protector.protect(ln)
            protected.append(p)
            maps.append(toks)
        hits = self._glossary_hits(lines)

        text = self._call("\n".join(protected), len(lines), False, hits, cancel)
        out = self._split(text, len(lines), False)
        if out is None:
            payload = "\n".join(f"{i + 1}| {p}" for i, p in enumerate(protected))
            text = self._call(payload, len(lines), True, hits, cancel)
            out = self._split(text, len(lines), True)
        if out is None:
            if len(lines) == 1:
                raise LLMError(_tx("Модель не вернула ровно одну строку", "モデルが1行ちょうどを返しませんでした"))
            if _depth >= self.MAX_RECURSION:
                raise LLMError(_tx("Не удалось разбить батч на строки", "バッチを行に分割できませんでした"))
            mid = len(lines) // 2
            return (self.translate_lines(lines[:mid], cancel, _depth + 1)
                    + self.translate_lines(lines[mid:], cancel, _depth + 1))
        return [self._post(raw, src, toks)
                for raw, src, toks in zip(out, lines, maps)]

    def translate_single(self, src, cancel, context=""):
        """Переводит одну строку с защитой от потери плейсхолдеров (Auto-Retry)."""
        if not src.strip():
            return src

        protected, tokens = self.protector.protect(src)
        hits = self._glossary_hits([src])

        src_name = LANG_MAP.get(self.src, self.src.upper())
        tgt_name = LANG_MAP.get(self.tgt, self.tgt.upper())
        sysp = (self.system_prompt.replace("{SRC}", src_name).replace("{TGT}", tgt_name))

        extra = [
            "Translate the following text.",
            "Tokens ｟0｠ ｟1｠ … are atomic placeholders — copy them verbatim.",
            "Output the translation DIRECTLY — no reasoning, no thinking, no comments.",
            "CRITICAL: Match the capitalization of the source text exactly."
        ]
        extra += self._context_instructions(context)
        if hits:
            extra.append("GLOSSARY (mandatory terminology):")
            extra += [f'"{a}" → "{b}"' for a, b in hits[:40]]

        system = sysp + "\n\n" + "\n".join(extra)
        
        # Делаем до 2 попыток (первая обычная, вторая с предупреждением)
        for attempt in range(2):
            if attempt == 1:
                # Если токены потеряны, добавляем строгое предупреждение в промпт
                system += "\n\nCRITICAL ERROR: In your previous response, you LOST some placeholders (like %d, {0}, <tag>). You MUST include them exactly as provided in the original text. Do not omit them."
                self.log("warn", _tx(f"Потеряны плейсхолдеры, повторный запрос... [{src[:30]}]", f"プレースホルダーが失われたため再リクエストします… [{src[:30]}]"))

            if self.dry_run:
                out = protected
            elif isinstance(self.client, (DeepLClient, YandexClient, GoogleFreeClient)):
                out = self.client.translate_lines([protected], cancel)[0]
            else:
                out = self.client.chat(system, protected, cancel)

            res = self._post(out, src, tokens)
            
            # Проверяем, все ли плейсхолдеры на месте
            ok, lost = check_placeholders(src, res)
            if ok:
                return res  # Всё отлично, возвращаем перевод
                
            if attempt == 1:
                # Если и вторая попытка провалилась, возвращаем оригинал, чтобы игра не вылетела
                self.log("err", _tx(f"Нейросеть потеряла плейсхолдеры: {lost}. Оставлен оригинал.", f"AI がプレースホルダーを失いました: {lost}。原文のままにします。"))
                return src 
                
        return src
        
    def fix_placeholders_batch(self, bad_items, cancel):
        """Принимает список (src, dst) с потерянными токенами и просит LLM исправить их."""
        if not bad_items:
            return []

        sysp = "You are an expert in video game localization. You will receive a list of translations that are MISSING some placeholders (like %d, <tag>, {0})."
        user_prompt = "Fix the following translations. Restore the missing placeholders from the Original into the Broken Translation. Return ONLY the fixed translations, one per line, matching the exact order. Do NOT include numbering or original text in your response.\n\n"
        
        for i, (src, dst) in enumerate(bad_items):
            user_prompt += f"[{i+1}] ORIGINAL: {src}\nBROKEN: {dst}\n"

        user_prompt += "\nFIXED TRANSLATIONS:\n"

        try:
            if self.dry_run:
                return [dst for src, dst in bad_items]
            
            if isinstance(self.client, (DeepLClient, YandexClient, GoogleFreeClient)):
                return [dst for src, dst in bad_items]
            
            raw_res = self.client.chat(sysp, user_prompt, cancel)
            
            lines = [ln.strip() for ln in raw_res.strip().split("\n") if ln.strip()]
            
            cleaned_lines = []
            for ln in lines:
                ln = re.sub(r"^\d+[\.\)]\s*", "", ln)
                cleaned_lines.append(ln)
                
            if len(cleaned_lines) == len(bad_items):
                return cleaned_lines
            else:
                self.log("warn", _tx(f"LLM вернула {len(cleaned_lines)} строк вместо {len(bad_items)} при исправлении токенов.", f"トークン修正中、LLM が {len(bad_items)} 行ではなく {len(cleaned_lines)} 行を返しました。"))
                return [dst for src, dst in bad_items]
                
        except Exception as e:
            self.log("err", _tx(f"Ошибка при исправлении плейсхолдеров: {e}", f"プレースホルダー修正中のエラー: {e}"))
            return [dst for src, dst in bad_items]


_UNIT_RULES = [
    (re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:футов|фута|футы|фут|фт)\b", re.I), 0.3048, "м"),
    (re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:feet|ft)\b", re.I), 0.3048, " м"),
    (re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:миль|мили|миля|милю)\b", re.I), 1.609, "км"),
    (re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:miles|mi)\b", re.I), 1.609, " км"),
    (re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:дюймов|дюйма|дюймы|дюйм)\b", re.I), 2.54, "см"),
]


def _convert_units(s):
    for rx, k, suf in _UNIT_RULES:
        def sub(m, k=k, suf=suf):
            v = float(m.group(1).replace(",", ".")) * k
            v = round(v, 1) if v < 100 else round(v)
            return f"{v}{suf}"
        s = rx.sub(sub, s)
    return s


# ============================================================================
# Бинарные форматы: .strings, BSA, BA2
# ============================================================================
def _zlib_try(data):
    try:
        return zlib.decompress(data)
    except Exception:
        return zlib.decompress(data, -15)


def read_strings_bytes(data, ext, encoding="utf-8"):
    """Парсит байты .strings/.dlstrings/.ilstrings из памяти."""
    length_prefixed = ext in (".dlstrings", ".ilstrings")
    if len(data) < 8:
        return []
    count, _data_size = struct.unpack_from("<II", data, 0)
    base = 8 + 8 * count
    out = []
    for i in range(count):
        sid, off = struct.unpack_from("<II", data, 8 + 8 * i)
        start = base + off
        if start >= len(data):
            out.append((sid, ""))
            continue
        if length_prefixed:
            if start + 4 > len(data):
                out.append((sid, ""))
                continue
            length, = struct.unpack_from("<I", data, start)
            txt = data[start + 4:start + 4 + length]
        else:
            end = data.find(b"\x00", start)
            if end < 0:
                end = len(data)
            txt = data[start:end]
        out.append((sid, txt.decode(encoding, "replace")))
    return out


def read_strings_file(path, encoding="utf-8"):
    """Читает .strings / .dlstrings / .ilstrings из файла."""
    ext = os.path.splitext(path)[1].lower()
    with open(path, "rb") as f:
        data = f.read()
    return read_strings_bytes(data, ext, encoding)


def write_strings_file(path, entries, encoding="utf-8"):
    """Запись .strings / .dlstrings / .ilstrings в корректном формате."""
    ext = os.path.splitext(path)[1].lower()
    length_prefixed = ext in (".dlstrings", ".ilstrings")
    blobs = []
    offsets = []
    total = 0
    for _sid, text in entries:
        raw = text.encode(encoding, "replace")
        offsets.append(total)
        if length_prefixed:
            chunk = struct.pack("<I", len(raw)) + raw
        else:
            chunk = raw + b"\x00"
        blobs.append(chunk)
        total += len(chunk)
    table = b"".join(struct.pack("<II", sid, off)
                     for (sid, _t), off in zip(entries, offsets))
    with open(path, "wb") as f:
        f.write(struct.pack("<II", len(entries), total))
        f.write(table)
        for b in blobs:
            f.write(b)


def read_bsa_text(path, wanted=TEXT_EXT, max_files=400, log_func=None):
    """Извлекает текстовые файлы из BSA (v103+) с корректным чтением смещений."""
    out = {}
    with open(path, "rb") as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as data:
            if len(data) < 36: return out
            magic, ver = struct.unpack_from("<II", data, 0)
            if magic != 0x00415342 or ver < 103: return out
            
            # Читаем заголовок
            header_offset, flags, fcount_dir, fcount, _l1, _l2, _fflags = struct.unpack_from("<IIIIIII", data, 8)
            archive_compressed = bool(flags & 0x4)
            
            fpos = 36
            folders = []
            # Читаем записи папок (16 байт каждая)
            for _d in range(fcount_dir):
                if fpos + 16 > len(data): break
                _h, = struct.unpack_from("<Q", data, fpos)
                cnt, = struct.unpack_from("<I", data, fpos + 8)
                off, = struct.unpack_from("<I", data, fpos + 12)
                folders.append((cnt, off))
                fpos += 16

            # Таблица имен файлов находится по адресу header_offset
            names = []
            pos = header_offset
            for _r in range(fcount):
                if pos >= len(data): break
                end = data.find(b"\x00", pos)
                if end < 0: break
                names.append(data[pos:end].decode("utf-8", "replace"))
                pos = end + 1
                
            name_idx = 0
            for cnt, off in folders:
                pos = off
                if pos >= len(data): continue
                # Длина имени папки (1 байт) + имя
                (nlen,) = struct.unpack_from("<B", data, pos)
                pos += 1
                fname = data[pos:pos+nlen].decode("cp1252", "replace")
                pos += nlen
                
                for _i in range(cnt):
                    if pos + 16 > len(data) or name_idx >= len(names): break
                    _h, = struct.unpack_from("<Q", data, pos)
                    size, = struct.unpack_from("<I", data, pos + 8)
                    file_off, = struct.unpack_from("<I", data, pos + 12)
                    pos += 16
                    
                    nm = names[name_idx]
                    name_idx += 1
                    
                    raw_size = size & ~0x40000000
                    bit_compressed = bool(size & 0x40000000)
                    actually_compressed = (archive_compressed and not bit_compressed) or (not archive_compressed and bit_compressed)
                    
                    full = f"{fname}/{nm}".replace("\\", "/")
                    if full.lower().endswith(wanted):
                        if len(out) >= max_files: break
                        try:
                            if actually_compressed:
                                blob = _zlib_try(data[file_off + 4:file_off + raw_size])
                            else:
                                blob = data[file_off:file_off + raw_size]
                            out[full] = blob
                        except Exception as e:
                            if log_func:
                                log_func("err", f"BSA: {full}: {e}")
    return out


def read_ba2_text(path, wanted=TEXT_EXT, max_files=400, log_func=None):
    """Извлекает текстовые файлы из BA2 (FO4, GNRL) через mmap."""
    out = {}
    with open(path, "rb") as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as data:
            if len(data) < 24:
                return out
            if data[:4] != b"BTDX":
                return out
            typ = data[8:12]
            if typ != b"GNRL":
                return out
            count, = struct.unpack_from("<I", data, 12)
            name_off, = struct.unpack_from("<Q", data, 16)

            entry = struct.Struct("<I4sIIQIII")
            pos = 24
            recs = []
            for _i in range(count):
                if pos + entry.size > len(data):
                    break
                _nh, ext, _dh, _flg, off, psize, usize, _align = entry.unpack_from(data, pos)
                pos += entry.size
                recs.append((ext.decode("ascii", "replace").rstrip("\x00"),
                             psize, usize, off))

            names = []
            name_pos = name_off
            for _i in range(count):
                if name_pos + 2 > len(data):
                    break
                (nl,) = struct.unpack_from("<H", data, name_pos)
                name_pos += 2
                names.append(data[name_pos:name_pos + nl].decode("utf-8", "replace"))
                name_pos += nl

            truncated = False
            for (ext, psize, usize, off), nm in zip(recs, names):
                if len(out) >= max_files:
                    truncated = True
                    break
                if not ("." + ext.lower()).endswith(wanted):
                    continue
                try:
                    if psize == 0:
                        blob = data[off:off + usize]
                    elif psize < usize:
                        blob = zlib.decompress(data[off:off + psize])
                    else:
                        blob = data[off:off + psize]
                except Exception:
                    blob = data[off:off + (psize or usize)]
                out[nm.replace("\\", "/")] = blob
            if truncated and log_func:
                log_func("warn",
                         _tx(f"{os.path.basename(path)}: больше {max_files} файлов, "
                         f"остальные пропущены", f"{os.path.basename(path)}: ファイルが {max_files} 個を超えたため、残りはスキップしました"))
    return out


# ============================================================================
# ESP-парсер
# ============================================================================
RECORD_HEADER_SIZE = 24
GROUP_HEADER_SIZE = 24
SUBRECORD_HEADER_SIZE = 6
FLAG_LOCALIZED = 0x80
FLAG_COMPRESSED = 0x00040000
LSTRING_SUBRECORDS = {b"FULL", b"DESC"}
ZSTRING_META_SUBRECORDS = {b"CNAM", b"SNAM"}
EXPANDED_SUBRECORDS = {
    b"MGEF": {b"DNAM": False}, 
    b"INFO": {b"NAM1": False},   # RNAM — uint32-носитель индекса, не строка
    b"QUST": {b"NNAM": False, b"QNAM": False}, 
    b"MESG": {b"ITXT": False},
    b"BOOK": {b"CNAM": False}, 
    b"WOOP": {b"WNAM": False}, 
    b"SHOU": {b"WNAM": False},
    b"PERK": {b"DESC": False, b"EPFD": False},
    b"NPC_": {b"SHRT": False},
    b"ACTI": {b"RNAM": False},
    b"FLOR": {b"RNAM": False},
    b"WEAP": {b"NNAM": False},
}

# Подзаписи, чьи строки в .esp идут вместе с индексом. DSD требует поле "index":
# у одной записи один и тот же тип подзаписи может встречаться несколько раз
# (например реплики диалога INFO), и без индекса все эти строки перезаписали бы
# одну и ту же — в игре была бы видна только первая. Индекс берётся из парной
# подзаписи-носителя (см. INDEX_PAIR_SUBRECORDS); если её нет, откат на счётчик
# по порядку появления внутри записи: (form_id, тип подзаписи) -> 0, 1, ...
INDEXED_META_SUBRECORDS = {
    b"INFO": {b"NAM1"},
    b"QUST": {b"NNAM", b"QNAM"},
    b"MESG": {b"ITXT"},
    b"PERK": {b"EPFD"},
    b"ACTI": {b"RNAM"},
    b"FLOR": {b"RNAM"},
}

# Парная подзапись, хранящая real index для строковой подзаписи того же типа
# записи: значение читается как uint32, для INDX — как uint16.
INDEX_PAIR_SUBRECORDS = {
    b"INFO": (b"RNAM", "<I"),   # индекс реплики для NAM1
    b"MESG": (b"INDX", "<H"),   # индекс описания для ITXT
    b"PERK": (b"EPF2", "<I"),   # индекс эффекта для EPFD
}


def esp_masters(data: bytes) -> List[str]:
    """TES4 ヘッダの MAST（マスター）一覧。レコード FormID の上位バイトはこの並びの番号。"""
    if len(data) < RECORD_HEADER_SIZE or data[:4] != b"TES4":
        return []
    size = struct.unpack_from("<I", data, 4)[0]
    body = data[RECORD_HEADER_SIZE:RECORD_HEADER_SIZE + size]
    out, pos = [], 0
    while pos + SUBRECORD_HEADER_SIZE <= len(body):
        t = body[pos:pos + 4]
        sz = struct.unpack_from("<H", body, pos + 4)[0]
        if t == b"MAST":
            out.append(body[pos + 6:pos + 6 + sz].rstrip(b"\x00").decode("cp1252", "replace"))
        pos += SUBRECORD_HEADER_SIZE + sz
    return out


_OFFICIAL_MASTERS = {"skyrim.esm", "update.esm", "dawnguard.esm", "hearthfires.esm",
                     "dragonborn.esm", "_resourcepack.esl"}


def is_official_master(name: str) -> bool:
    """本体・DLC・Creation Club のプラグインか（公式の日本語訳があるもの）。"""
    n = (name or "").lower()
    return n in _OFFICIAL_MASTERS or (n.startswith("cc") and n.endswith((".esm", ".esl")))


def dsd_form_ref(form_id: int, plugin_file: str, masters: List[str]):
    """DSD の form_id 文字列。上書きレコードは元のプラグイン名で指定する。
    本体/DLC/CC のレコードの上書きは None（公式訳を PLaMo 等の訳で上書きしないため出力しない）。"""
    idx = form_id >> 24
    if idx < len(masters):
        owner = masters[idx]
        if is_official_master(owner):
            return None
        return f"{form_id & 0xFFFFFF:06X}|{owner}"
    return f"{form_id & 0xFFFFFF:06X}|{plugin_file}"


def _safe_decode(data: bytes, encoding: str) -> str:
    for enc in (encoding, "utf-8", "cp1252", "latin1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _safe_encode(text: str, encoding: str) -> bytes:
    try:
        return text.encode(encoding)
    except UnicodeEncodeError:
        return text.encode(encoding, errors="replace")


class EspStringExtractor:
    def __init__(self, encoding: str = "utf-8"):
        self.encoding = encoding
        self.localized = False
        self._changes = 0
        self.extracted_strings: List[str] = []
        self.trans_dict: Dict[str, str] = {}
        self.extracted_meta: List[Dict] = []
        self.indexed_extracted = 0
        self._meta_counters: Dict[Tuple[int, bytes], int] = {}

    def extract_strings(self, data: bytes) -> List[str]:
        self.extracted_strings = []
        self.localized = False
        if len(data) < RECORD_HEADER_SIZE or data[:4] != b"TES4":
            return []
        self._process_blocks(data, 0, len(data), mode="extract")
        return self.extracted_strings

    def extract_strings_with_meta(self, data: bytes) -> List[Dict]:
        """Извлекает строки вместе с FormID и типом подзаписи (для экспорта в DSD).
        Байты файла не изменяются."""
        self.extracted_meta = []
        self.indexed_extracted = 0
        self._meta_counters = {}
        self.localized = False
        if len(data) < RECORD_HEADER_SIZE or data[:4] != b"TES4":
            return []
        self._process_blocks(data, 0, len(data), mode="extract_meta")
        return self.extracted_meta

    def apply_translations(self, data: bytes, trans_dict: Dict[str, str]) -> Tuple[int, bytes]:
        self.trans_dict = trans_dict
        self._changes = 0
        self.localized = False
        if len(data) < RECORD_HEADER_SIZE or data[:4] != b"TES4":
            return 0, data
        out = self._process_blocks(data, 0, len(data), mode="apply")
        return self._changes, out

    def _process_blocks(self, data: bytes, start: int, end: int, mode: str) -> bytes:
        parts, offset = [], start
        while offset < end:
            if offset + 4 > end:
                break
            if data[offset:offset + 4] == b"GRUP":
                if offset + GROUP_HEADER_SIZE > end:
                    break
                gsize = struct.unpack_from("<I", data, offset + 4)[0]
                g_end = offset + gsize
                if gsize < GROUP_HEADER_SIZE or g_end <= offset:
                    # битый GRUP — избегаем зацикливания
                    offset += 4
                    continue
                if g_end <= end:
                    parts.append(self._process_group(data, offset, mode))
                    offset = g_end
                else:
                    parts.append(self._process_group(data, offset, mode, force_g_end=end))
                    offset = end
            else:
                if offset + RECORD_HEADER_SIZE > end:
                    break
                rec_size = struct.unpack_from("<I", data, offset + 4)[0]
                rec_end = offset + RECORD_HEADER_SIZE + rec_size
                if rec_end > end or rec_end <= offset:
                    break
                parts.append(self._process_record(data, offset, mode))
                offset = rec_end
        return b"".join(parts)

    def _process_group(self, data: bytes, offset: int, mode: str,
                       force_g_end: Optional[int] = None) -> bytes:
        header = bytearray(data[offset:offset + GROUP_HEADER_SIZE])
        gsize = struct.unpack_from("<I", data, offset + 4)[0]
        g_end = force_g_end if force_g_end else offset + gsize
        children = self._process_blocks(data, offset + GROUP_HEADER_SIZE, g_end, mode)
        struct.pack_into("<I", header, 4, GROUP_HEADER_SIZE + len(children))
        return bytes(header) + children

    def _process_record(self, data: bytes, offset: int, mode: str) -> bytes:
        header = bytearray(data[offset:offset + RECORD_HEADER_SIZE])
        record_type = bytes(header[:4])
        data_size = struct.unpack_from("<I", header, 4)[0]
        flags = struct.unpack_from("<I", header, 8)[0]
        form_id = struct.unpack_from("<I", header, 12)[0]
        if record_type == b"TES4":
            self.localized = (flags & FLAG_LOCALIZED) != 0
        if record_type == b"TES4" and self.localized:
            # Не выводим каждый раз, а только при первом обнаружении
            if not getattr(self, "_warned_localized", False):
                print(_tx("ПРЕДУПРЕЖДЕНИЕ: Плагин использует флаг localized. Строки хранятся в .strings файлах. Перевод .esp пропущен.", "警告: プラグインに localized フラグがあります。文字列は .strings ファイルにあるため .esp の翻訳はスキップします。"))
                self._warned_localized = True
        compressed = (flags & FLAG_COMPRESSED) != 0
        raw = data[offset + RECORD_HEADER_SIZE:offset + RECORD_HEADER_SIZE + data_size]

        try:
            payload = zlib.decompress(raw[4:]) if compressed else raw
        except zlib.error:
            return bytes(header) + raw

        new_payload = self._process_subrecords(record_type, payload, form_id, mode)

        if compressed:
            if new_payload == payload:
                # Ничего не изменилось — сохраняем оригинальные байты
                new_raw = raw
            else:
                new_raw = struct.pack("<I", len(new_payload)) + zlib.compress(new_payload)
        else:
            new_raw = new_payload

        if len(new_raw) != data_size:
            struct.pack_into("<I", header, 4, len(new_raw))
        return bytes(header) + new_raw

    def _process_subrecords(self, record_type: bytes, data: bytes,
                            form_id: int, mode: str) -> bytes:
        out, pos, length = bytearray(), 0, len(data)
        # Индекс из парной подзаписи этой записи; сбрасывается на каждой записи,
        # чтобы индексы одного диалога не перетекали в другой.
        current_index = None
        pair_sr, pair_fmt = INDEX_PAIR_SUBRECORDS.get(record_type, (None, None))
        while pos < length:
            if pos + SUBRECORD_HEADER_SIZE > length:
                out.extend(data[pos:])
                break
            sr_type = data[pos:pos + 4]
            sr_size = struct.unpack_from("<H", data, pos + 4)[0]
            sr_start, sr_end = pos + SUBRECORD_HEADER_SIZE, pos + SUBRECORD_HEADER_SIZE + sr_size
            if sr_end > length:
                out.extend(data[pos:])
                break
            sr_data = data[sr_start:sr_end]

            if mode == "extract_meta" and pair_sr is not None and sr_type == pair_sr:
                if sr_size >= struct.calcsize(pair_fmt):
                    current_index = struct.unpack_from(pair_fmt, sr_data, 0)[0]
                new_sr = sr_data
            else:
                new_sr = self._maybe_translate_subrecord(record_type, sr_type, sr_data,
                                                         form_id, mode, current_index)
            if new_sr is None:
                new_sr = sr_data
            elif new_sr != sr_data and mode == "apply":
                self._changes += 1

            if len(new_sr) > 0xFFFF:
                new_sr = sr_data
            out.extend(sr_type + struct.pack("<H", len(new_sr)) + new_sr)
            pos = sr_end
        return bytes(out)

    def _maybe_translate_subrecord(self, record_type: bytes, sr_type: bytes,
                                   data: bytes, form_id: int, mode: str,
                                   current_index: Optional[int] = None) -> Optional[bytes]:
        is_lstring = (sr_type in LSTRING_SUBRECORDS
                      or (record_type in EXPANDED_SUBRECORDS
                          and EXPANDED_SUBRECORDS[record_type].get(sr_type) is True))
        is_zstring = (sr_type in ZSTRING_META_SUBRECORDS and record_type == b"TES4") \
                     or (record_type in EXPANDED_SUBRECORDS
                         and EXPANDED_SUBRECORDS[record_type].get(sr_type) is False)

        if (is_lstring or is_zstring) and not self.localized:
            if mode == "extract_meta":
                # TES4 CNAM/SNAM — имена автора, для DSD бесполезны.
                if record_type != b"TES4" and data and data[-1:] == b"\x00":
                    meta_index = None
                    if sr_type in INDEXED_META_SUBRECORDS.get(record_type, ()):
                        # Реальный index из парной подзаписи; если её не было — откат на счётчик.
                        if current_index is not None:
                            meta_index = current_index
                        else:
                            meta_index = self._meta_counters.get((form_id, sr_type), 0)
                            self._meta_counters[(form_id, sr_type)] = meta_index + 1
                        self.indexed_extracted += 1
                    text = _safe_decode(data[:-1], self.encoding)
                    if text.strip():
                        entry = {
                            "src": text,
                            "form_id": form_id,
                            "type": f"{record_type.decode('ascii')} {sr_type.decode('ascii')}"
                        }
                        if meta_index is not None:
                            entry["index"] = meta_index
                        self.extracted_meta.append(entry)
                return None
            if mode == "extract" and record_type == b"TES4":
                return None       # 作者名(CNAM)・説明(SNAM): DSD で差し替えられないので訳さない
            return self._translate_zstring(data, mode)
        return None

    def _translate_zstring(self, data: bytes, mode: str) -> Optional[bytes]:
        if not data or data[-1:] != b"\x00":
            return None
        text = _safe_decode(data[:-1], self.encoding)
        if not text.strip():
            return None

        if mode == "extract":
            if text not in self.extracted_strings:
                self.extracted_strings.append(text)
            return None

        if mode == "apply":
            translated = self.trans_dict.get(text, text)
            if translated == text:
                return None
            return _safe_encode(translated, self.encoding) + b"\x00"
        return None


# ── Papyrus スクリプト（.pex）内の表示用文字列 ─────────────────────────────
# .pex の文字列表は、画面に出す文字列とイベント名・キー・比較用の文字列を共有している。
# 表をそのまま書き換えると壊れるので、次の方式にする:
#   1. 表示用の関数（MCM の AddToggleOption など）に渡される文字列の「使用箇所」だけを探す
#   2. 訳文は文字列表の末尾に追加し、その使用箇所の参照番号だけを差し替える
# 元の文字列は残るので、同じ文字列を比較やキーに使っている箇所には影響しない。

class PexError(Exception):
    pass


# SkyUI SKI_ConfigBase / Debug の関数名 → 表示用の引数位置（0 始まり、self は含まない）
PEX_DISPLAY_METHODS = {
    "addheaderoption": (0,),
    "addtextoption": (0, 1),
    "addtoggleoption": (0,),
    "addslideroption": (0, 2),
    "addmenuoption": (0, 1),
    "addcoloroption": (0,),
    "addkeymapoption": (0,),
    "addinputoption": (0, 1),
    "addtextoptionst": (1, 2),
    "addtoggleoptionst": (1,),
    "addslideroptionst": (1, 3),
    "addmenuoptionst": (1, 2),
    "addcoloroptionst": (1,),
    "addkeymapoptionst": (1,),
    "addinputoptionst": (1, 2),
    "settextoptionvalue": (1,),
    "setslideroptionvalue": (2,),
    "setmenuoptionvalue": (1,),
    "setinputoptionvalue": (1,),
    "settextoptionvaluest": (0,),
    "setslideroptionvaluest": (1,),
    "setmenuoptionvaluest": (0,),
    "setinputoptionvaluest": (0,),
    "setinfotext": (0,),
    "settitletext": (0,),
    "showmessage": (0, 2, 3),
}
PEX_DISPLAY_STATICS = {
    ("debug", "notification"): (0,),
    ("debug", "messagebox"): (0,),
}

# Skyrim のオペコード → 固定引数の数（23-25 は可変長引数つき）
_PEX_OP_ARGS = {
    0: 0, 1: 3, 2: 3, 3: 3, 4: 3, 5: 3, 6: 3, 7: 3, 8: 3, 9: 3,
    10: 2, 11: 2, 12: 2, 13: 2, 14: 2,
    15: 3, 16: 3, 17: 3, 18: 3, 19: 3,
    20: 1, 21: 2, 22: 2,
    23: 3, 24: 2, 25: 3,
    26: 1, 27: 3, 28: 3, 29: 3,
    30: 2, 31: 2, 32: 3, 33: 3, 34: 4, 35: 4,
}
_PEX_VARARG_OPS = (23, 24, 25)
_PEX_JUMP_OPS = (20, 21, 22)
# 書き込み先（dest）になる引数の位置
_PEX_DEST_ARG = {op: 0 for op in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
                                    15, 16, 17, 18, 19, 27, 30, 31, 32)}
_PEX_DEST_ARG.update({23: 2, 24: 1, 25: 2, 28: 2, 34: 1, 35: 1})
_PEX_OP_ASSIGN, _PEX_OP_CAST, _PEX_OP_STRCAT = 13, 14, 27


class _PexReader:
    """Skyrim の .pex（ビッグエンディアン）を読む。"""

    def __init__(self, data):
        self.d = data
        self.p = 0

    def take(self, fmt):
        v = struct.unpack_from(">" + fmt, self.d, self.p)
        self.p += struct.calcsize(">" + fmt)
        return v[0]

    def wstring(self):
        n = self.take("H")
        s = self.d[self.p:self.p + n]
        if len(s) != n:
            raise PexError("文字列が途中で切れています")
        self.p += n
        return s

    def vardata(self):
        t = self.take("B")
        off = self.p + 0
        if t == 0:
            return (0, None, off)
        if t in (1, 2):
            return (t, self.take("H"), off)
        if t == 3:
            return (t, self.take("i"), off)
        if t == 4:
            return (t, self.take("f"), off)
        if t == 5:
            return (t, self.take("B"), off)
        raise PexError(f"不明な値の型 {t}（位置 {self.p - 1}）")

    def function(self, out):
        self.take("H"); self.take("H"); self.take("I"); self.take("B")   # 戻り値型・説明・フラグ
        for _ in range(self.take("H") * 2):                             # 引数（名前, 型）
            self.take("H")
        for _ in range(self.take("H") * 2):                             # ローカル変数（名前, 型）
            self.take("H")
        code = []
        for _ in range(self.take("H")):
            op = self.take("B")
            if op not in _PEX_OP_ARGS:
                raise PexError(f"不明なオペコード {op}")
            args = [self.vardata() for _ in range(_PEX_OP_ARGS[op])]
            if op in _PEX_VARARG_OPS:
                cnt = self.vardata()
                if cnt[0] != 3 or cnt[1] < 0:
                    raise PexError("可変長引数の数が不正です")
                args.extend(self.vardata() for _ in range(cnt[1]))
            code.append((op, args))
        out.append(code)


def pex_parse(data):
    """→ {"strings": [bytes], "st_start", "st_end", "functions": [[(op, args)]]}
    args は (型, 値, 値のファイル内位置)。型 1=識別子, 2=文字列（値は文字列表の番号）。"""
    if data[:4] != b"\xfa\x57\xc0\xde":
        raise PexError("Skyrim の .pex ではありません")
    r = _PexReader(data)
    r.p = 4 + 1 + 1 + 2 + 8
    for _ in range(3):                    # ソース名・ユーザー名・PC 名
        r.wstring()
    st_start = r.p
    strings = [r.wstring() for _ in range(r.take("H"))]
    st_end = r.p
    if r.take("B"):                       # デバッグ情報
        r.take("Q")
        for _ in range(r.take("H")):
            r.take("H"); r.take("H"); r.take("H"); r.take("B")
            n_lines = r.take("H")         # 先に読む（r.p += r.take() だと読み進めた分が消える）
            r.p += 2 * n_lines
    for _ in range(r.take("H")):          # ユーザーフラグ
        r.take("H"); r.take("B")
    funcs = []
    for _ in range(r.take("H")):          # オブジェクト
        r.take("H"); r.take("I")
        r.take("H"); r.take("H"); r.take("I"); r.take("H")
        for _ in range(r.take("H")):      # 変数
            r.take("H"); r.take("H"); r.take("I"); r.vardata()
        for _ in range(r.take("H")):      # プロパティ
            r.take("H"); r.take("H"); r.take("H"); r.take("I")
            flags = r.take("B")
            if flags & 4:
                r.take("H")
            else:
                if flags & 1:
                    r.function(funcs)
                if flags & 2:
                    r.function(funcs)
        for _ in range(r.take("H")):      # ステート
            r.take("H")
            for _ in range(r.take("H")):
                r.take("H")
                r.function(funcs)
    if r.p != len(data):
        raise PexError(f"解析位置がファイル末尾と一致しません（{r.p} / {len(data)}）")
    return {"strings": strings, "st_start": st_start, "st_end": st_end, "functions": funcs}


def _pex_name(pex, arg):
    if arg[0] in (1, 2) and arg[1] < len(pex["strings"]):
        return pex["strings"][arg[1]].decode("ascii", "replace").lower()
    return ""


def _pex_is_temp(pex, arg):
    return arg[0] == 1 and _pex_name(pex, arg).startswith("::temp")


def _pex_trace(pex, code, i, temp, targets, out, depth=0):
    """code[i] で使われる一時変数 temp の値を遡り、元になった文字列リテラルを out に集める。
    分岐が絡む・別の命令で作られた値は追わない（安全側）。"""
    if depth > 16:
        return
    k = i - 1
    while k >= 0:
        if (k + 1) in targets or code[k][0] in _PEX_JUMP_OPS:
            return
        op, args = code[k]
        di = _PEX_DEST_ARG.get(op)
        if di is not None and di < len(args) and args[di][0] == 1 and args[di][1] == temp[1]:
            if op == _PEX_OP_STRCAT:
                srcs = args[1:3]
            elif op == _PEX_OP_ASSIGN:
                srcs = args[1:2]
            else:
                return
            for a in srcs:
                if a[0] == 2:
                    out.append(a)
                elif _pex_is_temp(pex, a):
                    _pex_trace(pex, code, k, a, targets, out, depth + 1)
            return
        k -= 1


def pex_display_sites(pex):
    """表示用の関数に渡される文字列リテラルの使用箇所 → [(文字列表の番号, 値の位置)]"""
    sites = []
    for code in pex["functions"]:
        targets = set()
        for idx, (op, args) in enumerate(code):
            if op in _PEX_JUMP_OPS:
                off = args[0] if op == 20 else args[1]
                if off[0] == 3:
                    targets.add(idx + off[1])
        for idx, (op, args) in enumerate(code):
            if op == 23:                        # callmethod 名前, 対象, 戻り先, 引数…
                positions = PEX_DISPLAY_METHODS.get(_pex_name(pex, args[0]))
                call_args = args[3:]
            elif op == 25:                      # callstatic 型, 名前, 戻り先, 引数…
                positions = PEX_DISPLAY_STATICS.get((_pex_name(pex, args[0]), _pex_name(pex, args[1])))
                call_args = args[3:]
            else:
                continue
            if not positions:
                continue
            for pos in positions:
                if pos >= len(call_args):
                    continue
                a = call_args[pos]
                found = []
                if a[0] == 2:
                    found.append(a)
                elif _pex_is_temp(pex, a):
                    _pex_trace(pex, code, idx, a, targets, found)
                sites.extend((f[1], f[2]) for f in found)
    return sites


def _pex_is_display_text(s, tgt="ja", src="en"):
    t = s.strip()
    if not t or t.startswith("$"):
        return False                      # 空・$KEY（Translations 側で訳す）
    if not re.search(r"\s", t) and re.search(r"[a-z][A-Z]|_|\d", t):
        return False                      # 識別子っぽい（AND_ChestCurtain、SelectShySexInfoText など）
    if "\\" in t:
        return False                      # パス（Meshes\Terrain\ など）
    # タグの断片（<font color='…）・$KEY・{0} を除いて、単語が残るものだけ
    body = re.sub(r"<[^>]*>|<[^>]*$|^[^<]*?>", " ", t)
    body = re.sub(r"\$\S+|\{\d*\}", " ", body)
    if not re.search(r"[A-Za-z]{2,}", body):
        return False
    return not already_in_target(t, tgt, src)


def pex_extract_strings(data, encoding="utf-8", tgt="ja", src="en"):
    """表示用の文字列（重複なし）を返す。"""
    pex = pex_parse(data)
    seen = []
    for sidx, _off in pex_display_sites(pex):
        s = _safe_decode(pex["strings"][sidx], encoding)
        if s not in seen and _pex_is_display_text(s, tgt, src):
            seen.append(s)
    return seen


def _pex_encode(text, encoding):
    """訳文をバイト列にする。指定の文字コードで表せない文字があれば UTF-8（SE の日本語と同じ）にする。"""
    encs = (encoding,) if (encoding or "").lower() in ("utf-8", "cp1252", "windows-1251") else ()
    for enc in encs + ("utf-8",):
        try:
            return text.encode(enc)
        except (UnicodeEncodeError, LookupError):
            continue
    return None


def pex_apply_translations(data, trans_dict, encoding="utf-8"):
    """表示用の使用箇所だけ訳文に差し替えた .pex を返す → (差し替えた箇所の数, bytes)。"""
    pex = pex_parse(data)
    strings = list(pex["strings"])
    index_of = {}
    for i, s in enumerate(strings):
        index_of.setdefault(s, i)
    buf = bytearray(data)
    changes = 0
    for sidx, off in pex_display_sites(pex):
        src_text = _safe_decode(pex["strings"][sidx], encoding)
        dst = trans_dict.get(src_text)
        if not dst or dst == src_text:
            continue
        raw = _pex_encode(dst, encoding)
        if raw is None or len(raw) > 0xFFFF:
            continue
        ni = index_of.get(raw)
        if ni is None:
            if len(strings) >= 0xFFFF:
                raise PexError("文字列表が上限（65535 件）に達しました")
            ni = len(strings)
            strings.append(raw)
            index_of[raw] = ni
        struct.pack_into(">H", buf, off, ni)
        changes += 1
    if not changes:
        return 0, data
    table = bytearray(struct.pack(">H", len(strings)))
    for s in strings:
        table += struct.pack(">H", len(s)) + s
    out = bytes(buf[:pex["st_start"]]) + bytes(table) + bytes(buf[pex["st_end"]:])
    pex_parse(out)                        # 書き出す前に、壊れていないか読み直して確認
    return changes, out


# ============================================================================
# Сканирование модов
# ============================================================================
# ── SKSE メニュー（SKSE Menu Framework / ImGui 系の Mod）の訳ファイル ─────────────────
# メニューの文字列を DLL ではなく訳ファイルに持つ Mod のうち、形式を確認したものだけを対象にする。
#   overwrite: ファイルが 1 つだけで、Mod がそれを読む → 値だけ訳して上書き（元は .bak_en）
#   langfile : 言語ごとのファイル（en.txt / english.txt）→ 翻訳先のファイルを作る。既にあれば足りないキーだけ追記
SKSE_MENU_RULES = [
    (re.compile(r"skse/plugins/sksemenuframeworkstrings\.json"), "json", "overwrite"),       # SKSE Menu Framework
    (re.compile(r"skse/plugins/bfco ng/language\.json"), "json", "overwrite"),               # BFCO NG
    (re.compile(r"skse/plugins/mcmmemory/translation/translation\.json"), "json", "overwrite"),  # MCM Memory
    (re.compile(r"skse/plugins/dmenu/translations\.txt"), "kv", "overwrite"),                # dMenu
    (re.compile(r"skse/plugins/translations/partysheet_en\.txt"), "kv", "overwrite"),        # Skyrim Party Sheet（DLL が _en 固定）
    (re.compile(r"skse/plugins/[^/]+/translations/(en|english)\.txt"), "kv", "langfile"),    # Detailed MiniMap / Hotkey Atlas
]
_SKSE_LANG_NATIVE = {"ja": "日本語", "zh": "中文", "zh-CN": "简体中文", "zh-TW": "繁體中文", "ru": "Русский",
                     "de": "Deutsch", "fr": "Français", "es": "Español", "it": "Italiano", "pl": "Polski"}
_SKSE_JSON_LINE_RE = re.compile(r'^(\s*"((?:[^"\\]|\\.)*)"\s*:\s*")((?:[^"\\]|\\.)*)("\s*,?\s*(?://.*)?)$')
_SKSE_KV_LINE_RE = re.compile(r"^(\s*([^=\t;#\[\s][^=\t]*?)(?:\s*=\s*|\t+\s*))(.*?)(\s*)$")
# 値の前後にあるアイコン用の私用領域の文字（Font Awesome 等）と空白は訳さずに残す
_SKSE_AFFIX_RE = re.compile(r"^([\s\ue000-\uf8ff]*)(.*?)([\s\ue000-\uf8ff]*)$", re.S)


def skse_menu_rule(rel, src="en"):
    """rel（Mod 内の相対パス）が対象の訳ファイルなら (形式, 方式)、違えば None。"""
    if src != "en":
        return None
    rl = rel.replace("\\", "/").lower()
    for rx, fmt, mode in SKSE_MENU_RULES:
        if rx.fullmatch(rl):
            return fmt, mode
    return None


def skse_langfile_target_name(fn, tgt="ja"):
    """en.txt → ja.txt、english.txt → japanese.txt（大文字小文字の書き方は元に合わせる）"""
    stem, ext = os.path.splitext(fn)
    new = tgt if len(stem) <= 3 else LANG_SUFFIX.get(tgt, tgt)
    if stem.isupper():
        new = new.upper()
    elif stem[:1].isupper():
        new = new.capitalize()
    return new + ext


def _skse_read(path):
    with open(path, "rb") as f:
        raw = f.read()
    enc = detect_text_encoding(raw, "utf-8")
    return raw.decode(enc, errors="replace").lstrip("\ufeff"), enc


def _skse_split(value):
    """値 → (前のアイコン・空白, 訳す部分, 後ろのアイコン・空白)"""
    m = _SKSE_AFFIX_RE.match(value)
    return m.groups() if m else ("", value, "")


def _skse_translatable(value, tgt="ja", src="en"):
    core = _skse_split(value)[1]
    return bool(re.search(r"[A-Za-z]{2,}", core)) and not already_in_target(core, tgt, src)


def skse_menu_entries(text, fmt):
    """訳ファイルの本文 → [(行番号, キー, 値)]。値は json ならデコード済み。コメント行は飛ばす。"""
    out, in_block = [], False
    for i, line in enumerate(text.splitlines()):
        s = line.strip()
        if fmt == "json":
            if in_block:
                if "*/" in s:
                    in_block = False
                continue
            if s.startswith("/*"):
                in_block = "*/" not in s
                continue
            if s.startswith("//"):
                continue
            m = _SKSE_JSON_LINE_RE.match(line)
            if not m:
                continue
            try:
                value = json.loads('"' + m.group(3) + '"')
                key = json.loads('"' + m.group(2) + '"')
            except ValueError:
                continue
            out.append((i, key, value))
        else:
            if not s or s[0] in ";#[" or s.startswith("//"):
                continue
            m = _SKSE_KV_LINE_RE.match(line)
            if m and m.group(3):
                out.append((i, m.group(2).strip(), m.group(3)))
    return out


def skse_menu_gap(src_path, tgt="ja", src="en"):
    """langfile: → (翻訳先ファイルのパス or None, 足りないキーの集合 or None)。翻訳先がなければ (None, None)。"""
    tgt_path = _find_file_ci(os.path.dirname(src_path), skse_langfile_target_name(os.path.basename(src_path), tgt))
    if not tgt_path:
        return None, None
    try:
        src_text, _e = _skse_read(src_path)
        tgt_text, _e = _skse_read(tgt_path)
    except OSError:
        return None, None
    have = {k.lower() for _i, k, _v in skse_menu_entries(tgt_text, "kv")}
    missing = {k.lower() for _i, k, v in skse_menu_entries(src_text, "kv")
               if k.lower() not in have and _skse_translatable(v, tgt, src)
               and not (k.lower() == "name" and v.strip().lower() == "english")}
    return tgt_path, missing


def scan_skse_menu_file(full, rel, fmt, mode, tgt="ja", src="en"):
    """対象の訳ファイル 1 つ → 翻訳ユニットのリスト（kind=skse_kv）。"""
    text, _enc = _skse_read(full)
    merge_abs = merge_rel = None
    missing = None
    if mode == "langfile":
        merge_abs, missing = skse_menu_gap(full, tgt, src)
        if merge_abs:
            merge_rel = os.path.join(os.path.dirname(rel), os.path.basename(merge_abs)).replace("\\", "/")
    units = []
    for i, key, value in skse_menu_entries(text, fmt):
        if missing is not None and key.lower() not in missing:
            continue
        if mode == "langfile" and key.lower() == "name" and value.strip().lower() == "english":
            continue                      # 言語の一覧に出る名前 → 書き出し時に翻訳先言語の名前にする
        if not _skse_translatable(value, tgt, src):
            continue
        pre, core, post = _skse_split(value)
        units.append({"rel": rel, "kind": "skse_kv", "src": core, "dst": None, "orig_src": core,
                      "orig_path": rel, "abs": full, "line": i, "key": key, "raw_value": value,
                      "affix": [pre, post], "fmt": fmt, "mode": mode,
                      "merge_abs": merge_abs, "merge_target": merge_rel})
    return units


def _skse_escape(value, fmt):
    if fmt == "json":
        return json.dumps(value, ensure_ascii=False)[1:-1]
    return value.replace("\r\n", "\\n").replace("\n", "\\n")


def build_skse_menu_output(us, tgt="ja"):
    """1 ファイル分の skse_kv ユニット → (出力先 rel, 本文, エンコーディング, 書き込み方式)。
    書き込み方式: "overwrite"（元を上書き）/ "merge"（既存の翻訳先に追記）/ False（新しいファイル）"""
    u0 = us[0]
    fmt, mode = u0["fmt"], u0["mode"]
    text, enc = _skse_read(u0["abs"])
    nl = "\r\n" if "\r\n" in text else "\n"
    trans = {u["line"]: u for u in us}

    def value_of(u):
        pre, post = u.get("affix") or ["", ""]
        return pre + (u.get("dst") or u["src"]) + post

    if mode == "langfile" and u0.get("merge_abs"):
        base, enc = _skse_read(u0["merge_abs"])
        src_lines = text.splitlines()
        add = []
        for u in sorted(us, key=lambda x: x["line"]):
            m = _SKSE_KV_LINE_RE.match(src_lines[u["line"]]) if u["line"] < len(src_lines) else None
            if m:
                add.append(m.group(1).lstrip() + _skse_escape(value_of(u), fmt))
        return u0["merge_target"], merged_translation_body(base, add, nl) + nl, enc, "merge"

    lines = text.splitlines()
    rx = _SKSE_JSON_LINE_RE if fmt == "json" else _SKSE_KV_LINE_RE
    for i, line in enumerate(lines):
        u = trans.get(i)
        m = rx.match(line)
        if not m:
            continue
        if u is None:
            if mode == "langfile" and fmt == "kv" and m.group(2).strip().lower() == "name" \
                    and m.group(3).strip().lower() == "english":
                lines[i] = m.group(1) + _SKSE_LANG_NATIVE.get(tgt, LANG_SUFFIX.get(tgt, tgt)) + m.group(4)
            continue
        if fmt == "json":
            try:
                still = json.loads('"' + m.group(3) + '"') == u["raw_value"]
            except ValueError:
                still = False
        else:
            still = m.group(3) == u["raw_value"]
        if still:                         # 収集後にファイルが変わった行は触らない
            lines[i] = m.group(1) + _skse_escape(value_of(u), fmt) + m.group(4)
    body = nl.join(lines) + (nl if text.endswith(("\n", "\r")) else "")
    if mode == "langfile":
        out_rel = os.path.join(os.path.dirname(u0["rel"]),
                               skse_langfile_target_name(os.path.basename(u0["rel"]), tgt)).replace("\\", "/")
        return out_rel, body, enc, False
    return u0["rel"], body, enc, "overwrite"


def skse_menu_status(mod_path, tgt="ja", src="en", written=None):
    """→ (todo のリスト, 翻訳先言語ありのリスト)。written: このツールが上書き済みのファイル（rel の normcase）"""
    todo, ja = [], []
    written = written or set()
    if src != "en":
        return todo, ja
    sk = _find_file_ci(mod_path, "skse")
    pl = _find_file_ci(sk, "plugins") if sk else None
    if not pl or not os.path.isdir(pl):
        return todo, ja
    for dp, _dirs, fs in os.walk(pl):
        for fn in fs:
            full = os.path.join(dp, fn)
            rel = os.path.relpath(full, mod_path).replace("\\", "/")
            rule = skse_menu_rule(rel, src)
            if not rule:
                continue
            fmt, mode = rule
            try:
                if mode == "overwrite":
                    if os.path.normcase(os.path.normpath(rel)) in written:
                        continue
                    text, _e = _skse_read(full)
                    if already_in_target(text, tgt, src):
                        ja.append(rel)
                    elif any(_skse_translatable(v, tgt, src) for _i, _k, v in skse_menu_entries(text, fmt)):
                        todo.append(rel)
                else:
                    tgt_path, missing = skse_menu_gap(full, tgt, src)
                    if tgt_path is None:
                        text, _e = _skse_read(full)
                        if any(_skse_translatable(v, tgt, src) for _i, _k, v in skse_menu_entries(text, fmt)):
                            todo.append(rel)
                    elif missing:
                        todo.append(f"{rel}（キー不足 {len(missing)}）")
                    else:
                        ja.append(os.path.relpath(tgt_path, mod_path).replace("\\", "/"))
            except OSError:
                pass
    return todo, ja


def scan_mod_dir(root, extract_bsa, encoding="utf-8", log_func=None, allow_risky=False, cancel=None, src_lang="en",
                 include_pex=False, tgt_lang="ja", include_skse_menu=False):
    counts = {"plugins": 0, "strings": 0, "translations": 0, "json": 0, "xml": 0, "ini": 0, "scripts": 0}
    units = []
    root = os.path.abspath(root)

    for dirpath, _dirs, files in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root).replace("\\", "/")
        if rel_dir.lower().split("/")[0] == "mo2translationtool":
            continue    # このツール自身の記録ファイル
        for fn in files:
            if cancel is not None and cancel.is_set():
                return counts, units
            if re.search(r"\.bak_[a-z]{2}(-[a-z]{2})?$", fn, re.I):
                continue    # このツールが退避した元ファイル（config.json.bak_en 等）
            ext = os.path.splitext(fn)[1].lower()
            full = os.path.join(dirpath, fn)
            rel = fn if rel_dir == "." else f"{rel_dir}/{fn}"
            rel = rel.replace("\\", "/")

            # ── SKSE メニューの訳ファイル（形式を確認したものだけ。汎用の json/txt としては扱わない）──
            skse_rule = skse_menu_rule(rel, src_lang)
            if skse_rule:
                if include_skse_menu:
                    try:
                        found = scan_skse_menu_file(full, rel, skse_rule[0], skse_rule[1], tgt_lang, src_lang)
                    except Exception as e:
                        found = []
                        if log_func:
                            log_func("err", _tx(f"Ошибка чтения {fn}: {e}", f"{fn} の読み込みエラー: {e}"))
                    if found:
                        counts["translations"] += 1
                        units.extend(found)
                continue
            if ext == ".txt" and rel_dir.lower().startswith("skse/"):
                continue    # SKSE プラグインの独自の訳ファイル（上の規則にないもの）は形式が分からないので触らない
            # ── Плагины .esp/.esm/.esl ────────────────────────────────────
            # ゲームが読むのは Mod 直下（= Data 直下）のプラグインだけ。Docs/ の控え等は無視
            if ext in (".esp", ".esm", ".esl") and rel_dir != ".":
                continue
            if ext in (".esp", ".esm", ".esl"):
                counts["plugins"] += 1
                try:
                    with open(full, "rb") as f:
                        data = f.read()
                    esp = EspStringExtractor(encoding)
                    for s in esp.extract_strings(data):
                        units.append({"rel": rel, "kind": "esp_string",
                                      "src": s, "dst": None,
                                      "orig_path": rel, "orig_src": s})
                except Exception as e:
                    if log_func:
                        log_func("err", _tx(f"Ошибка чтения {fn}: {e}", f"{fn} の読み込みエラー: {e}"))

            # ── Скрипты Papyrus (.pex): только строки для показа ─────────────
            # ゲームが読むのは Scripts/ 直下の .pex だけ。表示用の関数に渡す文字列だけを訳す
            elif ext == ".pex":
                if not include_pex or rel_dir.lower() != "scripts":
                    continue
                try:
                    with open(full, "rb") as f:
                        data = f.read()
                    found = pex_extract_strings(data, encoding, tgt_lang, src_lang)
                except Exception as e:
                    if log_func:
                        log_func("warn", _tx(f"{fn}: не удалось разобрать скрипт ({e})",
                                             f"{fn}: スクリプトを解析できないので翻訳しません（{e}）"))
                    continue
                if found:
                    counts["scripts"] += 1
                for s in found:
                    units.append({"rel": rel, "kind": "pex_string",
                                  "src": s, "dst": None,
                                  "orig_path": rel, "orig_src": s})

            # ── .strings / .dlstrings / .ilstrings ────────────────────────
            elif ext in STRING_EXTS and not is_source_lang_file(fn, src_lang):
                continue
            elif ext == ".txt" and "translations" in rel_dir.lower() and not is_source_lang_file(fn, src_lang):
                continue
            elif ext in STRING_EXTS:
                counts["strings"] += 1
                try:
                    for sid, text in read_strings_file(full, encoding):
                        if text.strip():
                            units.append({"rel": rel, "kind": "strings",
                                          "sid": sid, "src": text, "dst": None,
                                          "orig_src": text, "ext": ext,
                                          "orig_path": rel})
                except Exception as e:
                    if log_func:
                        log_func("err", _tx(f"Ошибка чтения {fn}: {e}", f"{fn} の読み込みエラー: {e}"))

            # ── .json ─────────────────────────────────────────────────────
            elif ext == ".json" and (allow_risky or _is_mcm_config(rel)):
                counts["json"] += 1
                units.append({"rel": rel, "kind": "json", "path": full,
                              "src": None, "dst": None, "orig_path": rel})

            elif ext == ".xml" and allow_risky:
                counts["xml"] += 1
                units.append({"rel": rel, "kind": "xml", "path": full,
                              "src": None, "dst": None})                              

            # ── .ini ───────────────────────────────────────────────────────
            elif ext == ".ini" and allow_risky:
                counts["ini"] += 1
                units.append({"rel": rel, "kind": "ini", "path": full,
                              "src": None, "dst": None})

            # ── .txt в Translations ───────────────────────────────────────
            elif ext == ".txt" and "translations" in rel_dir.lower():
                counts["translations"] += 1
                units.append({"rel": rel, "kind": "swf_txt", "path": full,
                              "src": None, "dst": None, "orig_path": rel})

            # ── BSA / BA2 ─────────────────────────────────────────────────
            elif ext in (".bsa", ".ba2") and extract_bsa:
                reader = read_ba2_text if ext == ".ba2" else read_bsa_text
                try:
                    inner = reader(
                        full,
                        wanted=(".strings", ".dlstrings", ".ilstrings",
                                ".txt", ".json", ".esp", ".esm", ".esl"),
                        log_func=log_func)
                    if log_func and not inner:
                        log_func("info", _tx(f"{fn}: архив прочитан, "
                                         f"но переводимых файлов не найдено.", f"{fn}: アーカイブを読み込みましたが、翻訳可能なファイルは見つかりませんでした。"))

                    for ipath, blob in inner.items():
                        iext = os.path.splitext(ipath)[1].lower()
                        # Полный путь, включая расширение архива — чтобы
                        # потом можно было найти файл при сохранении ESP.
                        arch_rel = f"{fn}//{ipath}"

                        if iext in (".esp", ".esm", ".esl"):
                            continue    # BSA/BA2 内のプラグインはゲームに読み込まれない
                            try:
                                esp = EspStringExtractor(encoding)
                                for s in esp.extract_strings(blob):
                                    units.append({
                                        "rel": arch_rel,
                                        "kind": "esp_string",
                                        "src": s, "dst": None,
                                        "orig_path": arch_rel,
                                        "orig_src": s})
                            except Exception:
                                pass
                            continue

                        if iext in (STRING_EXTS + (".txt",)) and not is_source_lang_file(ipath, src_lang):
                            continue
                        if iext in STRING_EXTS:
                            counts["strings"] += 1
                            for sid, text in read_strings_bytes(blob, iext, encoding):
                                if text.strip():
                                    units.append({
                                        "rel": arch_rel, "kind": "strings",
                                        "sid": sid, "src": text, "dst": None,
                                        "orig_src": text, "ext": iext,
                                        "orig_path": arch_rel})
                            continue

                        if iext == ".json":
                            if not (allow_risky or _is_mcm_config(ipath)):
                                continue
                            counts["json"] += 1
                        elif iext == ".txt":
                            if "translations" not in ipath.lower():
                                # readme/changelog — пропускаем
                                continue
                            counts["translations"] += 1

                        units.append({"rel": arch_rel, "kind": "archive_txt",
                                      "data": blob, "iext": iext,
                                      "src": None, "dst": None,
                                      "orig_path": arch_rel})
                except Exception as e:
                    if log_func:
                        log_func("err", _tx(f"Ошибка чтения архива {fn}: {e}", f"アーカイブ {fn} の読み込みエラー: {e}"))

    return counts, units


MCM_TEXT_KEYS = {"displayname", "pagedisplayname", "text", "help",
                 "options", "shortnames", "formatstring"}


def _is_mcm_config(p):
    """MCM Helper の MCM/Config/<mod>/config.json か（相対/絶対/アーカイブ内パス可）。"""
    r = (p or "").replace("\\", "/").lower()
    return ("mcm/config/" in r) and r.endswith("/config.json")


def load_json_units(path=None, text=None, rel=None):
    try:
        if text is None:
            with open(path, encoding="utf-8-sig") as f:
                text = f.read()
        data = json.loads(text)
    except Exception:
        return []
    
    units = []
    total_strings = 0
    technical_strings = 0
    
    # Черный список ключей, которые НИКОГДА не переводятся
    BLACKLIST_KEYS = {
        "id", "formid", "mod", "plugin", "script", "event", "trigger", 
        "animation", "fragment", "condition", "node", "type", "class",
        "file", "path", "sound", "clip", "source", "target",
        # MCM Helper の識別子（翻訳すると MCM が壊れる）
        "modname", "propertyname", "scriptname", "sourcetype", "sourceform",
        "form", "function", "action",
    }

    is_mcm = _is_mcm_config(path) or _is_mcm_config(rel)

    def analyze_node(node, kp):
        nonlocal total_strings, technical_strings
        if isinstance(node, dict):
            for k, v in node.items():
                analyze_node(v, k if not kp else f"{kp}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                analyze_node(v, f"{kp}[{i}]")
        elif isinstance(node, str):
            if not node.strip() or not re.search(r"[A-Za-zА-Яа-яё]", node):
                return
                
            total_strings += 1
            lower_node = node.lower()
            last_key = kp.lower().split(".")[-1].split("[")[0]
            
            is_warn = False
            
            # 0. MCM config.json: 表示用キー以外は触らない / "$KEY" は翻訳キー参照
            if is_mcm and last_key not in MCM_TEXT_KEYS:
                is_warn = True
            elif is_mcm and not re.search(r"\s", node) and re.search(r"[a-z][A-Z]|_|\d", node):
                is_warn = True        # "MuDynamicNPCReplacer" のような識別子・Mod 名
            elif node.startswith("$"):
                is_warn = True
            # 1. Проверка по имени ключа
            elif last_key in BLACKLIST_KEYS:
                is_warn = True
            # 2. Проверка по содержимому (пути, HEX, расширения)
            elif any(lower_node.endswith(ext) for ext in (".esp", ".esm", ".esl", ".nif", ".dds", ".wav", ".xwm", ".fuz", ".pex", ".psc")):
                is_warn = True
            elif lower_node.startswith("0x") or "\\" in node or "/" in node:
                is_warn = True
            # 3. Триггеры и переменные (snake_case или CAPS_LOCK)
            elif re.fullmatch(r"[A-Z0-9_]{4,}", node) or re.fullmatch(r"[a-z0-9_]{4,}", node):
                if not node.lower() in ("none", "default", "true", "false", "yes", "no"):
                    is_warn = True
                    
            if is_warn:
                technical_strings += 1
                
            units.append({
                "rel": os.path.basename(path) if path else "data.json",
                "kind": "json_kv", "key": kp, "src": node, "dst": None,
                "warn": is_warn, 
                "orig_text": text
            })

    analyze_node(data, "")
    
    # Если в файле больше 70% технических строк — помечаем ВЕСЬ файл
    is_technical_file = False
    if total_strings > 0 and (technical_strings / total_strings > 0.7):
        is_technical_file = True
    elif total_strings == 0:
        is_technical_file = True
        
    # MCM の config.json は表示用キーで行ごとに判定済み。ファイル丸ごとの除外はしない
    if is_mcm:
        is_technical_file = False

    if is_technical_file:
        for u in units:
            u["warn"] = True
            
    return units
    
def load_xml_units(path=None, text=None):
    try:
        if text is None:
            with open(path, "rb") as f:
                raw = f.read()
            enc = detect_text_encoding(raw, "utf-8")
            text = raw.decode(enc, errors="replace")
    except Exception:
        return []
        
    units = []
    # Ищем текст между тегами >текст< и в атрибутах ="текст"
    # Это самый безопасный способ, так как он не ломает структуру XML
    pattern = re.compile(r'>([^<]+)<|="([^"]+)"')
    
    for match in pattern.finditer(text):
        val = match.group(1) or match.group(2)
        if not val or not re.search(r"[A-Za-zА-Яа-яё]", val):
            continue
            
        if not val.strip():
            continue
            
        lower_val = val.lower()
        is_warn = False
        
        # Проверка на технические пути, ID или скрипты
        if lower_val.startswith("0x") or "\\" in val or "/" in val:
            is_warn = True
        elif any(lower_val.endswith(ext) for ext in (".nif", ".dds", ".swf", ".esp", ".esm")):
            is_warn = True
        elif lower_val in ("true", "false", "none", "default"):
            is_warn = True
            
        units.append({
            "rel": os.path.basename(path) if path else "data.xml",
            "kind": "xml_text", "src": val, "dst": None,
            "warn": is_warn, "orig_text": text
        })
    return units    


def load_ini_units(path=None, text=None):
    """INI: строки вида key=value. Секции [..], комментарии и пути не переводятся."""
    try:
        if text is None:
            with open(path, "rb") as f:
                raw = f.read()
            enc = detect_text_encoding(raw, "utf-8")
            text = raw.decode(enc, errors="replace")
    except Exception:
        return []

    units = []
    # Если файл лежит в папке SKSE/Plugins — он на 99% технический (конфиги, маппинги)
    is_skse_plugin = path and "skse/plugins" in path.lower().replace("\\", "/")

    for line in text.splitlines():
        stripped = line.strip()
        # Пропускаем пустые строки, комментарии и секции [Section]
        if not stripped or stripped.startswith((";", "#", "[")):
            continue
        if "=" not in stripped:
            continue

        key, val = stripped.split("=", 1)
        key = key.strip()
        val = val.strip()
        if not key or not val or not re.search(r"[A-Za-zА-Яа-яё]", val):
            continue

        lower_val = val.lower()
        is_warn = False
        
        # 1. Любые файлы в SKSE/Plugins считаем техническими
        if is_skse_plugin:
            is_warn = True
            
        # 2. Проверяем на ID формата "Plugin.esp|0x1234" или простые 0x...
        elif "|0x" in lower_val or lower_val.startswith("0x"):
            is_warn = True
            
        # 3. Проверяем на пути к файлам
        elif "\\" in val or "/" in val:
            is_warn = True
            
        # 4. Проверяем на расширения
        elif any(lower_val.endswith(ext) for ext in
                 (".esp", ".esm", ".esl", ".nif", ".dds", ".wav", ".swf",
                  ".txt", ".ini", ".json", ".xml")):
            is_warn = True

        units.append({
            "rel": os.path.basename(path) if path else "data.ini",
            "kind": "ini_line", "key": key, "src": val, "dst": None,
            "warn": is_warn, "orig_text": text
        })
    return units


# ── Interface/Translations: 既存の訳ファイルへのマージ ─────────────────────
# 英語の訳ファイルにあって、対になる翻訳先ファイル（_japanese.txt など）にないキーだけを訳して追記する。
# 既存の行は変えない。キーの比較は大文字小文字を区別しない。

def decode_translation_text(raw, fallback="utf-8"):
    """Interface/Translations の txt（ふつうは UTF-16 LE + BOM）を文字列にする。"""
    enc = detect_text_encoding(raw, fallback)
    return raw.decode(enc, errors="replace").lstrip("\ufeff").replace("\x00", "")


def translation_keys(text):
    """→ {小文字のキー: 値}（値が空のキーも含む）"""
    keys = {}
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln.startswith("$"):
            continue
        if "\t" in ln:
            k, _, v = ln.partition("\t")
        elif "=" in ln:
            k, _, v = ln.partition("=")
        else:
            k, v = ln, ""
        keys.setdefault(k.strip().lower(), v.strip())
    return keys


def _find_file_ci(directory, name):
    """directory 内の name（大文字小文字を区別しない）→ 実際のパス or None"""
    try:
        low = name.lower()
        for fn in os.listdir(directory):
            if fn.lower() == low:
                return os.path.join(directory, fn)
    except OSError:
        pass
    return None


def translation_gap(src_path, tgt_code, encoding="utf-8"):
    """英語の訳ファイル src_path と、同じフォルダの翻訳先ファイルを比べる。
    → (翻訳先ファイルのパス or None, 翻訳先の本文, 足りないキーの集合)
    翻訳先ファイルがなければ (None, None, None)。"""
    tgt_path = _find_file_ci(os.path.dirname(src_path), _localize_name(os.path.basename(src_path), tgt_code))
    if not tgt_path or os.path.normcase(tgt_path) == os.path.normcase(src_path):
        return None, None, None
    try:
        with open(src_path, "rb") as f:
            src_keys = translation_keys(decode_translation_text(f.read(), encoding))
        with open(tgt_path, "rb") as f:
            tgt_text = decode_translation_text(f.read(), encoding)
    except OSError:
        return None, None, None
    tgt_keys = translation_keys(tgt_text)
    missing = {k for k, v in src_keys.items() if v and k not in tgt_keys}
    return tgt_path, tgt_text, missing


def apply_translation_merge(units, mod_path, tgt_code, encoding="utf-8"):
    """1 Mod 分のユニットのうち、ルーズの英語訳ファイル（swf_line）で翻訳先ファイルが既にあるものは
    足りないキーだけ残し、merge_base（既存の翻訳先の本文）を付ける。→ 新しいリスト"""
    out, cache = [], {}
    for u in units:
        rel = u.get("rel") or ""
        if u.get("kind") != "swf_line" or "//" in rel:
            out.append(u)
            continue
        if rel not in cache:
            cache[rel] = translation_gap(os.path.join(mod_path, rel), tgt_code, encoding)
        tgt_path, tgt_text, missing = cache[rel]
        if tgt_path is None:
            out.append(u)
            continue
        if (u.get("key") or "").strip().lower() not in missing:
            continue                      # 翻訳先ファイルに既にあるキー
        u["merge_base"] = tgt_text
        u["merge_target"] = os.path.relpath(tgt_path, mod_path).replace("\\", "/")
        out.append(u)
    return out


def merged_translation_body(base_text, new_lines, nl="\r\n"):
    """既存の翻訳先ファイルの本文に新しい行を追記する（既存の行はそのまま）。"""
    lines = base_text.splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    return nl.join(lines + list(new_lines))


def load_swf_txt(path, encoding="utf-8"):
    """Skyrim Interface/Translations: строки '$KEY\\tvalue' или '$KEY=value'."""
    units = []
    try:
        with open(path, "rb") as f:
            raw = f.read()
            
        # Автоопределение кодировки (UTF-16 часто используется для этих файлов)
        enc = detect_text_encoding(raw, encoding)
        content = raw.decode(enc, errors="replace")
        
        # Убираем BOM и артефакты нулевых байтов
        content = content.lstrip("\ufeff").replace("\x00", "")
        
        for ln in content.splitlines():
            ln = ln.strip()
            if not ln.startswith("$"):
                continue
            
            # Поддерживаем и табуляцию (стандарт), и знак равно
            if "\t" in ln:
                parts = ln.split("\t", 1)
            elif "=" in ln:
                parts = ln.split("=", 1)
            else:
                continue
                
            if len(parts) == 2 and parts[1].strip():
                units.append({
                    "rel": os.path.basename(path),
                    "kind": "swf_line", 
                    "key": parts[0],
                    "src": parts[1].strip(), 
                    "dst": None,
                    "orig_src": parts[1].strip()
                })
    except Exception:
        pass
    return units


# ── Языковой суффикс ────────────────────────────────────────────────────────
LANG_WORDS = ("english|german|french|spanish|italian|polish|japanese|chinese|chineses|chineset|"
              "russian|czech|arabic|danish|dutch|finnish|greek|hungarian|korean|norwegian|"
              "portuguese|brazilian|ptbr|swedish|turkish|ukrainian|thai|latam|mexican|"
              "spanishmx|traditionalchinese|simplifiedchinese")
_TRANSLATIONS_SUFFIX_RE = re.compile(r"_(" + LANG_WORDS + r")\b", re.IGNORECASE)
_LANG_TAIL_RE = re.compile(r"_(" + LANG_WORDS + r")$", re.IGNORECASE)


def file_lang(name):
    """ファイル名末尾（拡張子の直前）の言語名。なければ None。"""
    m = _LANG_TAIL_RE.search(os.path.splitext(os.path.basename(name))[0])
    return m.group(1).lower() if m else None


def is_source_lang_file(name, src="en"):
    """翻訳元として使ってよいか: 言語名なし、または翻訳元言語のファイルだけ。"""
    lang = file_lang(name)
    return lang is None or lang == LANG_SUFFIX.get(src, src).lower()


def _localize_name(name, tgt_code):
    """Заменяет языковой суффикс в имени файла перевода."""
    suf = LANG_SUFFIX.get(tgt_code, tgt_code)
    m = _TRANSLATIONS_SUFFIX_RE.search(name)
    if m:
        # Меняем только первое совпадение и не превращаем в x_russian_russian
        if m.group(1).lower() == suf:
            return name
        return _TRANSLATIONS_SUFFIX_RE.sub("_" + suf, name, count=1)
    stem, ext = os.path.splitext(name)
    return f"{stem}_{suf}{ext}"


# ============================================================================
# xTranslator の .sst 辞書（バイナリ SSU2/SSU8/SSU9 と、テキスト形式）
# ============================================================================
# エントリ = [prefix][レコード sig + その後ろの固定長部分][u32 原文長][UTF-16LE 原文][u32 訳文長][UTF-16LE 訳文]
# 版ごとにヘッダ長が違う（SSU2=4, SSU8=9, SSU9=13 を実ファイルで確認）。ヘッダ長は
# 「ファイル末尾までちょうど読み切れるか」で判別するので、未知の版でも構造が同じなら読める。
_SST_ENTRY_LAYOUTS = ((2, 0, 0), (9, 8, 10))   # (prefix, sig 長, sig の後ろの長さ)


def _sst_try_layout(raw, header, prefix, sig_len, after):
    n = len(raw)
    p = header
    out = []
    unpack = struct.unpack_from
    while p < n:
        p += prefix
        if sig_len:
            if p + sig_len > n:
                return None
            sig = raw[p:p + sig_len]
            if any(c < 32 or c > 126 for c in sig):
                return None
            p += sig_len + after
        pair = []
        for _ in range(2):
            if p + 4 > n:
                return None
            ln = unpack("<I", raw, p)[0]
            p += 4
            if ln & 1 or p + ln > n:
                return None
            try:
                pair.append(raw[p:p + ln].decode("utf-16-le"))
            except UnicodeDecodeError:
                return None
            p += ln
        out.append((pair[0], pair[1]))
    return out if p == n else None


def _sst_header_len(raw):
    """ヘッダ = "SSU<n>" + u8 + u32 マスター数 + マスター名（u32 長 + UTF-16LE）× 数。
    SSU9 はこの後ろに 4 バイト続く。読めなければ None。"""
    try:
        p = 5
        cnt = struct.unpack_from("<I", raw, p)[0]
        p += 4
        if cnt > 4096:
            return None
        for _ in range(cnt):
            ln = struct.unpack_from("<I", raw, p)[0]
            p += 4 + ln
            if ln & 1 or p > len(raw):
                return None
        return p
    except struct.error:
        return None


def parse_sst_binary(raw):
    """xTranslator のバイナリ .sst → [(原文, 訳文), ...]。この形式でなければ None。

    ヘッダだけの空の辞書は [] を返す（エラーではない）。
    """
    if len(raw) < 4 or raw[:3] != b"SSU":
        return None
    base = _sst_header_len(raw)
    if base is not None:
        for extra in (0, 4):   # SSU8 は 0、SSU9 は 4
            h = base + extra
            if h == len(raw):
                return []
            for prefix, sig_len, after in _SST_ENTRY_LAYOUTS:
                res = _sst_try_layout(raw, h, prefix, sig_len, after)
                if res:
                    return res
    # 構造どおりに読めない版（SSU2 など）は、ヘッダ長を総当たりで探す
    for header in range(4, min(33, len(raw))):
        for prefix, sig_len, after in _SST_ENTRY_LAYOUTS:
            res = _sst_try_layout(raw, header, prefix, sig_len, after)
            if res:   # 空の結果は「たまたま読み切れた」だけなので採らない
                return res
    return None


def _sst_parse_line(line):
    """テキスト形式の 1 行: 「原文 \\t 訳文」または「原文=訳文」。"""
    if "\t" in line:
        parts = line.split("\t")
        if len(parts) < 2:
            return None
        orig, dst = parts[0], parts[1]
    elif "=" in line:
        orig, dst = line.split("=", 1)
    else:
        return None
    orig, dst = orig.strip(), dst.strip()
    if not orig or not dst:
        return None
    return orig, dst


def _sst_decode_text(raw):
    enc = detect_text_encoding(raw)
    for cand in (enc, "utf-8", "utf-16-le", "utf-16-be", "cp1251", "cp1252"):
        try:
            return raw.decode(cand), cand
        except (UnicodeDecodeError, LookupError):
            continue
    return None, None


def read_sst_pairs(raw):
    """.sst のバイト列 → ({原文: 訳文}, 形式名)。読めなければ (None, 理由)。

    未翻訳のエントリ（訳文が空・原文と同じ）は除く。同じ原文に複数の訳がある場合
    （レコードごとに訳し分けている場合）は、いちばん多い訳を採る。
    """
    entries = parse_sst_binary(raw)
    fmt = raw[:4].decode("ascii", "replace") if entries is not None else None
    if entries is None:
        if raw[:3] == b"SSU":
            return None, "unknown_binary"
        text, enc = _sst_decode_text(raw)
        if text is None:
            return None, "bad_enc"
        fmt = f"text/{enc}"
        entries = []
        for line in text.replace("\x00", "").splitlines():
            line = line.strip().lstrip("\ufeff")
            if line:
                parsed = _sst_parse_line(line)
                if parsed:
                    entries.append(parsed)
    votes = {}
    for src, dst in entries:
        if not src or not dst.strip() or dst == src:
            continue
        votes.setdefault(src, Counter())[dst] += 1
    return {s: c.most_common(1)[0][0] for s, c in votes.items()}, fmt


def expand_sst_paths(paths):
    """ファイルとフォルダが混ざったリスト → 実在する .sst ファイルの一覧（フォルダは再帰）と、見つからないパス。"""
    files, missing, seen = [], [], set()
    for p in paths or []:
        if os.path.isdir(p):
            found = []
            for dp, _dn, fn in os.walk(p):
                found += [os.path.join(dp, x) for x in fn if x.lower().endswith(".sst")]
            cand = sorted(found, key=str.lower)
        elif os.path.isfile(p):
            cand = [p]
        else:
            missing.append(p)
            continue
        for f in cand:
            k = os.path.normcase(os.path.abspath(f))
            if k not in seen:
                seen.add(k)
                files.append(f)
    return files, missing


_SST_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9']*(?:-[A-Za-z0-9']+)*")
SST_TERM_MAX_WORDS = 4
SST_TERM_MAX_HITS = 15
_SST_TITLE_SMALL = frozenset("of the and a an to in on at for from with by or de".split())


def build_sst_terms(sst_dict):
    """SST 辞書から、LLM に用語ヒントとして渡す短い名前（人名・地名・アイテム名など）を選ぶ。

    文ではなく名前らしいものだけ: 1〜4 語、大文字で始まる、文末記号・改行・プレースホルダーなし、
    訳文も短い。1 語の場合は 3 文字以上。
    """
    terms = {}
    for src, dst in sst_dict.items():
        if src != src.strip() or not src[:1].isupper() or not src[:1].isascii():
            continue
        if len(src) > 40 or len(dst) > 40 or "\n" in src or "\n" in dst or "\r" in dst:
            continue
        if src[-1] in ".?!:;," or any(c in src for c in "<>{}[]%$|\\/\"="):
            continue
        words = src.split()
        if not (1 <= len(words) <= SST_TERM_MAX_WORDS):
            continue
        if len(words) == 1 and len(src) < 3:
            continue
        if not all(_SST_WORD_RE.fullmatch(w) for w in words):
            continue
        # 名前らしい書き方（Title Case）だけ。"Just be patient" のような短い文を除く
        if not all(w[:1].isupper() or w.isdigit() or w.lower() in _SST_TITLE_SMALL for w in words[1:]):
            continue
        if not dst.strip() or dst == src:
            continue
        terms[src] = dst.strip()
    return terms


def sst_term_hits(lines, terms, limit=SST_TERM_MAX_HITS):
    """行の中に出てくる SST の名前を探す（大文字小文字は区別、単語単位）。

    1〜4 語の連なりを辞書で引くので、辞書が大きくても速い。長い名前を優先し、
    長い名前に含まれる短い名前（"Iron Sword" の中の "Iron" など）は除く。
    """
    found = {}
    for line in lines:
        spans = [(m.start(), m.end()) for m in _SST_WORD_RE.finditer(line)]
        for i in range(len(spans)):
            for j in range(min(len(spans), i + SST_TERM_MAX_WORDS) - 1, i - 1, -1):
                phrase = line[spans[i][0]:spans[j][1]]
                if phrase in terms:
                    found.setdefault(phrase, terms[phrase])
                    break
    keys = sorted(found, key=len, reverse=True)
    picked = []
    for k in keys:
        if any(re.search(rf"(?<![A-Za-z]){re.escape(k)}(?![A-Za-z])", p) for p in picked):
            continue
        picked.append(k)
        if len(picked) >= limit:
            break
    return [(k, found[k]) for k in picked]


# ============================================================================
# Глоссарий и конфиг
# ============================================================================
class Glossary:
    def __init__(self):
        self.items = {}
        self.load()

    def path(self):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), GLOSSARY_NAME)

    def load(self):
        try:
            with open(self.path(), encoding="utf-8") as f:
                self.items = json.load(f)
        except Exception:
            self.items = {}

    def save(self, log_func=None):
        try:
            with open(self.path(), "w", encoding="utf-8") as f:
                json.dump(self.items, f, ensure_ascii=False, indent=2)
        except Exception as e:
            if log_func:
                log_func("err", _tx(f"Словарь не сохранён: {e}", f"用語集を保存できませんでした: {e}"))


DEFAULT_CONFIG = {
    "backend": "LM Studio",
    "source": "en", "target": "ja", "encoding": "utf-8", "ui_lang": "ja",
    "openai_url": "https://api.openai.com/v1", "openai_model": "gpt-4o-mini",
    "openai_key": "",
    "ollama_url": "http://localhost:11434", "ollama_model": "llama3.1",
    "lmstudio_url": "http://127.0.0.1:1234/v1", "lmstudio_model": "",
    "openrouter_key": "", "openrouter_model": "openai/gpt-4o-mini",
    "deepl_key": "", "yandex_key": "",
    "temperature": 0.2, "max_tokens": 2048,
    "system_prompt": DEFAULT_SYSTEM_PROMPT,
    "convert_units": True, "delay_ms": 3, "threads": 1, "dry_run": False,
    "extract_bsa": True, "gen_report": False,
    "out_folder": os.path.expanduser("~/Desktop"),
    "out_name": "", "save_zip": True, "save_dsd": True, "allow_risky": False, "per_mod_save": False, "in_place": False,
    "translate_pex": False,
    "translate_skse_menu": False,
    "status_filter": ["done", "stale", "ja", "todo", "none"], "notify_done": True,
    "batch_size": 1,
    "sst_paths": [],
    "sst_hints": True,
}


def _cfg_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_NAME)


def load_config(log_func=None):
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(_cfg_path(), encoding="utf-8") as f:
            cfg.update(json.load(f))
    except FileNotFoundError:
        pass
    except Exception as e:
        cfg["_cfg_err"] = str(e)
        if log_func:
            log_func("err", _tx(f"Конфиг не загружен: {e}", f"設定を読み込めませんでした: {e}"))
    return cfg


try:
    _UI_LANG[0] = load_config().get("ui_lang", "ja")
except Exception:
    pass


def save_config(cfg, log_func=None):
    try:
        with open(_cfg_path(), "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        if log_func:
            log_func("err", _tx(f"Конфиг не сохранён: {e}", f"設定を保存できませんでした: {e}"))


# ============================================================================
# Диалог
# ============================================================================
class TranslationDialog(QtWidgets.QDialog):
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.cfg = load_config()
        self.glossary = Glossary()
        self.lang = self.cfg.get("ui_lang", "ja")
        _UI_LANG[0] = self.lang
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.resize(1180, 860)
        self.setMinimumSize(900, 640)
        self.setStyleSheet(STYLESHEET)
        try:
            self.setFont(QtGui.QFont("Segoe UI", 9))
        except Exception:
            pass

        self.mods = []
        self.units = []
        self.jobs = []
        self.unit_rows = {}
        self.q = queue.Queue()
        self.file_states = {}
        self.cancel_ev = threading.Event()
        self.running = False
        self.run_id = 0
        self._pending_units = None
        self.cache_save_counter = 0 
        self.translation_cache = {}
        self.sst_dict = {}          # словарь .sst (xTranslator): оригинал → перевод
        self.sst_files = []         # загруженные файлы словаря (для лога и повторной загрузки)
        self.stats = {"done": 0, "total": 0, "errors": 0, "sst": 0, "t0": time.time()}
        self._delay_lock = threading.Lock()
        self._last_req_ts = 0.0
        self._loading_preview = False
        self._name_manual = False
        self._permod_queue = None     # Mod ごと自動保存: 残りの Mod
        self._permod_current = None
        self._permod_total = 0
        self._autofix_active = False  # 終了後のプレースホルダー自動修正中

        self._build_ui()
        self._retranslate()
        self._restore_fields()
        self._restore_window_state()

        self._gloss_save_timer = QtCore.QTimer(self)
        self._gloss_save_timer.setSingleShot(True)
        self._gloss_save_timer.setInterval(500)
        self._gloss_save_timer.timeout.connect(self._gloss_save_now)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(150)
        self.timer.timeout.connect(self._poll)
        self.timer.start()

        self._log("info", f"{APP_NAME} v{APP_VERSION} · {QT_FLAVOR}")
        cfg_err = self.cfg.pop("_cfg_err", None)
        if cfg_err:
            self._log("err", _tx(f"Конфиг не загружен: {cfg_err}", f"設定を読み込めませんでした: {cfg_err}"))
        if self.cfg.get("sst_paths"):
            QtCore.QTimer.singleShot(0, self._sst_reload)
        else:
            self._sst_update_tip()
        if HAS_MOBASE and getattr(plugin, "_organizer", None):
            QtCore.QTimer.singleShot(100, self.refresh_mods)
        else:
            self._log("warn",
                      _tx("Запуск вне MO2: используйте «Добавить папки…» / «Открыть файл…».", "MO2 外で起動しています: 「フォルダを追加…」/「ファイルを開く…」を使ってください。"))

    # ── i18n ───────────────────────────────────────────────────────────────
    def tr(self, key):
        ru, en = T.get(key, (key, key))
        if self.lang == "ja":
            return T_JA.get(key, en)
        return ru if self.lang == "ru" else en

    def _tr_lbl(self, w, key):
        w.setProperty("trkey", key)
        if isinstance(w, (QtWidgets.QLabel, QtWidgets.QPushButton,
                          QtWidgets.QCheckBox)):
            w.setText(self.tr(key))

    def _retranslate(self):
        for w in (self.findChildren(QtWidgets.QLabel)
                  + self.findChildren(QtWidgets.QPushButton)
                  + self.findChildren(QtWidgets.QCheckBox)):
            k = w.property("trkey")
            if k:
                w.setText(self.tr(k))
        
        self.ed_search.setPlaceholderText(self.tr("search_mods"))
        self._relabel_headers()
        self.tabs.setTabText(0, self.tr("tab_log"))
        self.tabs.setTabText(1, self.tr("tab_preview"))
        self.tabs.setTabText(2, self.tr("tab_glossary"))
        
        for w, k in self._top_labels:
            w.setText(self.tr(k))
            
        if hasattr(self, "btn_replace"):
            self.btn_replace.setText(self.tr("btn_replace"))
        if hasattr(self, "btn_sst"):
            self._build_sst_menu()
            self._sst_update_tip()
        if hasattr(self, "chk_risky"):
            self.chk_risky.setToolTip(self.tr("tip_risky"))
        if hasattr(self, "chk_pex"):
            self.chk_pex.setToolTip(self.tr("tip_pex"))
        if hasattr(self, "chk_skse"):
            self.chk_skse.setToolTip(self.tr("tip_skse_menu"))
        if hasattr(self, "chk_permod"):
            self.chk_permod.setToolTip(self.tr("tip_per_mod"))
        if hasattr(self, "chk_inplace"):
            self.chk_inplace.setToolTip(self.tr("tip_in_place"))
        self._update_state_filter_labels()
        if hasattr(self, "cb_preview_filter"):
            self._update_filter_combo()
        if hasattr(self, "ed_preview_search"):
            self.ed_preview_search.setPlaceholderText(
                _tx("Поиск по оригиналу или переводу...", "原文・訳文を検索..."))
        # -----------------------------------------------

    def _relabel_headers(self):
        self.mod_table.setHorizontalHeaderLabels(
            ["", self.tr("col_mod"), self.tr("col_plugins"),
             self.tr("col_strings"), f"{self.tr('col_trans')}/JSON", f"{self.tr('col_xml')}/INI",
             self.tr("col_state")])
        self.prev_table.setHorizontalHeaderLabels(
            ["№", self.tr("col_file"), self.tr("col_src"),
             self.tr("col_dst"), self.tr("col_status")])
        self.gloss_table.setHorizontalHeaderLabels(
            [self.tr("col_src"), self.tr("col_dst")])

    def _on_uilang(self, val):
        self.lang = {"RU": "ru", "EN": "en", "JA": "ja"}.get(val, "en")
        _UI_LANG[0] = self.lang
        self._retranslate()

    def _restore_fields(self):
        c = self.cfg
        self.cb_backend.setCurrentText(c["backend"])
        for cb, val in ((self.cb_src, c["source"]), (self.cb_tgt, c["target"])):
            for i in range(cb.count()):
                if cb.itemData(i) == val:
                    cb.setCurrentIndex(i)
        self.cb_enc.setCurrentText(c["encoding"])
        self.cb_uilang.setCurrentText({"ru": "RU", "ja": "JA"}.get(self.lang, "EN"))
        self.chk_units.setChecked(c["convert_units"])
        self.sp_delay.setValue(c["delay_ms"])
        self.sp_threads.setValue(c["threads"])
        self.sp_batch.setValue(c.get("batch_size", 1))
        self.chk_dry.setChecked(c["dry_run"])
        self.chk_bsa.setChecked(c["extract_bsa"])
        self.chk_report.setChecked(c["gen_report"])
        self.ed_openai_url.setText(c["openai_url"])
        self.ed_openai_model.setText(c["openai_model"])
        self.ed_openai_key.setText(c["openai_key"])
        self.ed_ollama_url.setText(c["ollama_url"])
        self.ed_ollama_model.setText(c["ollama_model"])
        self.ed_lm_url.setText(c["lmstudio_url"])
        self.ed_lm_model.setText(c["lmstudio_model"])
        self.ed_or_key.setText(c["openrouter_key"])
        self.ed_or_model.setText(c["openrouter_model"])
        self.ed_deepl.setText(c["deepl_key"])
        self.ed_yandex.setText(c["yandex_key"])
        self.sp_temp.setValue(c["temperature"])
        self.sp_maxtok.setValue(c["max_tokens"])
        self.txt_prompt.setPlainText(c["system_prompt"])
        self.ed_folder.setText(c["out_folder"])
        self.ed_name.setText(c.get("out_name", ""))
        self.chk_zip.setChecked(c["save_zip"])
        self.chk_dsd.setChecked(c.get("save_dsd", True))
        self.chk_risky.setChecked(c.get("allow_risky", False))
        self.chk_pex.setChecked(c.get("translate_pex", False))
        self.chk_skse.setChecked(c.get("translate_skse_menu", False))
        self.chk_permod.setChecked(c.get("per_mod_save", False))
        self.chk_inplace.setChecked(c.get("in_place", False))
        self.chk_notify.setChecked(c.get("notify_done", True))
        shown = set(c.get("status_filter") or ["done", "stale", "ja", "todo", "none"])
        for code, cb in self.chk_states.items():
            cb.blockSignals(True)
            cb.setChecked(code in shown)
            cb.blockSignals(False)
        self.chk_inplace.toggled.connect(self._sync_risky)
        self.chk_risky.toggled.connect(self._sync_risky)
        self.chk_pex.toggled.connect(self._on_pex_toggled)
        self.chk_skse.toggled.connect(self._on_pex_toggled)
        self._sync_risky()
        self._gloss_reload()

    def _on_pex_toggled(self, *_):
        """.pex / SKSE メニューを対象にするかで「状態」列の判定が変わるので、判定し直す。"""
        if getattr(self, "running", False) or not getattr(self, "mods", None):
            return
        self._compute_statuses()
        self._fill_mod_table()

    def _sync_risky(self, *_):
        """安全モード（危険な形式オフ）では .esp は DSD 出力に固定。"""
        safe = not self.chk_risky.isChecked()
        inplace = self.chk_inplace.isChecked() if hasattr(self, "chk_inplace") else False
        if safe or inplace:
            self.chk_dsd.setChecked(True)
        self.chk_dsd.setEnabled(not (safe or inplace))
        for w in (self.ed_folder, self.btn_browse, self.ed_name, self.chk_zip, self.chk_permod):
            w.setEnabled(not inplace)

    # ── UI ─────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 8)
        root.setSpacing(7)

        top = QtWidgets.QHBoxLayout()
        top.setSpacing(6)
        t = QtWidgets.QLabel("MO2 Translation Tool")
        t.setObjectName("title")
        v = QtWidgets.QLabel(f"v{APP_VERSION}")
        v.setObjectName("ver")
        top.addWidget(t)
        top.addWidget(v)
        top.addSpacing(12)

        def combo_label(key):
            l = QtWidgets.QLabel()
            l.setObjectName("hint")
            l.setProperty("tr", key)
            return l

        self._top_labels = []
        self.cb_backend = QtWidgets.QComboBox()
        self.cb_backend.addItems(BACKENDS)
        self.cb_src = QtWidgets.QComboBox()
        for code, name in LANGS:
            self.cb_src.addItem(f"{code} · {name}", code)
        self.cb_tgt = QtWidgets.QComboBox()
        for code, name in LANGS:
            self.cb_tgt.addItem(f"{code} · {name}", code)
        self.cb_enc = QtWidgets.QComboBox()
        self.cb_enc.addItems(ENCODINGS)
        self.cb_uilang = QtWidgets.QComboBox()
        self.cb_uilang.addItems(["RU", "EN", "JA"])
        self.cb_uilang.currentTextChanged.connect(self._on_uilang)

        for lbl_key, w in (("backend", self.cb_backend), ("source", self.cb_src),
                           ("target", self.cb_tgt), ("encoding", self.cb_enc),
                           ("lang_ui", self.cb_uilang)):
            l = combo_label(lbl_key)
            self._top_labels.append((l, lbl_key))
            top.addWidget(l)
            top.addWidget(w)
        top.addStretch(1)
        self.chk_api = QtWidgets.QCheckBox()
        self.chk_api.setChecked(False)
        self.chk_api.toggled.connect(self._toggle_api_dialog)
        self._top_labels.append((self.chk_api, "show_api"))
        top.addWidget(self.chk_api)
        root.addLayout(top)

        # ── Панель настроек перевода ──────────────────────────────────────
        g1 = QtWidgets.QFrame()
        g1.setObjectName("panel")
        gl = QtWidgets.QGridLayout(g1)
        gl.setContentsMargins(10, 8, 10, 8)
        gl.setHorizontalSpacing(10)
        self.lbl_trset = QtWidgets.QLabel()
        self.lbl_trset.setObjectName("group")
        self._tr_lbl(self.lbl_trset, "tr_settings")
        gl.addWidget(self.lbl_trset, 0, 0, 1, 10)

        self.chk_units = QtWidgets.QCheckBox()
        self.chk_delay_l = QtWidgets.QLabel()
        self.chk_delay_l.setObjectName("hint")
        self.sp_delay = QtWidgets.QSpinBox()
        self.sp_delay.setRange(0, 10000)

        self.chk_threads_l = QtWidgets.QLabel()
        self.chk_threads_l.setObjectName("hint")
        self.sp_threads = QtWidgets.QSpinBox()
        self.sp_threads.setRange(1, 8)

        self.lbl_batch = QtWidgets.QLabel()
        self.lbl_batch.setObjectName("hint")
        self.sp_batch = QtWidgets.QSpinBox()
        self.sp_batch.setRange(1, 100)
        self.sp_batch.setToolTip(
            _tx("Сколько строк отправлять в LLM за один запрос. "
            "Для локальных моделей рекомендуется 1-3.", "1回のリクエストで LLM に送る行数。ローカルモデルでは 1〜3 を推奨。"))

        self.chk_dry = QtWidgets.QCheckBox()
        self.chk_bsa = QtWidgets.QCheckBox()
        self.chk_report = QtWidgets.QCheckBox()
        self.chk_risky = QtWidgets.QCheckBox()
        self.chk_pex = QtWidgets.QCheckBox()
        self.chk_skse = QtWidgets.QCheckBox()

        for w, k in ((self.chk_units, "convert_units"),
                     (self.chk_delay_l, "delay"),
                     (self.chk_threads_l, "threads"),
                     (self.lbl_batch, "batch"),
                     (self.chk_dry, "dry_run"),
                     (self.chk_bsa, "extract_bsa"),
                     (self.chk_report, "gen_report"),
                     (self.chk_risky, "allow_risky"),
                     (self.chk_pex, "translate_pex"),
                     (self.chk_skse, "translate_skse_menu")):
            self._tr_lbl(w, k)

        gl.addWidget(self.chk_units, 1, 0)
        gl.addWidget(self.chk_delay_l, 1, 1)
        gl.addWidget(self.sp_delay, 1, 2)
        gl.addWidget(self.chk_threads_l, 1, 3)
        gl.addWidget(self.sp_threads, 1, 4)
        gl.addWidget(self.lbl_batch, 1, 5)
        gl.addWidget(self.sp_batch, 1, 6)
        gl.addWidget(self.chk_dry, 1, 7)
        gl.addWidget(self.chk_bsa, 1, 8)
        gl.addWidget(self.chk_report, 1, 9)
        gl.addWidget(self.chk_risky, 2, 0, 1, 10)
        gl.addWidget(self.chk_pex, 3, 0, 1, 10)
        gl.addWidget(self.chk_skse, 4, 0, 1, 10)
        root.addWidget(g1)

        # ── Панель API ────────────────────────────────────────────────────
        self.api_panel = QtWidgets.QFrame()
        self.api_panel.setObjectName("panel")
        ag = QtWidgets.QGridLayout(self.api_panel)
        ag.setContentsMargins(10, 8, 10, 8)
        ag.setHorizontalSpacing(8)
        ag.setVerticalSpacing(6)
        self.lbl_api = QtWidgets.QLabel()
        self.lbl_api.setObjectName("group")
        self._tr_lbl(self.lbl_api, "api_settings")
        ag.addWidget(self.lbl_api, 0, 0, 1, 6)

        self.ed_openai_url = QtWidgets.QLineEdit()
        self.ed_openai_model = QtWidgets.QLineEdit()
        self.ed_openai_key = QtWidgets.QLineEdit()
        self.ed_openai_key.setEchoMode(ECHO_PASSWORD)
        self.ed_ollama_url = QtWidgets.QLineEdit()
        self.ed_ollama_model = QtWidgets.QLineEdit()
        self.ed_lm_url = QtWidgets.QLineEdit()
        self.ed_lm_model = QtWidgets.QLineEdit()
        self.ed_or_key = QtWidgets.QLineEdit()
        self.ed_or_key.setEchoMode(ECHO_PASSWORD)
        self.ed_or_model = QtWidgets.QLineEdit()
        self.ed_deepl = QtWidgets.QLineEdit()
        self.ed_deepl.setEchoMode(ECHO_PASSWORD)
        self.ed_yandex = QtWidgets.QLineEdit()
        self.ed_yandex.setEchoMode(ECHO_PASSWORD)
        self.sp_temp = QtWidgets.QDoubleSpinBox()
        self.sp_temp.setRange(0, 2)
        self.sp_temp.setSingleStep(0.05)
        self.sp_maxtok = QtWidgets.QSpinBox()
        self.sp_maxtok.setRange(64, 16000)

        rows = [
            ("openai_url", self.ed_openai_url, "openai_model", self.ed_openai_model),
            ("ollama_url", self.ed_ollama_url, "openai_model", self.ed_ollama_model),
            ("lmstudio_url", self.ed_lm_url, "openai_model", self.ed_lm_model),
            ("openrouter_key", self.ed_or_key, "openai_model", self.ed_or_model),
        ]
        r = 1
        for k1, w1, k2, w2 in rows:
            l1 = QtWidgets.QLabel()
            l1.setObjectName("hint")
            l2 = QtWidgets.QLabel()
            l2.setObjectName("hint")
            self._tr_lbl(l1, k1)
            self._tr_lbl(l2, k2)
            ag.addWidget(l1, r, 0)
            ag.addWidget(w1, r, 1, 1, 2)
            ag.addWidget(l2, r, 3)
            ag.addWidget(w2, r, 4, 1, 2)
            r += 1
        l_key = QtWidgets.QLabel()
        l_key.setObjectName("hint")
        self._tr_lbl(l_key, "openai_key")
        ag.addWidget(l_key, r, 0)
        ag.addWidget(self.ed_openai_key, r, 1, 1, 2)
        l_dl = QtWidgets.QLabel()
        l_dl.setObjectName("hint")
        self._tr_lbl(l_dl, "deepl_key")
        ag.addWidget(l_dl, r, 3)
        ag.addWidget(self.ed_deepl, r, 4, 1, 2)
        r += 1
        l_ya = QtWidgets.QLabel()
        l_ya.setObjectName("hint")
        self._tr_lbl(l_ya, "yandex_key")
        ag.addWidget(l_ya, r, 0)
        ag.addWidget(self.ed_yandex, r, 1, 1, 2)
        l_t = QtWidgets.QLabel()
        l_t.setObjectName("hint")
        self._tr_lbl(l_t, "temperature")
        ag.addWidget(l_t, r, 3)
        ag.addWidget(self.sp_temp, r, 4)
        l_mt = QtWidgets.QLabel()
        l_mt.setObjectName("hint")
        self._tr_lbl(l_mt, "max_tokens")
        ag.addWidget(l_mt, r, 5)
        ag.addWidget(self.sp_maxtok, r, 6)
        ag.setColumnStretch(1, 1)
        ag.setColumnStretch(4, 1)
        # API 設定は別ウィンドウで開く（メイン画面に差し込むと高さが足りず潰れるため）
        self.api_dialog = QtWidgets.QDialog(self)
        self.api_dialog.setModal(False)
        self.api_dialog.setMinimumWidth(820)
        adl = QtWidgets.QVBoxLayout(self.api_dialog)
        adl.addWidget(self.api_panel)
        trow = QtWidgets.QHBoxLayout()
        self.btn_conn_test = QtWidgets.QPushButton()
        self._tr_lbl(self.btn_conn_test, "conn_test")
        self.btn_conn_test.clicked.connect(self._run_conn_test)
        self.lbl_conn = QtWidgets.QLabel("")
        self.lbl_conn.setWordWrap(True)
        self.lbl_conn.setTextInteractionFlags(_pick("Qt.TextInteractionFlag.TextSelectableByMouse",
                                                    "Qt.TextSelectableByMouse"))
        trow.addWidget(self.btn_conn_test, 0)
        trow.addWidget(self.lbl_conn, 1)
        adl.addLayout(trow)
        adl.addStretch(1)
        api_btns = QtWidgets.QDialogButtonBox(BTN_OK)
        api_btns.accepted.connect(self.api_dialog.accept)
        adl.addWidget(api_btns)
        self.api_dialog.finished.connect(lambda _r: (self.chk_api.setChecked(False), self._save_settings()))

        # ── Системный промпт ──────────────────────────────────────────────
        self.lbl_prompt = QtWidgets.QLabel()
        self.lbl_prompt.setObjectName("group")
        self._tr_lbl(self.lbl_prompt, "sys_prompt")
        prow = QtWidgets.QHBoxLayout()
        prow.addWidget(self.lbl_prompt)
        prow.addStretch(1)
        self.btn_reset = QtWidgets.QPushButton()
        self._tr_lbl(self.btn_reset, "reset_default")
        self.btn_reset.clicked.connect(
            lambda: self.txt_prompt.setPlainText(DEFAULT_SYSTEM_PROMPT))
        prow.addWidget(self.btn_reset)
        root.addLayout(prow)
        self.txt_prompt = QtWidgets.QPlainTextEdit()
        self.txt_prompt.setObjectName("prompt")
        self.txt_prompt.setFixedHeight(110)
        root.addWidget(self.txt_prompt)

        # ── Список модов ──────────────────────────────────────────────────
        mrow = QtWidgets.QHBoxLayout()
        self.ed_search = QtWidgets.QLineEdit()
        self.ed_search.setPlaceholderText(self.tr("search_mods"))
        self.ed_search.textChanged.connect(self._filter_mods)
        mrow.addWidget(self.ed_search, 1)
        self.btn_all = QtWidgets.QPushButton()
        self.btn_none = QtWidgets.QPushButton()
        self.btn_todo = QtWidgets.QPushButton()
        self.btn_refresh = QtWidgets.QPushButton()
        self.btn_addf = QtWidgets.QPushButton()
        self.btn_openfile = QtWidgets.QPushButton()
        self.btn_sst = QtWidgets.QPushButton()
        for b, k in ((self.btn_all, "select_all"), (self.btn_none, "select_none"), (self.btn_todo, "select_todo"),
                     (self.btn_refresh, "refresh"), (self.btn_addf, "add_folders"),
                     (self.btn_openfile, "btn_open_file"), (self.btn_sst, "btn_load_sst")):
            self._tr_lbl(b, k)
        self._build_sst_menu()
        self.btn_all.clicked.connect(lambda: self._set_all_mods(True))
        self.btn_none.clicked.connect(lambda: self._set_all_mods(False))
        self.btn_todo.clicked.connect(self._select_todo_mods)
        self.btn_refresh.clicked.connect(self.refresh_mods)
        self.btn_addf.clicked.connect(self.add_folders)
        self.btn_openfile.clicked.connect(self.open_single_file)
        for b in (self.btn_all, self.btn_none, self.btn_todo, self.btn_refresh, self.btn_addf,
                  self.btn_openfile, self.btn_sst):
            mrow.addWidget(b)
        root.addLayout(mrow)

        srow = QtWidgets.QHBoxLayout()
        self.lbl_show_states = QtWidgets.QLabel()
        self.lbl_show_states.setObjectName("hint")
        self._tr_lbl(self.lbl_show_states, "show_states")
        srow.addWidget(self.lbl_show_states)
        self.chk_states = {}
        for code in ("todo", "stale", "done", "ja", "none"):
            cb = QtWidgets.QCheckBox()
            cb.setChecked(True)
            cb.setStyleSheet(f"QCheckBox {{ color: {C[self._STATUS_COLORS.get(code, 'text')]}; }}")
            cb.toggled.connect(lambda _on: self._fill_mod_table())
            self.chk_states[code] = cb
            srow.addWidget(cb)
        srow.addStretch(1)
        self.lbl_mod_count = QtWidgets.QLabel("")
        self.lbl_mod_count.setObjectName("hint")
        srow.addWidget(self.lbl_mod_count)
        root.addLayout(srow)

        self.mod_table = QtWidgets.QTableWidget(0, 7)
        self.mod_table.setHorizontalHeaderLabels(["", "Mod", "P", "S", "T", "X", "State"])
        h = self.mod_table.horizontalHeader()
        h.setSectionResizeMode(0, HDR_FIXED)
        h.setSectionResizeMode(1, HDR_STRETCH)
        for c in (2, 3, 4, 5, 6):
            h.setSectionResizeMode(c, HDR_CONTENTS)
        self.mod_table.setColumnWidth(0, 30)
        self.mod_table.setSelectionBehavior(SEL_ROWS)
        self.mod_table.verticalHeader().setVisible(False)
        self.mod_table.setEditTriggers(NO_EDIT)
        self.mod_table.itemChanged.connect(self._mod_checked)
        self.mod_table.cellDoubleClicked.connect(self._on_mod_double_clicked)
        # 読み込み中・表示する Mod がないときに、一覧の上に重ねて出すメッセージ
        self.mod_overlay = QtWidgets.QLabel(self.mod_table.viewport())
        self.mod_overlay.setObjectName("hint")
        self.mod_overlay.setAlignment(ALIGN_CENTER)
        self.mod_overlay.setWordWrap(True)
        self.mod_overlay.hide()
        self.mod_table.viewport().installEventFilter(self)
        self._mods_loading = False
        root.addWidget(self.mod_table, 2)

        # ── Вкладки ───────────────────────────────────────────────────────
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setTabPosition(TAB_N)

        self.log = QtWidgets.QPlainTextEdit()
        self.log.setObjectName("log")
        self.log.setReadOnly(True)
        self.tabs.addTab(self.log, "Log")

        # Создаем контейнер для вкладки "Предпросмотр"
        preview_widget = QtWidgets.QWidget()
        preview_layout = QtWidgets.QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(4, 4, 4, 4)

        # 1. Панель поиска и фильтров
        filter_layout = QtWidgets.QHBoxLayout()
        
        self.ed_preview_search = QtWidgets.QLineEdit()
        self.ed_preview_search.setPlaceholderText(_tx("Поиск по оригиналу или переводу...", "原文・訳文を検索..."))
        self.ed_preview_search.textChanged.connect(self._filter_preview_table)
        
        filter_layout.addWidget(self.ed_preview_search, 1)
        
        # Кнопка замены
        self.btn_replace = QtWidgets.QPushButton(self.tr("btn_replace"))
        self.btn_replace.clicked.connect(self._open_replace_dialog)
        filter_layout.addWidget(self.btn_replace)
        
        # Фильтр по файлу: изолирует строки одного файла в таблице предпросмотра
        self.cb_file_filter = QtWidgets.QComboBox()
        self.cb_file_filter.addItem(self.tr("all_files"))
        self.cb_file_filter.currentIndexChanged.connect(self._filter_preview_table)
        filter_layout.addWidget(self.cb_file_filter)

        # Фильтр
        self.cb_preview_filter = QtWidgets.QComboBox()
        self._update_filter_combo() # Заполняем список фильтров
        self.cb_preview_filter.currentIndexChanged.connect(self._filter_preview_table)
        filter_layout.addWidget(self.cb_preview_filter)
        
        preview_layout.addLayout(filter_layout)

        # 2. Сама таблица
        self.prev_table = QtWidgets.QTableWidget(0, 5)
        self.prev_table.setHorizontalHeaderLabels(["#", "File", "Original",
                                                   "Translation", "Status"])
        ph = self.prev_table.horizontalHeader()
        ph.setSectionResizeMode(0, HDR_FIXED)
        ph.setSectionResizeMode(1, HDR_INTERACTIVE) # <--- Теперь можно тянуть мышкой
        ph.setSectionResizeMode(2, HDR_STRETCH)
        ph.setSectionResizeMode(3, HDR_STRETCH)
        ph.setSectionResizeMode(4, HDR_FIXED)
        self.prev_table.setColumnWidth(0, 44)
        self.prev_table.setColumnWidth(1, 250) # <--- Задаем стартовую ширину для файлов
        self.prev_table.setColumnWidth(4, 70)
        self.prev_table.setSelectionBehavior(SEL_ROWS)
        self.prev_table.verticalHeader().setVisible(False)
        self.prev_table.setEditTriggers(EDIT_DBL | EDIT_SEL)
        self.prev_table.cellChanged.connect(self._preview_edited)
        
        self.prev_table.setSelectionMode(SEL_MULTI)
        self._space_shortcut = QShortcut(QKeySequence("Space"), self.prev_table)
        self._space_shortcut.activated.connect(self._toggle_selected_rows)
        self.prev_table.setContextMenuPolicy(CTX_MENU)
        self.prev_table.customContextMenuRequested.connect(self._preview_context_menu)
        self._copy_shortcut = QShortcut(KEY_COPY, self.prev_table)
        self._copy_shortcut.activated.connect(self._copy_selected_text)

        self._loading_preview = False
        preview_layout.addWidget(self.prev_table)

        # 3. Добавляем готовую вкладку
        self.tabs.addTab(preview_widget, "Preview")

        gloss_w = QtWidgets.QWidget()
        gv = QtWidgets.QVBoxLayout(gloss_w)
        gv.setContentsMargins(6, 6, 6, 6)
        self.gloss_hint = QtWidgets.QLabel()
        self.gloss_hint.setObjectName("hint")
        self.gloss_hint.setWordWrap(True)
        self._tr_lbl(self.gloss_hint, "gloss_hint")
        gv.addWidget(self.gloss_hint)
        gtop = QtWidgets.QHBoxLayout()
        self.ed_g_src = QtWidgets.QLineEdit()
        self.ed_g_dst = QtWidgets.QLineEdit()
        self.btn_g_add = QtWidgets.QPushButton()
        self.btn_g_del = QtWidgets.QPushButton()
        self._tr_lbl(self.btn_g_add, "gloss_add")
        self._tr_lbl(self.btn_g_del, "gloss_del")
        self.ed_g_src.setPlaceholderText("Dragonborn")
        self.ed_g_dst.setPlaceholderText(_tx("Довакин", "ドヴァーキン"))
        gtop.addWidget(self.ed_g_src, 1)
        gtop.addWidget(self.ed_g_dst, 1)
        gtop.addWidget(self.btn_g_add)
        gtop.addWidget(self.btn_g_del)
        gv.addLayout(gtop)
        self.gloss_table = QtWidgets.QTableWidget(0, 2)
        self.gloss_table.setHorizontalHeaderLabels(["Source", "Target"])
        self.gloss_table.horizontalHeader().setSectionResizeMode(HDR_STRETCH)
        self.gloss_table.verticalHeader().setVisible(False)
        self.gloss_table.setEditTriggers(EDIT_DBL | EDIT_SEL)
        self.gloss_table.cellChanged.connect(self._gloss_edited)
        gv.addWidget(self.gloss_table, 1)
        self.btn_g_add.clicked.connect(self._gloss_add)
        self.btn_g_del.clicked.connect(self._gloss_del)
        self.tabs.addTab(gloss_w, "Glossary")
        root.addWidget(self.tabs, 3)

        # ── Настройки вывода ──────────────────────────────────────────────
        out_f = QtWidgets.QFrame()
        out_f.setObjectName("panel")
        ol = QtWidgets.QGridLayout(out_f)
        ol.setContentsMargins(10, 8, 10, 8)
        self.lbl_out = QtWidgets.QLabel()
        self.lbl_out.setObjectName("group")
        self._tr_lbl(self.lbl_out, "out_settings")
        ol.addWidget(self.lbl_out, 0, 0, 1, 7)
        self.lbl_folder = QtWidgets.QLabel()
        self.lbl_folder.setObjectName("hint")
        self._tr_lbl(self.lbl_folder, "folder")
        self.ed_folder = QtWidgets.QLineEdit()
        self.btn_browse = QtWidgets.QPushButton()
        self._tr_lbl(self.btn_browse, "browse")
        self.btn_browse.clicked.connect(self._browse_out)
        self.lbl_name = QtWidgets.QLabel()
        self.lbl_name.setObjectName("hint")
        self._tr_lbl(self.lbl_name, "mod_name")
        self.ed_name = QtWidgets.QLineEdit()
        self.chk_zip = QtWidgets.QCheckBox()
        self._tr_lbl(self.chk_zip, "save_zip")
        self.chk_dsd = QtWidgets.QCheckBox()
        self._tr_lbl(self.chk_dsd, "save_dsd")
        self.chk_permod = QtWidgets.QCheckBox()
        self._tr_lbl(self.chk_permod, "per_mod_save")
        self.chk_inplace = QtWidgets.QCheckBox()
        self._tr_lbl(self.chk_inplace, "in_place")
        self.ed_name.textEdited.connect(lambda _t: setattr(self, "_name_manual", True))
        self.cb_tgt.currentIndexChanged.connect(lambda _i: self._sync_out_name())
        ol.addWidget(self.lbl_folder, 1, 0)
        ol.addWidget(self.ed_folder, 1, 1, 1, 2)
        ol.addWidget(self.btn_browse, 1, 3)
        ol.addWidget(self.lbl_name, 1, 4)
        ol.addWidget(self.ed_name, 1, 5)
        ol.addWidget(self.chk_zip, 1, 6)
        ol.addWidget(self.chk_dsd, 2, 1)
        ol.addWidget(self.chk_permod, 2, 5, 1, 2)
        ol.addWidget(self.chk_inplace, 2, 2, 1, 3)
        self.chk_notify = QtWidgets.QCheckBox()
        self._tr_lbl(self.chk_notify, "notify_done")
        ol.addWidget(self.chk_notify, 3, 1, 1, 4)
        ol.setColumnStretch(1, 1)
        root.addWidget(out_f)

        # ── Прогресс ──────────────────────────────────────────────────────
        pr = QtWidgets.QHBoxLayout()
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 1000)
        self.lbl_progress = QtWidgets.QLabel("")
        self.lbl_progress.setObjectName("statusmsg")
        self.lbl_progress.setMinimumWidth(230)
        pr.addWidget(self.progress, 1)
        pr.addWidget(self.lbl_progress)
        root.addLayout(pr)
        # 全体の進み具合（複数 Mod を1つずつ処理するときだけ表示）
        pr2 = QtWidgets.QHBoxLayout()
        self.progress_all = QtWidgets.QProgressBar()
        self.progress_all.setRange(0, 1)
        self.progress_all.setFormat("%v / %m")
        self.lbl_progress_all = QtWidgets.QLabel("")
        self.lbl_progress_all.setObjectName("statusmsg")
        self.lbl_progress_all.setMinimumWidth(230)
        pr2.addWidget(self.progress_all, 1)
        pr2.addWidget(self.lbl_progress_all)
        root.addLayout(pr2)
        self.progress_all.setVisible(False)
        self.lbl_progress_all.setVisible(False)
        self._overall_t0 = 0.0
        self._overall_last = 0.0

        # ── Кнопки ────────────────────────────────────────────────────────
        br = QtWidgets.QHBoxLayout()
        self.btn_translate = QtWidgets.QPushButton()
        self.btn_translate.setObjectName("primary")
        self.btn_save = QtWidgets.QPushButton()
        self.btn_cancel = QtWidgets.QPushButton()
        self.btn_cancel.setObjectName("danger")
        self.btn_openout = QtWidgets.QPushButton()
        self.btn_close = QtWidgets.QPushButton()
        for b, k in ((self.btn_translate, "btn_translate"),
                     (self.btn_save, "btn_save"),
                     (self.btn_cancel, "btn_cancel"),
                     (self.btn_openout, "btn_open_out"),
                     (self.btn_close, "btn_close")):
            self._tr_lbl(b, k)
        self.btn_translate.clicked.connect(self.start_translation)
        self.btn_save.clicked.connect(self.save_output)
        self.btn_cancel.clicked.connect(self.cancel_translation)
        self.btn_openout.clicked.connect(self._open_out)
        self.btn_close.clicked.connect(self.close)
        for b in (self.btn_translate, self.btn_save, self.btn_cancel,
                  self.btn_openout, self.btn_close):
            br.addWidget(b)
        br.addStretch(1)
        self.btn_save.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        root.addLayout(br)

        self._relabel_headers()

    # ── журнал ─────────────────────────────────────────────────────────────
    def _log(self, level, text):
        # Qt の部品は GUI スレッド以外から触ると落ちる（Qt6Gui.dll のアクセス違反）。
        # 翻訳スレッドからの呼び出し（Translator.log 等）はキュー経由で _poll に回す。
        if QtCore.QThread.currentThread() is not self.thread() and \
                QtCore.QThread.currentThread() != self.thread():
            self.q.put(("log", level, text))
            return
        doc = self.log.document()
        if doc.blockCount() > 5000:
            cur = self.log.textCursor()
            cur.movePosition(CURSOR_START)
            cur.movePosition(CURSOR_DOWN, KEEP_ANCHOR, 1000)
            cur.removeSelectedText()
        colors = {"info": C["dim"], "ok": C["ok"],
                  "warn": C["accent"], "err": C["err"]}
        cur = self.log.textCursor()
        cur.movePosition(CURSOR_END)
        fmt = QtGui.QTextCharFormat()
        fmt.setForeground(QtGui.QBrush(QtGui.QColor(colors.get(level, C["dim"]))))
        cur.setCharFormat(fmt)
        cur.insertText(f"[{time.strftime('%H:%M:%S')}] {text}\n")
        self.log.setTextCursor(cur)
        self.log.ensureCursorVisible()

    # ── моды ───────────────────────────────────────────────────────────────
    def eventFilter(self, obj, ev):
        if getattr(self, "mod_overlay", None) is not None and obj is self.mod_table.viewport() \
                and ev.type() == EV_RESIZE:
            self.mod_overlay.setGeometry(obj.rect())
        return super().eventFilter(obj, ev)

    def _set_mod_overlay(self, text=None):
        """Mod 一覧の上にメッセージを重ねて表示する（None で消す）。"""
        ov = getattr(self, "mod_overlay", None)
        if ov is None:
            return
        if text:
            ov.setText(text)
            ov.setGeometry(self.mod_table.viewport().rect())
            ov.show()
            ov.raise_()
        else:
            ov.hide()

    def _loading_progress(self, step, i, n):
        if self._mods_loading:
            self._set_mod_overlay(_tx(f"Загрузка модов… {step} {i}/{n}",
                                      f"Mod を読み込み中…\n{step} {i} / {n}"))

    def _update_empty_overlay(self):
        """読み込みが終わって 1 行も表示されていなければ、理由を表示する。"""
        if self._mods_loading:
            return
        if self.mod_table.rowCount() or not self.mods:
            self._set_mod_overlay(None)
            return
        shown = [self.tr("st_" + c) for c in ("done", "stale", "ja", "todo", "none") if c in self._shown_states()]
        if self.ed_search.text().strip():
            msg = _tx("Нет модов, подходящих под поиск.", "検索に一致する Mod がありません。")
        else:
            msg = _tx("Нет модов в выбранных состояниях.",
                      "表示中の状態（" + ("・".join(shown) or "なし") + "）の Mod はありません。\n"
                      "上の状態のチェックで、ほかの状態の Mod も表示できます。")
        self._set_mod_overlay(msg)

    def refresh_mods(self):
        self._pending_units = None
        self.mods = []
        self._mods_loading = True
        self.mod_table.setRowCount(0)
        self._set_mod_overlay(_tx("Загрузка списка модов…", "Mod 一覧を読み込み中…"))
        QtWidgets.QApplication.processEvents()
        try:
            self._refresh_mods_inner()
        finally:
            self._mods_loading = False
            self._set_mod_overlay(None)
            self._update_empty_overlay()

    def _refresh_mods_inner(self):
        org = getattr(self.plugin, "_organizer", None)
        if org is None:
            self._log("warn", _tx("MO2 недоступен — список модов пуст.", "MO2 にアクセスできません — Mod 一覧は空です。"))
            return
        try:
            self._mods_root = os.path.normcase(os.path.abspath(org.modsPath()))
        except Exception:
            self._mods_root = None
        try:
            names = org.modList().allMods()
        except Exception as e:
            self._log("err", _tx(f"Ошибка списка модов: {e}", f"Mod 一覧の取得エラー: {e}"))
            return
        for nm in names:
            try:
                path = org.modList().getMod(nm).absolutePath()
            except Exception:
                continue
            if not os.path.isdir(path):
                continue
            try:
                active = bool(int(org.modList().state(nm)) & int(mobase.ModState.ACTIVE))
            except Exception:
                active = True
            mods_root = getattr(self, "_mods_root", None)
            external = bool(mods_root) and \
                os.path.dirname(os.path.normcase(os.path.abspath(path))) != mods_root
            self.mods.append({"name": nm, "path": path, "active": active, "external": external,
                              "counts": {"plugins": 0, "strings": 0,
                                         "translations": 0, "json": 0, "xml": 0, "ini": 0},
                              "selected": False, "scanned": False})
        self._scan_counts()
        self._fill_mod_table()
        self._sync_out_name()
        self._log("ok", _tx(f"Найдено {len(self.mods)} модов.", f"{len(self.mods)} 個の Mod が見つかりました。"))

    def _scan_counts(self):
        """Быстрый подсчёт файлов для таблицы (без чтения BSA/BA2)."""
        for i, m in enumerate(self.mods):
            if m.get("external"):
                m["counts"] = {"plugins": 0, "strings": 0, "translations": 0, "json": 0, "xml": 0, "ini": 0}
                m["scanned"] = True
                continue
            try:
                counts = {"plugins": 0, "strings": 0, "translations": 0, "json": 0, "xml": 0, "ini": 0}
                for dp, _d, fs in os.walk(m["path"]):
                    rel = os.path.relpath(dp, m["path"]).replace("\\", "/").lower()
                    for fn in fs:
                        ext = os.path.splitext(fn)[1].lower()
                        if ext in (".esp", ".esm", ".esl"):
                            counts["plugins"] += 1
                        elif ext in STRING_EXTS:
                            counts["strings"] += 1
                        elif ext == ".json":
                            counts["json"] += 1
                        elif ext == ".txt" and "translations" in rel:
                            counts["translations"] += 1
                        elif ext == ".xml":
                            counts["xml"] += 1                            
                        elif ext == ".ini":
                            counts["ini"] += 1
                m["counts"] = counts
                m["scanned"] = True
            except Exception:
                pass
            if i % 50 == 0:
                self._loading_progress(_tx("файлы", "ファイルを確認中"), i, len(self.mods))
                QtWidgets.QApplication.processEvents()
        self._compute_statuses()

    def _compute_statuses(self, mods=None):
        """Mod ごとの翻訳状態（状態列）を判定する。"""
        tgt = self.cb_tgt.currentData() or "ja"
        src = self.cb_src.currentData() or "en"
        covered = set()
        for m in self.mods:
            if not m.get("active", True):
                continue
            dd = os.path.join(m["path"], "SKSE", "Plugins", "DynamicStringDistributor")
            if os.path.isdir(dd):
                try:
                    for x in os.listdir(dd):
                        sub = os.path.join(dd, x)
                        if not os.path.isdir(sub):
                            continue
                        # 他 Mod の DSD のうち、中身が翻訳先言語のものだけを数える
                        # （自分の出力は記録ファイル側で管理。Mod 自身が英語の台詞を DSD で入れている場合は数えない）
                        for fn in os.listdir(sub):
                            fl = fn.lower()
                            if not fl.endswith(".json") or fl.startswith("mo2translationtool_"):
                                continue
                            try:
                                with open(os.path.join(sub, fn), "rb") as f:
                                    head = f.read(1_000_000).decode("utf-8", "replace")
                            except OSError:
                                continue
                            if already_in_target(head, tgt, src):
                                covered.add(x.lower())
                                break
                except OSError:
                    pass
        self._dsd_covered = frozenset(covered)
        for i, m in enumerate(mods if mods is not None else self.mods):
            if m.get("external"):
                m["status"] = "none"
                m["status_detail"] = _tx("Вне управления MO2 (DLC / Creation Club)",
                                         "MO2 の管理外（本体 DLC / Creation Club など）。公式の日本語訳があるので対象外です")
                continue
            try:
                m["status"], m["status_detail"] = compute_mod_status(
                    m["path"], m["name"], tgt, src, self._dsd_covered,
                    include_pex=self.chk_pex.isChecked(),
                    include_skse_menu=self.chk_skse.isChecked())
            except Exception as e:
                m["status"], m["status_detail"] = "todo", f"判定エラー: {e}"
            if i % 50 == 0:
                self._loading_progress(_tx("состояние", "翻訳状態を判定中"), i, len(self.mods))
                QtWidgets.QApplication.processEvents()

    def add_folders(self):
        self._pending_units = None
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, self.tr("add_folders"), os.path.expanduser("~"))
        if not path:
            return
        self.mods.append({"name": os.path.basename(path), "path": path,
                          "counts": {"plugins": 0, "strings": 0,
                                         "translations": 0, "json": 0, "xml": 0, "ini": 0},
                          "selected": True, "scanned": False})
        self._scan_counts()
        self._fill_mod_table()
        self._sync_out_name()

    # ── Словарь терминов .sst (Skyrim String Translator / xTranslator) ─────
    # 読み込んだファイル・フォルダは cfg["sst_paths"] に保存し、次回起動時に自動で読み込む。
    # フォルダは毎回中身を探し直すので、xTranslator の UserDictionaries を指定しておけば
    # 後から増えた辞書も拾える。
    _parse_sst_line = staticmethod(_sst_parse_line)
    _decode_sst = staticmethod(_sst_decode_text)

    def _sst_lookup(self, src):
        """Точное совпадение со словарём .sst (плюс вариант без пробелов по краям)."""
        if not self.sst_dict:
            return None
        res = self.sst_dict.get(src)
        if res is None:
            s = src.strip()
            if s and s != src:
                res = self.sst_dict.get(s)
                if res is not None:   # 前後の空白は原文のまま残す
                    res = src[:len(src) - len(src.lstrip())] + res + src[len(src.rstrip()):]
        return res

    def _build_sst_menu(self):
        m = QtWidgets.QMenu(self.btn_sst)
        m.addAction(self.tr("sst_add_files"), self._sst_add_files)
        m.addAction(self.tr("sst_add_folder"), self._sst_add_folder)
        m.addSeparator()
        m.addAction(self.tr("sst_reload"), lambda: self._sst_reload(interactive=True))
        m.addAction(self.tr("sst_clear"), self._sst_clear)
        m.addSeparator()
        act = m.addAction(self.tr("sst_hints"))
        act.setCheckable(True)
        act.setChecked(bool(self.cfg.get("sst_hints", True)))
        act.setToolTip(self.tr("tip_sst_hints"))
        act.toggled.connect(self._sst_set_hints)
        m.setToolTipsVisible(True)
        self.btn_sst.setMenu(m)

    def _sst_set_hints(self, on):
        self.cfg["sst_hints"] = bool(on)
        save_config(self.cfg, self._log)
        self._sst_update_tip()

    def _sst_hint_terms(self):
        """翻訳開始時に Translator へ渡す用語ヒント（オフなら空）。"""
        if not self.cfg.get("sst_hints", True) or not self.sst_dict:
            return {}
        if getattr(self, "_sst_terms_src", None) is not self.sst_dict or self._sst_terms_n != len(self.sst_dict):
            self._sst_terms = build_sst_terms(self.sst_dict)
            self._sst_terms_src, self._sst_terms_n = self.sst_dict, len(self.sst_dict)
        if self._sst_terms:
            self._log("info", self.tr("sst_hints_on").format(n=len(self._sst_terms)))
        return self._sst_terms

    def _sst_update_tip(self):
        if not hasattr(self, "btn_sst"):
            return
        tip = self.tr("tip_load_sst")
        paths = self.cfg.get("sst_paths") or []
        tip += "\n\n" + self.tr("sst_status").format(total=len(self.sst_dict), files=len(self.sst_files))
        if self.cfg.get("sst_hints", True):
            tip += "\n" + self.tr("sst_hints")
        if paths:
            tip += "\n" + "\n".join(paths[:10]) + ("\n…" if len(paths) > 10 else "")
        self.btn_sst.setToolTip(tip)

    def _sst_start_dir(self):
        paths = self.cfg.get("sst_paths") or []
        if paths:
            last = paths[-1]
            return last if os.path.isdir(last) else os.path.dirname(last)
        return os.path.expanduser("~")

    def _sst_add_files(self):
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, self.tr("btn_load_sst"), self._sst_start_dir(),
            _tx("Skyrim String Translator (*.sst);;Все файлы (*)", "Skyrim String Translator (*.sst);;すべてのファイル (*)"))
        if files:
            self._sst_add_paths(files)

    def _sst_add_folder(self):
        d = QtWidgets.QFileDialog.getExistingDirectory(self, self.tr("sst_add_folder"), self._sst_start_dir())
        if d:
            self._sst_add_paths([d])

    # 互換: 以前のボタン処理名
    _load_sst_dictionary = _sst_add_files

    def _sst_add_paths(self, paths):
        paths = [os.path.normpath(p) for p in paths]
        n = self._sst_load(paths, interactive=True)
        if n:
            cur = list(self.cfg.get("sst_paths") or [])
            keys = {os.path.normcase(x) for x in cur}
            cur += [p for p in paths if os.path.normcase(p) not in keys]
            self.cfg["sst_paths"] = cur
            save_config(self.cfg, self._log)
        self._sst_update_tip()

    def _sst_reload(self, interactive=False):
        self.sst_dict = {}
        self.sst_files = []
        paths = self.cfg.get("sst_paths") or []
        if paths:
            self._sst_load(paths, interactive=interactive)
        self._sst_update_tip()

    def _sst_clear(self):
        self.sst_dict = {}
        self.sst_files = []
        self.cfg["sst_paths"] = []
        save_config(self.cfg, self._log)
        self._log("info", self.tr("sst_cleared"))
        self._sst_update_tip()

    def _sst_load(self, paths, interactive=False):
        """ファイル/フォルダを読み込んで self.sst_dict に追加する。追加した語数を返す。

        後から読んだ辞書が同じ原文の訳を上書きする（xTranslator と同じく後勝ち）。
        """
        files, missing = expand_sst_paths(paths)
        for m in missing:
            self._log("warn", f"{self.tr('sst_missing')} {m}")
        added, n_ok, failed = {}, 0, []
        for path in files:
            try:
                with open(path, "rb") as f:
                    raw = f.read()
                pairs, fmt = read_sst_pairs(raw)
            except Exception as e:
                failed.append(f"{os.path.basename(path)}: {e}")
                continue
            if pairs is None:
                reason = self.tr("sst_bad_enc") if fmt == "bad_enc" else self.tr("sst_unknown_fmt")
                failed.append(f"{os.path.basename(path)}: {reason}")
                continue
            n_ok += 1
            added.update(pairs)
            if path not in self.sst_files:
                self.sst_files.append(path)
            if len(files) <= 5:
                self._log("ok", self.tr("sst_loaded").format(
                    n=len(pairs), path=f"{os.path.basename(path)}, {fmt}", total=len(self.sst_dict) + len(added)))
        for msg in failed[:20]:
            self._log("err", f"{self.tr('sst_error')} {msg}")
        if len(failed) > 20:
            self._log("err", f"{self.tr('sst_error')} … +{len(failed) - 20}")
        self.sst_dict.update(added)
        if len(files) > 5 or not files:
            self._log("ok" if added else "warn", self.tr("sst_loaded_many").format(
                files=n_ok, n=len(added), total=len(self.sst_dict)))
        if interactive and not added:
            msg = self.tr("sst_no_pairs") if not failed else "\n".join(failed[:10])
            QtWidgets.QMessageBox.warning(self, self.tr("btn_load_sst"), msg)
        return len(added)

    def _fill_mod_table(self):
        self.mod_table.blockSignals(True)
        self.mod_table.setRowCount(0)
        q = self.ed_search.text().lower()
        shown_states = self._shown_states()
        for m in self.mods:
            if q and q not in m["name"].lower():
                continue
            if m.get("status") and m["status"] not in shown_states:
                continue
            row = self.mod_table.rowCount()
            self.mod_table.insertRow(row)
            chk = QtWidgets.QTableWidgetItem()
            if m.get("external"):
                m["selected"] = False
                chk.setFlags(ITEM_SELECTABLE)
            else:
                chk.setFlags(ITEM_ENABLED | ITEM_SELECTABLE | ITEM_USERCHECK)
            chk.setCheckState(ITEM_CHECKED if m["selected"] else ITEM_UNCHECKED)
            chk.setData(ROLE_USER, m["name"])
            self.mod_table.setItem(row, 0, chk)
            nm = QtWidgets.QTableWidgetItem(m["name"])
            nm.setFlags(ITEM_ENABLED | ITEM_SELECTABLE)
            self.mod_table.setItem(row, 1, nm)
            c = m["counts"]
            for col, val in ((2, c["plugins"]), (3, c["strings"]),
                             (4, c["translations"] + c["json"]),
                             (5, c.get("xml", 0) + c.get("ini", 0))):
                it = QtWidgets.QTableWidgetItem(str(val))
                it.setFlags(ITEM_ENABLED | ITEM_SELECTABLE)
                it.setTextAlignment(ALIGN_CENTER)
                if val:
                    it.setForeground(QtGui.QBrush(QtGui.QColor(C["teal"])))
                self.mod_table.setItem(row, col, it)
            self.mod_table.setItem(row, 6, self._status_item(m))
        self.mod_table.blockSignals(False)
        self._update_state_filter_labels()
        self._update_empty_overlay()

    def _shown_states(self):
        if not hasattr(self, "chk_states"):
            return {"done", "stale", "ja", "todo", "none"}
        return {c for c, cb in self.chk_states.items() if cb.isChecked()}

    def _update_state_filter_labels(self):
        """チェックボックスに状態ごとの件数を表示し、表示中/全体の件数を出す。"""
        if not hasattr(self, "chk_states"):
            return
        cnt = Counter(m.get("status") for m in self.mods)
        for code, cb in self.chk_states.items():
            cb.setText(f"{self.tr('st_' + code)} ({cnt.get(code, 0)})")
        self.lbl_mod_count.setText(_tx(f"Показано {self.mod_table.rowCount()} / {len(self.mods)}",
                                       f"表示 {self.mod_table.rowCount()} / {len(self.mods)}"))

    _STATUS_COLORS = {"done": "ok", "stale": "accent", "ja": "teal", "todo": "text", "none": "dim"}

    def _status_item(self, m):
        code = m.get("status")
        it = QtWidgets.QTableWidgetItem(self.tr(f"st_{code}") if code else "")
        it.setFlags(ITEM_ENABLED | ITEM_SELECTABLE)
        it.setForeground(QtGui.QBrush(QtGui.QColor(C[self._STATUS_COLORS.get(code, "dim")])))
        if m.get("status_detail"):
            it.setToolTip(m["status_detail"])
        return it

    def _update_mod_status_row(self, m):
        for row in range(self.mod_table.rowCount()):
            it = self.mod_table.item(row, 0)
            if it is not None and it.data(ROLE_USER) == m["name"]:
                self.mod_table.blockSignals(True)
                self.mod_table.setItem(row, 6, self._status_item(m))
                self.mod_table.blockSignals(False)
                self._update_state_filter_labels()
                return

    def _select_todo_mods(self):
        n = 0
        for m in self.mods:
            m["selected"] = m.get("status") in ("todo", "stale")
            n += m["selected"]
        self._fill_mod_table()
        self._sync_out_name()
        self._log("info", _tx(f"Выбрано непереведённых: {n}", f"未翻訳・要再翻訳の Mod を {n} 個選択しました"))

    def _filter_mods(self, _t):
        self._fill_mod_table()

    def _mod_checked(self, item):
        if item.column() != 0:
            return
        nm = item.data(ROLE_USER)
        for m in self.mods:
            if m["name"] == nm:
                m["selected"] = item.checkState() == ITEM_CHECKED
        
        self.units = [] # Сбрасываем предпросмотр, так как выбор изменился
        self._sync_out_name()

    def _set_all_mods(self, val):
        # 選択は表示中（検索・状態フィルタで絞った後）の Mod だけ。解除は全 Mod
        visible = {self.mod_table.item(r, 0).data(ROLE_USER)
                   for r in range(self.mod_table.rowCount()) if self.mod_table.item(r, 0)}
        for m in self.mods:
            if val and (m["name"] not in visible or m.get("external")):
                continue
            m["selected"] = val
        self._fill_mod_table()
        self._sync_out_name()
        
    def _on_mod_double_clicked(self, row, col):
        if self.running:
            return
        item = self.mod_table.item(row, 1)
        if not item: return
        
        mod_name = item.text()
        mod = next((m for m in self.mods if m["name"] == mod_name), None)
        if mod:
            mod["selected"] = True
            self.mod_table.blockSignals(True)
            chk = self.mod_table.item(row, 0)
            if chk:
                chk.setCheckState(ITEM_CHECKED)
            self.mod_table.blockSignals(False)
            self._load_mod_preview(mod)
            
    def _run_conn_test(self):
        """選択中のバックエンドに接続し、モデル一覧の取得と1行の試訳を行う（別スレッド）。"""
        if getattr(self, "_conn_testing", False):
            return
        try:
            client = self._build_client()
        except Exception as e:
            self._show_conn_result(False, str(e))
            return
        backend = self.cb_backend.currentText()
        model = getattr(client, "model", "")
        self._conn_testing = True
        self.btn_conn_test.setEnabled(False)
        self.lbl_conn.setStyleSheet(f"color: {C['dim']};")
        self.lbl_conn.setText(_tx("Проверка…", f"{backend} に接続中…"))

        def work():
            ev = threading.Event()
            try:
                lines = []
                if isinstance(client, OpenAIClient):
                    models = openai_list_models(client.base, client.key, timeout=8)
                    lines.append(_tx(f"Соединение OK ({client.base})", f"接続 OK（{client.base}）"))
                    if models:
                        shown = ", ".join(models[:5]) + (" …" if len(models) > 5 else "")
                        lines.append(_tx(f"Модели: {shown}", f"読み込み中のモデル: {shown}"))
                    else:
                        lines.append(_tx("Модели не загружены", "⚠️ モデルが読み込まれていません。LM Studio でモデルをロードしてください。"))
                    if model and models and model not in models and model != "local-model":
                        lines.append(_tx(f"⚠️ Модель «{model}» не найдена",
                                         f"⚠️ 設定のモデル名「{model}」がサーバーにありません。モデル欄を空にするか、上の名前に合わせてください。"))
                    client.timeout, client.retries = 60, 0
                    out = client.chat("Translate the following text from ENGLISH to JAPANESE. "
                                      "Return ONLY the translation.", "Open the door", ev)
                else:
                    out = client.translate_lines(["Open the door"], ev)[0]
                lines.append(_tx(f"Пробный перевод: Open the door → {out}",
                                 f"試訳: Open the door → {out.strip()[:80]}"))
                self.q.put(("conn_result", True, "\n".join(lines)))
            except Exception as e:
                hint = _conn_hint(e)
                self.q.put(("conn_result", False, f"{e}" + (f"\n{hint}" if hint else "")))
        threading.Thread(target=work, daemon=True).start()

    def _show_conn_result(self, ok, text):
        self._conn_testing = False
        if hasattr(self, "btn_conn_test"):
            self.btn_conn_test.setEnabled(True)
            self.lbl_conn.setStyleSheet(f"color: {C['ok'] if ok else C['err']};")
            self.lbl_conn.setText(("✓ " if ok else "✗ ") + text)
        self._log("ok" if ok else "err", (_tx("Тест соединения: ", "接続テスト: ")) + text.replace("\n", " / "))

    def _preflight_ok(self, client):
        """翻訳開始前の接続確認（OpenAI 互換のみ・数秒）。失敗したら理由を表示して False。"""
        if self.cfg.get("dry_run") or not isinstance(client, OpenAIClient):
            return True
        try:
            models = openai_list_models(client.base, client.key, timeout=5)
        except LLMError as e:
            hint = _conn_hint(e)
            msg = f"{e}" + (f"\n\n{hint}" if hint else "")
            self._log("err", _tx("Нет соединения: ", "接続できないため翻訳を開始しません: ") + msg.replace("\n", " "))
            QtWidgets.QMessageBox.warning(self, APP_NAME, _tx("Не удалось подключиться к серверу.\n\n",
                                                               "翻訳サーバーに接続できません。\n\n") + msg)
            return False
        if not models and self.cb_backend.currentText() in ("LM Studio", "Ollama"):
            self._log("warn", _tx("Сервер не сообщил о загруженных моделях.",
                                  "サーバーに読み込み済みのモデルがありません。翻訳が失敗する場合はモデルをロードしてください。"))
        return True

    def _notify_done(self, text, ok=True):
        """作業完了の通知: システム音 + タスクバー点滅 + ダイアログ（非モーダル）。"""
        if not self.chk_notify.isChecked():
            return
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK if ok else winsound.MB_ICONEXCLAMATION)
        except Exception:
            QtWidgets.QApplication.beep()
        try:
            QtWidgets.QApplication.alert(self, 0)     # 他のウィンドウを見ていてもタスクバーで分かる
        except Exception:
            pass
        box = QtWidgets.QMessageBox(self)
        box.setIcon(_pick("QtWidgets.QMessageBox.Icon.Information", "QtWidgets.QMessageBox.Information")
                    if ok else _pick("QtWidgets.QMessageBox.Icon.Warning", "QtWidgets.QMessageBox.Warning"))
        box.setWindowTitle(APP_NAME)
        box.setText(text)
        box.setModal(False)                         # 処理を止めない
        box.setAttribute(_pick("Qt.WidgetAttribute.WA_DeleteOnClose", "Qt.WA_DeleteOnClose"))
        box.show()
        box.raise_()
        self._last_notify_box = box

    def _toggle_api_dialog(self, on):
        if on:
            self.api_dialog.setWindowTitle(f"{APP_NAME} — {self.tr('api_settings')}")
            self.api_dialog.show()
            self.api_dialog.raise_()
            self.api_dialog.activateWindow()
        elif self.api_dialog.isVisible():
            self.api_dialog.hide()

    def _capture_scan_opts(self):
        """ワーカースレッドで使う UI の値（GUI スレッドで読む）。"""
        return {"bsa": self.chk_bsa.isChecked(), "enc": self.cb_enc.currentText(),
                "risky": self.chk_risky.isChecked(), "src": self.cb_src.currentData() or "en",
                "pex": self.chk_pex.isChecked(), "tgt": self.cb_tgt.currentData() or "ja",
                "skse": self.chk_skse.isChecked()}

    def _load_mod_preview(self, mod):
        # Блокируем кнопки на время сканирования
        self.running = True
        self.btn_translate.setEnabled(False)
        self.btn_save.setEnabled(False)
        self.progress.setValue(0)
        self.lbl_progress.setText(_tx(f"Загрузка {mod['name']}…", f"{mod['name']} を読み込み中…"))
        self.units = []
        self.jobs = []
        self.cancel_ev.clear()
        self.run_id += 1
        
        self._scan_opts = self._capture_scan_opts()
        # Запускаем отдельный поток, который не переводит, а только собирает строки
        threading.Thread(target=self._preview_worker, args=(self.run_id, mod), daemon=True).start()            

    # ── глоссарий ──────────────────────────────────────────────────────────
    def _gloss_reload(self):
        self.gloss_table.blockSignals(True)
        self.gloss_table.setRowCount(0)
        for src, dst in self.glossary.items.items():
            r = self.gloss_table.rowCount()
            self.gloss_table.insertRow(r)
            a = QtWidgets.QTableWidgetItem(src)
            b = QtWidgets.QTableWidgetItem(dst)
            a.setFlags(ITEM_ENABLED | ITEM_SELECTABLE | ITEM_EDITABLE)
            b.setFlags(ITEM_ENABLED | ITEM_SELECTABLE | ITEM_EDITABLE)
            self.gloss_table.setItem(r, 0, a)
            self.gloss_table.setItem(r, 1, b)
        self.gloss_table.blockSignals(False)

    def _gloss_add(self):
        s = self.ed_g_src.text().strip()
        d = self.ed_g_dst.text().strip()
        if not s or not d:
            return
        self.glossary.items[s] = d
        self.glossary.save(self._log)
        self._gloss_reload()
        self.ed_g_src.clear()
        self.ed_g_dst.clear()
        self._log("ok", _tx(f"Глоссарий: «{s}» → «{d}»", f"用語集: 「{s}」→「{d}」"))

    def _gloss_del(self):
        rows = sorted({i.row() for i in self.gloss_table.selectedIndexes()},
                      reverse=True)
        for r in rows:
            item = self.gloss_table.item(r, 0)
            if item:
                self.glossary.items.pop(item.text(), None)
        if rows:
            self.glossary.save(self._log)
            self._gloss_reload()

    def _gloss_edited(self, _row, _col):
        if self.gloss_table.signalsBlocked():
            return
        items = {}
        for r in range(self.gloss_table.rowCount()):
            a = self.gloss_table.item(r, 0)
            b = self.gloss_table.item(r, 1)
            if a and b and a.text().strip():
                items[a.text().strip()] = b.text()
        self.glossary.items = items
        self._gloss_save_timer.start()

    def _gloss_save_now(self):
        self.glossary.save(self._log)

    # ── файлы ──────────────────────────────────────────────────────────────
    def open_single_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, self.tr("btn_open_file"), os.path.expanduser("~"),
            _tx("Все поддерживаемые (*.txt *.json *.strings *.dlstrings *.ilstrings *.esp *.esm *.esl *.zip);;"
            "Архивы (*.zip);;Плагины (*.esp *.esm *.esl);;Текст/JSON (*.txt *.json *.strings);;Все файлы (*)", "対応ファイル (*.txt *.json *.strings *.dlstrings *.ilstrings *.esp *.esm *.esl *.zip);;アーカイブ (*.zip);;プラグイン (*.esp *.esm *.esl);;テキスト/JSON (*.txt *.json *.strings);;すべてのファイル (*)"))
        if not path:
            return
            
        ext = os.path.splitext(path)[1].lower()
        nm = os.path.basename(path)
        units = []

        # Обработка ZIP-архива
        if ext == ".zip":
            self.chk_zip.setChecked(True)
            temp_dir = tempfile.mkdtemp(prefix="mo2trans_zip_")
            try:
                with zipfile.ZipFile(path, 'r') as z:
                    z.extractall(temp_dir)
                
                # Сканируем распакованную папку
                _counts, scanned = scan_mod_dir(
                    temp_dir, self.chk_bsa.isChecked(), self.cb_enc.currentText(),
                    lambda lvl, msg: self._log(lvl, f"[{nm}] {msg}"),
                    allow_risky=self.chk_risky.isChecked(), src_lang=self.cb_src.currentData() or "en",
                    include_pex=self.chk_pex.isChecked(), tgt_lang=self.cb_tgt.currentData() or "ja",
                    include_skse_menu=self.chk_skse.isChecked()
                )
                
                for u in scanned:
                    u["mod"] = nm
                    if "orig_src" not in u: u["orig_src"] = u.get("src", "")
                    
                    if u["kind"] == "json" and u.get("path"):
                        for ju in load_json_units(u["path"]):
                            ju["mod"] = nm
                            ju["rel"] = u["rel"]
                            ju["temp_path"] = u["path"] # Запоминаем путь во временной папке
                            if "orig_src" not in ju: ju["orig_src"] = ju.get("src", "")
                            units.append(ju)
                    elif u["kind"] == "swf_txt" and u.get("path"):
                        for su in load_swf_txt(u["path"], self.cb_enc.currentText()):
                            su["mod"] = nm
                            su["rel"] = u["rel"]
                            su["temp_path"] = u["path"]
                            if "orig_src" not in su: su["orig_src"] = su.get("src", "")
                            units.append(su)
                    elif u["kind"] in ("strings", "esp_string", "json_kv", "pex_string", "skse_kv"):
                        units.append(u)
                        
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, APP_NAME, _tx(f"Ошибка чтения ZIP:\n{e}", f"ZIP の読み込みエラー:\n{e}"))
                return
            
            self.mods = [{"name": nm, "path": temp_dir,
                          "counts": {"plugins": 0, "strings": 0, "translations": 0, "json": len(units)},
                          "selected": True, "scanned": True, "is_zip": True}]
            self._pending_units = units
            self._zip_source_path = path # Запоминаем исходный архив для сохранения
            
        elif ext in (".rar", ".7z"):
            QtWidgets.QMessageBox.warning(self, APP_NAME, _tx("Прямая поддержка .rar и .7z недоступна.\nПожалуйста, распакуйте архив и используйте кнопку «Добавить папки…».", ".rar と .7z は直接サポートしていません。\nアーカイブを展開してから「フォルダを追加…」ボタンを使ってください。"))
            return
            
        elif ext in (".esp", ".esm", ".esl"):
            with open(path, "rb") as f:
                data = f.read()
            esp = EspStringExtractor(self.cb_enc.currentText())
            for s in esp.extract_strings(data):
                units.append({"rel": nm, "kind": "esp_string", "src": s, "dst": None, "orig_path": nm})
            for u in units: u["mod"] = nm
            self.mods = [{"name": nm, "path": os.path.dirname(path),
                          "counts": {"plugins": 1, "strings": 0, "translations": 0, "json": 0},
                          "selected": True, "scanned": True}]
            self._pending_units = units
            self._zip_source_path = None
            
        elif ext in STRING_EXTS:
            for sid, text in read_strings_file(path):
                if text.strip():
                    units.append({"rel": nm, "kind": "strings", "sid": sid,
                                  "src": text, "dst": None, "ext": ext})
            for u in units: u["mod"] = nm
            self.mods = [{"name": nm, "path": os.path.dirname(path),
                          "counts": {"plugins": 0, "strings": 1, "translations": 0, "json": 0},
                          "selected": True, "scanned": True}]
            self._pending_units = units
            self._zip_source_path = None
            
        else:
            try:
                with open(path, encoding=self.cb_enc.currentText(), errors="replace") as f:
                    for ln in f.read().splitlines():
                        if ln.strip():
                            units.append({"rel": nm, "kind": "txt_line", "src": ln, "dst": None})
                for u in units: u["mod"] = nm
                self.mods = [{"name": nm, "path": os.path.dirname(path),
                              "counts": {"plugins": 0, "strings": 0, "translations": 1, "json": 0},
                              "selected": True, "scanned": True}]
                self._pending_units = units
                self._zip_source_path = None
            except Exception as e:
                self._log("err", str(e))
                return

        self._fill_mod_table()
        self._sync_out_name()
        self._log("ok", _tx(f"Загружен {nm}: {len(units)} строк.", f"{nm} を読み込みました: {len(units)} 行。"))

    # ── сбор клиента ──────────────────────────────────────────────────────
    def _build_client(self):
        backend = self.cb_backend.currentText()
        temp = self.sp_temp.value()
        maxtok = self.sp_maxtok.value()
        if backend == "DeepL":
            return DeepLClient(self.ed_deepl.text().strip(),
                               self.cb_tgt.currentData() or "ru")
        if backend == "Yandex":
            return YandexClient(self.ed_yandex.text().strip(),
                                self.cb_src.currentData() or "en",
                                self.cb_tgt.currentData() or "ru")
                                
        if backend == "Google Translate":
            return GoogleFreeClient(self.cb_src.currentData() or "en", self.cb_tgt.currentData() or "ru")                                
                                
        if backend == "Ollama":
            url = self.ed_ollama_url.text().strip().rstrip("/") or \
                  "http://localhost:11434"
            if not url.endswith("/v1"):
                url += "/v1"
            return OpenAIClient(
                url, "",
                self.ed_ollama_model.text().strip() or "llama3.1",
                temp, maxtok,
                extra_body={"chat_template_kwargs": {"enable_thinking": False},
                            "reasoning_effort": "none"})
        if backend == "LM Studio":
            return OpenAIClient(
                normalize_openai_url(self.ed_lm_url.text(), "http://127.0.0.1:1234/v1"),
                "",
                self.ed_lm_model.text().strip() or "local-model",
                temp, maxtok,
                extra_body={"chat_template_kwargs": {"enable_thinking": False},
                            "reasoning_effort": "none"})
        if backend == "OpenRouter":
            return OpenAIClient("https://openrouter.ai/api/v1",
                                self.ed_or_key.text().strip(),
                                self.ed_or_model.text().strip(), temp, maxtok)
        return OpenAIClient(
            self.ed_openai_url.text().strip() or "https://api.openai.com/v1",
            self.ed_openai_key.text().strip(),
            self.ed_openai_model.text().strip(), temp, maxtok)

    # ── запуск перевода ───────────────────────────────────────────────────
    def _gather_window_state(self):
        """ウィンドウの位置・サイズ（最大化を含む）とプレビュー表の「ファイル」列の幅を self.cfg に入れる。"""
        try:
            self.cfg["window_geometry"] = bytes(self.saveGeometry().toHex().data()).decode("ascii")
            if hasattr(self, "prev_table"):
                self.cfg["preview_file_col_width"] = self.prev_table.columnWidth(1)
        except Exception:
            pass

    def _restore_window_state(self):
        """保存したウィンドウの位置・サイズを戻す（画面構成が変わっていれば Qt が画面内に収める）。"""
        geo = self.cfg.get("window_geometry")
        if geo:
            try:
                self.restoreGeometry(QtCore.QByteArray.fromHex(geo.encode("ascii")))
            except Exception:
                pass
        w = self.cfg.get("preview_file_col_width")
        if isinstance(w, int) and 40 <= w <= 2000 and hasattr(self, "prev_table"):
            self.prev_table.setColumnWidth(1, w)

    def _gather_cfg(self):
        """画面の設定値を self.cfg に反映する（保存はしない）。"""
        self._gather_window_state()
        self.cfg.update({
            "backend": self.cb_backend.currentText(),
            "source": self.cb_src.currentData() or "en",
            "target": self.cb_tgt.currentData() or "ru",
            "encoding": self.cb_enc.currentText(),
            "ui_lang": self.lang,
            "openai_url": self.ed_openai_url.text().strip(),
            "openai_model": self.ed_openai_model.text().strip(),
            "openai_key": self.ed_openai_key.text().strip(),
            "ollama_url": self.ed_ollama_url.text().strip(),
            "ollama_model": self.ed_ollama_model.text().strip(),
            "lmstudio_url": self.ed_lm_url.text().strip(),
            "lmstudio_model": self.ed_lm_model.text().strip(),
            "openrouter_key": self.ed_or_key.text().strip(),
            "openrouter_model": self.ed_or_model.text().strip(),
            "deepl_key": self.ed_deepl.text().strip(),
            "yandex_key": self.ed_yandex.text().strip(),
            "temperature": self.sp_temp.value(),
            "max_tokens": self.sp_maxtok.value(),
            "system_prompt": self.txt_prompt.toPlainText(),
            "convert_units": self.chk_units.isChecked(),
            "delay_ms": self.sp_delay.value(),
            "threads": self.sp_threads.value(),
            "batch_size": self.sp_batch.value() if hasattr(self, "sp_batch") else 1,
            "dry_run": self.chk_dry.isChecked(),
            "extract_bsa": self.chk_bsa.isChecked(),
            "gen_report": self.chk_report.isChecked(),
            "out_folder": self.ed_folder.text().strip(),
            "out_name": self.ed_name.text().strip(),
            "save_zip": self.chk_zip.isChecked(),
            "save_dsd": self.chk_dsd.isChecked(),
            "allow_risky": self.chk_risky.isChecked(),
            "translate_pex": self.chk_pex.isChecked(),
            "translate_skse_menu": self.chk_skse.isChecked(),
            "per_mod_save": self.chk_permod.isChecked(),
            "in_place": self.chk_inplace.isChecked(),
            "status_filter": sorted(self._shown_states()),
            "notify_done": self.chk_notify.isChecked(),
        })

    def _save_settings(self):
        """画面の設定を設定ファイルに保存する（閉じるとき・API 設定を閉じたときにも呼ぶ）。"""
        try:
            self._gather_cfg()
            save_config(self.cfg, self._log)
        except Exception as e:
            try:
                self._log("err", _tx(f"Настройки не сохранены: {e}", f"設定を保存できませんでした: {e}"))
            except Exception:
                pass

    def done(self, r):
        # Esc / 閉じるボタン / × のどれで閉じても設定を保存する
        self._save_settings()
        super().done(r)

    def start_translation(self):
        if self.running:
            return
        
        # 1. Сохраняем текущие настройки из интерфейса
        self._gather_cfg()
        save_config(self.cfg, self._log)

        # 2. Проверка: есть ли что переводить
        if not self.units:
            selected = [m for m in self.mods if m["selected"]]
            if not selected:
                QtWidgets.QMessageBox.warning(self, APP_NAME, _tx("Выберите хотя бы один мод или загрузите его в предпросмотр двойным кликом.", "Mod を1つ以上選択するか、ダブルクリックでプレビューに読み込んでください。"))
                return

        # 3. Инициализация клиента и переводчика
        try:
            client = self._build_client()
            self.translator = Translator(
                client, PlaceholderProtector(), self.cfg["system_prompt"],
                self.cfg["source"], self.cfg["target"], self.glossary.items,
                repair=True, dry_run=self.cfg["dry_run"],
                unit_convert=self.cfg["convert_units"],
                log=self._log, sst_terms=self._sst_hint_terms())
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, APP_NAME, _tx(f"Ошибка инициализации переводчика:\n{e}", f"翻訳エンジンの初期化エラー:\n{e}"))
            return
        if not self._preflight_ok(client):
            return

        # 4. Загрузка кэша
        self.cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "translation_cache.json")
        self.translation_cache = {}
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.translation_cache = json.load(f)
                self._log("info", _tx(f"Загружен кэш: {len(self.translation_cache)} строк", f"キャッシュを読み込みました: {len(self.translation_cache)} 行"))
            except Exception as e:
                self._log("err", _tx(f"Не удалось загрузить кэш: {e}", f"キャッシュを読み込めませんでした: {e}"))

        # 5. Подготовка к работе
        self.cancel_ev.clear()
        self.run_id += 1
        my_run = self.run_id
        self._last_req_ts = 0.0
        self.running = True
        self.btn_translate.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_save.setEnabled(False)
        self.progress.setValue(0)
        
        # 6a. Mod ごとに自動保存: 1 Mod ずつ収集→翻訳→保存
        if not self.units and (self.chk_permod.isChecked() or self.chk_inplace.isChecked()):
            if not self.chk_inplace.isChecked() and not self.ed_folder.text().strip():
                self.running = False
                self.btn_translate.setEnabled(True)
                self.btn_cancel.setEnabled(False)
                QtWidgets.QMessageBox.warning(self, APP_NAME, self.tr("msg_no_folder"))
                return
            self._permod_queue = [m for m in self.mods if m["selected"]]
            self._permod_total = len(self._permod_queue)
            self._overall_t0 = time.time()
            self.progress_all.setRange(0, max(1, self._permod_total))
            self.progress_all.setValue(0)
            self.progress_all.setVisible(True)
            self.lbl_progress_all.setVisible(True)
            self.running = False          # _permod_start_next が立て直す
            self._permod_start_next()
            return

        # 6. Если предпросмотр пуст — запускаем сбор строк в фоне
        if not self.units:
            self.lbl_progress.setText(_tx("Сбор строк…", "文字列を収集中…"))
            self._scan_opts = self._capture_scan_opts()
            threading.Thread(
                target=self._collect_worker, 
                args=(my_run, self.chk_bsa.isChecked(), self.cb_enc.currentText(),
                      self.chk_risky.isChecked()), 
                daemon=True
            ).start()
            return
            threading.Thread(target=self._collect_worker, args=(my_run,), daemon=True).start()
            return

        # 7. Если строки уже загружены (двойным кликом), начинаем перевод сразу
        # Отфильтровываем строки, исключенные пользователем
        self.jobs = []
        for i, u in enumerate(self.units):
            src = u.get("src") or ""
            if not src.strip() or not TOKEN_RE.sub("", src).strip():
                continue
            # Проверяем, не снята ли галочка с файла
            if hasattr(self, "file_states") and not self.file_states.get(u["rel"], True):
                continue
            self.jobs.append(i)

        if not self.jobs:
            self._finish()
            QtWidgets.QMessageBox.information(self, APP_NAME, _tx("Нет активных строк для перевода (все файлы исключены или пусты).", "翻訳対象の行がありません（すべて除外済みか空です）。"))
            return

        self.tabs.setCurrentIndex(1)
        self.stats = {"done": 0, "total": len(self.jobs), "errors": 0, "sst": 0, "t0": time.time()}
        self._log("warn", _tx(f"Перевод {len(self.jobs)} строк · {self.cfg['backend']} · потоков {self.cfg['threads']}", f"{len(self.jobs)} 行を翻訳 · {self.cfg['backend']} · スレッド {self.cfg['threads']}"))

        # 8. Формируем пакеты и запускаем потоки
        batches = self._make_batches()
        if not batches:
            self._finish()
            self.lbl_progress.setText(_tx("Нет пакетов для перевода.", "翻訳するバッチがありません。"))
            return

        self.job_q = queue.Queue()
        for b in batches:
            self.job_q.put(b)
        for _ in range(self.cfg["threads"]):
            self.job_q.put(None)
            
        for _w in range(self.cfg["threads"]):
            threading.Thread(target=self._worker, args=(my_run, self.job_q), daemon=True).start()


    def _collect_worker(self, run_id, extract_bsa, encoding, allow_risky=False, mods=None):
        try:
            if self._pending_units is not None:
                units = self._pending_units
                self._pending_units = None
            else:
                units = []
                selected = list(mods) if mods is not None else [m for m in self.mods if m["selected"]]
                total = len(selected)
                if total == 0:
                    self.q.put(("stop", run_id))
                    return

                for idx, m in enumerate(selected):
                    if self.run_id != run_id or self.cancel_ev.is_set():
                        self.q.put(("stop", run_id))
                        return
                    self.q.put(("log", "info", _tx(f"Сканирование {m['name']} ({idx + 1}/{total})…", f"{m['name']} をスキャン中 ({idx + 1}/{total})…")))
                    
                    try:
                        _so = getattr(self, "_scan_opts", None) or {}
                        _counts, scanned = scan_mod_dir(
                            m["path"], extract_bsa, encoding,
                            lambda lvl, msg: self.q.put(("log", lvl, f"[{m['name']}] {msg}")),
                            allow_risky=allow_risky, cancel=self.cancel_ev,
                            src_lang=_so.get("src", "en"),
                            include_pex=_so.get("pex", False), tgt_lang=_so.get("tgt", "ja"),
                            include_skse_menu=_so.get("skse", False))
                    except Exception as e:
                        self.q.put(("log", "err", f"{m['name']}: {e}"))
                        continue

                    mod_start = len(units)
                    for u in scanned:
                        u["mod"] = m["name"]
                        if "orig_src" not in u:
                            u["orig_src"] = u.get("src", "")

                        if u["kind"] == "json" and u.get("path"):
                            for ju in load_json_units(u["path"]):
                                ju["mod"] = m["name"]
                                ju["rel"] = u["rel"]
                                if "orig_src" not in ju: ju["orig_src"] = ju.get("src", "")
                                units.append(ju)
                                
                        elif u["kind"] == "xml" and u.get("path"):
                            for xu in load_xml_units(u["path"]):
                                xu["mod"] = m["name"]
                                xu["rel"] = u["rel"]
                                if "orig_src" not in xu: xu["orig_src"] = xu.get("src", "")
                                units.append(xu)                                
                                
                        elif u["kind"] == "ini" and u.get("path"):
                            for iu in load_ini_units(u["path"]):
                                iu["mod"] = m["name"]
                                iu["rel"] = u["rel"]
                                if "orig_src" not in iu: iu["orig_src"] = iu.get("src", "")
                                units.append(iu)

                        elif u["kind"] == "swf_txt" and u.get("path"):
                            # Проверяем, на каком языке файл перевода
                            stem = os.path.splitext(os.path.basename(u["path"]))[0].lower()
                            file_lang = None
                            m_lang = re.search(r"_(english|french|german|italian|spanish|russian|polish|czech|japanese)$", stem)
                            if m_lang:
                                file_lang = m_lang.group(1)
                        
                            # Пропускаем, если язык файла не совпадает с исходным
                            src_lang = (getattr(self, "_scan_opts", None) or {}).get("src", "en")
                            if file_lang and file_lang != src_lang and not (src_lang == "en" and file_lang == "english"):
                                continue
                        
                            for su in load_swf_txt(u["path"], encoding):
                                su["mod"] = m["name"]
                                su["rel"] = u["rel"]
                                if "orig_src" not in su: su["orig_src"] = su.get("src", "")
                                units.append(su)
                                
                        elif u["kind"] == "archive_txt":
                            try:
                                txt = u["data"].decode(encoding, "replace")
                            except Exception:
                                txt = ""
                            if u["iext"] == ".json":
                                for ju in load_json_units(text=txt, rel=u["rel"]):
                                    ju["mod"] = m["name"]
                                    ju["rel"] = u["rel"]
                                    if "orig_src" not in ju: ju["orig_src"] = ju.get("src", "")
                                    units.append(ju)
                            else:
                                for ln in txt.splitlines():
                                    if ln.startswith("$"):
                                        parts = ln.split("\t", 1)
                                        if len(parts) == 2 and parts[1].strip():
                                            units.append({
                                                "mod": m["name"], "rel": u["rel"],
                                                "kind": "swf_line",
                                                "key": parts[0], "src": parts[1],
                                                "dst": None, "orig_src": parts[1],
                                                "iext": u["iext"]})
                                    elif ln.strip():
                                        units.append({
                                            "mod": m["name"], "rel": u["rel"],
                                            "kind": "txt_line", "src": ln,
                                            "dst": None, "orig_src": ln,
                                            "iext": u["iext"]})
                        elif u["kind"] in ("strings", "json_kv", "esp_string", "pex_string", "skse_kv"):
                            units.append(u)

                    units[mod_start:] = self._merge_existing_translations(
                        units[mod_start:], m, encoding)

            if self.run_id == run_id:
                self.q.put(("collected", run_id, units))
        except Exception as e:
            self.q.put(("log", "err", _tx(f"Критическая ошибка сбора: {e}", f"収集中の致命的エラー: {e}")))
            self.q.put(("stop", run_id))
            
    def _preview_worker(self, run_id, mod):
        try:
            opts = getattr(self, "_scan_opts", None) or {"bsa": True, "enc": "utf-8", "risky": False, "src": "en"}
            enc = opts["enc"]
            self.q.put(("log", "info", _tx(f"Сканирование {mod['name']} для предпросмотра…", f"プレビュー用に {mod['name']} をスキャン中…")))
            
            try:
                _counts, scanned = scan_mod_dir(
                    mod["path"], opts["bsa"], enc,
                    lambda lvl, msg: self.q.put(("log", lvl, f"[{mod['name']}] {msg}")),
                    allow_risky=opts["risky"], cancel=self.cancel_ev, src_lang=opts["src"],
                    include_pex=opts.get("pex", False), tgt_lang=opts.get("tgt", "ja"),
                    include_skse_menu=opts.get("skse", False)
                )
            except Exception as e:
                self.q.put(("log", "err", f"{mod['name']}: {e}"))
                self.q.put(("stop_preview", run_id))
                return
                
            units = []
            for u in scanned:
                u["mod"] = mod["name"]
                if "orig_src" not in u: u["orig_src"] = u.get("src", "")
                
                if u["kind"] == "json" and u.get("path"):
                    for ju in load_json_units(u["path"]):
                        ju["mod"] = mod["name"]
                        ju["rel"] = u["rel"]
                        if "orig_src" not in ju: ju["orig_src"] = ju.get("src", "")
                        units.append(ju)
                        
                elif u["kind"] == "xml" and u.get("path"):
                    for xu in load_xml_units(u["path"]):
                        xu["mod"] = mod["name"]
                        xu["rel"] = u["rel"]
                        if "orig_src" not in xu: xu["orig_src"] = xu.get("src", "")
                        units.append(xu)                        
                        
                elif u["kind"] == "ini" and u.get("path"):
                    for iu in load_ini_units(u["path"]):
                        iu["mod"] = mod["name"]
                        iu["rel"] = u["rel"]
                        if "orig_src" not in iu: iu["orig_src"] = iu.get("src", "")
                        units.append(iu)

                elif u["kind"] == "swf_txt" and u.get("path"):
                    # Проверяем, на каком языке файл перевода
                    stem = os.path.splitext(os.path.basename(u["path"]))[0].lower()
                    file_lang = None
                    m_lang = re.search(r"_(english|french|german|italian|spanish|russian|polish|czech|japanese)$", stem)
                    if m_lang:
                        file_lang = m_lang.group(1)
                        
                    # Пропускаем, если язык файла не совпадает с исходным
                    src_lang = (getattr(self, "_scan_opts", None) or {}).get("src", "en")
                    if file_lang and file_lang != src_lang and not (src_lang == "en" and file_lang == "english"):
                        continue
                        
                    for su in load_swf_txt(u["path"], enc):
                        su["mod"] = mod["name"] # (или m["name"])
                        su["rel"] = u["rel"]
                        if "orig_src" not in su: su["orig_src"] = su.get("src", "")
                        units.append(su)
                        
                elif u["kind"] == "archive_txt":
                    try: txt = u["data"].decode(enc, "replace")
                    except Exception: txt = ""
                    if u["iext"] == ".json":
                        for ju in load_json_units(text=txt, rel=u["rel"]):
                            ju["mod"] = mod["name"]
                            ju["rel"] = u["rel"]
                            if "orig_src" not in ju: ju["orig_src"] = ju.get("src", "")
                            units.append(ju)
                    else:
                        for ln in txt.splitlines():
                            if ln.startswith("$"):
                                parts = ln.split("\t", 1)
                                if len(parts) == 2 and parts[1].strip():
                                    units.append({"mod": mod["name"], "rel": u["rel"], "kind": "swf_line", "key": parts[0], "src": parts[1], "dst": None, "orig_src": parts[1], "iext": u["iext"]})
                            elif ln.strip():
                                units.append({"mod": mod["name"], "rel": u["rel"], "kind": "txt_line", "src": ln, "dst": None, "orig_src": ln, "iext": u["iext"]})
                elif u["kind"] in ("strings", "json_kv", "esp_string", "pex_string", "skse_kv"):
                    units.append(u)

            units = self._merge_existing_translations(units, mod, enc)

            if self.run_id == run_id:
                self.q.put(("collected_preview", run_id, units))
                
        except Exception as e:
            self.q.put(("log", "err", _tx(f"Критическая ошибка предпросмотра: {e}", f"プレビューの致命的エラー: {e}")))
            self.q.put(("stop_preview", run_id))            

    LARGE_JOB_LIMIT = 20000

    def _merge_existing_translations(self, units, mod, encoding):
        """翻訳先の訳ファイルが既にある英語の訳ファイルは、足りないキーだけを翻訳対象に残す（ワーカーから呼ぶ）。"""
        tgt = (getattr(self, "_scan_opts", None) or {}).get("tgt", "ja")
        try:
            merged = apply_translation_merge(units, mod["path"], tgt, encoding)
        except Exception as e:
            self.q.put(("log", "warn", f"[{mod['name']}] merge: {e}"))
            return units
        per_file = Counter(u["merge_target"] for u in merged if u.get("merge_target"))
        before = {u["rel"] for u in units if u.get("kind") == "swf_line"}
        after = {u["rel"] for u in merged if u.get("kind") == "swf_line"}
        for rel in sorted(before - after):        # 全キーが翻訳先ファイルにあって丸ごと外れたもの
            self.q.put(("log", "info", _tx(
                f"[{mod['name']}] {rel}: все ключи уже переведены",
                f"[{mod['name']}] {rel}: 翻訳先のファイルにすべてのキーがあるので翻訳しません")))
        for tgt_rel, n in per_file.items():
            self.q.put(("log", "info", _tx(
                f"[{mod['name']}] {tgt_rel}: не хватает {n} ключей — будут добавлены",
                f"[{mod['name']}] {tgt_rel}: 足りないキー {n} 件だけを翻訳して追記します")))
        return merged

    def _inplace_blocked_rels(self):
        """in_place 時、出力先の別名ファイルが Mod 側に既にある（＝作者の訳など）元ファイルの rel 集合。"""
        blocked = set()
        if not self.chk_inplace.isChecked():
            return blocked
        tgt = self.cfg.get("target") or (self.cb_tgt.currentData() or "ja")
        cache = {}
        for u in self.units:
            if u.get("kind") not in ("strings", "swf_line", "txt_line"):
                continue
            if u.get("merge_base") is not None:
                continue                  # 既存の翻訳先ファイルへのマージ（足りないキーの追記）は守る対象外
            key = (u.get("mod"), u.get("rel"))
            if key in cache:
                continue
            mod = next((m for m in self.mods if m["name"] == u.get("mod")), None)
            if not mod:
                cache[key] = False
                continue
            rel_clean = u["rel"].split("//")[-1]
            out_rel = os.path.join(os.path.dirname(rel_clean), _localize_name(os.path.basename(rel_clean), tgt))
            full = os.path.join(mod["path"], out_rel)
            ours = set()
            mp = self._inplace_manifest_path(mod["path"], mod["name"])
            if os.path.exists(mp):
                try:
                    with open(mp, encoding="utf-8") as f:
                        ours = {os.path.normcase(os.path.normpath(x)) for x in json.load(f).get("files", [])}
                except Exception:
                    pass
            hit = os.path.exists(full) and os.path.normcase(os.path.normpath(out_rel)) not in ours
            cache[key] = hit
            if hit:
                blocked.add(key)
                self._log("info", _tx(f"{u['mod']}: {out_rel} уже есть — пропуск",
                                      f"{u['mod']}: {out_rel} が既にあるので、この元ファイルは翻訳しません"))
        return blocked

    def _build_jobs(self):
        """self.units → self.jobs。技術的な行（warn）は excluded=True にして
        最初から表にも載せない。ファイル全体が技術的なら load_*_units 側で
        全行 warn になるので、そのファイルは丸ごと消える。"""
        self.jobs = []
        tech_rows = 0
        blocked = self._inplace_blocked_rels()
        dsd_cov = getattr(self, "_dsd_covered", None) or frozenset()
        dsd_skipped = {}
        for i, u in enumerate(self.units):
            if blocked and (u.get("mod"), u.get("rel")) in blocked:
                u["excluded"] = True
                continue
            if u.get("kind") == "esp_string" and dsd_cov:
                plugin = os.path.basename(u["rel"].split("//")[-1]).lower()
                if plugin in dsd_cov:
                    u["excluded"] = True
                    dsd_skipped[plugin] = dsd_skipped.get(plugin, 0) + 1
                    continue
            src = u.get("src") or ""
            if not (src.strip() and TOKEN_RE.sub("", src).strip()):
                continue
            if u.get("warn"):
                u["excluded"] = True
                tech_rows += 1
                continue
            self.jobs.append(i)
        if tech_rows:
            self._log("info", _tx(
                f"Технические строки исключены: {tech_rows}",
                f"技術的な行を除外: {tech_rows} 行"))
        for plugin, n in dsd_skipped.items():
            self._log("info", _tx(
                f"{plugin}: уже переведён через DSD другого мода — пропуск ({n} строк)",
                f"{plugin}: 別の Mod の DSD で日本語化済みなので翻訳しません（{n} 行）"))

    def _confirm_large_jobs(self):
        """行数が LARGE_JOB_LIMIT を超えたら続行確認。False = 中止。"""
        n = len(self.jobs)
        if n <= self.LARGE_JOB_LIMIT:
            return True
        n_files = len({self.units[i].get("rel") for i in self.jobs})
        n_mods = len({self.units[i].get("mod") for i in self.jobs})
        ans = QtWidgets.QMessageBox.question(
            self, APP_NAME,
            _tx(f"Найдено {n:,} строк ({n_files:,} файлов, {n_mods} модов).\n\n"
                f"Построение таблицы и перевод займут очень много времени.\nПродолжить?",
                f"翻訳対象が {n:,} 行（{n_files:,} ファイル / {n_mods} Mod）あります。\n\n"
                f"プレビュー表の作成と翻訳に非常に長い時間がかかります。\n"
                f"Mod を絞り込むことをおすすめします。続行しますか？"),
            BTN_YES | BTN_NO, BTN_NO)
        if ans != BTN_YES:
            self._log("warn", _tx(f"Отменено пользователем: {n:,} строк",
                                  f"ユーザーが中止しました（{n:,} 行）。Mod を絞り込んでください。"))
            self.jobs = []
            return False
        return True

    def _make_batches(self):
        batch_size = self.cfg.get("batch_size", 1)
        active_jobs = []
        
        for idx in self.jobs:
            u = self.units[idx]
            # Берем только те строки, где не стоит галочка "excluded"
            if not u.get("excluded", False):
                active_jobs.append(idx)
                
        # ВАЖНО: пересчитываем total, чтобы прогресс-бар дошел до 100%
        if hasattr(self, "stats") and "total" in self.stats:
            self.stats["total"] = len(active_jobs)
            
        if not active_jobs:
            return []
            
        return [active_jobs[i:i + batch_size] for i in range(0, len(active_jobs), batch_size)]

    def _throttle(self):
        delay_ms = self.cfg.get("delay_ms", 0)
        if delay_ms <= 0:
            return
        with self._delay_lock:
            now = time.time()
            wait = self._last_req_ts + delay_ms / 1000.0 - now
            if wait > 0:
                time.sleep(wait)
            self._last_req_ts = time.time()

    def _worker(self, run_id, job_q):
        import hashlib # Импортируем здесь, чтобы не загрязнять начало файла
        while True:
            if self.run_id != run_id:
                return
            try:
                batch = job_q.get(timeout=1.0)
            except queue.Empty:
                if self.run_id != run_id:
                    return
                continue
            if batch is None:
                return
            if self.run_id != run_id:
                return
            if self.cancel_ev.is_set():
                self.q.put(("stop", run_id))
                return

            # Словарь .sst: точное совпадение переводится из словаря, без LLM и без троттлинга
            sst_res = [self._sst_lookup(self.units[i]["src"]) for i in batch]
            if all(r is not None for r in sst_res):
                self.stats["sst"] += len(batch)
                self.q.put(("done", run_id, batch, sst_res, False, "sst"))
                continue

            self._throttle()
            
            idx = batch[0]
            src_text = self.units[idx]["src"]
            file_context = self.units[idx].get("rel", "")
            
            # --- ЗАЩИТА ОТ ХОТКЕЕВ И ОДИНОЧНЫХ СИМВОЛОВ ---
            # Убираем все теги, плейсхолдеры и пробелы
            clean_text = PLACEHOLDER_RE.sub("", src_text).strip()
            # Если осталась 1 буква (например "Y", "N", "A"), не отправляем в LLM
            if len(clean_text) <= 1:
                self.q.put(("done", run_id, batch, [src_text], False))
                continue
            # 既に翻訳先の言語（例: かな・漢字を含む）なら LLM に送らない。キャッシュより先に判定
            # するので、過去に誤訳されてキャッシュに残った結果も使われない。
            if already_in_target(src_text, self.cfg.get("target", ""), self.cfg.get("source", "en")):
                self.q.put(("done", run_id, batch, [src_text], False))
                continue
            # -----------------------------------------------
            
            # Создаем уникальный хэш (отпечаток) для строки
            cache_key = hashlib.md5(src_text.encode("utf-8")).hexdigest()
            
            # ПРОВЕРКА КЭША: если строка уже переводилась, берем готовое
            if cache_key in self.translation_cache:
                res = self.translation_cache[cache_key]
                self.q.put(("done", run_id, batch, [res], False))
                continue # Мгновенно переходим к следующей строке
                
            try:
                res = self.translator.translate_single(src_text, self.cancel_ev, context=file_context)
                self.translation_cache[cache_key] = res
                self.q.put(("done", run_id, batch, [res], False))
            except LLMError as e:
                if "Отменено" in str(e):
                    self.q.put(("stop", run_id))
                    return
                self.q.put(("done", run_id, batch, [src_text], True))
                self.q.put(("log", "err", _tx(f"Ошибка: {e}", f"エラー: {e}")))
            except Exception as e:
                self.q.put(("done", run_id, batch, [src_text], True))
                self.q.put(("log", "err", f"{type(e).__name__}: {e}"))

    def _fill_preview(self):
        self._loading_preview = True
        self.prev_table.setRowCount(0)
        self.unit_rows = {}

        # 0. Список файлов для изоляции (только те, что реально есть в таблице)
        prev_file = self.cb_file_filter.currentText()
        files = sorted({self.units[i]["rel"] for i in self.jobs if i < len(self.units)})
        self.cb_file_filter.blockSignals(True)
        self.cb_file_filter.clear()
        self.cb_file_filter.addItem(self.tr("all_files"))
        self.cb_file_filter.addItems(files)
        self.cb_file_filter.setCurrentText(prev_file if prev_file in files else self.tr("all_files"))
        self.cb_file_filter.blockSignals(False)

        # 1. Находим файлы, в которых есть ХОТЯ БЫ ОДНА техническая строка
        bad_files = set()  # 技術的な行は _build_jobs で行単位に除外済み
        
        # 2. Отключаем ВСЕ строки из этих файлов по умолчанию
        for u in self.units:
            if u["rel"] in bad_files:
                if "excluded" not in u:
                    u["excluded"] = True
            elif "excluded" not in u:
                u["excluded"] = False
        
        self.prev_table.setUpdatesEnabled(False)
        self.prev_table.setRowCount(len(self.jobs))
        for n, i in enumerate(self.jobs):
            u = self.units[i]
            row = n
            self.unit_rows[row] = i
            
            # Колонка 0: Номер
            it_num = QtWidgets.QTableWidgetItem(str(n + 1))
            it_num.setFlags(ITEM_ENABLED | ITEM_SELECTABLE)
            it_num.setTextAlignment(ALIGN_CENTER)
            self.prev_table.setItem(row, 0, it_num)
            
            # Колонка 1: Файл (с чекбоксом)
            fname = u["rel"]
            it_file = QtWidgets.QTableWidgetItem(fname)
            it_file.setFlags(ITEM_ENABLED | ITEM_SELECTABLE | ITEM_USERCHECK)
            it_file.setToolTip(fname)            
            
            # Если файл в черном списке или строка техническая, чекбокс снят
            is_excluded = u.get("excluded", False) or u["rel"] in bad_files
            it_file.setCheckState(ITEM_UNCHECKED if is_excluded else ITEM_CHECKED)
            self.prev_table.setItem(row, 1, it_file)
            
            # Колонка 2: Оригинал
            it_src = QtWidgets.QTableWidgetItem(u["src"])
            it_src.setFlags(ITEM_ENABLED | ITEM_SELECTABLE | ITEM_EDITABLE)
            self.prev_table.setItem(row, 2, it_src)
            
            # Колонка 3: Перевод
            it_dst = QtWidgets.QTableWidgetItem(u.get("dst", ""))
            it_dst.setFlags(ITEM_ENABLED | ITEM_SELECTABLE | ITEM_EDITABLE)
            self.prev_table.setItem(row, 3, it_dst)
            
            # Колонка 4: Статус
            if u.get("warn") or u["rel"] in bad_files:
                it_stat = QtWidgets.QTableWidgetItem("⚠️")
                it_stat.setForeground(QtGui.QBrush(QtGui.QColor(C["accent"])))
                it_stat.setToolTip(_tx("Технический файл/строка. Исключен из перевода.", "技術的なファイル/行。翻訳対象から除外されています。"))
            else:
                it_stat = QtWidgets.QTableWidgetItem("…")
                it_stat.setForeground(QtGui.QBrush(QtGui.QColor(C["dim"])))
            
            it_stat.setFlags(ITEM_ENABLED | ITEM_SELECTABLE)
            it_stat.setTextAlignment(ALIGN_CENTER)
            self.prev_table.setItem(row, 4, it_stat)
            
        self.prev_table.setUpdatesEnabled(True)
        self._loading_preview = False

    def _preview_edited(self, row, col):
        if self._loading_preview:
            return
        i = self.unit_rows.get(row)
        if i is None:
            return

        if col == 2:
            # Правка «оригинала» — фиксируем в unit.
            self.units[i]["src"] = self.prev_table.item(row, 2).text()
            # Если перевода ещё нет — продублируем, чтобы результат не потерялся.
            if not self.units[i].get("dst"):
                self.units[i]["dst"] = self.units[i]["src"]
            st = self.prev_table.item(row, 4)
            if st:
                st.setText("✎")
                st.setForeground(QtGui.QBrush(QtGui.QColor(C["accent"])))
        elif col == 3:
            self.units[i]["dst"] = self.prev_table.item(row, 3).text()
            st = self.prev_table.item(row, 4)
            if st:
                st.setText("✓")
                st.setForeground(QtGui.QBrush(QtGui.QColor(C["ok"])))
                
    def _on_preview_item_changed(self, item):
        if self._loading_preview:
            return
        if item.column() == 1:
            row = item.row()
            i = self.unit_rows.get(row)
            if i is not None:
                is_checked = (item.checkState() == ITEM_CHECKED)
                self.units[i]["excluded"] = not is_checked      

    def _copy_selected_text(self):
        selected = self.prev_table.selectedIndexes()
        if not selected:
            return
        if self.prev_table.state() == ST_EDIT:
            return
        rows = sorted({idx.row() for idx in selected})
        cols = sorted({idx.column() for idx in selected})
        if len(rows) > 1 or len(cols) > 1:
            lines = []
            for r in rows:
                row_data = []
                for c in cols:
                    it = self.prev_table.item(r, c)
                    row_data.append(it.text() if it else "")
                lines.append("\t".join(row_data))
            QtWidgets.QApplication.clipboard().setText("\n".join(lines))
        else:
            it = self.prev_table.item(rows[0], cols[0])
            if it:
                QtWidgets.QApplication.clipboard().setText(it.text())
                
    def _toggle_selected_rows(self):
        selected = self.prev_table.selectedIndexes()
        if not selected: return
        rows = sorted({idx.row() for idx in selected})
        if not rows: return
        
        self._loading_preview = True
        self.prev_table.blockSignals(True)
        
        # Определяем, включаем мы или выключаем, по первой выделенной строке
        first_item = self.prev_table.item(rows[0], 1)
        target_state = ITEM_UNCHECKED if first_item.checkState() == ITEM_CHECKED else ITEM_CHECKED
        is_checked = (target_state == ITEM_CHECKED)
        
        for r in rows:
            item = self.prev_table.item(r, 1)
            if item:
                item.setCheckState(target_state)
                i = self.unit_rows.get(r)
                if i is not None:
                    self.units[i]["excluded"] = not is_checked
                    
        self.prev_table.blockSignals(False)
        self._loading_preview = False

    def _preview_context_menu(self, pos):
        # Если ничего не выделено, не показываем меню
        if not self.prev_table.selectedIndexes():
            return

        menu = QtWidgets.QMenu(self)
        act_translate_sel = menu.addAction(_tx("Перевести выделенные строки", "選択した行を翻訳"))
        act_toggle = menu.addAction(_tx("Переключить выделенные (Space)", "選択行の有効/無効を切替 (Space)"))
        menu.addSeparator()
        act_file_off = menu.addAction(_tx("Исключить весь файл", "ファイル全体を除外"))
        act_file_on = menu.addAction(_tx("Включить весь файл", "ファイル全体を対象に戻す"))
        
        # Универсальный вызов для PyQt5 и PyQt6
        if hasattr(menu, "exec"):
            action = menu.exec(self.prev_table.mapToGlobal(pos))
        else:
            action = menu.exec_(self.prev_table.mapToGlobal(pos))
            
        if not action: 
            return
        
        selected_rows = sorted({idx.row() for idx in self.prev_table.selectedIndexes()})
        if not selected_rows: 
            return
        
        self._loading_preview = True
        self.prev_table.blockSignals(True)
        
        if action == act_translate_sel:
            self._loading_preview = False
            self.prev_table.blockSignals(False)
            self._translate_selected_rows(selected_rows)
            return

        if action == act_toggle:
            self._loading_preview = False
            self.prev_table.blockSignals(False)
            self._toggle_selected_rows()
            return
            
        is_checked = (action == act_file_on)
        target_state = ITEM_CHECKED if is_checked else ITEM_UNCHECKED
        
        # Собираем имена файлов из выделенных строк
        files_to_update = set()
        for r in selected_rows:
            item = self.prev_table.item(r, 1)
            if item: files_to_update.add(item.text())
            
        # Обновляем все строки таблицы, которые относятся к этим файлам
        for r in range(self.prev_table.rowCount()):
            item = self.prev_table.item(r, 1)
            if item and item.text() in files_to_update:
                item.setCheckState(target_state)
                i = self.unit_rows.get(r)
                if i is not None:
                    self.units[i]["excluded"] = not is_checked
                    
        self.prev_table.blockSignals(False)
        self._loading_preview = False     

    def _poll(self):
        try:
            self._update_overall_label()
        except Exception:
            pass
        try:
            while True:
                msg = self.q.get_nowait()
                kind = msg[0]
                
                try:
                    if kind == "conn_result":
                        self._show_conn_result(msg[1], msg[2])
                    elif kind == "log":
                        self._log(msg[1], msg[2])
                        
                    elif kind == "stop":
                        if msg[1] == self.run_id:
                            self._finish(cancelled=True)
                            
                    elif kind == "stop_preview":
                        if msg[1] == self.run_id:
                            self._finish()
                            self.lbl_progress.setText(_tx("Остановлено", "停止しました"))
                            
                    elif kind == "collected_preview":
                        _k, run_id, units = msg
                        if run_id != self.run_id: 
                            continue
                            
                        self.units = units
                        self._build_jobs()
                        
                        if self.jobs and not self._confirm_large_jobs():
                            self._finish()
                            continue

                        if not self.jobs:
                            self._finish()
                            QtWidgets.QMessageBox.information(self, APP_NAME, _tx("В моде не найдено переводимых строк.", "この Mod に翻訳可能な文字列は見つかりませんでした。"))
                            continue

                        self._fill_preview()
                        self.tabs.setCurrentIndex(1)                               
                        self._finish()
                        self.lbl_progress.setText(_tx(f"Загружено {len(self.jobs)} строк для ручного редактирования", f"手動編集用に {len(self.jobs)} 行を読み込みました"))

                    elif kind == "collected":
                        _k, run_id, units = msg
                        if run_id != self.run_id or not self.running:
                            continue
                            
                        self.units = units
                        if not self.units:
                            self._finish()
                            if self._permod_queue is None:
                                QtWidgets.QMessageBox.information(self, APP_NAME, self.tr("msg_no_units"))
                            else:
                                self._log("info", _tx("Нет строк для перевода — пропуск.", "翻訳対象がないのでスキップします。"))
                            continue
                        
                        self._build_jobs()
                        
                        if not self.jobs:
                            self._finish()
                            if self._permod_queue is None:
                                QtWidgets.QMessageBox.information(self, APP_NAME, self.tr("msg_no_text"))
                            else:
                                self._log("info", _tx("Нет строк для перевода — пропуск.", "翻訳対象がないのでスキップします。"))
                            continue

                        if not self._confirm_large_jobs():
                            self._finish(cancelled=True)
                            continue

                        self._fill_preview()
                        self.tabs.setCurrentIndex(1)
                        self.stats = {"done": 0, "total": len(self.jobs), "errors": 0, "sst": 0, "t0": time.time()}
                        self._log("warn", _tx(f"Перевод {len(self.jobs)} строк · {self.cfg['backend']} · потоков {self.cfg['threads']}", f"{len(self.jobs)} 行を翻訳 · {self.cfg['backend']} · スレッド {self.cfg['threads']}"))

                        batches = self._make_batches()
                        if not batches:
                            self._finish()
                            self.lbl_progress.setText(_tx("Нет активных строк (все файлы исключены).", "有効な行がありません（すべてのファイルが除外されています）。"))
                            continue
                            
                        self.job_q = queue.Queue()
                        for b in batches:
                            self.job_q.put(b)
                        for _ in range(self.cfg["threads"]):
                            self.job_q.put(None)
                        
                        for _w in range(self.cfg["threads"]):
                            threading.Thread(target=self._worker, args=(run_id, self.job_q), daemon=True).start()

                    elif kind == "done":
                        _k, run_id, batch, res, failed = msg[:5]
                        from_sst = len(msg) > 5 and msg[5] == "sst"
                        if run_id != self.run_id or not self.running:
                            continue
                            
                        for i, text in zip(batch, res):
                            self.units[i]["dst"] = (
                                text if text and not failed else self.units[i]["src"])
                            self.units[i]["err"] = failed
                            self.units[i]["sst"] = bool(from_sst) and not failed
                            
                        self.stats["done"] += len(batch)
                        if failed:
                            self.stats["errors"] += len(batch)
                        if not from_sst:   # переводы из словаря не пишем в кэш LLM
                            self.cache_save_counter += len(batch)
                        if self.cache_save_counter >= 100:
                            try:
                                with open(self.cache_file, "w", encoding="utf-8") as f:
                                    json.dump(self.translation_cache, f, ensure_ascii=False, indent=2)
                                self.cache_save_counter = 0
                            except Exception as e:
                                self._log("err", _tx(f"Ошибка сохранения кэша: {e}", f"キャッシュの保存エラー: {e}"))
                            
                        self._update_preview_rows(batch)
                        pct = self.stats["done"] / max(1, self.stats["total"])
                        self.progress.setValue(int(pct * 1000))
                        
                        el = time.time() - self.stats["t0"]
                        eta = ""
                        if 0 < self.stats["done"] < self.stats["total"]:
                            left = el / self.stats["done"] * (self.stats["total"] - self.stats["done"])
                            eta = f" · ~{int(left // 60):02d}:{int(left % 60):02d}"
                            
                        self.lbl_progress.setText(
                            f"{self.stats['done']}/{self.stats['total']} · {pct:.0%}{eta}")
                            
                        if self.stats["done"] >= self.stats["total"]:
                            self._finish()
                            
                except Exception as e:
                    self._log("err", _tx(f"Ошибка при обновлении интерфейса: {e}", f"UI 更新中のエラー: {e}"))
                    
        except queue.Empty:
            pass

    @staticmethod
    def _mixed_words(src, dst):
        """Английские слова, оставшиеся в переводе (без дублей; имена собственные из src игнорируются)."""
        known = {w.lower() for w in _EN_WORD_RE.findall(src or "") if w[0].isupper()}
        out = []
        for w in _EN_WORD_RE.findall(PLACEHOLDER_RE.sub(" ", dst or "")):
            lw = w.lower()
            if lw not in known and lw not in out:
                out.append(w)
        return out

    def _update_preview_rows(self, batch):
        rev = {i: r for r, i in self.unit_rows.items()}
        tgt = getattr(self.translator, "tgt", None) or self.cfg.get("target", "ru")
        for i in batch:
            row = rev.get(i)
            if row is None or i >= len(self.units):
                continue
            u = self.units[i]
            dst = self.prev_table.item(row, 3)
            st = self.prev_table.item(row, 4)
            text = u["dst"] or ""

            # Валидатор длины: MCM/JSON/XML — длинный перевод не влезет в интерфейс
            too_long = is_ui_length_file(u.get("rel", "")) and is_too_long(u["src"], text)
            u["too_long"] = too_long
            u["mixed"] = False
            if dst:
                dst.setText(text[:300])
                dst.setForeground(QtGui.QBrush(
                    QtGui.QColor(C["warn_len"] if too_long else C["text"])))

            if st:
                notes = []
                if too_long:
                    notes.append(self.tr("tip_len_warn"))
                    notes.append(self.tr("tip_len_note").format(
                        n=len(text), m=len(u["src"])))
                if u.get("sst"):
                    notes.append(self.tr("tip_sst"))

                if u.get("err"):
                    st.setText("✗")
                    st.setForeground(QtGui.QBrush(QtGui.QColor(C["err"])))
                else:
                    ok, lost = check_placeholders(u["src"], text)
                    if not ok:
                        u["lost_tokens"] = lost
                        st.setText("🚫")
                        st.setToolTip(_tx("Потеряны плейсхолдеры! Это вызовет вылет игры.", "プレースホルダーが失われています！ゲームがクラッシュします。")
                                      + (_tx(f"\nПотеряно: {', '.join(lost[:6])}", f"\n欠落: {', '.join(lost[:6])}") if lost else "")
                                      + (("\n" + "\n".join(notes)) if notes else ""))
                        st.setForeground(QtGui.QBrush(QtGui.QColor(C["err"])))
                    elif has_mixed_language(u["src"], text, tgt):
                        u.pop("lost_tokens", None)
                        u["mixed"] = True
                        words = self._mixed_words(u["src"], text)
                        st.setText("🔤")
                        st.setToolTip(self.tr("tip_mixed")
                                      + (f"\n{self.tr('tip_mixed_words').format(words=', '.join(words[:6]))}"
                                         if words else "")
                                      + (("\n" + "\n".join(notes)) if notes else ""))
                        st.setForeground(QtGui.QBrush(QtGui.QColor(C["mixed"])))
                    elif u.get("sst"):
                        u.pop("lost_tokens", None)
                        st.setText("📖")
                        st.setToolTip(self.tr("tip_sst"))
                        st.setForeground(QtGui.QBrush(QtGui.QColor(C["ok"])))
                    else:
                        u.pop("lost_tokens", None)
                        st.setText("✓")
                        if notes:
                            st.setToolTip("\n".join(notes))
                        st.setForeground(QtGui.QBrush(QtGui.QColor(C["ok"])))

    def _finish(self, cancelled=False):
        if not self.running:
            return
        self.running = False
        self.btn_translate.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.btn_save.setEnabled(True)
        
        # --- СОХРАНЕНИЕ КЭША НА ДИСК ---
        if hasattr(self, "translation_cache") and hasattr(self, "cache_file"):
            try:
                with open(self.cache_file, "w", encoding="utf-8") as f:
                    json.dump(self.translation_cache, f, ensure_ascii=False, indent=2)
            except Exception as e:
                self._log("err", _tx(f"Ошибка сохранения кэша: {e}", f"キャッシュの保存エラー: {e}"))
        # -------------------------------
        
        if cancelled:
            self._log("warn", _tx(f"Остановлено: {self.stats['done']}/{self.stats['total']}", f"停止: {self.stats['done']}/{self.stats['total']}"))
            self.lbl_progress.setText(_tx("остановлено", "停止"))
        else:
            # --- АВТО-ИСПРАВЛЕНИЕ ПОТЕРЯННЫХ ТОКЕНОВ ---
            bad_items = []
            bad_idxs = []
            for i, u in enumerate(self.units):
                if u.get("excluded", False) or not (u.get("dst") or "").strip():
                    continue
                if u.get("err"):
                    continue
                ok, _ = check_placeholders(u["src"], u["dst"])
                if not ok:
                    bad_items.append((u["src"], u["dst"]))
                    bad_idxs.append(i)
            
            if bad_items:
                self._log("warn", _tx(f"Найдено {len(bad_items)} строк с потерянными токенами. Запуск авто-исправления…", f"トークンが欠落した行が {len(bad_items)} 件あります。自動修正を開始…"))
                self.lbl_progress.setText(_tx("Авто-исправление токенов…", "トークンを自動修正中…"))
                
                batch_size = 20
                self._autofix_active = True
                self.btn_cancel.setEnabled(True)
                self.btn_translate.setEnabled(False)
                try:
                    for chunk_start in range(0, len(bad_items), batch_size):
                        # 画面を固めない & キャンセルを受け付ける
                        QtWidgets.QApplication.processEvents()
                        if self.cancel_ev.is_set():
                            self._log("warn", _tx("Автоисправление прервано.", "自動修正を中断しました。"))
                            break
                        chunk = bad_items[chunk_start:chunk_start+batch_size]
                        idx_chunk = bad_idxs[chunk_start:chunk_start+batch_size]
                        
                        # LLM 呼び出しは別スレッドで。待つ間も画面とキャンセルボタンを動かす
                        box = {}
                        th = threading.Thread(
                            target=lambda c=chunk: box.__setitem__(
                                "r", self.translator.fix_placeholders_batch(c, self.cancel_ev)),
                            daemon=True)
                        th.start()
                        while th.is_alive() and not self.cancel_ev.is_set():
                            QtWidgets.QApplication.processEvents()
                            th.join(0.05)
                        if self.cancel_ev.is_set():
                            self._log("warn", _tx("Автоисправление прервано.", "自動修正を中断しました。"))
                            break
                        fixed_results = box.get("r") or [d for _s, d in chunk]
                        
                        for i, fixed_text in zip(idx_chunk, fixed_results):
                            self.units[i]["dst"] = fixed_text
                            self._update_preview_rows([i])
                finally:
                    self._autofix_active = False
                    self.btn_cancel.setEnabled(False)
                    self.btn_translate.setEnabled(True)
                
                remaining = sum(1 for u in self.units if not u.get("excluded") and not u.get("err") and not check_placeholders(u["src"], u.get("dst") or "")[0])
                if remaining == 0:
                    self._log("ok", _tx("Авто-исправление успешно: все плейсхолдеры восстановлены.", "自動修正成功: すべてのプレースホルダーを復元しました。"))
                else:
                    self._log("err", _tx(f"Не удалось восстановить токены в {remaining} строках. Проверьте вручную.", f"{remaining} 行のトークンを復元できませんでした。手動で確認してください。"))
            # --------------------------------------------

            extra = (_tx(f", из словаря {self.stats.get('sst', 0)}", f"、辞書から {self.stats.get('sst', 0)} 件")
                     if self.stats.get("sst") else "")
            self._log("ok", _tx(f"Готово: {self.stats['done'] - self.stats['errors']} переведено, "
                            f"ошибок {self.stats['errors']}{extra}.", f"完了: {self.stats['done'] - self.stats['errors']} 件翻訳、エラー {self.stats['errors']} 件{extra}。"))
            n_long = sum(1 for u in self.units if u.get("too_long"))
            n_mixed = sum(1 for u in self.units if u.get("mixed"))
            if n_long or n_mixed:
                self._log("warn", self.tr("sum_warnings").format(long=n_long, mixed=n_mixed))
            self.progress.setValue(1000)
            self.lbl_progress.setText(_tx(f"готово · {self.stats['done']}/{self.stats['total']}", f"完了 · {self.stats['done']}/{self.stats['total']}"))
            if self._permod_queue is None:
                errs = self.stats.get("errors", 0)
                self._notify_done(_tx(
                    f"Перевод завершён: {self.stats['done'] - errs} строк, ошибок {errs}.",
                    f"翻訳が完了しました。\n\n翻訳 {self.stats['done'] - errs} 行 / エラー {errs} 行 / "
                    f"所要 {self._fmt_dur(time.time() - self.stats.get('t0', time.time()))}\n\n"
                    f"内容を確認してから「出力を保存」を押してください。"), ok=(errs == 0))

        # --- Mod ごとに自動保存 ---
        if self._permod_queue is not None:
            if cancelled or self.cancel_ev.is_set():
                self._log("warn", _tx("Пакетный режим остановлен.",
                                      f"Mod ごとの処理を中止しました（残り {len(self._permod_queue)} 個は未処理）。"))
                self.lbl_progress_all.setText(_tx(
                    f"Остановлено {self.progress_all.value()}/{self._permod_total}",
                    f"全体 中止 {self.progress_all.value()}/{self._permod_total} · {self._fmt_dur(time.time() - self._overall_t0)}"))
                self._permod_queue = None
                self._permod_current = None
            else:
                try:
                    self._permod_save_current()
                except Exception as e:
                    self._log("err", _tx(f"Ошибка автосохранения: {e}", f"自動保存エラー: {e}"))
                QtCore.QTimer.singleShot(0, self._permod_start_next)

    # ── Mod ごとに自動保存 ────────────────────────────────────────────────
    def _permod_out_name(self, mod_name):
        tgt = self.cfg.get("target") or "ru"
        suffix = "rus" if tgt == "ru" else tgt
        base = re.sub(r'[<>:"/\\|?*]', "_", mod_name).strip().rstrip(".") or "TranslatedMod"
        return f"{base}_{suffix}"

    def _permod_start_next(self):
        if self._permod_queue is None:
            return
        if not self._permod_queue:
            total = self._permod_total
            self._permod_queue = None
            self._permod_current = None
            self.progress_all.setValue(self.progress_all.maximum())
            self.lbl_progress_all.setText(_tx(
                f"Всего готово {total}/{total} · {self._fmt_dur(time.time() - self._overall_t0)}",
                f"全体 完了 {total}/{total} · 所要 {self._fmt_dur(time.time() - self._overall_t0)}"))
            self._log("ok", _tx(f"Все моды обработаны: {total}", f"全 {total} 個の Mod の処理が終わりました。"))
            if self.chk_inplace.isChecked():
                self._refresh_organizer()
            self._notify_done(_tx(
                f"Все моды обработаны: {total}.",
                f"全 {total} 個の Mod の翻訳と保存が完了しました。\n\n"
                f"所要 {self._fmt_dur(time.time() - self._overall_t0)}\n"
                + ("訳は各 Mod のフォルダに書き込みました（MO2 の表示も更新済み）。"
                   if self.chk_inplace.isChecked() else
                   f"保存先: {self.ed_folder.text().strip()}")))
            self.lbl_progress.setText(_tx("готово", "すべて完了"))
            return
        mod = self._permod_queue.pop(0)
        self._permod_current = mod
        n = self._permod_total - len(self._permod_queue)
        self.progress_all.setValue(n - 1)
        self._update_overall_label(force=True)
        # 前の Mod のデータを捨ててメモリを空ける
        self.units = []
        self.jobs = []
        self.unit_rows = {}
        self.prev_table.setRowCount(0)
        self.cancel_ev.clear()
        self.run_id += 1
        self._last_req_ts = 0.0
        self.running = True
        self.btn_translate.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_save.setEnabled(False)
        self.progress.setValue(0)
        self.stats = {"done": 0, "total": 0, "errors": 0, "sst": 0, "t0": time.time()}
        self._log("info", _tx(f"[{n}/{self._permod_total}] {mod['name']}", f"[{n}/{self._permod_total}] {mod['name']}"))
        self.lbl_progress.setText(f"[{n}/{self._permod_total}] {mod['name']}")
        self._scan_opts = self._capture_scan_opts()
        threading.Thread(
            target=self._collect_worker,
            args=(self.run_id, self._scan_opts["bsa"], self._scan_opts["enc"],
                  self._scan_opts["risky"], [mod]),
            daemon=True).start()

    @staticmethod
    def _fmt_dur(sec):
        sec = int(max(0, sec))
        h, rem = divmod(sec, 3600)
        m, s_ = divmod(rem, 60)
        return f"{h}:{m:02d}:{s_:02d}" if h else f"{m:02d}:{s_:02d}"

    def _update_overall_label(self, force=False):
        if self._permod_queue is None:
            return
        now = time.time()
        if not force and now - self._overall_last < 1.0:
            return
        self._overall_last = now
        total = self._permod_total
        cur = (self._permod_current or {}).get("name", "")
        done_n = self.progress_all.value()          # 終わった Mod 数
        elapsed = now - self._overall_t0
        # 現在の Mod の進み具合も加味した完了率
        frac_cur = 0.0
        if self.running and self.stats.get("total"):
            frac_cur = min(1.0, self.stats.get("done", 0) / max(1, self.stats["total"]))
        progress = (done_n + frac_cur) / max(1, total)
        eta = ""
        if progress > 0.02 and done_n >= 1:
            eta = _tx(f" · осталось ~{self._fmt_dur(elapsed / progress - elapsed)}",
                      f" · 残り目安 {self._fmt_dur(elapsed / progress - elapsed)}")
        self.lbl_progress_all.setText(_tx(
            f"Всего {done_n + 1}/{total} · {self._fmt_dur(elapsed)}{eta}",
            f"全体 {done_n + 1}/{total} · 経過 {self._fmt_dur(elapsed)}{eta}"))
        self.lbl_progress_all.setToolTip(cur)

    def _refresh_organizer(self):
        """元 Mod に書き込んだファイルを MO2 に認識させる（F5 相当）。"""
        org = getattr(self.plugin, "_organizer", None)
        if org is None:
            return
        try:
            org.refresh(True)
            self._log("ok", _tx("MO2 обновлён.", "MO2 の表示を更新しました（F5 相当）。"))
        except Exception as e:
            self._log("warn", _tx(f"Не удалось обновить MO2: {e}",
                                  f"MO2 の更新に失敗しました。手動で F5 を押してください: {e}"))

    def _inplace_manifest_path(self, mod_root, mod_name):
        return find_manifest(mod_root, mod_name)

    def _permod_save_current(self):
        mod = self._permod_current
        if not mod:
            return
        if not any((u.get("dst") or "").strip() and not u.get("excluded") for u in self.units):
            if self.chk_inplace.isChecked():
                # 訳す行が無い Mod も「確認済み」として記録（次回から未翻訳に出さない）
                self._log("info", _tx(f"{mod['name']}: нечего переводить — отмечено как проверенное",
                                      f"{mod['name']}: 翻訳する行がないので、確認済みとして記録します"))
            else:
                self._log("info", _tx(f"{mod['name']}: нечего сохранять",
                                      f"{mod['name']}: 翻訳済みの行がないので出力しません"))
                return
        if self.chk_inplace.isChecked():
            self.save_output(name_override=mod["name"], auto=True,
                             out_root_override=mod["path"], inplace=True)
            try:
                self._compute_statuses([mod])
                self._update_mod_status_row(mod)
            except Exception:
                pass
        else:
            self.save_output(name_override=self._permod_out_name(mod["name"]), auto=True)

    def cancel_translation(self):
        if not (self.running or self._autofix_active or self._permod_queue is not None):
            return
        self.cancel_ev.set()
        self._log("warn", _tx("Отмена…", "キャンセル中…"))
        if self._autofix_active:
            return              # 自動修正ループが cancel_ev を見て抜ける
        if self.running:
            # 応答待ち中の LLM リクエストや収集スレッドの完了を待たずに止める。
            # run_id を進めるので、後から届く結果は _poll で捨てられる。
            self.run_id += 1
            self._finish(cancelled=True)
        elif self._permod_queue is not None:
            self._log("warn", _tx("Пакетный режим остановлен.",
                                  f"Mod ごとの処理を中止しました（残り {len(self._permod_queue)} 個は未処理）。"))
            self.lbl_progress_all.setText(_tx(
                f"Остановлено {self.progress_all.value()}/{self._permod_total}",
                f"全体 中止 {self.progress_all.value()}/{self._permod_total}"))
            self._permod_queue = None
            self._permod_current = None

    # ── сохранение ────────────────────────────────────────────────────────
    def _auto_out_name(self):
        tgt = self.cb_tgt.currentData() or "ru"
        suffix = "rus" if tgt == "ru" else tgt
        sel = [m for m in self.mods if m["selected"]]
        if len(sel) == 1:
            base = sel[0]["name"]
            for ext in (".esp", ".esm", ".esl", ".zip", ".7z", ".rar",
                        ".bsa", ".ba2"):
                if base.lower().endswith(ext):
                    base = base[:-len(ext)]
                    break
        else:
            mods = sorted({u.get("mod", "") for u in self.units if u.get("mod")})
            base = mods[0] if len(mods) == 1 else "TranslatedMod"
        return f"{base}_{suffix}"

    def _sync_out_name(self):
        if not self._name_manual:
            self.ed_name.setText(self._auto_out_name())
              
    def save_output(self, *_args, name_override=None, auto=False,
                    out_root_override=None, inplace=False):
        """auto=True（Mod ごと自動保存）ではダイアログを出さない:
        プレースホルダー欠落行は原文に戻し、既存 zip は上書きする。
        inplace=True は元の Mod フォルダ（out_root_override）へ直接書き込む。"""
        # 手動保存で「元の Mod に直接書き込む」がオン → Mod ごとに分けて保存
        if not inplace and self.chk_inplace.isChecked():
            all_units = self.units
            by_mod = OrderedDict()
            for u in all_units:
                by_mod.setdefault(u.get("mod"), []).append(u)
            try:
                for mod_name, us in by_mod.items():
                    mod_obj = next((m for m in self.mods if m["name"] == mod_name), None)
                    if not mod_obj:
                        self._log("err", _tx(f"{mod_name}: папка мода не найдена",
                                             f"{mod_name}: Mod フォルダが見つからないので保存しません"))
                        continue
                    self.units = us
                    self.save_output(name_override=mod_name, auto=auto,
                                     out_root_override=mod_obj["path"], inplace=True)
            finally:
                self.units = all_units
            self._refresh_organizer()
            return
        folder = self.ed_folder.text().strip()
        if out_root_override:
            folder = os.path.dirname(os.path.abspath(out_root_override))
        if inplace:
            root_n = os.path.normcase(os.path.abspath(out_root_override or ""))
            mods_root = getattr(self, "_mods_root", None)
            if not out_root_override or not os.path.isdir(out_root_override) or \
                    (mods_root and os.path.dirname(root_n) != mods_root):
                # DLC / 非管理 Mod（ゲームの Data を指す）などには書き込まない
                self._log("err", _tx(f"{name_override}: не в папке mods — пропуск",
                                     f"{name_override}: MO2 の mods フォルダ内の Mod ではないので書き込みません"))
                return
        if not folder:
            if auto:
                self._log("err", self.tr("msg_no_folder"))
                return
            QtWidgets.QMessageBox.warning(self, APP_NAME, self.tr("msg_no_folder"))
            return
        if name_override:
            name = name_override
        else:
            if not self.ed_name.text().strip():
                self.ed_name.setText(self._auto_out_name())
            name = self.ed_name.text().strip()
        want_zip = self.chk_zip.isChecked() and not out_root_override
        os.makedirs(folder, exist_ok=True)
        written = 0
        errors = 0
        tmp_dir = None
        
        # Защита от потери плейсхолдеров
        bad_rows = 0
        for u in self.units:
            if u.get("excluded", False) or not (u.get("dst") or "").strip():
                continue
            if u.get("lost_tokens") or not check_placeholders(u["src"], u["dst"])[0]:
                bad_rows += 1
                
        if bad_rows and auto:
            for u in self.units:
                if u.get("excluded", False) or not (u.get("dst") or "").strip():
                    continue
                if u.get("lost_tokens") or not check_placeholders(u["src"], u["dst"])[0]:
                    u["dst"] = u["src"]
            self._log("warn", _tx(f"{bad_rows} строк с потерянными плейсхолдерами сохранены в оригинале",
                                  f"プレースホルダーが欠けた {bad_rows} 行は原文のまま保存します"))
        elif bad_rows:
            ans = QtWidgets.QMessageBox.warning(
                self, APP_NAME, self.tr("msg_placeholder_warn").replace("{n}", str(bad_rows)),
                BTN_YES | BTN_NO,
                BTN_NO)
            if ans != BTN_YES:
                self._log("warn", _tx(f"Сохранение отменено: {bad_rows} строк с потерянными плейсхолдерами", f"保存を中止しました: プレースホルダー欠落行 {bad_rows} 件"))
                return

        try:
            groups = {}
            for u in self.units:
                # Пропускаем файлы, с которых снята галочка в предпросмотре
                if u.get("excluded", False):
                    continue
                key = (u.get("mod", name), u.get("orig_path") or u["rel"],
                       u["kind"].split("_")[0])
                groups.setdefault(key, []).append(u)
                
            if want_zip:
                zpath = os.path.join(folder, name + ".zip")
                if os.path.exists(zpath) and auto:
                    self._log("info", _tx(f"Перезапись: {zpath}", f"上書きします: {zpath}"))
                elif os.path.exists(zpath):
                    ans = QtWidgets.QMessageBox.question(
                        self, APP_NAME,
                        self.tr("msg_zip_overwrite").format(path=zpath),
                        BTN_YES | BTN_NO)
                    if ans != BTN_YES:
                        return
                tmp_dir = tempfile.mkdtemp(prefix=name + "_")
                out_root = os.path.join(tmp_dir, name)
            elif out_root_override:
                out_root = out_root_override
                zpath = None
            else:
                out_root = os.path.join(folder, name)
                zpath = None

            target_code = self.cfg["target"]
            # in_place: 自分が書いたファイルの記録（Mod ごとに別名 → MO2 上で競合表示にならない）
            manifest_path = self._inplace_manifest_path(out_root, name) if inplace else None
            manifest = {"tool": APP_NAME, "target": target_code, "files": [], "backups": []}
            if inplace and os.path.exists(manifest_path):
                try:
                    with open(manifest_path, encoding="utf-8") as f:
                        manifest.update(json.load(f))
                except Exception:
                    pass
            ours = {os.path.normcase(x) for x in manifest.get("files", [])}
            src_code = self.cfg.get("source", "en")
            skipped_existing = 0
            dests = {}

            for (mod, rel, _kind), us in groups.items():
                u0 = us[0]
                kind = u0["kind"]
                
                rel_clean = rel.split("//")[-1] if "//" in rel else rel
                dir_part = os.path.dirname(rel_clean)
                fname = _localize_name(os.path.basename(rel_clean), target_code)
                
                if kind in ("strings", "txt_line", "archive_txt", "swf_line", "ini_line", "ini"):
                    out_rel = os.path.join(dir_part, fname) if dir_part else fname
                else:
                    out_rel = rel_clean
                
                enc_to_use = self.cfg["encoding"]
                if target_code in ("zh-CN", "zh-TW", "zh"):
                    enc_to_use = "utf-8"
                else:
                    mod_obj = next((m for m in self.mods if m["name"] == u0.get("mod")), None)
                    if mod_obj and "//" not in rel:
                        orig_path = os.path.normpath(os.path.join(mod_obj["path"], rel))
                        if os.path.exists(orig_path):
                            try:
                                with open(orig_path, "rb") as f:
                                    enc_to_use = detect_text_encoding(f.read(), self.cfg["encoding"])
                            except Exception:
                                pass

                if kind == "strings":
                    entries = [(u["sid"], u["dst"] if u["dst"] is not None else u["src"]) for u in us]
                    if not out_rel.lower().endswith((".strings", ".dlstrings", ".ilstrings")):
                        out_rel = os.path.splitext(out_rel)[0] + u0.get("ext", ".strings")
                    dests[out_rel] = ("strings", entries, enc_to_use)
                    
                elif kind in ("swf_line", "txt_line", "archive_txt"):
                    is_scaleform = (kind == "swf_line"
                                    or "translations" in out_rel.replace("\\", "/").lower())
                    nl = "\r\n" if is_scaleform else "\n"
                    merge_base = u0.get("merge_base") if kind == "swf_line" else None
                    if merge_base is not None:
                        # 既存の翻訳先ファイルに、足りなかったキーの訳を追記する
                        out_rel = os.path.normpath(u0.get("merge_target") or out_rel)
                        body = merged_translation_body(
                            merge_base, (f"{u['key']}\t{u['dst'] or u['src']}" for u in us), nl)
                    elif kind == "swf_line":
                        body = nl.join(f"{u['key']}\t{u['dst'] or u['src']}" for u in us)
                    else:
                        body = nl.join(u["dst"] or u["src"] for u in us)
                    if not out_rel.lower().endswith(".txt"):
                        out_rel += ".txt"
                    # Skyrim の Interface/Translations は UTF-16 LE（BOM 必須）でないと読めない
                    dests[out_rel] = ("text", body, "utf-16-bom" if is_scaleform else enc_to_use,
                                      merge_base is not None)
                    
                elif kind in ("json", "json_kv"):
                    if not out_rel.endswith(".json"):
                        out_rel += ".json"
                    dests[out_rel] = ("json", us, "utf-8")
                    
                elif kind == "xml":
                    dests[out_rel] = ("xml", us, enc_to_use)

                elif kind in ("ini", "ini_line"):
                    dests[out_rel] = ("ini", us, enc_to_use)
                    
                elif kind == "esp_string":
                    dests[out_rel] = ("esp_string", us, "binary")

                elif kind == "pex_string":
                    dests[out_rel] = ("pex", us, "binary")

                elif kind == "skse_kv":
                    s_rel, s_body, s_enc, s_mode = build_skse_menu_output(us, target_code)
                    dests[os.path.normpath(s_rel)] = ("text", s_body, s_enc, s_mode)

            for out_rel, payload in dests.items():
                full = os.path.join(out_root, out_rel)
                try:
                    os.makedirs(os.path.dirname(full) or out_root, exist_ok=True)
                    ptype = payload[0]
                    pdata = payload[1]
                    enc = payload[2] if len(payload) > 2 else self.cfg["encoding"]
                    text_mode = payload[3] if ptype == "text" and len(payload) > 3 else False
                    is_merge = bool(text_mode) and text_mode != "overwrite"
                    is_overwrite = text_mode == "overwrite"

                    if inplace and ptype != "esp_string":
                        rel_key = os.path.normcase(os.path.normpath(out_rel))
                        if os.path.exists(full) and rel_key not in ours:
                            if ptype in ("json", "xml", "ini", "pex") or is_merge or is_overwrite:
                                # 元ファイルを上書きする形式: 元の版を .bak_<言語> に退避（既に訳済みなら退避し直さない）
                                # マージは作者などの翻訳先ファイルに追記するので、翻訳先言語の名前で退避する
                                bak = f"{full}.bak_{target_code if is_merge else src_code}"
                                try:
                                    with open(full, "rb") as f:
                                        cur = f.read()
                                    cur_txt = cur.decode(detect_text_encoding(cur, "utf-8"), "replace")
                                except Exception:
                                    cur, cur_txt = None, ""
                                # .pex はバイナリなので文字で判定できない → 退避が既にあれば作り直さない
                                renew = (not os.path.exists(bak)
                                         or (ptype != "pex" and not is_merge
                                             and not already_in_target(cur_txt, target_code, src_code)))
                                if cur is not None and renew:
                                    shutil.copy2(full, bak)
                                    b_rel = os.path.relpath(bak, out_root).replace("\\", "/")
                                    if b_rel not in manifest["backups"]:
                                        manifest["backups"].append(b_rel)
                            else:
                                # _japanese.txt / .strings 等が Mod 側に既にある → 本物の訳かもしれないので守る
                                skipped_existing += 1
                                self._log("warn", _tx(f"{out_rel}: файл уже есть в моде — не перезаписываю",
                                                      f"{out_rel}: Mod に同名ファイルが既にあるので上書きしません"))
                                continue
                        o_rel = out_rel.replace("\\", "/")
                        if o_rel not in manifest["files"]:
                            manifest["files"].append(o_rel)

                    if ptype == "strings":
                        write_strings_file(full, pdata, encoding=enc)
                        
                    elif ptype == "text":
                        if enc == "utf-16-bom":
                            with open(full, "wb") as f:
                                f.write(b"\xff\xfe" + pdata.encode("utf-16-le"))
                        else:
                            with open(full, "w", encoding=enc, newline="") as f:
                                f.write(pdata)
                            
                    elif ptype == "json":
                        self._write_json(full, pdata)

                    elif ptype == "xml":
                        rel = pdata[0].get("orig_path") or pdata[0].get("rel") or out_rel
                        orig_xml = pdata[0].get("orig_text", "")
                        if orig_xml:
                            out_xml = orig_xml
                            for u in pdata:
                                src = u.get("orig_src", u["src"])
                                trans = u["dst"] if u["dst"] else u["src"]
                                if src != trans:
                                    out_xml = out_xml.replace(src, trans)
                            with open(full, "w", encoding=enc, newline="") as f:
                                f.write(out_xml)
                        else:
                            self._log("warn", _tx(f"{rel}: нет исходного текста XML, файл пропущен", f"{rel}: XML の元テキストがないためスキップしました"))

                    elif ptype == "ini":
                        rel = pdata[0].get("orig_path") or pdata[0].get("rel") or out_rel
                        orig_ini = pdata[0].get("orig_text", "")
                        if orig_ini:
                            out_ini = orig_ini
                            for u in pdata:
                                src = u.get("orig_src", u["src"])
                                trans = u["dst"] if u["dst"] else u["src"]
                                if src != trans:
                                    out_ini = re.sub(
                                        rf'^(\s*{re.escape(u["key"])}\s*=\s*){re.escape(src)}',
                                        lambda match: match.group(1) + trans,
                                        out_ini, flags=re.MULTILINE
                                    )
                            with open(full, "w", encoding=enc, newline="") as f:
                                f.write(out_ini)
                        else:
                            self._log("warn", _tx(f"{rel}: нет исходного текста INI, файл пропущен", f"{rel}: INI の元テキストがないためスキップしました"))
                        
                    elif ptype == "pex":
                        rel = pdata[0].get("orig_path") or pdata[0].get("rel") or out_rel
                        mod_obj = next((m for m in self.mods if m["name"] == pdata[0].get("mod")), None)
                        src_path = os.path.normpath(os.path.join(mod_obj["path"], rel)) if mod_obj else ""
                        # 収集時に読んだのと同じファイル（in_place の再翻訳では訳済みの .pex）に差し替えを足す
                        if not src_path or not os.path.exists(src_path):
                            raise RuntimeError(_tx(f"не найден исходный скрипт {rel}",
                                                   f"元のスクリプト {rel} が見つかりません"))
                        with open(src_path, "rb") as f:
                            orig_data = f.read()
                        trans_dict = {u.get("orig_src", u["src"]): u["dst"]
                                      for u in pdata if u.get("dst") and not u.get("excluded")}
                        changes, new_data = pex_apply_translations(orig_data, trans_dict, self.cfg["encoding"])
                        with open(full, "wb") as f:
                            f.write(new_data)
                        self._log("ok" if changes else "warn", _tx(
                            f"{out_rel}: заменено {changes} мест",
                            f"{out_rel}: 表示用の文字列を {changes} か所差し替えました"))

                    elif ptype == "esp_string":
                        # 注意: ループ外の rel は別ファイルの値が残っているので、ユニットから取り直す
                        rel = pdata[0].get("orig_path") or pdata[0].get("rel") or out_rel
                        if self.chk_dsd.isChecked() or not self.chk_risky.isChecked() or inplace:
                            # --- ЭКСПОРТ В DSD ---
                            mod_name = pdata[0].get("mod")
                            plugin_file = os.path.basename(rel)
                            orig_data = None
                            mod_obj = next((m for m in self.mods if m["name"] == mod_name), None)
                            if mod_obj:
                                mod_path = mod_obj["path"]
                                if "//" not in rel:
                                    loose_path = os.path.normpath(os.path.join(mod_path, rel))
                                    if os.path.exists(loose_path):
                                        with open(loose_path, "rb") as f:
                                            orig_data = f.read()
                            
                            if orig_data:
                                esp_meta = EspStringExtractor(self.cfg["encoding"])
                                meta_list = esp_meta.extract_strings_with_meta(orig_data)
                                trans_map = {u.get("orig_src", u["src"]): (u["dst"] if u["dst"] else u["src"]) for u in pdata}
                                masters = esp_masters(orig_data)
                                dsd_entries = []
                                skipped_official = 0
                                for meta in meta_list:
                                    src_text = meta["src"]
                                    if src_text in trans_map and trans_map[src_text] != src_text:
                                        ref = dsd_form_ref(meta["form_id"], plugin_file, masters)
                                        if ref is None:
                                            skipped_official += 1
                                            continue
                                        entry = {
                                            "form_id": ref,
                                            "type": meta["type"],
                                            "string": trans_map[src_text]
                                        }
                                        if "index" in meta:
                                            entry["index"] = meta["index"]
                                        dsd_entries.append(entry)
                                
                                if skipped_official:
                                    self._log("info", _tx(
                                        f"DSD {plugin_file}: пропущено {skipped_official} строк официальных записей",
                                        f"DSD {plugin_file}: 本体/DLC/CC のレコードを上書きしている {skipped_official} 行は公式訳を残すため出力しません"))
                                if dsd_entries:
                                    dsd_dir = os.path.join(out_root, "SKSE", "Plugins", "DynamicStringDistributor", plugin_file)
                                    os.makedirs(dsd_dir, exist_ok=True)
                                    dsd_name = (f"MO2TranslationTool_{target_code}.json" if inplace
                                                else "translation.json")
                                    dsd_path = os.path.join(dsd_dir, dsd_name)
                                    if inplace:
                                        d_rel = os.path.relpath(dsd_path, out_root).replace("\\", "/")
                                        if d_rel not in manifest["files"]:
                                            manifest["files"].append(d_rel)
                                    with open(dsd_path, "w", encoding="utf-8") as f:
                                        json.dump(dsd_entries, f, ensure_ascii=False, indent=2)
                                    self._log("ok", _tx(f"DSD: создан {dsd_path} ({len(dsd_entries)} строк)", f"DSD: {dsd_path} を作成しました ({len(dsd_entries)} 行)"))
                                else:
                                    self._log("warn", _tx(f"DSD: нет переведённых строк для {plugin_file}", f"DSD: {plugin_file} に翻訳済みの行がありません"))
                            else:
                                self._log("err", _tx(f"DSD: не найден оригинал {plugin_file}", f"DSD: 元の {plugin_file} が見つかりません"))
                        else:
                            # --- ОБЫЧНОЕ СОХРАНЕНИЕ .ESP ---
                            mod_name = pdata[0].get("mod")
                            mod_obj = next((m for m in self.mods if m["name"] == mod_name), None)
                            orig_data = None
                            orig_path_found = ""
                            
                            if mod_obj:
                                mod_path = mod_obj["path"]
                                if "//" in rel:
                                    bsa_name, inner_path = rel.split("//", 1)
                                    bsa_path = os.path.join(mod_path, bsa_name)
                                    reader = read_ba2_text if bsa_path.lower().endswith(".ba2") else read_bsa_text
                                    try:
                                        inner = reader(bsa_path, wanted=(os.path.splitext(inner_path)[1],))
                                        orig_data = inner.get(inner_path.replace("\\", "/"))
                                    except Exception as e:
                                        self._log("err", _tx(f"Ошибка чтения BSA {bsa_name}: {e}", f"BSA {bsa_name} の読み込みエラー: {e}"))
                                else:
                                    loose_path = os.path.normpath(os.path.join(mod_path, rel))
                                    orig_path_found = loose_path
                                    if os.path.exists(loose_path):
                                        with open(loose_path, "rb") as f:
                                            orig_data = f.read()
                            
                            if orig_data:
                                trans_dict = {u.get("orig_src", u["src"]): (u["dst"] if u["dst"] else u["src"]) for u in pdata}
                                esp = EspStringExtractor(self.cfg["encoding"])
                                changes, new_data = esp.apply_translations(orig_data, trans_dict)
                                with open(full, "wb") as f:
                                    f.write(new_data)
                                if changes == 0:
                                    self._log("warn", _tx(f"{out_rel}: текст не изменился, но .esp сохранен.", f"{out_rel}: テキストに変更はありませんが .esp を保存しました。"))
                            else:
                                self._log("err", _tx(f"{out_rel}: Не найден оригинальный .esp: {orig_path_found}", f"{out_rel}: 元の .esp が見つかりません: {orig_path_found}"))

                    written += 1
                except Exception as e:
                    errors += 1
                    self._log("err", _tx(f"Ошибка записи {out_rel}: {e}", f"{out_rel} の書き込みエラー: {e}"))

            if inplace:
                written_set = {os.path.normcase(os.path.normpath(x)) for x in manifest["files"]}
                manifest["written"] = {r: _file_sig(os.path.join(out_root, r))
                                       for r in manifest["files"]
                                       if os.path.exists(os.path.join(out_root, r))}
                srcs = dict(manifest.get("sources") or {})
                for rel_g in {(u.get("orig_path") or u.get("rel") or "") for u in self.units}:
                    if not rel_g:
                        continue
                    src_rel = rel_g.split("//")[0].replace("\\", "/")
                    if os.path.normcase(os.path.normpath(src_rel)) in written_set:
                        continue      # その場で上書きしたファイル（config.json 等）は written 側で見る
                    sig = _file_sig(os.path.join(out_root, src_rel))
                    if sig:
                        srcs[src_rel] = sig
                manifest["sources"] = srcs
                try:
                    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
                    with open(manifest_path, "w", encoding="utf-8") as f:
                        json.dump(manifest, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    self._log("err", _tx(f"Манифест не сохранён: {e}", f"記録ファイルを保存できませんでした: {e}"))
                if skipped_existing:
                    self._log("info", _tx(f"Пропущено существующих файлов: {skipped_existing}",
                                          f"既存ファイルを保護してスキップ: {skipped_existing} 件"))

            if self.chk_report.isChecked() and not inplace:
                try:
                    report_path = os.path.join(out_root, "_report.txt")
                    with open(report_path, "w", encoding="utf-8") as f:
                        f.write(_tx("=== ОТЧЁТ О ПЕРЕВОДЕ ===\n\n", "=== 翻訳レポート ===\n\n"))
                        for u in self.units:
                            if u.get("src"):
                                status = "OK" if u.get("dst") and u["dst"] != u["src"] else _tx("БЕЗ ИЗМЕНЕНИЙ / ОШИБКА", "変更なし / エラー")
                                f.write(f"[{u.get('rel', 'Unknown')}]\n")
                                f.write(_tx(f"Оригинал: {u['src']}\n", f"原文: {u['src']}\n"))
                                f.write(_tx(f"Перевод:  {u.get('dst', '')} (Статус: {status})\n\n", f"訳文: {u.get('dst', '')} (状態: {status})\n\n"))
                    written += 1
                    self._log("ok", _tx(f"Отчёт сохранен: {report_path}", f"レポートを保存しました: {report_path}"))
                except Exception as e:
                    self._log("err", _tx(f"Ошибка отчёта: {e}", f"レポートのエラー: {e}"))

            if want_zip:
                with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
                    for dp, _d, fs in os.walk(out_root):
                        for fn in fs:
                            fp = os.path.join(dp, fn)
                            z.write(fp, f"{name}/{os.path.relpath(fp, out_root)}")
                self._log("ok", _tx(f"Архив: {zpath} ({written} файлов)", f"アーカイブ: {zpath} ({written} ファイル)"))
            else:
                self._log("ok", _tx(f"Сохранено файлов: {written}, ошибок: {errors} → {out_root}", f"保存: {written} ファイル、エラー: {errors} → {out_root}"))

        except Exception as e:
            if auto:
                self._log("err", f"{self.tr('msg_save_error')} {name}: {e}")
                return
            QtWidgets.QMessageBox.critical(
                self, APP_NAME, f"{self.tr('msg_save_error')}\n{e}")
            return
        finally:
            if tmp_dir and os.path.isdir(tmp_dir):
                shutil.rmtree(tmp_dir, ignore_errors=True)                

    def _write_json(self, path, us):
        try:
            data = json.loads(us[0].get("orig_text") or "{}")
        except Exception:
            data = {}

        def parse_key(kp):
            # load_json_units のキー表記 "a.b[0].c" → ["a", "b", 0, "c"]
            if isinstance(kp, (list, tuple)):
                return list(kp)
            return [int(i) if i else k
                    for k, i in re.findall(r"([^.\[\]]+)|\[(\d+)\]", kp)]

        def setv(data, key_path, val):
            key_path = parse_key(key_path)
            if not key_path:
                return False
            node = data
            for i, k in enumerate(key_path):
                last = (i == len(key_path) - 1)
                if isinstance(k, int):
                    if not isinstance(node, list) or k < 0 or k >= len(node):
                        return False
                else:
                    if not isinstance(node, dict) or k not in node:
                        return False
                if last:
                    node[k] = val
                else:
                    node = node[k]
            return True

        misses = []
        for u in us:
            if u["kind"] == "json_kv":
                if not setv(data, u["key"], u["dst"] or u["src"]):
                    misses.append(u["key"])
        if misses:
            self._log("warn", _tx(f"JSON {os.path.basename(path)}: "
                              f"не найдено {len(misses)} ключей (пропущены)", f"JSON {os.path.basename(path)}: {len(misses)} 個のキーが見つからずスキップしました"))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _browse_out(self):
        d = QtWidgets.QFileDialog.getExistingDirectory(
            self, self.tr("folder"), self.ed_folder.text() or "~")
        if d:
            self.ed_folder.setText(d)

    def _open_out(self):
        folder = self.ed_folder.text().strip()
        if not folder or not os.path.isdir(folder):
            return
        try:
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                os.system(f'open "{folder}"')
            else:
                os.system(f'xdg-open "{folder}" 2>/dev/null')
        except Exception as e:
            self._log("err", _tx(f"Не удалось открыть: {e}", f"開けませんでした: {e}"))

    def closeEvent(self, ev):
        self._save_settings()
        if self.running:
            self.cancel_ev.set()
        self._gloss_save_timer.stop()
        try:
            self.glossary.save(self._log)
        except Exception as e:
            self._log("err", _tx(f"Словарь не сохранён при закрытии: {e}", f"終了時に用語集を保存できませんでした: {e}"))
        self.timer.stop()
        super().closeEvent(ev)
        
    def _filter_preview_table(self):
        search_text = self.ed_preview_search.text().lower()
        filter_idx = self.cb_preview_filter.currentIndex()
        file_filter = self.cb_file_filter.currentText()

        for row in range(self.prev_table.rowCount()):
            src_item = self.prev_table.item(row, 2)
            dst_item = self.prev_table.item(row, 3)
            stat_item = self.prev_table.item(row, 4)
            file_item = self.prev_table.item(row, 1)

            src = src_item.text().lower() if src_item else ""
            dst = dst_item.text().lower() if dst_item else ""
            status = stat_item.text() if stat_item else ""

            match_search = not search_text or (search_text in src) or (search_text in dst)

            match_file = (file_filter in ALL_FILES_LABELS) or (
                file_item is not None and file_item.text() == file_filter)

            match_filter = True
            if filter_idx == 1: # Ожидающие
                match_filter = (status == "…" or status == "Ожидает")
            elif filter_idx == 2: # Ошибки
                match_filter = (status == "✗")
            elif filter_idx == 3: # Технические
                match_filter = (status == "⚠️")
            elif filter_idx == 4: # Пропущенные
                match_filter = (status == "🚫")

            self.prev_table.setRowHidden(row, not (match_search and match_filter and match_file))
            
    def _translate_selected_rows(self, rows):
        if self.running: return
        
        idxs = [self.unit_rows[r] for r in rows if r in self.unit_rows]
        if not idxs: return
        
        # 1. Сохраняем текущие настройки из интерфейса
        self.cfg.update({
            "backend": self.cb_backend.currentText(),
            "source": self.cb_src.currentData() or "en",
            "target": self.cb_tgt.currentData() or "ru",
            "encoding": self.cb_enc.currentText(),
            "ui_lang": self.lang,
            "openai_url": self.ed_openai_url.text().strip(),
            "openai_model": self.ed_openai_model.text().strip(),
            "openai_key": self.ed_openai_key.text().strip(),
            "ollama_url": self.ed_ollama_url.text().strip(),
            "ollama_model": self.ed_ollama_model.text().strip(),
            "lmstudio_url": self.ed_lm_url.text().strip(),
            "lmstudio_model": self.ed_lm_model.text().strip(),
            "openrouter_key": self.ed_or_key.text().strip(),
            "openrouter_model": self.ed_or_model.text().strip(),
            "deepl_key": self.ed_deepl.text().strip(),
            "yandex_key": self.ed_yandex.text().strip(),
            "temperature": self.sp_temp.value(),
            "max_tokens": self.sp_maxtok.value(),
            "system_prompt": self.txt_prompt.toPlainText(),
            "convert_units": self.chk_units.isChecked(),
            "delay_ms": self.sp_delay.value(),
            "threads": self.sp_threads.value(),
            "batch_size": self.sp_batch.value() if hasattr(self, "sp_batch") else 1,
            "dry_run": self.chk_dry.isChecked(),
            "extract_bsa": self.chk_bsa.isChecked(),
            "gen_report": self.chk_report.isChecked(),
            "out_folder": self.ed_folder.text().strip(),
            "out_name": self.ed_name.text().strip(),
            "save_zip": self.chk_zip.isChecked(),
            "save_dsd": self.chk_dsd.isChecked(),
            "allow_risky": self.chk_risky.isChecked(),
            "translate_pex": self.chk_pex.isChecked(),
            "translate_skse_menu": self.chk_skse.isChecked(),
            "per_mod_save": self.chk_permod.isChecked(),
            "in_place": self.chk_inplace.isChecked(),
            "status_filter": sorted(self._shown_states()),
            "notify_done": self.chk_notify.isChecked(),
        })
        save_config(self.cfg, self._log)

        # 2. Инициализация клиента и переводчика
        try:
            client = self._build_client()
            self.translator = Translator(
                client, PlaceholderProtector(), self.cfg["system_prompt"],
                self.cfg["source"], self.cfg["target"], self.glossary.items,
                repair=True, dry_run=self.cfg["dry_run"],
                unit_convert=self.cfg["convert_units"],
                log=self._log, sst_terms=self._sst_hint_terms())
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, APP_NAME, _tx(f"Ошибка инициализации переводчика:\n{e}", f"翻訳エンジンの初期化エラー:\n{e}"))
            return
        if not self._preflight_ok(client):
            return

        # 3. Загрузка кэша
        self.cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "translation_cache.json")
        self.translation_cache = {}
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.translation_cache = json.load(f)
                self._log("info", _tx(f"Загружен кэш: {len(self.translation_cache)} строк", f"キャッシュを読み込みました: {len(self.translation_cache)} 行"))
            except Exception as e:
                self._log("err", _tx(f"Не удалось загрузить кэш: {e}", f"キャッシュを読み込めませんでした: {e}"))

        # 4. Подготовка к работе
        self.cancel_ev.clear()
        self.run_id += 1
        my_run = self.run_id
        self.running = True
        self.btn_translate.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        
        self.stats = {"done": 0, "total": len(idxs), "errors": 0, "sst": 0, "t0": time.time()}
        self._log("warn", _tx(f"Выборочный перевод {len(idxs)} строк · {self.cfg['backend']} · потоков {self.cfg['threads']}...", f"選択した {len(idxs)} 行を翻訳 · {self.cfg['backend']} · スレッド {self.cfg['threads']}..."))
        
        # 5. Создаем пакеты только из выбранных строк
        batch_size = self.cfg.get("batch_size", 1)
        batches = [idxs[i:i + batch_size] for i in range(0, len(idxs), batch_size)]
        
        self.job_q = queue.Queue()
        for b in batches:
            self.job_q.put(b)
        for _ in range(self.cfg["threads"]):
            self.job_q.put(None)
            
        for _w in range(self.cfg["threads"]):
            threading.Thread(target=self._worker, args=(my_run, self.job_q), daemon=True).start()

    def _open_replace_dialog(self):
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle(self.tr("dlg_replace_title"))
        dlg.setMinimumWidth(400)
        
        layout = QtWidgets.QVBoxLayout(dlg)
        
        find_layout = QtWidgets.QHBoxLayout()
        find_layout.addWidget(QtWidgets.QLabel(self.tr("dlg_find")))
        ed_find = QtWidgets.QLineEdit()
        find_layout.addWidget(ed_find)
        layout.addLayout(find_layout)
        
        repl_layout = QtWidgets.QHBoxLayout()
        repl_layout.addWidget(QtWidgets.QLabel(self.tr("dlg_replace_to")))
        ed_repl = QtWidgets.QLineEdit()
        repl_layout.addWidget(ed_repl)
        layout.addLayout(repl_layout)
        
        cb_scope = QtWidgets.QComboBox()
        cb_scope.addItems([
            self.tr("dlg_scope_all"),    # 0: Везде (поиск и замена текста)
            self.tr("dlg_scope_src"),    # 1: Только в Оригинале (поиск и замена текста)
            self.tr("dlg_scope_dst"),    # 2: Только в Переводе (поиск и замена текста)
            _tx("По Оригиналу (Заменить весь Перевод)", "原文で一致（訳文全体を置換）") # 3: УМНЫЙ РЕЖИМ
        ])
        layout.addWidget(cb_scope)
        
        chk_visible = QtWidgets.QCheckBox(self.tr("dlg_filtered_only"))
        chk_visible.setChecked(True)
        layout.addWidget(chk_visible)
        
        btns = QtWidgets.QDialogButtonBox(
            BTN_OK | 
            BTN_CANCEL
        )
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)
        
        if _exec_dialog(dlg) == DLG_ACCEPTED:
            self._do_replace(ed_find.text(), ed_repl.text(), cb_scope.currentIndex(), chk_visible.isChecked())
            
    def _do_replace(self, find_text, repl_text, scope_idx, only_visible):
        if not find_text:
            return
            
        self._loading_preview = True
        self.prev_table.blockSignals(True)
        
        changes = 0
        
        try:
            for row in range(self.prev_table.rowCount()):
                if only_visible and self.prev_table.isRowHidden(row):
                    continue
                    
                idx = self.unit_rows.get(row)
                if idx is None:
                    continue
                    
                u = self.units[idx]
                changed = False
                
                # РЕЖИМ 3: Ищем в оригинале, перезаписываем перевод целиком
                if scope_idx == 3:
                    src_item = self.prev_table.item(row, 2)
                    dst_item = self.prev_table.item(row, 3)
                    if src_item and dst_item and find_text in src_item.text():
                        dst_item.setText(repl_text)
                        u["dst"] = repl_text
                        changed = True
                
                # Стандартные режимы (0, 1, 2)
                else:
                    # 1. Замена в Оригинале
                    if scope_idx in (0, 1):
                        src_item = self.prev_table.item(row, 2)
                        if src_item and find_text in src_item.text():
                            new_src = src_item.text().replace(find_text, repl_text)
                            if new_src != src_item.text():
                                src_item.setText(new_src)
                                u["src"] = new_src
                                changed = True
                                
                    # 2. Замена в Переводе
                    if scope_idx in (0, 2):
                        dst_item = self.prev_table.item(row, 3)
                        if dst_item and find_text in dst_item.text():
                            new_dst = dst_item.text().replace(find_text, repl_text)
                            if new_dst != dst_item.text():
                                dst_item.setText(new_dst)
                                u["dst"] = new_dst
                                changed = True
                                
                if changed:
                    changes += 1
                    st = self.prev_table.item(row, 4)
                    if st:
                        st.setText("✎")
                        st.setForeground(QtGui.QBrush(QtGui.QColor(C["accent"])))
        finally:
            self.prev_table.blockSignals(False)
            self._loading_preview = False
            
        if changes > 0:
            self._log("ok", _tx(f"Заменено '{find_text}' на '{repl_text}' в {changes} строках.", f"'{find_text}' を '{repl_text}' に置換しました（{changes} 行）。"))
            QtWidgets.QMessageBox.information(self, _tx("Готово", "完了"), _tx(f"Успешно изменено строк: {changes}.", f"{changes} 行を変更しました。"))
        else:
            self._log("warn", _tx("Совпадений для замены не найдено.", "置換対象が見つかりませんでした。"))
            QtWidgets.QMessageBox.warning(
                self, _tx("Не найдено", "見つかりません"), 
                _tx(f"Не найдено совпадений для '{find_text}'.\n\n"
                f"Проверьте, в какой колонке вы ищете.", f"'{find_text}' に一致するものが見つかりません。\n\n検索している列を確認してください。")
            )

    def _update_filter_combo(self):
        current_idx = self.cb_preview_filter.currentIndex()
        if current_idx < 0: current_idx = 0
        
        self.cb_preview_filter.blockSignals(True)
        self.cb_preview_filter.clear()
        self.cb_preview_filter.addItems([
            self.tr("filter_all"),
            self.tr("filter_pending"),
            self.tr("filter_errors"),
            self.tr("filter_warn"),
            self.tr("filter_missing")
        ])
        self.cb_preview_filter.setCurrentIndex(current_idx)
        self.cb_preview_filter.blockSignals(False)            


# ============================================================================
# Плагин MO2
# ============================================================================
class MO2TranslationToolPlugin(_PLUGIN_BASE):
    def __init__(self):
        if HAS_MOBASE:
            super().__init__()
        self._organizer = None
        self._parentWidget = None

    def name(self):
        return APP_NAME

    def localName(self):
        return APP_NAME

    def author(self):
        return "InfernoKgn (日本語化・改造: BluishCat)"

    def description(self):
        return (_tx("Перевод модов (plugins, strings, BSA/BA2, JSON) через LLM "
                "с глоссарием и защитой плейсхолдеров.", "LLM で Mod（プラグイン、strings、BSA/BA2、JSON）を翻訳。用語集とプレースホルダー保護付き。"))
                
    def baseName(self):
        return "MO2TranslationTool"

    def flags(self):
        return mobase.PluginFlag.NoFlags if hasattr(mobase, "PluginFlag") else 0

    def executionMode(self):
        return mobase.ExecutableMode.Basic if hasattr(mobase, "ExecutableMode") else 0

    def version(self):
        if not HAS_MOBASE:
            return None
        # "3.0.1-ja.1" → MO2 には数字部分 3.0.1 を渡す（表示名には APP_VERSION 全体を使う）
        nums = [int(x) for x in re.findall(r"\d+", APP_VERSION.split("-")[0])[:3]] + [0, 0, 0]
        try:
            return mobase.VersionInfo.fromString(".".join(map(str, nums[:3])))
        except Exception:
            try:
                return mobase.VersionInfo(nums[0], nums[1], nums[2])
            except Exception:
                return mobase.VersionInfo(nums[0], nums[1], nums[2], 0)

    def isActive(self):
        return True

    def settings(self):
        return []

    def init(self, organizer):
        self._organizer = organizer
        return True

    def displayName(self):
        return APP_NAME

    def tooltip(self):
        return _tx("Перевести моды через LLM (BSA/BA2, strings, JSON, txt)", "LLM で Mod を翻訳 (BSA/BA2, strings, JSON, txt)")

    def icon(self):
        try:
            px = QtGui.QPixmap(24, 24)
            px.fill(QtGui.QColor(0, 0, 0, 0))
            p = QtGui.QPainter(px)
            pen = QtGui.QPen(QtGui.QColor(C["accent"]))
            pen.setWidth(2)
            p.setPen(pen)
            p.setBrush(QtGui.QColor(C["panel2"]))
            p.drawRoundedRect(1, 1, 22, 22, 5, 5)
            p.setPen(QtGui.QPen(QtGui.QColor(C["accent"])))
            f = QtGui.QFont(
                "Segoe UI", 10,
                QtGui.QFont.Weight.Bold if hasattr(QtGui.QFont, "Weight")
                else QtGui.QFont.Bold)
            p.setFont(f)
            p.drawText(QtCore.QRect(0, 0, 24, 24), ALIGN_CENTER, "⇄")
            p.end()
            return QtGui.QIcon(px)
        except Exception:
            return QtGui.QIcon()

    def setParentWidget(self, widget):
        self._parentWidget = widget

    def display(self):
        parent = self._parentWidget
        if parent is None:
            try:
                parent = self._organizer.mainWindow()
            except Exception:
                parent = None
        dlg = TranslationDialog(self, parent)
        _exec_dialog(dlg)


def createPlugin():
    return MO2TranslationToolPlugin()


if __name__ == "__main__":
    if not HAS_MOBASE:
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        _ru, _en = T["msg_plugin_only"]
        QtWidgets.QMessageBox.warning(None, APP_NAME, _ru)
        sys.exit(0)