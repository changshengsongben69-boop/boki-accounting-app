# -*- coding: utf-8 -*-
"""問題データ・用語データの構造検証。会計の正確性は人間がレビューする。
ここで見るのは機械的に判定できることだけ。"""
import sys, io, glob, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    import yaml
except ImportError:
    sys.exit("pyyaml が必要です:  python -m pip install pyyaml")

ROOT = os.path.dirname(os.path.abspath(__file__))
BASES = {'asbj-34', 'asbj-13', 'rent-legacy'}
GRADES = {'3', '2', '1', 'jokyu', 'tantou'}
EXAMS = {'nissho', 'zenkei', 'cpa'}

errors, warnings, qcount, tcount = [], [], 0, 0
seen_ids, known_topics, referenced_topics = set(), set(), set()

# 論点タグのシード（build_topics.py が生成）。topic_id の実在チェックに使う。
SEED = os.path.join(ROOT, 'seed', 'topics.json')
if not os.path.exists(SEED):
    sys.exit("seed/topics.json が無い。先に build_topics.py を実行すること。")
_seed = json.load(open(SEED, encoding='utf-8'))
TOPICS = {t['id']: t for t in _seed['topics']}
SCOPE = {}
for _r in _seed['topic_scope']:
    SCOPE.setdefault(_r['topic_id'], []).append(_r)


def check_topic(path, qid, tid, grades, exams):
    """topic_id の実在と、宣言した級・試験が出題範囲と矛盾しないかを見る。"""
    if not tid:
        err(path, f"{qid}: topic_id が無い")
        return
    if tid not in TOPICS:
        err(path, f"{qid}: 論点タグ '{tid}' が存在しない（打ち間違いか、タグ体系に未登録）")
        return
    rows = SCOPE.get(tid, [])
    if not rows:
        err(path, f"{qid}: 論点 '{tid}' に出題範囲が1件も無い")
        return
    for e in (exams or sorted({r['exam'] for r in rows})):
        allowed = {r['grade'] for r in rows if r['exam'] == e}
        if not allowed:
            err(path, f"{qid}: 論点 '{tid}' は {e} の出題範囲に含まれない")
            continue
        for g in (grades or []):
            if str(g) not in allowed:
                err(path, f"{qid}: {e} の {g}級は論点 '{tid}' の出題範囲外"
                          f"（範囲は {sorted(allowed)}）")


def err(f, msg):
    errors.append(f"[{os.path.basename(f)}] {msg}")


def warn(f, msg):
    warnings.append(f"[{os.path.basename(f)}] {msg}")


# ---- 問題 ----
for path in sorted(glob.glob(os.path.join(ROOT, 'questions', '*.yaml'))):
    doc = yaml.safe_load(open(path, encoding='utf-8'))
    default_topic = doc.get('topic_default')
    if default_topic:
        known_topics.add(default_topic)
    for q in doc.get('questions', []):
        qcount += 1
        qid = q.get('id', '(id無し)')
        if qid in seen_ids:
            err(path, f"{qid}: IDが重複している")
        seen_ids.add(qid)

        for field in ('id', 'question', 'choices', 'answer', 'explanation'):
            if q.get(field) is None:
                err(path, f"{qid}: 必須フィールド '{field}' が無い")

        ch = q.get('choices') or []
        if not 2 <= len(ch) <= 9:
            err(path, f"{qid}: 選択肢が{len(ch)}個（2〜9でなければならない）")
        if len(set(ch)) != len(ch):
            err(path, f"{qid}: 選択肢が重複している")
        a = q.get('answer')
        if isinstance(a, int) and not 0 <= a < len(ch):
            err(path, f"{qid}: answer={a} が選択肢の範囲外")

        b = q.get('basis')
        if b and b not in BASES:
            err(path, f"{qid}: 未知の basis '{b}'")
        for g in (q.get('grades') or []):
            if str(g) not in GRADES:
                err(path, f"{qid}: 未知の grade '{g}'")
        for e in (q.get('exams') or []):
            if e not in EXAMS:
                err(path, f"{qid}: 未知の exam '{e}'")

        vf, vu = q.get('valid_from'), q.get('valid_until')
        if vf and vu and vu < vf:
            err(path, f"{qid}: valid_until < valid_from")
        # 基準改定の影響を受ける問題は年度が切られていなければ危険
        if b in ('asbj-34',) and not vf:
            warn(path, f"{qid}: basis=asbj-34 だが valid_from が無い（2026年度に漏れる恐れ）")
        if b in ('asbj-13',) and not vu and not doc.get('topic_default', '').endswith('L-01'):
            pass  # topic_scope 側で切っている場合があるため警告しない

        tid = q.get('topic_id') or default_topic
        referenced_topics.add(tid)
        check_topic(path, qid, tid, q.get('grades'), q.get('exams'))
        if q.get('explanation') and len(q['explanation'].strip()) < 40:
            warn(path, f"{qid}: 解説が短い（誤答の理由に触れているか確認）")

