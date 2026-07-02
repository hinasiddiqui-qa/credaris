# Jenkins CI/CD setup

This project includes a declarative `Jenkinsfile` that runs the smoke suite, publishes JUnit + Allure reports, and archives screenshots/logs.

## Prerequisites on the Jenkins agent

| Requirement | Notes |
|---|---|
| Python 3.10+ | Available as `python` on PATH |
| Google Chrome | Required for Selenium |
| Network access | Agent must reach ZPA + `sugar-test.intern.credaris.ch` |
| Allure Jenkins plugin | Optional but recommended for HTML reports |

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
git remote add origin https://github.com/YOUR_ORG/credaris-selenium-automation.git
# git remote add origin https://dev.azure.com/YOUR_ORG/YOUR_PROJECT/_git/credaris-selenium-automation
# git remote add origin https://gitlab.com/YOUR_ORG/credaris-selenium-automation.git

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
   - Repository URL: your remote URL
   - Credentials: Jenkins credential with read access to the repo
   - Branch: `main`
   - Script Path: `Jenkinsfile`
4. Save and **Build Now**

### Job parameters

| Parameter | Default | Purpose |
|---|---|---|
| `AGENT_LABEL` | `selenium` | Label of agents with Chrome + ZPA access |
| `TEST_MARKER` | `smoke` | Pytest marker (`smoke`, `regression`, `contacts`, `leads`) |

## 4. Label your Jenkins agent

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

## 5. Reports

After each build:

| Artifact | Location |
|---|---|
| JUnit | `reports/pytest-junit.xml` (JUnit plugin) |
| Allure | `reports/allure-results` (Allure plugin) |
| HTML report | `reports/pytest-report.html` (archived artifact) |
| Screenshots | `screenshots/` on failure |

## 6. Local CI dry-run

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
| ZPA / privacy error | Agent must run inside corporate network with ZPA connected |
