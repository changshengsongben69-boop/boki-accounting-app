# -*- coding: utf-8 -*-
"""questions/*.yaml から演習アプリ（単一HTML）を生成する。

グローバル CLAUDE.md の規約に従い、テンプレートの APP_CONFIG と allQuestions
だけを差し替える。エンジン部分には一切手を入れない。

    python build_app.py            # 定義済みのアプリをすべて生成
    python build_app.py lease      # 名前を指定して1つだけ生成

アプリの定義は BUILDS。`categories` に列挙した topic_id 接頭辞に一致する問題だけを
拾うので、questions/ にどれだけファイルが増えても他のアプリには混ざらない。
出題順も `categories` の並び順になる。
"""
import sys, io, os, json, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = r"C:\Users\shouk\.claude\boki-apps\_template\index.html"
APPS = r"C:\Users\shouk\.claude\boki-apps"

FOOTER_3KYU = "※2027年度出題区分表（確定版）準拠。紙の手形・小切手は出題範囲外です。"

BUILDS = {
    "lease": {
        "outdir": os.path.join(APPS, "リース-vol1"),
        "config": {
            "title": "リース（新基準対応）Vol.1",
            "subtitle": "日商2級・1級／全経上級／短答 — 適用年度に注意",
            "storageKey": "boki_lease_v1",
        },
        "footer": ("※企業会計基準第34号（新リース基準）対応。日商簿記では2027年度から適用。<br>"
                   "受験級・受験年度により正解が異なる問題を含みます。"),
        "categories": [
            ("BK-2-15-01", "リース・借手の処理"),
            ("BK-2-15-02", "短期／少額リース"),
            ("BK-2-15-03", "リース・1級論点"),
            ("BK-2-15-05", "リース・1級論点"),
            ("BK-2-18",    "収益と費用（勘定科目の選択）"),
        ],
    },
    "3kyu-kihon": {
        "outdir": os.path.join(APPS, "3級-基本原理と株式会社会計-vol1"),
        "config": {
            "title": "基本原理と株式会社会計（3級）",
            "subtitle": "2027年度出題区分表（確定版）準拠",
            "storageKey": "boki_3kyu_kihon_kabushiki_v1",
        },
        "footer": FOOTER_3KYU,
        "categories": [
            ("BK-1-01", "基礎概念"),
            ("BK-1-02", "取引"),
            ("BK-1-03", "勘定"),
            ("BK-1-04", "帳簿"),
            ("BK-1-05", "証ひょうと伝票"),
            ("BK-4",    "株式会社会計"),
        ],
    },
    "3kyu-baikake": {
        "outdir": os.path.join(APPS, "3級-売掛金買掛金-vol1"),
        "config": {
            "title": "売掛金・買掛金・電子記録債権（3級）",
            "subtitle": "BK-2-03／2027年度出題区分表（確定版）準拠",
            "storageKey": "boki_3kyu_bk203_v1",
        },
        "footer": FOOTER_3KYU,
        "categories": [
            ("BK-2-03-01", "売掛金・買掛金"),
            ("BK-2-03-02", "売掛金元帳・買掛金元帳"),
            ("BK-2-03-04", "電子記録債権・債務"),
            ("BK-2-03-06", "クレジット売掛金"),
        ],
    },
    "3kyu-shotorihiki": {
        "outdir": os.path.join(APPS, "3級-諸取引の処理まとめ-vol1"),
        "config": {
            "title": "諸取引の処理まとめ（3級）",
            "subtitle": "2027年度出題区分表（確定版）準拠",
            "storageKey": "boki_3kyu_shotorihiki_v1",
        },
        "footer": FOOTER_3KYU,
        "categories": [
            ("BK-2-01", "現金預金"),
            ("BK-2-04", "その他の債権と債務"),
            ("BK-2-05", "貸倒引当金"),
            ("BK-2-07", "商品売買"),
            ("BK-2-10", "有形固定資産"),
            ("BK-2-19", "税金"),
        ],
    },
    "3kyu-kessan": {
        "outdir": os.path.join(APPS, "3級-決算-vol1"),
        "config": {
            "title": "決算（3級）",
            "subtitle": "2027年度出題区分表（確定版）準拠",
            "storageKey": "boki_3kyu_kessan_v1",
        },
        "footer": FOOTER_3KYU,
        "categories": [
            ("BK-3-01", "試算表"),
            ("BK-3-03", "決算整理"),
            ("BK-3-02", "精算表"),
            ("BK-3-04", "決算整理後残高試算表"),
            ("BK-3-05", "帳簿の締切"),
            ("BK-3-06", "帳簿の締切"),
            ("BK-3-08", "帳簿の締切"),
            ("BK-3-09", "財務諸表"),
        ],
    },
}


