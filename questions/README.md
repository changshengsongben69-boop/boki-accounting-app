# 問題データの形式

中分類論点ごとに1ファイル。ファイル名は論点ID（`BK-2-15.yaml`）。

## フィールド

```yaml
topic_default: BK-2-15-01     # 各問で topic_id を省略したときの既定値
questions:
  - id: BK-2-15-01-001        # 論点ID + 3桁連番。ファイル内で一意
    topic_id: BK-2-15-02      # 省略可。省略時は topic_default
    basis: asbj-34            # 準拠基準。省略可（基準非依存の問題）
    exams: [nissho, cpa]      # 省略時は topic_scope に従う
    grades: ["2", "1"]        # 省略時は topic_scope に従う
    valid_from: 2027          # 省略時は topic_scope に従う
    valid_until: 2026         # 同上
    difficulty: 2             # 1〜5
    question: |
      問題文
    choices:
      - 選択肢1
      - 選択肢2
    answer: 1                 # 正解のindex（0始まり）
    explanation: |
      解説
```

- `answer` は**0始まり**。既存の演習アプリのテンプレートと同じ
- `choices` は原則4つ。キーボードの数字キーに対応するため最大9つ
- `grades` の値は文字列。日商は `"3"` `"2"` `"1"`、全経上級は `"jokyu"`、
  CPA短答式は `"tantou"`
- `basis` の値: `asbj-34`（新リース）、`asbj-13`（旧リース）、`rent-legacy`（賃貸借処理の
  旧勘定科目）など。基準改定で正解が変わる問題には必ず付ける

## 執筆の原則

1. **迷った論点は出題しない**（CLAUDE.md 7）。一次情報で確認できない事項は書かない
2. 解説は「なぜ正解か」に加えて、**紛らわしい誤答がなぜ誤りかにも触れる**
3. 基準改定で正解が変わる問題は、`basis` と `valid_from/until` を必ず設定する。
   これを怠ると、2026年度受験者に2027年度の正解を出してしまう
4. 出題範囲は `論点タグ体系_*.md` を根拠にする。予備校教材の範囲感で判断しない

## 進捗

| ファイル | 論点 | 問題数 | 状態 |
|---|---|---|---|
| `BK-2-18.yaml` | 収益と費用（不動産賃借の勘定科目） | 3 | draft |
| `BK-2-15.yaml` | リース（新基準・2027年度〜） | 11 | draft |
| `BK-2-17L.yaml` | リース取引（旧基準・2022〜2026年度） | 5 | draft |

| `../terms/lease.yaml` | 用語辞書（リース） | 12語 | draft |

すべて `status: draft`。**会計の正確性レビューが済むまで `published` にしない。**

## 検証

```bash
python validate.py
```

機械的に判定できることだけを見る。会計の正確性は人間がレビューする。

- 必須フィールドの有無、ID重複、選択肢の数（2〜9）と重複
- `answer` が選択肢の範囲内か
- `basis` / `grades` / `exams` の値が既知のものか
- `valid_until < valid_from` の矛盾
- `basis: asbj-34` なのに `valid_from` が無い（2026年度に新基準が漏れる）
- 用語に `topics` が無い（辞書から演習への導線が張れない）
