# -*- coding: utf-8 -*-
"""論点タグ体系の Markdown から topic / topic_scope を生成する。

技術選定5の実装。Markdown を単一の真実の源とし、機械可読なシードを生成する。
SQLを手書きすると Markdown と二重管理になり、必ず食い違うため。

出力:
  seed/topics.json  … validate.py が読む（topic_id の実在チェック用）
  seed/topics.sql   … DBに流す
"""
import sys, io, os, re, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'seed')

# 対象文書。全経突合編はスコープ外のため読まない（CLAUDE.md 6）。
DOCS = [
    {
        "file": "論点タグ体系_商業簿記会計学編.md",
        "namespace": "BK",
        "exam": "nissho",
        "valid_from": 2027,      # 2027年度適用【確定版】
        "valid_until": None,
    },
    {
        "file": "論点タグ体系_工業簿記原価計算編.md",
        "namespace": "KG",
        "exam": "nissho",
        "valid_from": 2022,      # 2022年度適用。2027年度も変更なし
        "valid_until": None,
    },
    {
        "file": "論点タグ体系_CPA短答式レイヤー.md",
        "namespace": "CPA",
        "exam": "cpa",
        "valid_from": 2027,      # 令和9年（第Ⅱ回＝2027年5月）
        "valid_until": None,
        "fixed_grade": "tantou",  # 級の列を持たない。すべて短答式
    },
]

ID_RE = re.compile(r'^(BK|KG|CPA-F|CPA-M)-[0-9A-Za-z\-]+$')
H2_RE = re.compile(r'^##\s+(.*?)\s*\(((?:BK|KG)-\d+)\)')
# 第二のように「### 1. 現金預金」で中分類を立てている箇所を拾う
H3_RE = re.compile(r'^###\s+(\d+)\.\s*(.+?)\s*$')
GRADE_COL = {"3級": "3", "2級": "2", "1級": "1"}
SUBITEM_RE = re.compile(r'\s*(?:[ア-ン]\.|\(\w\)|└).*$')

# CPA は文書に大分類の見出しが無いため、ここで与える
ROOT_TITLES = {
    "CPA-F": "財務会計論（日商1級を超える範囲）",
    "CPA-M": "管理会計論（日商1級を超える範囲）",
}


def clean(cell):
    s = cell.strip()
    s = s.replace("**", "").replace("　", " ")
    return s.strip()


def status_of(cell):
    """級の列の値 → 'included' | 'simplified' | None（範囲外）"""
    s = clean(cell)
    if "◯" in s or "○" in s:
        return "included"
    if "※" in s:
        return "simplified"
    return None


def parse_doc(spec):
    path = os.path.join(ROOT, spec["file"])
    lines = open(path, encoding='utf-8').read().split("\n")

    topics = {}     # id -> {title, namespace, depth, parent_id, sort}
    scopes = []
    heading_titles = {}
    header = None
    order = 0

    current_h2 = None
    for ln in lines:
        m = H2_RE.match(ln)
        if m:
            heading_titles[m.group(2)] = m.group(1)
            current_h2 = m.group(2)
            header = None
            continue
        m3 = H3_RE.match(ln)
        if m3 and current_h2:
            heading_titles[f"{current_h2}-{int(m3.group(1)):02d}"] = m3.group(2)
            header = None
            continue
        if not ln.startswith("|"):
            header = None
            continue

        cells = [c for c in ln.strip().strip("|").split("|")]
        first = clean(cells[0])
        if first == "ID":
            header = [clean(c) for c in cells]
            continue
        if set(first) <= set("-: ") or header is None:
            continue
        if not ID_RE.match(first):
            continue

        order += 1
        tid = first
        title = clean(cells[1]) if len(cells) > 1 else tid
        title = title.lstrip("└ ").strip()
        topics[tid] = {
            "id": tid,
            "title": title,
            "namespace": spec["namespace"] if spec["namespace"] != "CPA" else tid.rsplit("-", 1)[0],
            "sort": order,
        }

        if spec.get("fixed_grade"):
            scopes.append((tid, spec["exam"], spec["fixed_grade"], "included"))
        else:
            for i, h in enumerate(header):
                g = GRADE_COL.get(h)
                if g and i < len(cells):
                    st = status_of(cells[i])
                    if st:
                        scopes.append((tid, spec["exam"], g, st))

    return topics, scopes, heading_titles


def ancestors(tid):
    parts = tid.split("-")
    out = []
    # CPA-F-01 → CPA-F ／ BK-2-15-01 → BK-2-15 → BK-2
    floor = 2 if parts[0] == "CPA" else 1
    for k in range(len(parts) - 1, floor, -1):
        out.append("-".join(parts[:k]))
    if parts[0] == "CPA":
        out.append("-".join(parts[:2]))
    else:
        out.append(parts[0] + "-" + parts[1])
    return out


