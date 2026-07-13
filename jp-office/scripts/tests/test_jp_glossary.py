import jp_glossary


def test_scan_variants_katakana_choon():
    g = jp_glossary.scan_variants("サーバーを設定。サーバは冗長化。サーバー監視。")
    surfs = [set(x["surfaces"]) for x in g]
    assert any({"サーバー", "サーバ"} <= s for s in surfs)


def test_scan_variants_fullwidth_halfwidth():
    g = jp_glossary.scan_variants("Ｗｅｂ会議とWeb会議を併用。Webは便利。")
    assert any({"Ｗｅｂ", "Web"} <= set(x["surfaces"]) for x in g)


def test_scan_variants_single_surface_excluded():
    # 表記が1種類だけなら表記ゆれではない → 除外
    g = jp_glossary.scan_variants("データベースを更新。データベースを参照。")
    assert all(len(x["surfaces"]) >= 2 for x in g)


def test_term_candidates_katakana():
    cands = jp_glossary.term_candidates("クラウド移行。クラウドは拡張性。オンプレミス比較。")
    terms = {c["term"] for c in cands}
    assert "クラウド" in terms


def test_main_variants_stdin(capsys, monkeypatch):
    import io
    monkeypatch.setattr("sys.stdin", io.StringIO("サーバーとサーバ"))
    rc = jp_glossary.main(["jp_glossary.py", "variants", "-"])
    assert rc == 0
    assert "サーバ" in capsys.readouterr().out
