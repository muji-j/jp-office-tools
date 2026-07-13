import io, os, subprocess, sys
from pathlib import Path

import pytest
import jp_office_common as jc

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent

def test_is_xlsx(tmp_path):
    assert jc.is_xlsx("a.XLSX") and jc.is_xlsx("b.xlsm")
    assert not jc.is_xlsx("c.csv")

def test_detect_encoding_euc_jp(tmp_path):
    f = tmp_path / "e.txt"
    f.write_bytes("日本語のテスト".encode("euc_jp"))
    enc, _ = jc.detect_encoding(str(f))
    assert enc == "euc_jp"

def test_detect_encoding_bom(tmp_path):
    f = tmp_path / "b.csv"
    f.write_bytes(b"\xef\xbb\xbf" + "あ".encode("utf-8"))
    assert jc.detect_encoding(str(f))[0] == "utf-8-sig"

def test_read_text_auto_cp932(tmp_path):
    f = tmp_path / "c.txt"
    f.write_bytes("表記".encode("cp932"))
    assert "表記" in jc.read_text_auto(str(f))

def test_run_cli_catches_valueerror(capsys):
    def boom(argv):
        raise ValueError("だめな値です")
    rc = jc.run_cli(boom, ["prog"])
    assert rc == 1
    assert "だめな値です" in capsys.readouterr().err

def test_run_cli_catches_filenotfound(capsys):
    def boom(argv):
        open("no_such_file_xyz.txt")
    rc = jc.run_cli(boom, ["prog"])
    assert rc == 1
    assert "見つかりません" in capsys.readouterr().err

def test_run_cli_passthrough_success(capsys):
    def ok(argv):
        print("done"); return 0
    assert jc.run_cli(ok, ["prog"]) == 0
    assert capsys.readouterr().out.strip() == "done"

def test_run_cli_reraises_systemexit():
    def se(argv):
        raise SystemExit(2)
    with pytest.raises(SystemExit):
        jc.run_cli(se, ["prog"])


# ---- SP5 Fix 2: broad Exception catch + JP_OFFICE_DEBUG bypass ----

def test_run_cli_catches_unanticipated_exception(capsys):
    """KeyError/RuntimeError 直系のような未想定例外も、トレースバックを見せず rc=1 で終わる。"""
    def boom(argv):
        raise KeyError("想定外のキー")
    rc = jc.run_cli(boom, ["prog"])
    err = capsys.readouterr().err
    assert rc == 1
    assert err.strip() != ""
    assert "Traceback" not in err


def test_run_cli_debug_env_reraises(monkeypatch):
    """JP_OFFICE_DEBUG が設定されていれば未想定例外を再raiseする(開発者向け)。"""
    monkeypatch.setenv("JP_OFFICE_DEBUG", "1")

    def boom(argv):
        raise KeyError("想定外のキー")
    with pytest.raises(KeyError):
        jc.run_cli(boom, ["prog"])


# ---- SP5 Fix 1: run_cli で stdout/stderr を utf-8 に reconfigure ----

def test_run_cli_stderr_utf8_subprocess():
    """cp932 なWindows環境でも run_cli の親切エラー(stderr)が utf-8 で文字化けしないことを
    実プロセス経由で確認する(修正前は cp932 バイト列になり utf-8 デコードに失敗していた)。"""
    script = _SCRIPTS_DIR / "jp_dates.py"
    env = dict(os.environ)
    env.pop("PYTHONIOENCODING", None)
    result = subprocess.run(
        [sys.executable, str(script), "holiday", "notdate"],
        capture_output=True, env=env, cwd=str(_SCRIPTS_DIR),
    )
    assert result.returncode == 1
    decoded = result.stderr.decode("utf-8")  # 修正前は cp932 バイト列で utf-8 デコードに失敗していた
    assert "エラー" in decoded
    assert "Traceback" not in decoded
