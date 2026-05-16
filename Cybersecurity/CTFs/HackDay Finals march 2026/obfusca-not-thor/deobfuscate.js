// Deobfuscation script for obfuscated.js
// The string array (after rotation stabilizes at the correct offset)
// Based on the obfuscated code, the string array is:
const _arr = ['Welcome\x20guest','4yLTFPA','/vuln','30904Xqnjvn','2177UMQZVs','130hyXqvt','send','/vuqsqsddqsdln123','body','log','use','disable','get','post','/vuqsqsqdsddqsd2189ln','/vuqsqsqdsddqsdl1221n','4929897UCtxHg','722307QCOqZr','/vuqsqsqdsdqsddqsdln','/vuqsqsq11212dsddqsdln','Hello\x20World!','mi12n','3870270VguSFA','admin','203495djbriC','listen','328977RKzETf','Welcome\x20admin','/vuqsqsqdsddqsdln','data','92qCdBYq','/vuqsdqsdln','Server\x20is\x20running\x20on\x20port\x20','/vul18ddqsdln126','/vuqsq1212qsqdsddqsdln','node-serialize','53707093OWMjaY','unserialize','urlencoded','ad1','/vuqs1244qsqdsddqsdln','x-powered-by'];

function lookup(idx) {
    idx = idx - 0x74;
    return _arr[idx];
}

// Print all mappings
console.log("=== String Lookup Table ===");
for (let i = 0x74; i < 0x74 + _arr.length; i++) {
    console.log(`0x${i.toString(16)} => "${lookup(i)}"`);
}

// Now reconstruct the deobfuscated logic:
console.log("\n=== Deobfuscated Code Analysis ===");

// Key mappings:
// 0x74 = '/vuln'
// 0x75 = '30904Xqnjvn'  (number)
// 0x76 = '4yLTFPA'      (number)
// 0x77 = '/vuqsdqsdln'
// 0x78 = '/vuqsqsddqsdln123' => route
// 0x79 = 'Hello World!'
// 0x7a = 'mi12n'
// 0x7b = '2177UMQZVs'   (number)
// 0x7c = 'admin'
// 0x7d = '4929897UCtxHg'  (number => but wait)
// wait let me recount

// arr[0] = 'Welcome guest'   => 0x74+0 = 0x74
// arr[1] = '4yLTFPA'        => 0x75
// arr[2] = '/vuln'           => 0x76
// arr[3] = '30904Xqnjvn'    => 0x77
// arr[4] = '2177UMQZVs'     => 0x78
// arr[5] = '130hyXqvt'      => 0x79
// arr[6] = 'send'            => 0x7a
// arr[7] = '/vuqsqsddqsdln123' => 0x7b
// arr[8] = 'body'            => 0x7c
// arr[9] = 'log'             => 0x7d
// arr[10] = 'use'            => 0x7e
// arr[11] = 'disable'        => 0x7f
// arr[12] = 'get'            => 0x80
// arr[13] = 'post'           => 0x81
// arr[14] = '/vuqsqsqdsddqsd2189ln' => 0x82
// arr[15] = '/vuqsqsqdsddqsdl1221n' => 0x83
// arr[16] = '4929897UCtxHg'  => 0x84
// arr[17] = '722307QCOqZr'   => 0x85
// arr[18] = '/vuqsqsqdsdqsddqsdln' => 0x86
// arr[19] = '/vuqsqsq11212dsddqsdln' => 0x87
// arr[20] = 'Hello World!'   => 0x88
// arr[21] = 'mi12n'          => 0x89
// arr[22] = '3870270VguSFA'  => 0x8a -- unserialize? No wait
// arr[23] = 'admin'          => 0x8b
// arr[24] = '203495djbriC'   => 0x8c
// arr[25] = 'listen'         => 0x8d
// arr[26] = '328977RKzETf'   => 0x8e
// arr[27] = 'Welcome admin'  => 0x8f
// arr[28] = '/vuqsqsqdsddqsdln' => 0x90
// arr[29] = 'data'           => 0x91
// arr[30] = '92qCdBYq'       => 0x92
// arr[31] = '/vuqsdqsdln'    => 0x93
// arr[32] = 'Server is running on port ' => 0x94
// arr[33] = '/vul18ddqsdln126' => 0x95
// arr[34] = '/vuqsq1212qsqdsddqsdln' => 0x96
// arr[35] = 'node-serialize' => 0x97
// arr[36] = '53707093OWMjaY' => 0x98
// arr[37] = 'unserialize'    => 0x99
// arr[38] = 'urlencoded'     => 0x9a
// arr[39] = 'ad1'            => 0x9b
// arr[40] = '/vuqs1244qsqdsddqsdln' => 0x9c
// arr[41] = 'x-powered-by'   => 0x9d

// But the actual offsets used in code are different due to the rotation!
// The self-invoking rotation function rotates the array until the sum equals 0xe5670
// We need to figure out how many rotations happened.

// Let me try to compute the deobfuscated routes by checking actual code references
// From the code:
// serialize=require(_0x1d7bcf(0x88))  => node-serialize
// app[_0x1d7bcf(0x9a)](_0x1d7bcf(0x8e)) => app.use('x-powered-by') -- disable
// app[_0x1d7bcf(0x99)](express.json())
// app[_0x1d7bcf(0x99)](express[_0x1d7bcf(0x8b)]({'extended':true})) => urlencoded

