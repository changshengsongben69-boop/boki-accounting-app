import yaml
from pathlib import Path
import random

root = Path(__file__).resolve().parents[1]
input_file = root / 'questions' / 'financial-statement' / 'generated-financials.yaml'
out_file = root / 'questions' / 'financial-statement' / 'generated-financials-enhanced.yaml'
review_dir = root / 'questions' / 'financial-statement' / 'review'

data = yaml.safe_load(input_file.read_text(encoding='utf-8'))
questions = data.get('questions', [])
enhanced = []

for q in questions:
    # try parse the lines to compute correct value from the question text
    text = q.get('question','')
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    # filter out the prompt line(s)
    lines = [ln for ln in lines if not ln.startswith('以下は')]
    # parse account lines like "売掛金 (借方) 150000円"
    entries = []
    for ln in lines:
        try:
            parts = ln.split()
            # fallback: last token is amount with 円
            amt_token = parts[-1]
            if amt_token.endswith('円'):
                amt = int(amt_token[:-1])
            else:
                # try comma removal
                amt = int(amt_token.replace(',',''))
            acc = parts[0]
            side = 'debit' if '(借方)' in ln else 'credit'
            entries.append((acc, side, amt))
        except Exception:
            continue
    # determine whether question asks net income or total assets
    if '当期純利益' in q.get('question','') or '当期純利益' in text:
        # revenues (credit) - expenses (debit)
        revenues = sum(a for (acc, side, a) in entries if side=='credit' and acc in ['売上','受取利息','受取配当金','有価証券売却益'])
        expenses = sum(a for (acc, side, a) in entries if side=='debit' and acc in ['仕入','給料','減価償却費','支払利息','租税公課'])
        correct = revenues - expenses
        explanation = f"計算: 収益合計 {revenues} - 費用合計 {expenses} = {correct}"
    else:
        # total assets = sum debit assets - contra credits
        asset_names = ['現金','普通預金','売掛金','備品','繰越商品','前払金']
        contra_names = ['備品減価償却累計額','建物減価償却累計額','減価償却累計額']
        assets = sum(a for (acc, side, a) in entries if side=='debit' and acc in asset_names)
        contra = sum(a for (acc, side, a) in entries if side=='credit' and acc in contra_names)
        correct = assets - contra
        explanation = f"計算: 資産合計 {assets} - 減価償却等(控除) {contra} = {correct}"

    # Build better choices around correct value
    offsets = [ -30000, -10000, 10000, 30000 ]
    random.shuffle(offsets)
    # place correct at random position
    correct_index = random.randint(0,3)
    choices = []
    for idx in range(4):
        if idx == correct_index:
            choices.append(str(correct))
        else:
            val = max(0, correct + offsets.pop())
            choices.append(str(val))

    # update question
    q_new = dict(q)
    q_new['choices'] = choices
    q_new['answer'] = correct_index
    q_new['explanation'] = explanation + '\n\n（参考）試算表の各科目を貸借で分類して集計してください。'
    enhanced.append(q_new)

# write enhanced file
out_file.write_text(yaml.safe_dump({'format':'multiple-choice','questions':enhanced}, allow_unicode=True, sort_keys=False), encoding='utf-8')

# split into review files of 5 each
review_dir.mkdir(parents=True, exist_ok=True)
for i in range(0, len(enhanced), 5):
    chunk = enhanced[i:i+5]
    fname = review_dir / f'generated-financials-review-{i//5+1:02d}.yaml'
    fname.write_text(yaml.safe_dump({'format':'multiple-choice','questions':chunk}, allow_unicode=True, sort_keys=False), encoding='utf-8')

print('WROTE enhanced and review chunks')
