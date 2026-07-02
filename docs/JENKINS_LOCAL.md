# Local Jenkins setup (http://localhost:10000)

Your Jenkins instance is already configured for email. The Credaris pipeline uses that **global SMTP** — no duplicate SMTP setup in the repo.

## Your Jenkins email settings (already configured)

Read from `C:\ProgramData\Jenkins\.jenkins\` on your machine:

| Setting | Value |
|---|---|
| Jenkins URL | `http://localhost:10000/` |
| System admin email | `hina.siddiqui@rolustech.com` |
| SMTP server | `smtp.gmail.com` |
| SMTP port | `587` |
| TLS | Enabled |
| SSL | Disabled |
| Default email suffix | `@rolustech.com` |
| SMTP credential ID | `smtp-rolustech-hina` |
| Default recipient (Email Extension) | `hina.siddiqui@rolustech.com` |

The Credaris `Jenkinsfile` calls `emailext(...)`, which sends mail through these global settings (same as your Dakota Extension job).

## Credaris pipeline job

| Setting | Value |
|---|---|
| Job name | `credaris-selenium-automation` |
| Git repo | `https://github.com/hinasiddiqui-qa/credaris.git` |
| Git credential | `github-hinasiddiqui-qa` |
| Branch | `main` |
| Script Path | `Jenkinsfile` |
| Agent label (default) | `windows-dakota-perf` |
| Notify email | `hina.siddiqui@rolustech.com` |

### Create / update the job

**Option A — Reload from disk** (after files are copied):

1. Ensure folder exists: `C:\ProgramData\Jenkins\.jenkins\jobs\credaris-selenium-automation\`
2. Copy `scripts\jenkins\credaris-pipeline-job.xml` → `config.xml` in that folder
3. **Manage Jenkins → Reload Configuration from Disk**

**Option B — UI**

1. **New Item** → `credaris-selenium-automation` → **Pipeline**
2. Pipeline from SCM → Git → URL above → branch `*/main` → `Jenkinsfile`
3. Add Git credential `github-hinasiddiqui-qa` if repo is private

**Option C — Script**

```powershell
$env:JENKINS_URL   = "http://localhost:10000"
$env:JENKINS_USER  = "your-jenkins-user"
$env:JENKINS_TOKEN = "your-api-token"
.\scripts\jenkins\setup_pipeline.ps1
```

## Required Jenkins credentials (test login — add if missing)

| Credential ID | Type | Purpose |
|---|---|---|
| `credaris-microsoft-username` | Secret text | Microsoft SSO username |
| `credaris-microsoft-password` | Secret text | Microsoft SSO password |
| `credaris-sugar-username` | Secret text | Sugar CRM username |
| `credaris-sugar-password` | Secret text | Sugar CRM password |
| `github-hinasiddiqui-qa` | Username/password | Clone private GitHub repo |
| `smtp-rolustech-hina` | Already exists | Global SMTP (do not duplicate) |

## What each build email contains

Sent to **hina.siddiqui@rolustech.com** after **every** build:

- Build status (SUCCESS / FAILURE) with pass/fail/total counts
- **Open Allure Report** button → `http://localhost:10000/job/credaris-selenium-automation/<build>/allure/`
- `allure-report.zip` attachment when Allure CLI is on the agent
- Same HTML style as your Dakota Extension pipeline

## Agent requirements

Default agent: **`windows-dakota-perf`** (same node as Dakota Extension).

Install on that agent:

- Python 3.10+
- Google Chrome
- ZPA / network access to `sugar-test.intern.credaris.ch`
- Optional: Allure CLI (`scoop install allure`) for ZIP attachment

## Troubleshooting

| Issue | Fix |
|---|---|
| Email not sent | Verify **Manage Jenkins → System → Extended E-mail Notification** still shows `smtp.gmail.com:587` and credential `smtp-rolustech-hina` |
| Git clone fails | Add or fix `github-hinasiddiqui-qa` credential |
| Tests fail on login | Add the four `credaris-*` credentials in Jenkins |
| Job not visible | Reload configuration from disk or restart Jenkins |