// So: 0x88 = 'node-serialize', 0x9a = 'use', 0x8e = 'x-powered-by' or 'disable'
// 0x99 = 'use', 0x8b = 'urlencoded'

// From the string array, unrotated:
// 'node-serialize' is at index 35 => base = 0x74, so position 35 = 0x74+35 = 0x97
// But in code it's 0x88. So offset = 0x97 - 0x88 = 0x0F = 15
// The array was rotated 15 times (or the array shifted by 15 positions left)

// Let's verify: if rotated by 15:
// new_arr[0] = old_arr[15] = '/vuqsqsqdsddqsdl1221n'
// So: lookup(0x74) = '/vuqsqsqdsddqsdl1221n'
// lookup(0x88) = old_arr[15+20] = old_arr[35-wait...

// If the rotation is: each shift moves arr[0] to the end
// After 15 rotations, arr[15] is now at position 0
// So lookup(idx) = original_arr[(idx - 0x74 + 15) % arr.length]

function lookupRotated(idx, rotation) {
    idx = idx - 0x74;
    return _arr[(idx + rotation) % _arr.length];
}

// Verify: 0x88 should be 'node-serialize'
// With rotation=15: (0x88-0x74+15) % 42 = (20+15) % 42 = 35 => _arr[35] = 'node-serialize' ✓
console.log("\n=== Testing rotation=15 ===");
console.log("0x88 =>", lookupRotated(0x88, 15), "(expected: node-serialize)");
console.log("0x9a =>", lookupRotated(0x9a, 15), "(expected: use)");
console.log("0x8b =>", lookupRotated(0x8b, 15), "(expected: urlencoded)");
console.log("0x8e =>", lookupRotated(0x8e, 15), "(expected: disable or x-powered-by)");

console.log("\n=== Full Deobfuscated Mappings (rotation=15) ===");
for (let i = 0x74; i < 0x74 + _arr.length; i++) {
    console.log(`0x${i.toString(16)} => "${lookupRotated(i, 15)}"`);
}

// Now let's reconstruct the routes:
console.log("\n=== Routes Analysis ===");
// app[get]('/') => 'Hello World!' 
// actually: app[_0x1d7bcf(0x9b)]('/',...) => get
console.log("0x9b =>", lookupRotated(0x9b, 15), "(app method for GET /)");
// app['post'](_0x1d7bcf(0x74),...) => first POST route
console.log("0x74 =>", lookupRotated(0x74, 15), "(first POST route)");
// app[_0x1d7bcf(0x9c)](_0x1d7bcf(0x91),...) => other routes
console.log("0x9c =>", lookupRotated(0x9c, 15), "(app method for routes)");
console.log("0x91 =>", lookupRotated(0x91, 15), "(route path)");
console.log("0x84 =>", lookupRotated(0x84, 15), "(route path)");
console.log("0x96 =>", lookupRotated(0x96, 15), "(route path)");
console.log("0x9d =>", lookupRotated(0x9d, 15), "(route path)");
console.log("0x8d =>", lookupRotated(0x8d, 15), "(route path for app.post)");
console.log("0x81 =>", lookupRotated(0x81, 15), "(route path)");
console.log("0x86 =>", lookupRotated(0x86, 15), "(route path)");
console.log("0x87 =>", lookupRotated(0x87, 15), "(route path)");
console.log("0x78 =>", lookupRotated(0x78, 15), "(route path)");
console.log("0x77 =>", lookupRotated(0x77, 15), "(route path)");
console.log("0x7e =>", lookupRotated(0x7e, 15), "(listen)");
console.log("0x7c =>", lookupRotated(0x7c, 15), "(check function compare)");
console.log("0x80 =>", lookupRotated(0x80, 15), "(check return 1)");
console.log("0x8f =>", lookupRotated(0x8f, 15), "(check return 2)");

// Key state variables:
console.log("\n=== State Logic ===");
// check(x): if x == lookup(0x7c) return lookup(0x80) else return lookup(0x8f)
// => if x == 'admin' return 'Welcome admin' else return 'Welcome guest'
console.log("check('admin') should return:", lookupRotated(0x80, 15));
console.log("check(other) should return:", lookupRotated(0x8f, 15));

// Route with serialize.unserialize:
// app[post](0x86,...) { if a['za']=='a12b' then body=serialize.unserialize(data) }
console.log("\n0x86 route (unserialize):", lookupRotated(0x86, 15));
console.log("0x8a =>", lookupRotated(0x8a, 15), "(unserialize method)");

// State machine:
// Route 0x96: if data == lookup(0x8c)+lookup(0x7a) then a['aa']='ad1mi12n'
console.log("\n=== Unlock Sequence ===");
console.log("0x8c =>", lookupRotated(0x8c, 15));
console.log("0x7a =>", lookupRotated(0x7a, 15));
console.log("Trigger string:", lookupRotated(0x8c, 15) + lookupRotated(0x7a, 15));
// Route vuqsqsqdsddqsdln1: if data=='ba12' && a['aa']=='ad1mi12n' then a['za']='a12b'
// Route 0x86: if a['za']=='a12b' then serialize.unserialize(data) -- RCE!