# ---- 仕訳問題 ----
master = yaml.safe_load(open(os.path.join(ROOT, 'accounts', 'kamokuhyo_2027.yaml'), encoding='utf-8'))
MASTER_STD = set()
for _sec, _gs in master['sections'].items():
    for _g, _items in _gs.items():
        for _it in _items:
            MASTER_STD.add(_it['std'])

jcount = 0
for path in sorted(glob.glob(os.path.join(ROOT, 'questions', 'journal', '*.yaml'))):
    doc = yaml.safe_load(open(path, encoding='utf-8'))
    if doc.get('format') != 'journal':
        err(path, "format: journal が宣言されていない")
    default_topic = doc.get('topic_default')
    for q in doc.get('questions', []):
        jcount += 1
        qid = q.get('id', '(id無し)')
        if qid in seen_ids:
            err(path, f"{qid}: IDが重複している")
        seen_ids.add(qid)

        for field in ('id', 'question', 'answer', 'explanation'):
            if q.get(field) is None:
                err(path, f"{qid}: 必須フィールド '{field}' が無い")
        ans = q.get('answer') or {}
        debit, credit = ans.get('debit') or [], ans.get('credit') or []
        if not debit or not credit:
            err(path, f"{qid}: answer に debit / credit が揃っていない")
            continue

        ds = sum(e.get('amount', 0) for e in debit)
        cs = sum(e.get('amount', 0) for e in credit)
        if ds != cs:
            err(path, f"{qid}: 正解の貸借が一致しない（借方 {ds:,} ／ 貸方 {cs:,}）")
        for e in debit + credit:
            if not isinstance(e.get('amount'), int) or e['amount'] <= 0:
                err(path, f"{qid}: 金額が正の整数でない → {e}")
            if not e.get('account'):
                err(path, f"{qid}: account の無い行がある")

        used = {e['account'] for e in debit + credit if e.get('account')}
        cand = q.get('accounts') or []
        if not cand:
            warn(path, f"{qid}: accounts（候補）が無い。マスタ全件から選ばせることになる")
        else:
            missing = used - set(cand)
            if missing:
                err(path, f"{qid}: 正解の科目が候補に無い → {sorted(missing)}")
            if len(cand) < 2:
                err(path, f"{qid}: 候補が少なすぎる（{len(cand)}件）")
            if len(cand) == len(used):
                warn(path, f"{qid}: 候補が正解の科目と完全に一致している（誤答候補が無い）")

        unknown = used - MASTER_STD
        if unknown:
            warn(path, f"{qid}: 2027年度版マスタに無い科目 → {sorted(unknown)}"
                       f"（旧基準の問題なら2022年度版マスタが必要）")

        tid = q.get('topic_id') or default_topic
        referenced_topics.add(tid)
        check_topic(path, qid, tid, q.get('grades'), q.get('exams'))

# ---- 用語 ----
for path in sorted(glob.glob(os.path.join(ROOT, 'terms', '*.yaml'))):
    doc = yaml.safe_load(open(path, encoding='utf-8'))
    ids = set()
    for t in doc.get('terms', []):
        tcount += 1
        tid = t.get('id', '(id無し)')
        if tid in ids:
            err(path, f"{tid}: IDが重複している")
        ids.add(tid)
        for field in ('id', 'headword', 'definition'):
            if not t.get(field):
                err(path, f"{tid}: 必須フィールド '{field}' が無い")
        if not t.get('topics'):
            err(path, f"{tid}: topics が無い（辞書から演習への導線が張れない）")
        for tp in (t.get('topics') or []):
            if tp not in TOPICS:
                err(path, f"{tid}: 論点タグ '{tp}' が存在しない")
        referenced_topics.update(t.get('topics') or [])
    for t in doc.get('terms', []):
        for r in (t.get('related') or []):
            if r not in ids:
                warn(path, f"{t.get('id')}: related '{r}' が同ファイル内に無い")

print(f"4択 {qcount}問 / 仕訳 {jcount}問 / 用語 {tcount}語 を検証した")
leaves = [t for t in TOPICS.values() if not any(
    o['id'].startswith(t['id'] + '-') for o in TOPICS.values())]
covered = {t for t in referenced_topics if t in TOPICS}
print(f"論点タグ {len(TOPICS)}件（うち末端 {len(leaves)}件）／ 問題のある論点 {len(covered)}件"
      f" = 末端の {len(covered) / len(leaves) * 100:.1f}%")
print()
if warnings:
    print(f"--- 警告 {len(warnings)}件 ---")
    for w in warnings:
        print("  " + w)
    print()
if errors:
    print(f"--- エラー {len(errors)}件 ---")
    for e in errors:
        print("  " + e)
    sys.exit(1)
print("エラーなし")
