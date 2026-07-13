import io, sys
import pytest
import jp_office_common as jc

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
