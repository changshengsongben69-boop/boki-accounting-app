# -*- coding: utf-8 -*-
"""questions/journal/*.yaml から仕訳演習アプリ（単一HTML）を生成する。

テンプレートの APP_CONFIG / ACCOUNTS / allQuestions だけを差し替える。
エンジン部分には手を入れない。
"""
import sys, io, os, json, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = r"C:\Users\shouk\.claude\boki-apps\_template_journal\index.html"
OUTDIR = r"C:\Users\shouk\.claude\boki-apps\リース仕訳-vol1"

APP_CONFIG = {
    "title": "リース仕訳 Vol.1",
    "subtitle": "新基準・旧基準／仕訳入力形式",
    "storageKey": "boki_lease_journal_v1",
}

CATEGORY_ORDER = [
    ("BK-2-15-01", "リース・借手の処理"),
    ("BK-2-15-02", "短期／少額リース"),
]


def unwrap(text):
    paragraphs = [p.replace("\n", "").strip() for p in text.strip().split("\n\n")]
    return "\n\n".join(p for p in paragraphs if p)


def category_of(tid):
    for prefix, cat in CATEGORY_ORDER:
        if tid.startswith(prefix):
            return cat
    raise SystemExit(f"カテゴリ未定義の topic_id: {tid}")


def rank_of(tid):
    for i, (prefix, _) in enumerate(CATEGORY_ORDER):
        if tid.startswith(prefix):
            return i
    return 999


def load_master():
    """勘定科目マスタを {科目名: (許容リスト, 区分)} に展開する。"""
    doc = yaml.safe_load(open(os.path.join(ROOT, 'accounts', 'kamokuhyo_2027.yaml'), encoding='utf-8'))
    out = {}
    for sec, grades in doc['sections'].items():
        for _g, items in grades.items():
            for it in items:
                std = it['std']
                alt = list(it.get('alt') or [])
                if std in out:            # 3級と2級の双方にある科目は許容科目を統合
                    prev_alt, prev_sec = out[std]
                    alt = sorted(set(prev_alt) | set(alt))
                    sec = prev_sec
                out[std] = (alt, sec)
    return out


def main():
    master = load_master()
    questions, used_accounts = [], []

    for path in sorted(glob.glob(os.path.join(ROOT, 'questions', 'journal', '*.yaml'))):
        doc = yaml.safe_load(open(path, encoding='utf-8'))
        default_topic = doc.get('topic_default')
        for seq, q in enumerate(doc.get('questions', [])):
            tid = q.get('topic_id') or default_topic
            cand = q.get('accounts') or []
            for c in cand:
                if c not in used_accounts:
                    used_accounts.append(c)
            questions.append({
                "_rank": (rank_of(tid), seq),
                "id": q['id'],
                "category": category_of(tid),
                "question": unwrap(q['question']),
                "rows": q.get('rows', 2),
                "accounts": cand,
                "answer": q['answer'],
                "explanation": unwrap(q['explanation']),
            })

    questions.sort(key=lambda x: x['_rank'])
    for q in questions:
        del q['_rank']

    accounts, unknown = [], []
    for name in used_accounts:
        if name in master:
            alt, sec = master[name]
        else:
            alt, sec = [], "その他"
            unknown.append(name)
        accounts.append({"std": name, "alt": alt, "section": sec})

    html = open(TEMPLATE, encoding='utf-8').read()
    i = html.index("const ACCOUNTS = [")
    j = html.index("];", i) + 2
    html = html[:i] + "const ACCOUNTS = " + json.dumps(accounts, ensure_ascii=False, indent=2) + ";" + html[j:]

    i = html.index("const APP_CONFIG = {")
    j = html.index("};", i) + 2
    html = html[:i] + "const APP_CONFIG = " + json.dumps(APP_CONFIG, ensure_ascii=False, indent=2) + ";" + html[j:]

    i = html.index("const allQuestions = [")
    j = html.index("];", i) + 2
    html = html[:i] + "const allQuestions = " + json.dumps(questions, ensure_ascii=False, indent=2) + ";" + html[j:]

    if "// ==== ここから下はエンジン" not in html:
        raise SystemExit("エンジン部のマーカーが消えている。置換範囲を確認すること。")

    os.makedirs(OUTDIR, exist_ok=True)
    dest = os.path.join(OUTDIR, "index.html")
    open(dest, 'w', encoding='utf-8').write(html)

    print(f"生成: {dest}")
    print(f"問題数: {len(questions)}  勘定科目の候補（延べ種類）: {len(accounts)}")
    if unknown:
        print(f"⚠ 2027年度版マスタに無い科目（旧基準の誤答候補等）: {unknown}")
    cats = {}
    for q in questions:
        cats[q['category']] = cats.get(q['category'], 0) + 1
    for c, n in cats.items():
        print(f"   {c}: {n}問")


if __name__ == '__main__':
    main()