def category_of(topic_id, categories):
    for prefix, cat in categories:
        if topic_id.startswith(prefix):
            return cat
    return None


def rank_of(topic_id, categories):
    for i, (prefix, _) in enumerate(categories):
        if topic_id.startswith(prefix):
            return i
    return 999


def unwrap(text, preformatted=False):
    """YAML のブロックスカラーが保持した折り返し改行をたたむ。

    テンプレートは white-space: pre-wrap で描画するため、原稿の見た目上の
    折り返しがそのまま画面に出てしまう。段落の区切り（空行）は残し、
    段落内の改行だけを詰める。日本語なので連結時に空白は入れない。

    preformatted=True の問題は改行をそのまま活かす。試算表・精算表のように
    資料を行単位で示す問題は、折りたたむと読めなくなるため。
    """
    if preformatted:
        return text.strip()
    paragraphs = [p.replace("\n", "").strip() for p in text.strip().split("\n\n")]
    return "\n\n".join(p for p in paragraphs if p)


def load_questions():
    out = []
    for path in sorted(glob.glob(os.path.join(ROOT, 'questions', '*.yaml'))):
        doc = yaml.safe_load(open(path, encoding='utf-8'))
        default_topic = doc.get('topic_default')
        for seq, q in enumerate(doc.get('questions', [])):
            tid = q.get('topic_id') or default_topic
            out.append({
                "_rank": (rank_of(tid), seq),
                "id": q['id'],
                "category": category_of(tid),
                "question": unwrap(q['question'], q.get('preformatted', False)),
                "choices": [str(c).strip() for c in q['choices']],
                "answer": q['answer'],
                "explanation": unwrap(q['explanation']),
            })
    out.sort(key=lambda x: x['_rank'])
    for q in out:
        del q['_rank']
    return out


def replace_block(src, start_marker, end_marker, new_text):
    i = src.index(start_marker)
    j = src.index(end_marker, i) + len(end_marker)
    return src[:i] + new_text + src[j:]


def main():
    html = open(TEMPLATE, encoding='utf-8').read()
    questions = load_questions()

    cfg = ("const APP_CONFIG = " +
           json.dumps(APP_CONFIG, ensure_ascii=False, indent=2) + ";")
    qs = ("const allQuestions = " +
          json.dumps(questions, ensure_ascii=False, indent=2) + ";")

    html = replace_block(html, "const APP_CONFIG = {", "};", cfg)
    html = replace_block(html, "const allQuestions = [", "];", qs)
    html = replace_block(html, "<footer>", "</footer>",
                         "<footer>\n  " + FOOTER + "\n</footer>")

    if "// ==== ここから下はエンジン" not in html:
        raise SystemExit("エンジン部のマーカーが消えている。置換範囲を確認すること。")

    os.makedirs(OUTDIR, exist_ok=True)
    dest = os.path.join(OUTDIR, "index.html")
    open(dest, 'w', encoding='utf-8').write(html)

    print(f"生成: {dest}")
    print(f"問題数: {len(questions)}")
    cats = {}
    for q in questions:
        cats[q['category']] = cats.get(q['category'], 0) + 1
    for c, n in cats.items():
        print(f"   {c}: {n}問")


if __name__ == '__main__':
    main()
