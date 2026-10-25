import re

for name in ['html_portfolio.txt', 'html_watchlist.txt', 'html_stock_AAPL.txt']:
    path = f'Dow is Up 50k/recon/{name}'
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    chunks = set(re.findall(r'/_next/static/chunks/[^\"]+\.js', content))
    print(f'=== {name} ===')
    for c in sorted(chunks):
        print('  ', c)
