# -*- coding: utf-8 -*-
"""リース論点パイロット: 出題可否の解決が正しく動くかを実際に動かして検証する。
SQLite で動かすが、ロジックは データスキーマ設計.md 4-1 と同一。"""
import sys, io, sqlite3
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

db = sqlite3.connect(":memory:")
db.executescript("""
create table topic (
  id text primary key, namespace text, parent_id text, depth integer,
  title text not null, supersedes_id text
);
create table topic_scope (
  topic_id text, exam text, grade text,
  valid_from integer, valid_until integer, status text default 'included',
  primary key (topic_id, exam, grade, valid_from)
);
create table question (
  id integer primary key, topic_id text, body text, basis text,
  exams text, grades text, valid_from integer, valid_until integer,
  status text default 'published'
);
create table tier_scope (tier integer, exam text, grade text, primary key (tier, exam, grade));
""")

T = [  # id, ns, parent, depth, title, supersedes
 ('BK-2-15','BK',None,2,'リース※（新基準・2027年度〜）',None),
 ('BK-2-15-01','BK','BK-2-15',3,'ア．リースの借手側の処理(利子込み法、利子抜き法(定額法))','BK-2-17L-01'),
 ('BK-2-15-01b','BK','BK-2-15',3,'└(利息法、級数法)','BK-2-17L-01b'),
 ('BK-2-15-02','BK','BK-2-15',3,'イ．短期リースおよび少額リースの取扱い',None),
 ('BK-2-15-03','BK','BK-2-15',3,'ウ．リースの貸手側の処理(ファイナンス・リース、オペレーティング・リース)','BK-2-17L-02'),
 ('BK-2-15-04','BK','BK-2-15',3,'エ．セール・アンド・リースバック取引およびサブリース取引など','BK-2-17L-03'),
 ('BK-2-15-05','BK','BK-2-15',3,'オ．借地権の処理',None),
 ('BK-2-17L','BK',None,2,'リース取引※（旧基準・2022〜2026年度）',None),
 ('BK-2-17L-01','BK','BK-2-17L',3,'ア．ファイナンス・リース取引の借手側の処理',None),
 ('BK-2-17L-01b','BK','BK-2-17L',3,'└(利息法、級数法)',None),
 ('BK-2-17L-02','BK','BK-2-17L',3,'イ．ファイナンス・リース取引の貸手側の処理',None),
 ('BK-2-17L-03','BK','BK-2-17L',3,'ウ．セール・アンド・リースバック取引など',None),
 ('BK-2-17L-04','BK','BK-2-17L',3,'エ．オペレーティング・リース取引の借手側の処理',None),
 ('BK-2-17L-04b','BK','BK-2-17L',3,'└貸手側の処理',None),
 ('BK-2-18','BK',None,2,'収益と費用（支払家賃・支払地代を含む）',None),
]
db.executemany("insert into topic values (?,?,?,?,?,?)", T)

S = [  # topic, exam, grade, from, until, status
 # 日商・新基準（2027年度〜）
 ('BK-2-15','nissho','2',2027,None,'simplified'),
 ('BK-2-15','nissho','1',2027,None,'included'),
 ('BK-2-15-01','nissho','2',2027,None,'simplified'),
 ('BK-2-15-01','nissho','1',2027,None,'included'),
 ('BK-2-15-01b','nissho','1',2027,None,'included'),
 ('BK-2-15-02','nissho','2',2027,None,'included'),
 ('BK-2-15-02','nissho','1',2027,None,'included'),
 ('BK-2-15-03','nissho','1',2027,None,'included'),
 ('BK-2-15-04','nissho','1',2027,None,'included'),
 ('BK-2-15-05','nissho','1',2027,None,'included'),
 # 日商・旧基準（2022〜2026年度）
 ('BK-2-17L','nissho','2',2022,2026,'simplified'),
 ('BK-2-17L','nissho','1',2022,2026,'included'),
 ('BK-2-17L-01','nissho','2',2022,2026,'simplified'),
 ('BK-2-17L-01','nissho','1',2022,2026,'included'),
 ('BK-2-17L-01b','nissho','1',2022,2026,'included'),
 ('BK-2-17L-02','nissho','1',2022,2026,'included'),
 ('BK-2-17L-03','nissho','1',2022,2026,'included'),
 ('BK-2-17L-04','nissho','2',2022,2026,'simplified'),
 ('BK-2-17L-04','nissho','1',2022,2026,'included'),
 ('BK-2-17L-04b','nissho','1',2022,2026,'included'),
 # 全経上級：令和6年度改定時点で旧基準のまま
 ('BK-2-17L','zenkei','jokyu',2024,None,'included'),
 ('BK-2-17L-01','zenkei','jokyu',2024,None,'included'),
 ('BK-2-17L-01b','zenkei','jokyu',2024,None,'included'),
 ('BK-2-17L-02','zenkei','jokyu',2024,None,'included'),
 ('BK-2-17L-04','zenkei','jokyu',2024,None,'included'),
 # CPA短答式：令和9年第Ⅱ回(2027年5月)は新基準が施行済み。早期適用により旧も範囲
 ('BK-2-15','cpa','tantou',2027,None,'included'),
 ('BK-2-15-01','cpa','tantou',2027,None,'included'),
 ('BK-2-15-02','cpa','tantou',2027,None,'included'),
 ('BK-2-15-03','cpa','tantou',2027,None,'included'),
 ('BK-2-15-04','cpa','tantou',2027,None,'included'),
 ('BK-2-17L','cpa','tantou',2027,None,'included'),
 ('BK-2-17L-01','cpa','tantou',2027,None,'included'),
 # 支払家賃・支払地代
 ('BK-2-18','nissho','3',2022,None,'included'),
 ('BK-2-18','nissho','2',2022,None,'included'),
 ('BK-2-18','nissho','1',2022,None,'included'),
]
db.executemany("insert into topic_scope values (?,?,?,?,?,?)", S)