def main():
    all_topics, all_scopes, synthesized = {}, [], []

    for spec in DOCS:
        topics, scopes, headings = parse_doc(spec)
        all_topics.update(topics)
        all_scopes.extend(scopes)

        # 祖先を補完する。表に行が無い中分類（BK-2-15 など）も topic として要る
        for tid in list(topics):
            for anc in ancestors(tid):
                if anc in all_topics:
                    continue
                if anc in headings:
                    title = headings[anc]
                elif anc in ROOT_TITLES:
                    title = ROOT_TITLES[anc]
                else:
                    # 配下の最初の論点名から、サブ項目の記号以降を落として推定する
                    child = min((t for t in topics if t.startswith(anc + "-")),
                                key=lambda t: topics[t]["sort"], default=None)
                    title = ""
                    if child:
                        title = SUBITEM_RE.sub("", topics[child]["title"]).strip()
                        if not title:            # 見出し語が無く丸ごと落ちた場合
                            title = topics[child]["title"]
                    title = title or anc
                    synthesized.append((anc, title))
                all_topics[anc] = {
                    "id": anc, "title": title,
                    "namespace": anc.split("-")[0] if not anc.startswith("CPA") else anc,
                    "sort": 0,
                }

    # 親子と深さを決める
    for t in all_topics.values():
        ancs = ancestors(t["id"])
        t["parent_id"] = ancs[0] if ancs and ancs[0] != t["id"] and ancs[0] in all_topics else None
        depth = 1
        p = t["parent_id"]
        while p:
            depth += 1
            p = all_topics[p].get("parent_id")
        t["depth"] = depth

    # 祖先の scope は配下の和集合にする（一覧・ドリルダウン用）
    by_topic = {}
    for tid, exam, grade, st in all_scopes:
        by_topic.setdefault(tid, set()).add((exam, grade, st))
    for tid in sorted(all_topics, key=lambda x: -len(x)):
        t = all_topics[tid]
        p = t.get("parent_id")
        if p:
            for exam, grade, st in by_topic.get(tid, ()):
                by_topic.setdefault(p, set()).add((exam, grade, "included"))

    spec_by_ns = {}
    for spec in DOCS:
        spec_by_ns[spec["namespace"]] = spec

    scope_rows = []
    for tid, entries in by_topic.items():
        ns = "CPA" if tid.startswith("CPA") else tid.split("-")[0]
        spec = spec_by_ns.get(ns, DOCS[0])
        seen = {}
        for exam, grade, st in entries:
            # included が simplified を上書きする（同じ級に両方来ることは無い想定だが保険）
            if seen.get((exam, grade)) != "included":
                seen[(exam, grade)] = st
        for (exam, grade), st in seen.items():
            scope_rows.append({
                "topic_id": tid, "exam": exam, "grade": grade,
                "valid_from": spec["valid_from"], "valid_until": spec["valid_until"],
                "status": st,
            })

    topics_out = sorted(all_topics.values(), key=lambda t: (t["id"].split("-")[0], t["depth"], t["id"]))
    scope_rows.sort(key=lambda r: (r["topic_id"], r["exam"], r["grade"]))

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "topics.json"), "w", encoding="utf-8") as f:
        json.dump({"topics": topics_out, "topic_scope": scope_rows}, f, ensure_ascii=False, indent=1)

    def q(s):
        return "null" if s is None else "'" + str(s).replace("'", "''") + "'"

    with open(os.path.join(OUT, "topics.sql"), "w", encoding="utf-8") as f:
        f.write("-- 自動生成: build_topics.py。手で編集しないこと。\n")
        f.write("-- 出典は 論点タグ体系_*.md。Markdown を直してから再生成する。\n\n")
        f.write("delete from topic_scope; delete from topic;\n\n")
        for t in topics_out:
            f.write(f"insert into topic (id, namespace, parent_id, depth, title, sort_key) values "
                    f"({q(t['id'])}, {q(t['namespace'])}, {q(t.get('parent_id'))}, {t['depth']}, "
                    f"{q(t['title'])}, {q('%s-%05d' % (t['id'].split('-')[0], t['sort']))});\n")
        f.write("\n")
        for r in scope_rows:
            vu = "null" if r["valid_until"] is None else r["valid_until"]
            f.write(f"insert into topic_scope (topic_id, exam, grade, valid_from, valid_until, status) values "
                    f"({q(r['topic_id'])}, {q(r['exam'])}, {q(r['grade'])}, {r['valid_from']}, {vu}, "
                    f"{q(r['status'])});\n")

    print(f"topic {len(topics_out)}件 / topic_scope {len(scope_rows)}件 を生成した")
    ns_count = {}
    for t in topics_out:
        k = t["id"].split("-")[0] if not t["id"].startswith("CPA") else "CPA"
        ns_count[k] = ns_count.get(k, 0) + 1
    for k, v in sorted(ns_count.items()):
        print(f"   {k}: {v}件")
    if synthesized:
        print(f"\n表に行が無く、配下から推定した中分類 {len(synthesized)}件:")
        for tid, title in synthesized[:40]:
            print(f"   {tid}  {title}")


if __name__ == '__main__':
    main()
