"""Application configuration loader with environment variable overrides."""

from __future__ import annotations

import configparser
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "config.properties"


@dataclass(frozen=True)
class AppConfig:
    auth_base_url: str
    auth_home_path: str
    application_url: str
    application_host: str
    application_login_path: str
    microsoft_login_url: str
    microsoft_username: str
    microsoft_password: str
    sugar_username: str
    sugar_password: str
    browser: str
    headless: bool
    implicit_wait: int
    explicit_wait: int
    quick_poll_timeout: int
    sugar_load_timeout: int
    screenshot_on_failure: bool
    log_level: str
    keep_browser_open: bool
    reuse_session: bool
    chrome_user_data_dir: str
    chrome_profile_directory: str
    mfa_wait_timeout: int

    # Backward-compatible aliases used by older page objects
    @property
    def base_url(self) -> str:
        return self.auth_base_url

    @property
    def home_path(self) -> str:
        return self.auth_home_path

    @property
    def home_url(self) -> str:
        return self.auth_home_url

    @property
    def auth_home_url(self) -> str:
        return f"{self.auth_base_url.rstrip('/')}{self.auth_home_path}"

    @property
    def application_login_url(self) -> str:
        base = self.application_url.rstrip("/")
        path = self.application_login_path.strip()
        if not path:
            return f"{base}/"
        if path.startswith(("http://", "https://")):
            return path
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{base}{path}"

    @property
    def resolved_user_data_dir(self) -> Path:
        raw = self.chrome_user_data_dir.strip()
        if not raw:
            return PROJECT_ROOT / ".chrome-profile" / "credaris-automation"
        path = Path(raw)
        return path if path.is_absolute() else PROJECT_ROOT / path


def _parse_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_config(config_path: Path | None = None) -> AppConfig:
    load_dotenv(PROJECT_ROOT / ".env")

    path = config_path or DEFAULT_CONFIG
    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found: {path}. Create config/config.properties with your settings."
        )

    parser = configparser.ConfigParser()
    raw = path.read_text(encoding="utf-8")
    parser.read_string("[app]\n" + raw)
    section = parser["app"]

    auth_base_url = os.getenv(
        "AUTH_BASE_URL",
        os.getenv("CREDARIS_BASE_URL", section.get("auth.base.url", section.get("base.url", ""))),
    ).strip()
    auth_home_path = os.getenv(
        "AUTH_HOME_PATH",
        os.getenv("CREDARIS_HOME_PATH", section.get("auth.home.path", section.get("home.path", "/#/home"))),
    ).strip()

    application_url = os.getenv(
        "APPLICATION_URL",
        section.get("application.url", "https://sugar-test.intern.credaris.ch"),
    ).strip()
    application_host = os.getenv(
        "APPLICATION_HOST",
        section.get("application.host", urlparse(application_url).netloc),
    ).strip()
    application_login_path = os.getenv(
        "APPLICATION_LOGIN_PATH",
        section.get("application.login.path", "/#/Login"),
    ).strip()
    microsoft_login_url = os.getenv(
        "MICROSOFT_LOGIN_URL",
        section.get("microsoft.login.url", "https://login.microsoftonline.com"),
    ).strip()

    microsoft_username = os.getenv(
        "MICROSOFT_USERNAME",
        os.getenv(
            "CREDARIS_USERNAME",
            section.get("microsoft.username", section.get("credaris.username", "")),
        ),
    ).strip()
    microsoft_password = os.getenv(
        "MICROSOFT_PASSWORD",
        os.getenv(
            "CREDARIS_PASSWORD",
            section.get("microsoft.password", section.get("credaris.password", "")),
        ),
    ).strip()
    sugar_username = os.getenv(
        "SUGAR_USERNAME",
        section.get("sugar.username", section.get("application.username", "")),
    ).strip()
    sugar_password = os.getenv(
        "SUGAR_PASSWORD",
        section.get("sugar.password", section.get("application.password", "")),
    ).strip()

    return AppConfig(
        auth_base_url=auth_base_url,
        auth_home_path=auth_home_path,
        application_url=application_url,
        application_host=application_host,
        application_login_path=application_login_path,
        microsoft_login_url=microsoft_login_url,
        microsoft_username=microsoft_username,
        microsoft_password=microsoft_password,
        sugar_username=sugar_username,
        sugar_password=sugar_password,
        browser=os.getenv("BROWSER", section.get("browser", "chrome")).strip().lower(),
        headless=_parse_bool(os.getenv("HEADLESS", section.get("headless", "false"))),
        implicit_wait=int(os.getenv("IMPLICIT_WAIT", section.get("implicit.wait", "0"))),
        explicit_wait=int(os.getenv("EXPLICIT_WAIT", section.get("explicit.wait", "15"))),
        quick_poll_timeout=int(
            os.getenv("QUICK_POLL_TIMEOUT", section.get("quick.poll.timeout", "2"))
        ),
        sugar_load_timeout=int(
            os.getenv("SUGAR_LOAD_TIMEOUT", section.get("sugar.load.timeout", "60"))
        ),
        screenshot_on_failure=_parse_bool(
            os.getenv("SCREENSHOT_ON_FAILURE", section.get("screenshot.on.failure", "true")),
            True,
        ),
        log_level=os.getenv("LOG_LEVEL", section.get("log.level", "INFO")).strip().upper(),
        keep_browser_open=_parse_bool(
            os.getenv("KEEP_BROWSER_OPEN", section.get("keep.browser.open", "true")),
            True,
        ),
        reuse_session=_parse_bool(
            os.getenv("REUSE_SESSION", section.get("reuse.session", "true")),
            True,
        ),
        chrome_user_data_dir=os.getenv(
            "CHROME_USER_DATA_DIR",
            section.get("chrome.user.data.dir", ".chrome-profile/credaris-automation"),
        ).strip(),
        chrome_profile_directory=os.getenv(
            "CHROME_PROFILE_DIRECTORY",
            section.get("chrome.profile.directory", "Default"),
        ).strip(),
        mfa_wait_timeout=int(os.getenv("MFA_WAIT_TIMEOUT", section.get("mfa.wait.timeout", "600"))),
    )
