import yaml
from pathlib import Path
root = Path(__file__).resolve().parents[1]
out = root / 'questions' / 'journal' / 'generated-journal.yaml'
# Topics to rotate through (ensure they exist in seed/topics.json)
topics = ['BK-1-03-01','BK-2-01-01','BK-2-07-01','BK-2-10-01','BK-3-08-01']
questions = []
for i in range(1,101):
    tid = topics[(i-1) % len(topics)]
    qid = f'GEN-J-{i:03d}'
    # simple patterns for amounts
    amt = 10000 * ((i % 9) + 1)
    if (i % 5) == 1:
        # cash sale
        q = {
            'id': qid,
            'topic_id': tid,
            'exams': ['nissho'],
            'grades': ['3'],
            'valid_from': 2027,
            'difficulty': 1,
            'rows': 2,
            'accounts': ['現金','売上','売掛金','普通預金'],
            'question': f'商品を現金で販売し、代金{amt}円を受け取った。仕訳を示しなさい。',
            'answer': {
                'debit':[{'account':'現金','amount':amt}],
                'credit':[{'account':'売上','amount':amt}]
            },
            'explanation': '現金の増加は借方、売上の増加は貸方に記入する。'
        }
    elif (i % 5) == 2:
        # credit sale
        q = {
            'id': qid,
            'topic_id': tid,
            'exams': ['nissho'],
            'grades': ['3'],
            'valid_from': 2027,
            'difficulty': 1,
            'rows': 2,
            'accounts': ['売掛金','売上','現金','普通預金'],
            'question': f'商品を掛けで販売し、売掛金{amt}円が発生した。仕訳を示しなさい。',
            'answer': {
                'debit':[{'account':'売掛金','amount':amt}],
                'credit':[{'account':'売上','amount':amt}]
            },
            'explanation': '掛け販売では売掛金（資産）が増えるため借方、売上は貸方。'
        }
    elif (i % 5) == 3:
        # purchase cash
        q = {
            'id': qid,
            'topic_id': tid,
            'exams': ['nissho'],
            'grades': ['3'],
            'valid_from': 2027,
            'difficulty': 1,
            'rows': 2,
            'accounts': ['仕入','現金','買掛金','普通預金'],
            'question': f'商品を現金で仕入れ、支払額は{amt}円であった。仕訳を示しなさい。',
            'answer': {
                'debit':[{'account':'仕入','amount':amt}],
                'credit':[{'account':'現金','amount':amt}]
            },
            'explanation': '仕入の増加は借方、現金の減少は貸方で記入する。'
        }
    elif (i % 5) == 4:
        # purchase credit
        q = {
            'id': qid,
            'topic_id': tid,
            'exams': ['nissho'],
            'grades': ['3'],
            'valid_from': 2027,
            'difficulty': 1,
            'rows': 2,
            'accounts': ['仕入','買掛金','現金','普通預金'],
            'question': f'商品を掛けで仕入れ、買掛金{amt}円が発生した。仕訳を示しなさい。',
            'answer': {
                'debit':[{'account':'仕入','amount':amt}],
                'credit':[{'account':'買掛金','amount':amt}]
            },
            'explanation': '掛け仕入では買掛金（負債）が増えるため貸方、仕入は借方で記入する。'
        }
    else:
        # depreciation / expense accrual
        q = {
            'id': qid,
            'topic_id': tid,
            'exams': ['nissho'],
            'grades': ['3'],
            'valid_from': 2027,
            'difficulty': 2,
            'rows': 2,
            'accounts': ['減価償却費','建物減価償却累計額','普通預金','現金'],
            'question': f'建物の期末減価償却費として{amt}円を計上する。仕訳を示しなさい。',
            'answer': {
                'debit':[{'account':'減価償却費','amount':amt}],
                'credit':[{'account':'建物減価償却累計額','amount':amt}]
            },
            'explanation': '減価償却費は費用の計上で借方、累計額で控除するため貸方に計上する。'
        }
    questions.append(q)
# assemble YAML
doc = {'format':'journal', 'topic_default': 'BK-1-03-01', 'questions': questions}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding='utf-8')
print('WROTE', out)
