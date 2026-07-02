"""Credaris ZPA auth portal home page (zpa-ba)."""

from __future__ import annotations

from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class AuthPortalPage(BasePage):
    APP_SHELL = (By.CSS_SELECTOR, "app-root, body")
    HOME_ROUTE_MARKER = (By.CSS_SELECTOR, "[routerlink*='home'], .home, #home, main")
    PAGE_TITLE = (By.CSS_SELECTOR, "h1, .page-title, .navbar-brand, .app-title")

    def open(self) -> AuthPortalPage:
        self.driver.get(self.config.auth_home_url)
        self.wait_for_page_ready()
        self.wait.until_present(self.APP_SHELL)
        return self

    def is_sso_login_redirect(self) -> bool:
        return "login.microsoftonline.com" in self.driver.current_url

    def is_on_authenticated_home_url(self) -> bool:
        url = self.driver.current_url
        return (
            self.config.auth_base_url.rstrip("/") in url
            and "/home" in url
            and not self.is_sso_login_redirect()
        )

    def is_authenticated(self) -> bool:
        if self.is_on_authenticated_home_url():
            return True
        self.open()
        return self.is_on_authenticated_home_url() and not self.is_sso_login_redirect()

    def get_current_url(self) -> str:
        return self.driver.current_url

    def get_title(self) -> str:
        return self.driver.title
