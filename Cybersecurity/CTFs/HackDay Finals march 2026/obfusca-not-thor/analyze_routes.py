import re

code = open('/mnt/c/Users/crist/OneDrive/Desktop/obfusca-not-thor/obfuscated.js').read()

# String array with rotation=15 applied
arr_original = ['Welcome guest','4yLTFPA','/vuln','30904Xqnjvn','2177UMQZVs','130hyXqvt','send','/vuqsqsddqsdln123','body','log','use','disable','get','post','/vuqsqsqdsddqsd2189ln','/vuqsqsqdsddqsdl1221n','4929897UCtxHg','722307QCOqZr','/vuqsqsqdsdqsddqsdln','/vuqsqsq11212dsddqsdln','Hello World!','mi12n','3870270VguSFA','admin','203495djbriC','listen','328977RKzETf','Welcome admin','/vuqsqsqdsddqsdln','data','92qCdBYq','/vuqsdqsdln','Server is running on port ','/vul18ddqsdln126','/vuqsq1212qsqdsddqsdln','node-serialize','53707093OWMjaY','unserialize','urlencoded','ad1','/vuqs1244qsqdsddqsdln','x-powered-by']

def lookup(idx, rotation=15):
    idx = idx - 0x74
    return arr_original[(idx + rotation) % len(arr_original)]

# Split on route handlers
parts = code.split('app[')
for i, p in enumerate(parts):
    print(f'=== Part {i} ===')
    print(p[:500])
    print()
