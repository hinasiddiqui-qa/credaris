"""
Session orchestrator — Initial Setup via sugar-test only.

Opens https://sugar-test.intern.credaris.ch/, waits for the app to finish loading,
and completes Microsoft SSO only when sugar-test redirects there. The zpa-ba auth
portal is never used during pytest prerequisites.
"""

from __future__ import annotations

import os

from selenium.webdriver.remote.webdriver import WebDriver

from core.config_loader import AppConfig
from pages.application_page import ApplicationPage
from pages.browser_environment_page import BrowserEnvironmentPage
from pages.microsoft_sso_page import MicrosoftSSOPage
from utils.logger import get_logger
from utils.session_storage import SessionStorage

logger = get_logger(__name__)


def _skip_session_restore() -> bool:
    return os.getenv("SKIP_SESSION_RESTORE", "").strip().lower() in {"1", "true", "yes", "on"}


class SessionOrchestrator:
    _initialized = False

    def __init__(self, driver: WebDriver, config: AppConfig, mfa_timeout: int | None = None):
        self.driver = driver
        self.config = config
        self.mfa_timeout = mfa_timeout or int(os.getenv("MFA_WAIT_TIMEOUT", "600"))
        self.storage = SessionStorage(config)
        self.browser_env = BrowserEnvironmentPage(driver, config)
        self.application = ApplicationPage(driver, config)

    def run(self, user: dict | None = None) -> ApplicationPage:
        if (
            SessionOrchestrator._initialized
            and self.application.is_loaded()
            and not self.application.requires_microsoft_login()
        ):
            logger.info("Initial setup already completed this session — skipping duplicate run")
            return self.application

        microsoft_user = self._microsoft_credentials(user)

        logger.info("=== Initial Setup: open sugar-test and wait for application to load ===")
        self.browser_env.dismiss_restore_pages_popup()

        if self.config.reuse_session and self.storage.has_saved_session() and not _skip_session_restore():
            logger.info("Restoring saved session artifacts")
            self.storage.restore_session(self.driver)
        elif _skip_session_restore():
            logger.info("Skipping saved session restore — expecting fresh Microsoft SSO")

        self._open_sugar_test_and_authenticate(microsoft_user)
        SessionOrchestrator._initialized = True
        return self.application

    def _microsoft_credentials(self, user: dict | None) -> dict:
        if user and user.get("username") and user.get("password"):
            return {"username": user["username"], "password": user["password"]}
        return {
            "username": self.config.microsoft_username,
            "password": self.config.microsoft_password,
        }

    def _is_on_sugar_test(self) -> bool:
        return self.config.application_host in self.driver.current_url

    def _open_sugar_test_and_authenticate(self, user: dict) -> None:
        """Open sugar-test, complete Microsoft SSO when redirected, then wait for load."""
        logger.info(
            "Opening sugar-test at %s (zpa-ba auth portal will not be used)",
            self.config.application_url,
        )
        self.browser_env.navigate_to_application()
        self.browser_env.bypass_privacy_error_if_present()

        if self.application.requires_microsoft_login():
            if self.config.skip_microsoft_login:
                raise RuntimeError(
                    "Saved session expired and Microsoft SSO is disabled for test runs "
                    "(skip.microsoft.login=true). Run scripts/bootstrap_session.py once to refresh the session."
                )

            if not user.get("username") or not user.get("password"):
                raise RuntimeError(
                    "sugar-test requires Microsoft SSO and credentials are missing. "
                    "Set microsoft.username and microsoft.password in config/config.properties"
                )

            logger.info(
                "Microsoft SSO required — enter credentials and approve Authenticator when prompted"
            )
            print("\n>>> Microsoft sign-in: approve Authenticator on your phone when prompted.\n")
            MicrosoftSSOPage(self.driver, self.config).login(
                user["username"],
                user["password"],
                mfa_timeout=self.mfa_timeout,
            )

        self.browser_env.open_sugar_test_and_wait(context="after authentication")

        if self.application.requires_microsoft_login():
            raise RuntimeError(
                "Initial setup failed: Microsoft SSO did not complete. "
                f"Current URL: {self.driver.current_url}"
            )

        if self.config.application_host not in self.driver.current_url:
            raise RuntimeError(
                "Initial setup failed: browser is not on sugar-test after authentication. "
                f"Current URL: {self.driver.current_url}"
            )

        if self.config.reuse_session:
            self.storage.save_session(self.driver)

        logger.info("Initial setup complete — sugar-test is ready; test execution can proceed")

    @classmethod
    def reset(cls) -> None:
        """Reset session guard — for isolated tests only."""
        cls._initialized = False
