# The Block City Times: Full Challenge Writeup

## Background
- **Challenge Type**: Web Exploitation
- **Difficulty**: Medium
- **Target App**: Spring Boot (Java) with Thymeleaf templates.

## 1. Proxy Bypass & Instance Deployment
The challenge was hosted behind a CTFd proxy.
1. **CTFd Registration**: We registered on `ctf.umasscybersec.org`, created a team, and generated an access token (`ctfd_4b7fe7...`).
2. **Authentication**: Submitted the token to `http://blockcitytimes.web.ctf.umasscybersec.org:5000/` which uses gunicorn/Flask to manage per-team instances.
3. **Deployment**: Triggered "Create Instance" which used Socket.IO to deploy a dedicated container (`3dea8698...`).

## 2. Vulnerability Discovery

### V1: XSS via Content-Type Sniffing
The TIP submission form accepts `text/plain` files. However, the server serves these files using `Files.probeContentType(file)`. By naming a file `payload.html`, we forced the server to set the `Content-Type` header to `text/html`, allowing us to execute arbitrary JavaScript when the Editorial bot views the "tip".

### V2: Actuator Configuration Injection (CSRF Disabled)
Spring Boot Actuator endpoints (`/actuator/**`) were publicly accessible and had CSRF protection disabled in `SecurityConfig.java`. This allowed the XSS payload (running as the authenticated Editorial bot) to:
- POST to `/actuator/env` to set `app.active-config=dev`.
- POST to `/actuator/refresh` to apply the config change.
This switched the app into "development mode", which was the prerequisite for triggering the admin report functionality.

### V3: Path Traversal ACL Bypass
The `/admin/report` endpoint was protected by a simple check:
```java
if (!endpoint.startsWith("/api/")) { ... redirect error ... }
```
We bypassed this using path traversal: `/api/../files/payload.html`. The payload starts with `/api/` (satisfying the check) but resolves to our XSS file in the `/files/` directory.

## 3. Exploit Execution Chain
1. **Upload Payload**: Uploaded `payload.html` via `/submit`.
2. **Editorial Bot Interaction**: The bot views the submission, triggering the XSS.
3. **Actuator Switch**: XSS reconfigures the app to `dev` mode and refreshes.
4. **Report Trigger**: XSS extracts the CSRF token from `/admin` and POSTs to `/admin/report` with the traversed path.
5. **Report Bot Execution**: The `report-runner` bot (holding the `FLAG` cookie) is spawned and navigates to the traversed path (our XSS).
6. **Exfiltration**: The XSS payload recognizes it's running in the report bot (detects `FLAG` cookie) and sends the cookie to our webhook.

## 4. Final Result
**Captured Flag**: `UMASS{A_mAn_h3s_f@l13N_1N_tH3_r1v3r}`

---
*Exploit developed and executed by Antigravity*
