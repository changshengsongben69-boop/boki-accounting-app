import yaml
from pathlib import Path

root = Path(__file__).resolve().parents[1]
enhanced_file = root / 'questions' / 'financial-statement' / 'generated-financials-enhanced.yaml'
review_dir = root / 'questions' / 'financial-statement' / 'review'

data = yaml.safe_load(enhanced_file.read_text(encoding='utf-8'))
questions = data.get('questions', [])

def parse_entries(text):
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    lines = [ln for ln in lines if not ln.startswith('以下は')]
    entries = []
    for ln in lines:
        try:
            parts = ln.split()
            amt_token = parts[-1]
            amt = int(amt_token[:-1]) if amt_token.endswith('円') else int(amt_token.replace(',',''))
            acc = parts[0]
            side = 'debit' if '(借方)' in ln else 'credit'
            entries.append((acc, side, amt))
        except Exception:
            continue
    return entries

for q in questions:
    entries = parse_entries(q.get('question',''))
    if '当期純利益' in q.get('question',''):
        revenues = sum(a for (acc, side, a) in entries if side=='credit' and acc in ['売上','受取利息','受取配当金','有価証券売却益'])
        expenses = sum(a for (acc, side, a) in entries if side=='debit' and acc in ['仕入','給料','減価償却費','支払利息','租税公課'])
        correct = revenues - expenses
        expl = []
        expl.append('計算手順：')
        expl.append(f'1) 収益合計を求める: $\text{{収益合計}} = {revenues}$')
        expl.append(f'2) 費用合計を求める: $\text{{費用合計}} = {expenses}$')
        expl.append(f'3) 当期純利益 = 収益合計 − 費用合計 = $ {revenues} - {expenses} = {correct} $')
        expl_text = '\n'.join(expl)
    else:
        asset_names = ['現金','普通預金','売掛金','備品','繰越商品','前払金']
        contra_names = ['備品減価償却累計額','建物減価償却累計額','減価償却累計額']
        assets = sum(a for (acc, side, a) in entries if side=='debit' and acc in asset_names)
        contra = sum(a for (acc, side, a) in entries if side=='credit' and acc in contra_names)
        correct = assets - contra
        expl = []
        expl.append('計算手順：')
        expl.append(f'1) 資産の合計を求める: $\text{{資産合計}} = {assets}$')
        expl.append(f'2) 控除科目(累計減価償却等)を求める: $\text{{控除}} = {contra}$')
        expl.append(f'3) 総資産 = 資産合計 − 控除 = $ {assets} - {contra} = {correct} $')
        expl_text = '\n'.join(expl)
    # attach KaTeX-enhanced explanation
    q['explanation'] = expl_text + '\n\n（注）上記は試算表の一部に基づく簡易計算。実際の決算整理では追加仕訳が入る場合がある。'

# overwrite enhanced file
enhanced_file.write_text(yaml.safe_dump({'format':'multiple-choice','questions':questions}, allow_unicode=True, sort_keys=False), encoding='utf-8')

# rewrite review chunks (5 per file)
for i in range(0, len(questions), 5):
    chunk = questions[i:i+5]
    fname = review_dir / f'generated-financials-review-{i//5+1:02d}.yaml'
    fname.write_text(yaml.safe_dump({'format':'multiple-choice','questions':chunk}, allow_unicode=True, sort_keys=False), encoding='utf-8')

print('Updated explanations with KaTeX math and rewrote review chunks')
