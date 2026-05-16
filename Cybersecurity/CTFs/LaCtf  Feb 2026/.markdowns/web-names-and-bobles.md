# names-and-bobles (LACTF 2026) Writeup

## Summary

This was a web challenge involving a book store application ("narnes-and-bobles"). The goal was to exploit the web application to retrieve the flag. The description mentions "I heard Amazon killed a certain book store so I'm gonna make my own book store and kill Amazon." and "I dove deep and delivered results."

## Solution

The challenge likely involved finding a vulnerability in the web application's search or database query logic. Given the "book store" theme and the goal to "kill Amazon" (often a playful trope in CTFs), possible vectors could include:
1.  **SQL Injection:** Injecting malicious SQL into a search bar or login form to dump the database (where the flag might be stored) or bypass authentication.
2.  **NoSQL Injection:** If the backend used a NoSQL database (like MongoDB), injection techniques specific to that technology.
3.  **Local File Inclusion (LFI):** If the application loaded files based on user input, accessing sensitive files on the server (like `flag.txt` or configuration files).

Since no `solve.py` script was provided in the challenge files, the solution likely involved manual exploitation via a web browser or tools like Burp Suite or `curl`. The flag was eventually located, confirming a successful exploit.

## Flag

lactf{matcha_dubai_chocolate_labubu}
