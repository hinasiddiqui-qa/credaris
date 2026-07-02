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

The job files can be installed to `C:\ProgramData\Jenkins\.jenkins\jobs\credaris-selenium-automation\`.

**Fastest — reload from disk** (you are already logged into Jenkins):

1. Open **http://localhost:10000/script**
2. Paste and **Run**:

```groovy
jenkins.model.Jenkins.getInstance().doReload()
```

3. Refresh the dashboard — **`credaris-selenium-automation`** should appear.

Or: **Manage Jenkins (gear) → Reload Configuration from Disk**

Or run from the project folder:

```powershell
.\scripts\jenkins\install_local_job.ps1
```

Then run the Script Console command above.

### Create manually in UI (if reload does not show the job)

1. **New Item** → name: **`credaris-selenium-automation`** → **Pipeline** → OK
2. **Pipeline** section:
   - Definition: **Pipeline script from SCM**
   - SCM: **Git**
   - Repository URL: `https://github.com/hinasiddiqui-qa/credaris.git`
   - Credentials: `github-hinasiddiqui-qa`
   - Branch: `*/main`
   - Script Path: `Jenkinsfile`
3. Save → **Build Now**

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
