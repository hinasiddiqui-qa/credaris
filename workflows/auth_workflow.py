"""Authentication workflows."""

from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver

from core.config_loader import AppConfig, load_config
from pages.auth_portal_page import AuthPortalPage
from pages.login_page import LoginPage
from pages.microsoft_sso_page import MicrosoftSSOPage
from utils.logger import get_logger

logger = get_logger(__name__)


class AuthWorkflow:
    def __init__(self, driver: WebDriver, config: AppConfig | None = None, mfa_timeout: int = 600):
        self.driver = driver
        self.config = config or load_config()
        self.mfa_timeout = mfa_timeout

    def login_at_auth_portal(self, user: dict) -> AuthPortalPage:
        """Scenario 1: open zpa-ba auth portal and complete Microsoft SSO if needed."""
        portal = AuthPortalPage(self.driver, self.config)
        portal.open()

        if portal.is_on_authenticated_home_url():
            logger.info("Auth portal already authenticated — skipping Microsoft login")
            return portal

        if portal.is_sso_login_redirect() or MicrosoftSSOPage(self.driver, self.config).is_displayed():
            return MicrosoftSSOPage(self.driver, self.config).login(
                user["username"],
                user["password"],
                mfa_timeout=self.mfa_timeout,
            )

        LoginPage(self.driver, self.config).login(user["username"], user["password"])
        return portal

    def login(self, user: dict) -> AuthPortalPage:
        return self.login_at_auth_portal(user)

    def login_expect_failure(self, user: dict) -> LoginPage:
        logger.info("Attempting invalid login for %s", user["username"])
        AuthPortalPage(self.driver, self.config).open()
        login_page = LoginPage(self.driver, self.config)
        login_page.type_text(LoginPage.USERNAME, user["username"])
        login_page.type_text(LoginPage.PASSWORD, user["password"])
        login_page.click(LoginPage.SUBMIT)
        return login_page
