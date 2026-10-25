import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('Dow is Up 50k/recon/stock_page.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
# find all server action references
actions = re.findall(r'createServerReference\([^\)]+\)', text)
for a in actions:
    print('Action:', a)

# print full formatted code
print('\n=== Full content ===\n')
print(text)

