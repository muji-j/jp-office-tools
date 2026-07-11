# jp-excel 定型作業レシピ

よくある作業を「手順」と「pandas コードスニペット」の対で示す。スクリプトで完結する作業はスクリプト呼び出しを、
スクリプトの結果を受けて分析する作業は pandas コードを示す。

## 1. 定型クレンジングパイプライン

**手順**

1. `jp_excel.py detect` でエンコーディングと判別根拠を確認する。
2. `jp_excel.py clean` でクレンジング済みコピーを別ファイルへ出力する(原本は変更しない)。
3. 出力される「クレンジング レポート」を読み、NFKC正規化・和暦変換・空白除去の件数が想定と合っているか確認する(想定より多い/少ない場合は元データの表記揺れを再確認)。

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_excel.py" detect 名簿.csv
python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_excel.py" clean 名簿.csv --out 名簿_cleaned.csv
```

```python
import pandas as pd

# クレンジング後のファイルを読み込み、想定どおりの形か確認する
df = pd.read_csv("名簿_cleaned.csv", dtype=str, encoding="utf-8-sig")
print(df.shape)
print(df.head())
```

## 2. 二つの名簿の突合(とつごう)

**手順**

1. 突合対象の両ファイルをそれぞれ `clean` でクレンジングし、表記揺れ(全角半角・和暦など)による偽差分を除去する。
2. `diff --key` に共通の一意キー列(社員番号・顧客IDなど)を指定して比較する。キー列に重複・空値があるとエラーになるため、事前に一意性を確認しておく。
3. 出力される「差分レポート」の変更セル・追加行・削除行を読み、業務的に意味のある差分かどうかを判断する。

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_excel.py" clean 名簿_旧.csv --out 名簿_旧_cleaned.csv
python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_excel.py" clean 名簿_新.csv --out 名簿_新_cleaned.csv
python "${CLAUDE_PLUGIN_ROOT}/scripts/jp_excel.py" diff 名簿_旧_cleaned.csv 名簿_新_cleaned.csv --key 社員番号
```

```python
import pandas as pd

old = pd.read_csv("名簿_旧_cleaned.csv", dtype=str, encoding="utf-8-sig")
new = pd.read_csv("名簿_新_cleaned.csv", dtype=str, encoding="utf-8-sig")

# 社員番号をキーに突合(追加・削除・変更を把握)
merged = old.merge(new, on="社員番号", how="outer",
                   suffixes=("_旧", "_新"), indicator=True)
added = merged[merged["_merge"] == "right_only"]    # 新規
removed = merged[merged["_merge"] == "left_only"]   # 削除
common = merged[merged["_merge"] == "both"]         # 変更の有無を各列で比較
```

## 3. クロス集計

**手順**

1. クレンジング済みデータを読み込み、集計軸(行・列)と集計対象の数値列を確認する。
2. `pd.pivot_table` で行・列・集計関数を指定し、`margins=True` で合計行・合計列も併せて出力する。
3. 数値化できていない列がある場合は事前に `pd.to_numeric` を通す(落とし穴9を参照)。

```python
import pandas as pd

df = pd.read_csv("売上_cleaned.csv", dtype=str, encoding="utf-8-sig")
df["金額"] = pd.to_numeric(df["金額"], errors="coerce")

table = pd.pivot_table(
    df,
    index="担当者",
    columns="商品カテゴリ",
    values="金額",
    aggfunc="sum",
    margins=True,
    margins_name="合計",
)
print(table)
```

## 4. 月次推移グラフ

**手順**

1. 集計対象データを月単位でピボットし、月を行(または列)にした系列を作る。
2. matplotlib で折れ線グラフを描く前に、日本語が文字化け(豆腐)しないようフォントを明示的に指定する。Windows 環境では Meiryo を第一候補とし、無ければ Yu Gothic、それも無ければ MS Gothic の順にフォールバックする。
3. `plt.rcParams["axes.unicode_minus"] = False` も合わせて設定し、マイナス記号の文字化けを防ぐ。

```python
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

# Windows 環境: Meiryo → Yu Gothic → MS Gothic の順でフォールバック
available = {f.name for f in matplotlib.font_manager.fontManager.ttflist}
for font in ("Meiryo", "Yu Gothic", "MS Gothic"):
    if font in available:
        plt.rcParams["font.family"] = font
        break
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_csv("売上_cleaned.csv", dtype=str, encoding="utf-8-sig")
df["金額"] = pd.to_numeric(df["金額"], errors="coerce")

monthly = df.pivot_table(index="年月", columns="商品カテゴリ", values="金額", aggfunc="sum")
monthly.plot(kind="line", marker="o")
plt.title("月次推移")
plt.xlabel("年月")
plt.ylabel("金額")
plt.tight_layout()
plt.savefig("月次推移.png")
```

## 5. 大容量ファイルの分割処理

**手順**

1. 行数ガード(本ツールでは50万行)を超えるファイルは `clean` が `RowGuardError` で停止し分割を促すため、そのまま一括では処理しない。
2. `pd.read_csv(chunksize=...)` でチャンク単位に読み込み、チャンクごとにクレンジング・集計を行ってから結果を結合する。
3. 集計は「チャンクごとの部分集計」→「全チャンクの合算」の2段階で行う(単純な `sum` の合算で足りない集計は要注意)。

```python
import pandas as pd
import unicodedata

CHUNK = 100_000
partial_sums = {}

for chunk in pd.read_csv("巨大ファイル.csv", dtype=str, encoding="utf-8-sig", chunksize=CHUNK):
    chunk = chunk.map(lambda v: unicodedata.normalize("NFKC", v) if isinstance(v, str) else v)
    chunk["金額"] = pd.to_numeric(chunk["金額"], errors="coerce")
    grp = chunk.groupby("担当者")["金額"].sum()
    for k, v in grp.items():
        partial_sums[k] = partial_sums.get(k, 0) + v

result = pd.Series(partial_sums).sort_values(ascending=False)
print(result)
```

## 6. xlsx 複数シートの一括処理

**手順**

1. `pd.read_excel(sheet_name=None)` で全シートを辞書(`{シート名: DataFrame}`)として一括取得する。
2. シートごとにクレンジング・整形を行い、必要に応じて `pd.concat` でシート名を列に持たせながら1つの表へ統合する。
3. 統合後は落とし穴9・12(数値の文字列化、横持ち/縦持ち)に注意して集計する。

```python
import pandas as pd

sheets = pd.read_excel("台帳.xlsx", sheet_name=None, dtype=str)

frames = []
for name, df in sheets.items():
    df = df.copy()
    df["シート名"] = name
    frames.append(df)

merged = pd.concat(frames, ignore_index=True)
print(merged["シート名"].value_counts())
```
