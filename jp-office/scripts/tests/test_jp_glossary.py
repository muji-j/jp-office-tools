import jp_glossary


def test_main_variants_euc_jp_file_no_crash(tmp_path):
    # H2回帰: euc_jp ファイルを cp932 と誤判定してクラッシュしないこと。
    f = tmp_path / "e.txt"
    f.write_bytes("サーバーとサーバの表記ゆれ".encode("euc_jp"))
    rc = jp_glossary.main(["jp_glossary.py", "variants", str(f)])
    assert rc == 0


def test_main_terms_file_path_acronym(tmp_path, capsys):
    # 日本語の漢字/かなは Python re の \w に含まれ \b が効かないため、
    # 記号や空白で区切って英字境界を作る(regex仕様に沿った現実的な入力)。
    f = tmp_path / "t.txt"
    f.write_text("(API)連携。(API)設計。SDK 利用。", encoding="utf-8")
    rc = jp_glossary.main(["jp_glossary.py", "terms", str(f)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "acronym" in out
    assert "API" in out


def test_term_candidates_acronym_kind():
    cands = jp_glossary.term_candidates("(API)を(API)で連携。SDK を利用。")
    kinds = {c["term"]: c["kind"] for c in cands}
    assert kinds.get("API") == "acronym"
    assert kinds.get("SDK") == "acronym"


def test_token_cap_still_detects_variants_after_cap():
    # M1-lite: 長さキャップ後もカタカナ/全角半角の表記ゆれ検出は不変。
    g = jp_glossary.scan_variants("サーバーを設定。サーバは冗長化。")
    surfs = [set(x["surfaces"]) for x in g]
    assert any({"サーバー", "サーバ"} <= s for s in surfs)
    g2 = jp_glossary.scan_variants("Ｗｅｂ会議とWeb会議を併用。")
    assert any({"Ｗｅｂ", "Web"} <= set(x["surfaces"]) for x in g2)


def test_token_cap_limits_long_kanji_run():
    # 長い漢字列("〜制度改正対応方針書類作成手続")が丸ごと1トークンに
    # ならず、キャップ長で区切られること(節・助詞まで飲み込む挙動の緩和)。
    text = "一二三四五六七八九十一二三四五六七八九十一二三四五六七八九十"
    toks = jp_glossary._TOKEN.findall(text)
    assert all(len(t) <= 12 for t in toks)


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


# ---- v0.7.2 Fix 2: 約語が日本語に隣接していても検出できる ----

def test_term_candidates_acronym_adjacent_to_japanese_no_parens_needed():
    # 修正前は \b が日本語文字との間に境界を作れず、括弧などの区切りが
    # ないと "API連携"・"KPI管理" の約語が検出できなかった。
    cands = jp_glossary.term_candidates("API連携を実装。KPI管理とSaaS事業。")
    terms = {c["term"]: c["kind"] for c in cands}
    assert terms.get("API") == "acronym"
    assert terms.get("KPI") == "acronym"
    assert terms.get("SaaS") == "acronym"


def test_term_candidates_long_english_word_not_fragmented():
    # 長い英単語("implementation")が2〜6文字の断片に分解されて
    # 誤検出されないこと(先読み/後読みで語の内部境界を弾く)。
    cands = jp_glossary.term_candidates("The implementation is done.")
    acronym_terms = {c["term"] for c in cands if c["kind"] == "acronym"}
    assert not any(t in "implementation" and len(t) < len("implementation")
                   for t in acronym_terms)
    assert "implementation" not in acronym_terms
