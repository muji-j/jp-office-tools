"""jp-office: スクリプト共通ユーティリティ(標準ライブラリのみ)."""
from __future__ import annotations
import os
import sys
from pathlib import Path

_XLSX_SUFFIXES = (".xlsx", ".xlsm")


class JpOfficeError(Exception):
    """利用者向けの日本語メッセージを持つ想定のドメイン例外の基底。"""


class UnsupportedFormatError(JpOfficeError):
    """サポート外のファイル形式(例: 旧 .xls バイナリ)."""


def is_xlsx(path) -> bool:
    return Path(path).suffix.lower() in _XLSX_SUFFIXES


def detect_encoding(path) -> tuple[str, str]:
    if is_xlsx(path):
        return "xlsx", "xlsx はバイナリ形式のため文字コード判定は不要"
    raw = Path(path).read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig", "UTF-8 BOM を検出"
    for enc in ("utf-8", "cp932", "euc_jp"):
        try:
            raw.decode(enc)
            return enc, f"{enc} で厳密デコード成功"
        except UnicodeDecodeError:
            continue
    return "cp932", "全候補で厳密デコード失敗 — cp932(errors='replace') でフォールバック"


def read_text_auto(path) -> str:
    enc, _ = detect_encoding(path)
    if enc == "xlsx":
        raise UnsupportedFormatError("xlsx はテキストとして読み込めません。")
    return Path(path).read_text(encoding=enc, errors="replace")


def run_cli(main_fn, argv) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass
    try:
        return main_fn(argv)
    except (FileNotFoundError, IsADirectoryError) as e:
        name = getattr(e, "filename", None) or ""
        print(f"ファイルが見つかりません: {name}".rstrip(), file=sys.stderr)
    except JpOfficeError as e:
        print(str(e), file=sys.stderr)
    except (ValueError, OSError, RuntimeError) as e:
        print(f"エラー: {e}", file=sys.stderr)
    except Exception as e:
        if os.environ.get("JP_OFFICE_DEBUG"):
            raise
        print(f"エラー: {e}", file=sys.stderr)
    return 1
