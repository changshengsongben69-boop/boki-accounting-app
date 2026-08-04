import yaml
from pathlib import Path
import random

root = Path(__file__).resolve().parents[1]
enhanced_file = root / 'questions' / 'financial-statement' / 'generated-financials-enhanced.yaml'
review_dir = root / 'questions' / 'financial-statement' / 'review'

data = yaml.safe_load(enhanced_file.read_text(encoding='utf-8'))
questions = data.get('questions', [])

# Typical exam-friendly amounts (円)
amount_pool = [30000,50000,80000,100000,120000,150000,200000,300000,500000]

def round_to_pool(n):
    # find closest in pool
    return min(amount_pool, key=lambda x: abs(x-n))

new_questions = []
for q in questions:
    # parse entries from question text
    lines = [ln.strip() for ln in q.get('question','').splitlines() if ln.strip()]
    lines = [ln for ln in lines if not ln.startswith('以下は')]
    entries = []
    for ln in lines:
        try:
            parts = ln.split()
            amt_token = parts[-1]
            amt = int(amt_token[:-1]) if amt_token.endswith('円') else int(amt_token.replace(',',''))
            acc = parts[0]
            side = 'debit' if '(借方)' in ln else 'credit'
            entries.append([acc, side, amt])
        except Exception:
            continue
    # adjust amounts to pool, but keep sign logic
    for e in entries:
        original = e[2]
        e[2] = round_to_pool(original)
        # small random perturbation occasionally
        if random.random() < 0.2:
            e[2] += random.choice([-10000, 10000])
    # rebuild question prompt and lines, choose phrasing more formal
    is_net_income = '当期純利益' in q.get('question','')
    if is_net_income:
        prompt = '次の残高試算表（一部）に基づき、当期純利益（損失）を計算し、最も適当な金額を選びなさい。'
    else:
        prompt = '次の残高試算表（一部）に基づき、総資産額に最も近い金額を選びなさい。'
    line_texts = [f"{acc} ({'借方' if side=='debit' else '貸方'}) {amt}円" for (acc, side, amt) in entries]
    new_text = prompt + '\n\n' + '\n'.join(line_texts)

    # recompute correct answer and choices (keep similar approach)
    if is_net_income:
        revenues = sum(a for (acc, side, a) in entries if side=='credit' and acc in ['売上','受取利息','受取配当金','有価証券売却益'])
        expenses = sum(a for (acc, side, a) in entries if side=='debit' and acc in ['仕入','給料','減価償却費','支払利息','租税公課'])
        correct = revenues - expenses
    else:
        asset_names = ['現金','普通預金','売掛金','備品','繰越商品','前払金']
        contra_names = ['備品減価償却累計額','建物減価償却累計額','減価償却累計額']
        assets = sum(a for (acc, side, a) in entries if side=='debit' and acc in asset_names)
        contra = sum(a for (acc, side, a) in entries if side=='credit' and acc in contra_names)
        correct = assets - contra

    # build choices with plausible distractors
    deltas = [-30000, -10000, 10000, 30000]
    random.shuffle(deltas)
    correct_index = random.randint(0,3)
    choices = []
    for idx in range(4):
        if idx == correct_index:
            choices.append(str(correct))
        else:
            # ensure non-negative
            val = max(0, correct + deltas.pop())
            choices.append(str(val))

    q_new = dict(q)
    q_new['question'] = new_text
    q_new['choices'] = choices
    q_new['answer'] = correct_index
    # improve explanation wording slightly
    q_new['explanation'] = '計算手順：\n' + q.get('explanation','')
    new_questions.append(q_new)

# write back enhanced file and rewrite review chunks
enhanced_file.write_text(yaml.safe_dump({'format':'multiple-choice','questions':new_questions}, allow_unicode=True, sort_keys=False), encoding='utf-8')
for i in range(0, len(new_questions), 5):
    chunk = new_questions[i:i+5]
    fname = review_dir / f'generated-financials-review-{i//5+1:02d}.yaml'
    fname.write_text(yaml.safe_dump({'format':'multiple-choice','questions':chunk}, allow_unicode=True, sort_keys=False), encoding='utf-8')

print('TUNED and rewrote enhanced and review chunks')
