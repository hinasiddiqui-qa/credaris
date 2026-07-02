# Credaris Selenium Automation Framework

Python + Selenium + pytest framework for Credaris Sugar CRM UI automation using the Page Object Model (POM).

## Target application

- **ZPA entry:** `https://zpa-ba.credaris.ch`
- **Sugar CRM:** `https://sugar-test.intern.credaris.ch`

## Quick start (local)

```powershell
cd credaris-selenium-automation
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy config\config.example.properties config\config.properties
```

Edit `config/config.properties` with your Microsoft SSO and Sugar credentials, then:

```powershell
pytest -m smoke -v
```

Reports:

| Report | Path |
|---|---|
| pytest HTML | `reports/pytest-report.html` |
| JUnit XML | `reports/pytest-junit.xml` |
| Allure | `reports/allure-results` |

Open Allure locally:

```powershell
allure.cmd serve reports/allure-results
```

## Project structure

| Folder | Purpose |
|---|---|
| `config/` | URLs, browser settings, timeouts (`config.example.properties` template) |
| `core/` | Driver factory, config loader, base test |
| `pages/` | Page Object Model classes |
| `login/`, `setup/` | Session prerequisites (SSO + Sugar login) |
| `tests/` | Feature tests (`contacts`, `leads`) |
| `test_data/` | JSON test input |
| `scripts/` | Bootstrap session, Allure helpers, CI scripts |
| `docs/` | Setup and Jenkins documentation |

Generated output (`reports/`, `logs/`, `screenshots/`, `.chrome-profile/`, `sessions/`) is gitignored.

## Tests

| Module | File | What it verifies |
|---|---|---|
| Contacts | `tests/contacts/test_contacts_create.py` | Suite contact detail view opens |
| Leads | `tests/leads/test_lead_create.py` | Create lead from contact → open lead detail |

Prerequisites run once per session via `tests/conftest.py`:

1. Initial setup (ZPA / Microsoft SSO)
2. Sugar CRM login
3. Shared suite contact creation

## Git

The repo is ready for version control. Secrets stay local:

```powershell
git status
git add .
git commit -m "Initial commit: Credaris Selenium automation framework"
git branch -M main
git remote add origin https://github.com/hinasiddiqui-qa/credaris.git
git push -u origin main
```

**Never commit:** `config/config.properties`, `.env`, `.chrome-profile/`, `sessions/`

Use `config/config.example.properties` as the template for new clones.

## Jenkins CI/CD

A declarative `Jenkinsfile` is included. Full setup steps:

**[docs/JENKINS.md](docs/JENKINS.md)**

Summary:

1. Push repo to Git (GitHub, GitLab, Azure DevOps, etc.)
2. Create Jenkins **Secret text** credentials (`credaris-microsoft-username`, etc.)
3. Create a **Pipeline** job from SCM pointing at `Jenkinsfile`
4. Use a labeled agent (`selenium`) with Chrome, Python, and ZPA/network access

CI generates `config/config.properties` from Jenkins credentials via `scripts/ci/generate_config_from_env.py`.

After each build, Jenkins emails **hina.siddiqui@rolustech.com** with the Allure report link and ZIP attachment. See [docs/JENKINS.md](docs/JENKINS.md) for SMTP setup.

## Configuration

Local settings live in `config/config.properties`. Environment variables override any property (used by Jenkins).

| Variable | Description |
|---|---|
| `MICROSOFT_USERNAME` / `MICROSOFT_PASSWORD` | Microsoft SSO |
| `SUGAR_USERNAME` / `SUGAR_PASSWORD` | Sugar CRM login |
| `HEADLESS` | Run Chrome headless (`true` in CI) |
| `REUSE_SESSION` | Reuse Chrome profile to skip MFA |
| `KEEP_BROWSER_OPEN` | Leave browser open after run |

See `config/config.example.properties` for all options.

## Session reuse (local development)

Microsoft MFA should not run before every test locally. Bootstrap once:

```powershell
python scripts\bootstrap_session.py
```

Then run tests with `reuse.session=true` in config. See `docs/INITIAL_SETUP.md` for prerequisite details.

## Important notes

- Run **one pytest process per Chrome profile** — Chrome locks the user-data directory
- Do **not commit** auth tokens or credentials
- CI agents need ZPA access or an MFA-exempt service account for unattended runs
