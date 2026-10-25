with open('Dow is Up 50k/recon/rsc_stock_AAPL.txt', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
matches = re.findall(r'\{"date":[^}]+\}', text)
print(f'Total date matches: {len(matches)}')
for m in matches[:5]:
    print(' ', m)
if matches:
    print('  ... last match:', matches[-1])
