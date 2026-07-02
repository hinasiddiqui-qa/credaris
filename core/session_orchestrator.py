"""
Session orchestrator — Initial Check with Scenario 1 / Scenario 2 routing.

Each URL and login step runs at most once per pytest session.
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
from workflows.auth_workflow import AuthWorkflow

logger = get_logger(__name__)


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

        logger.info("=== Initial Check: verifying authenticated session ===")
        self.browser_env.dismiss_restore_pages_popup()

        if self._try_scenario_2(microsoft_user):
            SessionOrchestrator._initialized = True
            return self.application

        logger.info("Initial Check result: no valid session → Scenario 1")
        if not microsoft_user["username"] or not microsoft_user["password"]:
            raise RuntimeError(
                "No valid session and Microsoft credentials are missing. "
                "Set microsoft.username and microsoft.password in config/config.properties"
            )

        app = self._scenario_1(microsoft_user)
        SessionOrchestrator._initialized = True
        return app

    def _microsoft_credentials(self, user: dict | None) -> dict:
        if user and user.get("username") and user.get("password"):
            return {"username": user["username"], "password": user["password"]}
        return {
            "username": self.config.microsoft_username,
            "password": self.config.microsoft_password,
        }

    def _open_application_once(self) -> None:
        """Navigate to sugar-test and handle privacy warning — single entry point."""
        self.browser_env.navigate_to_application()
        self.browser_env.bypass_privacy_error_if_present()
        self.browser_env.wait_for_application_ready()

    def _complete_microsoft_login_if_needed(self, user: dict) -> bool:
        """Complete Microsoft SSO when sugar-test redirects to Entra ID."""
        if not self.application.requires_microsoft_login():
            return True

        logger.info("sugar-test requires Microsoft SSO — completing application login")
        MicrosoftSSOPage(self.driver, self.config).login(
            user["username"],
            user["password"],
            mfa_timeout=self.mfa_timeout,
        )
        self.browser_env.wait_for_application_ready()
        return not self.application.requires_microsoft_login()

    def _application_accessible(self) -> bool:
        return self.application.is_accessible()

    def _try_scenario_2(self, user: dict | None) -> bool:
        """Scenario 2: restore session, open sugar-test directly."""
        if not self.config.reuse_session:
            logger.info("Scenario 2 skipped: reuse.session is disabled")
            return False

        if not self.storage.has_saved_session():
            logger.info("Scenario 2 skipped: no saved Chrome profile or cookie file")
            return False

        logger.info("Initial Check: restoring saved session artifacts")
        self.storage.restore_session(self.driver)

        logger.info("Scenario 2: opening sugar-test directly (skipping zpa-ba)")
        self._open_application_once()

        if self.application.is_ready():
            if self.config.reuse_session:
                self.storage.save_session(self.driver)
            logger.info("Scenario 2 complete: sugar-test ready using restored session")
            return True

        if user and self._complete_microsoft_login_if_needed(user) and self._application_accessible():
            logger.info(
                "Scenario 2 complete: sugar-test reachable — Sugar CRM login handled by tests"
            )
            return True

        if self.application.requires_microsoft_login():
            logger.info("Initial Check: Microsoft session expired — falling back to Scenario 1")

        return False

    def _scenario_1(self, user: dict) -> ApplicationPage:
        """Scenario 1: zpa-ba login once, open sugar-test once, then persist session."""
        logger.info("=== Scenario 1: authenticate via zpa-ba, then open sugar-test ===")
        AuthWorkflow(self.driver, self.config, mfa_timeout=self.mfa_timeout).login_at_auth_portal(user)

        logger.info("Scenario 1: opening sugar-test after authentication")
        self._open_application_once()

        if not self._complete_microsoft_login_if_needed(user):
            raise RuntimeError(
                "Scenario 1 failed: Microsoft authentication did not complete for sugar-test"
            )

        if not self._application_accessible():
            raise RuntimeError(
                "Scenario 1 failed: sugar-test application did not load after authentication"
            )

        logger.info("Scenario 1 complete: sugar-test reachable — Sugar CRM login handled by tests")
        return self.application

    @classmethod
    def reset(cls) -> None:
        """Reset session guard — for isolated tests only."""
        cls._initialized = False
