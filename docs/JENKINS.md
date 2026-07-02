# Jenkins CI/CD setup

This project includes a declarative `Jenkinsfile` that runs the smoke suite, publishes JUnit + Allure reports, and emails the Allure report after every build.

**Local Jenkins:** [docs/JENKINS_LOCAL.md](JENKINS_LOCAL.md) — setup for `http://localhost:10000`

## Prerequisites on the Jenkins agent

| Requirement | Notes |
|---|---|
| Python 3.10+ | Available as `python` on PATH |
| Google Chrome | Required for Selenium |
| Network access | Agent must reach ZPA + `sugar-test.intern.credaris.ch` |
| Allure Jenkins plugin | Publishes interactive Allure report in Jenkins |
| Allure CLI (optional) | Adds ZIP attachment to email (`allure` on PATH) |
| Email Extension Plugin | Required for build email notifications |

Microsoft MFA is interactive. For CI, use one of these approaches:

1. **Dedicated agent** with ZPA installed and a pre-bootstrapped Chrome profile (set `REUSE_SESSION=true` in the Jenkins job environment).
2. **Service account** exempt from MFA (preferred for unattended runs).
3. **Manual bootstrap** on the agent once, then reuse the profile directory between builds.

## 1. Push the repository to Git

From your machine:

```powershell
cd C:\Users\hina.siddiqui\credaris-selenium-automation

# First commit (if not done yet)
git add .
git status
git commit -m "Initial commit: Credaris Selenium automation framework"

# Rename branch to main (optional)
git branch -M main

# Add your remote (examples)
git remote add origin https://github.com/hinasiddiqui-qa/credaris.git
git push -u origin main
```

Never commit `config/config.properties`, `.env`, `.chrome-profile/`, or `sessions/` — they are gitignored and contain secrets.

## 2. Create Jenkins credentials

In **Manage Jenkins → Credentials**, create four **Secret text** credentials:

| Credential ID | Value |
|---|---|
| `credaris-microsoft-username` | Microsoft SSO username |
| `credaris-microsoft-password` | Microsoft SSO password |
| `credaris-sugar-username` | Sugar CRM username |
| `credaris-sugar-password` | Sugar CRM password |

These IDs must match the `Jenkinsfile` exactly (or update the IDs in the pipeline).

## 3. Create the Jenkins pipeline job

1. **New Item** → **Pipeline**
2. Name: `credaris-selenium-automation`
3. Under **Pipeline**:
   - Definition: **Pipeline script from SCM**
   - SCM: **Git**
   - Repository URL: `https://github.com/hinasiddiqui-qa/credaris.git`
   - Credentials: Jenkins credential with read access to the repo
   - Branch: `main`
   - Script Path: `Jenkinsfile`
4. Save and **Build Now**

### Job parameters

| Parameter | Default | Purpose |
|---|---|---|
| `AGENT_LABEL` | `selenium` | Label of agents with Chrome + ZPA access |
| `TEST_MARKER` | `smoke` | Pytest marker (`smoke`, `regression`, `contacts`, `leads`) |
| `NOTIFY_EMAIL` | `hina.siddiqui@rolustech.com` | Recipient for Allure report email after every build |

## 4. Configure Jenkins email (Allure notifications)

Install these plugins from **Manage Jenkins → Plugins**:

| Plugin | Purpose |
|---|---|
| **Email Extension Plugin** | Sends HTML email with attachments (`emailext`) |
| **Allure Jenkins Plugin** | Allure tab on each build |
| **JUnit Plugin** | JUnit test trends |

Configure SMTP in **Manage Jenkins → System → Extended E-mail Notification**:

| Setting | Example |
|---|---|
| SMTP server | `smtp.office365.com` (for Rolustech / Microsoft 365) |
| SMTP Port | `587` |
| Use TLS | Enabled |
| Username | Jenkins service mailbox |
| Password | App password or service account password |
| Default user e-mail suffix | `@rolustech.com` |

Also set **E-mail Notification → System Admin e-mail address** (required by Jenkins).

### What you receive after every build

An email is sent to **`hina.siddiqui@rolustech.com`** (change via the `NOTIFY_EMAIL` job parameter) containing:

1. Build status, job name, branch, and test marker
2. Link to the **Allure report in Jenkins** (`Build URL → Allure`)
3. **`allure-report.zip` attachment** (when Allure CLI is installed on the agent)

Pipeline stages:

```
Checkout → Run tests → Generate Allure report → Publish + Email
```

## 5. Label your Jenkins agent

On the node that will run UI tests:

1. Install Python 3, Chrome, and ZPA client (if required).
2. Set the agent label to `selenium` (or change `AGENT_LABEL` in the job).
3. For session reuse, bootstrap once on that agent:

```powershell
copy config\config.example.properties config\config.properties
# edit config.properties with real credentials
python scripts\bootstrap_session.py
```

Then set `REUSE_SESSION=true` in the Jenkins job **Environment** section if you want to skip MFA on subsequent runs.

Install **Allure CLI** on the agent so the email includes a ZIP attachment:

```powershell
# Windows (Scoop)
scoop install allure

# Or download from https://github.com/allure-framework/allure2/releases
```

## 6. Reports

After each build:

| Artifact | Location |
|---|---|
| JUnit | `reports/pytest-junit.xml` (JUnit plugin) |
| Allure | `reports/allure-results` (Allure plugin) |
| HTML report | `reports/pytest-report.html` (archived artifact) |
| Screenshots | `screenshots/` on failure |
| Email | Allure link + ZIP to `NOTIFY_EMAIL` after every build |

## 7. Local CI dry-run

Simulate Jenkins config generation without committing secrets:

```powershell
$env:MICROSOFT_USERNAME="your.user@credaris.onmicrosoft.com"
$env:MICROSOFT_PASSWORD="..."
$env:SUGAR_USERNAME="..."
$env:SUGAR_PASSWORD="..."
python scripts\ci\generate_config_from_env.py
pytest -m smoke -v
```

## Troubleshooting

| Issue | Fix |
|---|---|
| `Config file not found` | Run `generate_config_from_env.py` or copy `config.example.properties` |
| MFA blocks CI | Use dedicated agent + profile, or MFA-exempt service account |
| Chrome / driver errors | Ensure Chrome is installed; Selenium 4 manages ChromeDriver |
| Allure report empty | Install Allure CLI on agent or use the Jenkins Allure plugin only |
| No email received | Configure SMTP in Jenkins System settings; install Email Extension Plugin |
| Email without ZIP | Install Allure CLI on the agent (`allure generate`) |
| ZPA / privacy error | Agent must run inside corporate network with ZPA connected |
