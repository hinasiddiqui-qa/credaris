"""Credaris ZPA login page."""

from __future__ import annotations

from selenium.webdriver.common.by import By

from pages.auth_portal_page import AuthPortalPage
from pages.base_page import BasePage


class LoginPage(BasePage):
    USERNAME = (By.ID, "username")
    PASSWORD = (By.ID, "password")
    SUBMIT = (By.ID, "login_button")
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".alert-danger, .error-message, [role='alert']")

    def open(self) -> LoginPage:
        super().open("/")
        self.wait_for_page_ready()
        return self

    def login(self, username: str, password: str) -> AuthPortalPage:
        self.type_text(self.USERNAME, username)
        self.type_text(self.PASSWORD, password)
        self.click(self.SUBMIT)
        return AuthPortalPage(self.driver, self.config)

    def is_error_displayed(self) -> bool:
        return self.is_visible(self.ERROR_MESSAGE)

    def get_error_message(self) -> str:
        if self.is_error_displayed():
            return self.get_text(self.ERROR_MESSAGE)
        return ""
