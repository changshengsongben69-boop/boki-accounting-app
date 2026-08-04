import yaml
from pathlib import Path
import random

root = Path(__file__).resolve().parents[1]
out_dir = root / 'questions' / 'financial-statement'
out = out_dir / 'generated-financials.yaml'

# Simple templates: provide trial balance lines, ask to compute Net Income or Assets/Liabilities
# We'll produce multiple-choice style questions with 4 choices.

accounts = [
    ('売上', 'revenue'),
    ('仕入', 'expense'),
    ('給料', 'expense'),
    ('減価償却費', 'expense'),
    ('支払利息', 'expense'),
    ('受取利息', 'revenue'),
    ('租税公課', 'expense'),
    ('売掛金', 'asset'),
    ('現金', 'asset'),
    ('普通預金', 'asset'),
    ('買掛金', 'liability'),
    ('借入金', 'liability'),
    ('資本金', 'equity'),
    ('繰越利益剰余金', 'equity'),
    ('備品', 'asset'),
    ('備品減価償却累計額', 'contra')
]

questions = []

def make_trial_balance(num_lines=8):
    sample = random.sample(accounts, k=num_lines)
    tb = []
    for name, typ in sample:
        amt = random.choice([50000,100000,150000,200000,250000,300000])
        # For contra accounts use credit for contra
        side = 'debit'
        if typ in ('liability','equity','revenue','contra'):
            side = 'credit'
        tb.append({'account': name, 'side': side, 'amount': amt})
    return tb

for i in range(1,31):
    qid = f'GEN-FS-{i:03d}'
    tb = make_trial_balance()
    # Decide question type: compute Net Income (損益) or compute Total Assets
    if i % 2 == 1:
        # Net income = revenues - expenses
        rev = sum(item['amount'] for item in tb if item['side']=='credit' and any(item['account']==a[0] and a[1]=='revenue' for a in accounts))
        exp = sum(item['amount'] for item in tb if item['side']=='debit' and any(item['account']==a[0] and a[1]=='expense' for a in accounts))
        # Add small adjustment to ensure nonzero
        correct = rev - exp
        prompt = '以下は決算整理前の残高試算表の一部である。これらに基づいて当期純利益（損失）を計算し、最も近い金額を選びなさい。'
    else:
        # Total assets = sum of asset debits minus contra credits
        assets = sum(item['amount'] for item in tb if item['side']=='debit' and any(item['account']==a[0] and a[1]=='asset' for a in accounts))
        contra = sum(item['amount'] for item in tb if item['side']=='credit' and any(item['account']==a[0] and a[1]=='contra' for a in accounts))
        correct = assets - contra
        prompt = '以下は試算表の一部である。これらに基づいて総資産額に最も近い金額を選びなさい。'

    # Build choices around correct value
    choices = []
    deltas = [-30000, -10000, 10000, 30000]
    random.shuffle(deltas)
    correct_index = random.randint(0,3)
    for c in range(4):
        if c == correct_index:
            choices.append(str(correct))
        else:
            choices.append(str(max(0, correct + deltas[c])))

    # Build human-readable trial balance lines
    lines = [f"{l['account']} ({'借方' if l['side']=='debit' else '貸方'}) {l['amount']}円" for l in tb]
    question_text = prompt + '\n\n' + '\n'.join(lines)

    q = {
        'id': qid,
        'topic_id': 'BK-3-09-01',
        'exams': ['nissho'],
        'grades': ['3'],
        'valid_from': 2027,
        'difficulty': 2,
        'question': question_text,
        'choices': choices,
        'answer': correct_index,
        'explanation': '試算表の貸借を分類して計算する。'
    }
    questions.append(q)

# write YAML
out_dir.mkdir(parents=True, exist_ok=True)
out.write_text(yaml.safe_dump({'format':'multiple-choice','questions':questions}, allow_unicode=True, sort_keys=False), encoding='utf-8')
print('WROTE', out)