Q = [  # id, topic, body, basis, exams, grades, valid_from, valid_until
 (1,'BK-2-18','事務所の家賃を支払った（3級・賃貸借処理／支払家賃勘定）','rent-legacy','nissho','3',None,None),
 (2,'BK-2-18','事務所の家賃を支払った（2級以上・支払リース料勘定に統一）','asbj-34','nissho','2,1',2027,None),
 (3,'BK-2-18','事務所の家賃を支払った（2級以上・支払家賃勘定）','asbj-13','nissho','2,1',None,2026),
 (4,'BK-2-15-01','リース開始時の借手仕訳（使用権資産／リース負債・利子抜き法）','asbj-34',None,None,None,None),
 (5,'BK-2-17L-01','リース開始時の借手仕訳（リース資産／リース債務・利子抜き法）','asbj-13',None,None,None,None),
 (6,'BK-2-15-02','短期リースの賃貸借処理','asbj-34',None,None,None,None),
 (7,'BK-2-15-05','借地権の設定に係る権利金の処理','asbj-34',None,None,None,None),
 (8,'BK-2-15-03','貸手側のファイナンス／オペレーティングの区分（新基準）','asbj-34',None,None,None,None),
 (9,'BK-2-17L-02','貸手側のファイナンス・リースの処理（旧基準）','asbj-13',None,None,None,None),
]
db.executemany("insert into question (id,topic_id,body,basis,exams,grades,valid_from,valid_until) values (?,?,?,?,?,?,?,?)", Q)

db.executemany("insert into tier_scope values (?,?,?)", [
 (1,'nissho','3'),(1,'nissho','2'),
 (2,'nissho','1'),(2,'zenkei','jokyu'),
 (3,'cpa','tantou'),
])

ASKABLE = """
select q.id, q.basis, t.title, q.body
from question q
join topic t on t.id = q.topic_id
where q.status = 'published'
  and (q.exams  is null or ',' || q.exams  || ',' like '%,' || :exam  || ',%')
  and (q.grades is null or ',' || q.grades || ',' like '%,' || :grade || ',%')
  and coalesce(q.valid_from, -32768) <= :year
  and :year <= coalesce(q.valid_until, 32767)
  and exists (
    select 1 from topic_scope s
    where s.topic_id = q.topic_id and s.exam = :exam and s.grade = :grade
      and s.valid_from <= :year and :year <= coalesce(s.valid_until, 32767)
  )
  and exists (
    select 1 from tier_scope ts
    where ts.tier <= :tier and ts.exam = :exam and ts.grade = :grade
  )
order by q.id
"""

SCENARIOS = [
 ('日商3級 / 2027年度 / tier1', dict(exam='nissho', grade='3', year=2027, tier=1)),
 ('日商2級 / 2026年度 / tier1', dict(exam='nissho', grade='2', year=2026, tier=1)),
 ('日商2級 / 2027年度 / tier1', dict(exam='nissho', grade='2', year=2027, tier=1)),
 ('日商1級 / 2027年度 / tier2', dict(exam='nissho', grade='1', year=2027, tier=2)),
 ('日商1級 / 2027年度 / tier1(未課金)', dict(exam='nissho', grade='1', year=2027, tier=1)),
 ('全経上級 / 2026年度 / tier2', dict(exam='zenkei', grade='jokyu', year=2026, tier=2)),
 ('CPA短答 / 2027年度 / tier3', dict(exam='cpa', grade='tantou', year=2027, tier=3)),
]

for label, p in SCENARIOS:
    rows = db.execute(ASKABLE, p).fetchall()
    print("=" * 72)
    print(label, f"  → 出題可能 {len(rows)}問")
    for r in rows:
        print(f"   Q{r[0]} [{r[1]:<12}] {r[3]}")
