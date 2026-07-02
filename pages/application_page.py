"""Sugar CRM / Credaris test application page (sugar-test environment)."""

from __future__ import annotations

from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class ApplicationPage(BasePage):
    APP_SHELL = (By.CSS_SELECTOR, "app-root, body, #content, .main")

    @property
    def application_url(self) -> str:
        return self.config.application_url.rstrip("/") + "/"

    def open(self) -> ApplicationPage:
        self.driver.get(self.application_url)
        self.wait_for_page_ready()
        return self

    def is_loaded(self) -> bool:
        try:
            self.wait.until_document_ready()
            self.wait.until_present(self.APP_SHELL)
            return self.config.application_host in self.driver.current_url
        except Exception:
            return False

    def requires_microsoft_login(self) -> bool:
        return "login.microsoftonline.com" in self.driver.current_url

    def requires_sugar_login(self) -> bool:
        from pages.sugar_login_page import SugarLoginPage

        return SugarLoginPage(self.driver, self.config).is_displayed()

    def requires_login(self) -> bool:
        return self.requires_microsoft_login() or self.requires_sugar_login()

    def is_accessible(self) -> bool:
        """Sugar CRM loaded after ZPA/SSO — Sugar app login may still be required."""
        return self.is_loaded() and not self.requires_microsoft_login()

    def is_ready(self) -> bool:
        return self.is_accessible() and not self.requires_sugar_login()

    def is_session_active_quick(self) -> bool:
        """Fast post-login check without waiting for Home dashlets."""
        if self.requires_microsoft_login():
            return False
        from pages.sugar_login_page import SugarLoginPage

        return not SugarLoginPage(self.driver, self.config).is_login_form_visible_quick()

    def get_title(self) -> str:
        return self.driver.title
