# Local Jenkins setup (http://localhost:10000)

Use this guide for your local Jenkins instance.

## 1. Log in

Open: **http://localhost:10000**

Sign in with your Jenkins username and password.

> **Security:** Do not share Jenkins passwords in chat or commit them to Git.  
> If a password was exposed, change it in Jenkins → click your name → **Security**.

## 2. Install plugins

**Manage Jenkins → Plugins → Available plugins**

Install and restart if prompted:

| Plugin | Why |
|---|---|
| Email Extension Plugin | Sends Allure email after each build |
| Allure Jenkins Plugin | Allure tab on build page |
| Git plugin | Pull repo from GitHub |
| Pipeline / Workflow plugins | Run `Jenkinsfile` |

## 3. Configure email (Allure notifications)

**Manage Jenkins → System**

Scroll to **Extended E-mail Notification**:

| Field | Suggested value (Rolustech / Microsoft 365) |
|---|---|
| SMTP server | `smtp.office365.com` |
| Default user e-mail suffix | `@rolustech.com` |
| SMTP Port | `587` |
| Use TLS | ✓ |
| Credentials | Add Jenkins credential with your mailbox + password |

Set **System Admin e-mail address** under **E-mail Notification** (required).

Save.

## 4. Create the pipeline job

### Option A — UI (easiest)

1. **New Item** → name: `credaris-selenium-automation` → **Pipeline** → OK
2. Under **Pipeline**:
   - Definition: **Pipeline script from SCM**
   - SCM: **Git**
   - Repository URL: `https://github.com/hinasiddiqui-qa/credaris.git`
   - Branch: `*/main`
   - Script Path: `Jenkinsfile`
3. Save → **Build Now**

### Option B — Script (API token)

1. Jenkins → your name → **Security** → **Add new Token** → copy token
2. In PowerShell:

```powershell
cd C:\Users\hina.siddiqui\credaris-selenium-automation

$env:JENKINS_URL   = "http://localhost:10000"
$env:JENKINS_USER  = "hina.siddiqui@rolustech.com"
$env:JENKINS_TOKEN = "paste-api-token-here"

.\scripts\jenkins\setup_pipeline.ps1
```

Use an **API token**, not your web login password.

## 5. Add test credentials in Jenkins

**Manage Jenkins → Credentials → Add Credentials → Secret text**

| ID | Value |
|---|---|
| `credaris-microsoft-username` | Microsoft SSO username |
| `credaris-microsoft-password` | Microsoft SSO password |
| `credaris-sugar-username` | Sugar username |
| `credaris-sugar-password` | Sugar password |

These IDs must match the `Jenkinsfile`.

## 6. Prepare the Jenkins agent

Your local Jenkins agent needs:

- Python 3.10+
- Google Chrome
- ZPA / network access to `sugar-test.intern.credaris.ch`
- Label: `selenium` (or change `AGENT_LABEL` when building)

Optional — Allure ZIP in email:

```powershell
scoop install allure
```

## 7. What happens on each build

Pipeline stages:

```
Checkout → Run tests → Generate Allure report → Publish + Email
```

Email goes to **hina.siddiqui@rolustech.com** (change via `NOTIFY_EMAIL` parameter) with:

- Build status summary
- Link to Allure in Jenkins: `http://localhost:10000/job/credaris-selenium-automation/<build>/allure/`
- `allure-report.zip` attachment (if Allure CLI is installed)

## Troubleshooting

| Issue | Fix |
|---|---|
| Invalid username or password | Reset password in Jenkins Security; use API token for scripts |
| Email not sent | Check SMTP settings and Email Extension Plugin |
| Git clone fails | Add GitHub credentials in Jenkins if repo is private |
| Tests fail on MFA | Bootstrap session on agent or use MFA-exempt account |
