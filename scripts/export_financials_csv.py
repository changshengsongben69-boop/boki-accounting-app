import csv
import yaml
from pathlib import Path

root = Path(__file__).resolve().parents[1]
enhanced_file = root / 'questions' / 'financial-statement' / 'generated-financials-enhanced.yaml'
out_csv = root / 'questions' / 'financial-statement' / 'generated-financials.csv'

data = yaml.safe_load(enhanced_file.read_text(encoding='utf-8'))
questions = data.get('questions', [])

with out_csv.open('w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['id','question','choices','answer_index','explanation'])
    for q in questions:
        qid = q.get('id')
        question = q.get('question','').replace('\n','\\n')
        choices = '|'.join(q.get('choices',[]))
        answer = q.get('answer')
        explanation = q.get('explanation','').replace('\n','\\n')
        writer.writerow([qid, question, choices, answer, explanation])

print('WROTE', out_csv)
