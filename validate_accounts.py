# -*- coding: utf-8 -*-
"""勘定科目マスタの構造検証と、採点用の候補集合の組み立て確認。"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
doc = yaml.safe_load(open(os.path.join(ROOT, 'accounts', 'kamokuhyo_2027.yaml'), encoding='utf-8'))

sections = doc['sections']
errors = []
counts = {}
for sec, grades in sections.items():
    for g, items in grades.items():
        counts[(sec, g)] = len(items)
        seen = set()
        for it in items:
            std = it.get('std')
            if not std:
                errors.append(f"{sec}/{g}級: std の無い項目がある")
                continue
            if std in seen:
                errors.append(f"{sec}/{g}級: 標準科目 '{std}' が重複")
            seen.add(std)
            for a in (it.get('alt') or []):
                if a == std:
                    errors.append(f"{sec}/{g}級: '{std}' の許容科目が標準科目と同一")


def candidate_set(grade):
    """採点用の候補集合。2級には3級の科目がすべて含まれる（表の注意事項）。"""
    grades = ["3"] if grade == "3" else ["3", "2"]
    std, alt = set(), {}
    for sec, gs in sections.items():
        for g in grades:
            for it in gs.get(g, []):
                std.add(it['std'])
                for a in (it.get('alt') or []):
                    alt.setdefault(a, set()).add(it['std'])
    return std, alt


print("--- 科目数 ---")
tot3 = tot2 = 0
for sec in sections:
    n3 = counts.get((sec, "3"), 0)
    n2 = counts.get((sec, "2"), 0)
    tot3 += n3
    tot2 += n2
    print(f"  {sec:<6} 3級 {n3:>3}  /  2級 {n2:>3}")
print(f"  {'合計':<6} 3級 {tot3:>3}  /  2級 {tot2:>3}   （総計 {tot3 + tot2}）")

for grade in ("3", "2"):
    std, alt = candidate_set(grade)
    print(f"\n--- {grade}級の採点候補 ---")
    print(f"  標準科目 {len(std)}件 / 許容科目 {len(alt)}件（累積適用後）")

print("\n--- 抜粋: リース関連 ---")
std2, alt2 = candidate_set("2")
for name in ("使用権資産", "使用権資産減価償却累計額", "リース負債", "支払リース料",
             "支払家賃", "支払地代", "リース資産", "リース債務"):
    mark = "◯" if name in std2 else ("△許容" if name in alt2 else "×")
    print(f"  {mark}  {name}")

print()
if errors:
    print(f"--- エラー {len(errors)}件 ---")
    for e in errors:
        print("  " + e)
    sys.exit(1)
print("エラーなし")
