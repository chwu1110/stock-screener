import json, re

with open('disposal_history.json', 'r', encoding='utf-8') as f:
    raw = f.read()

raw_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', raw)

d = json.loads(raw_clean)
print('修復成功！共', len(d), '天')
print('含7721:', '7721' in str(d))

with open('disposal_history.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
