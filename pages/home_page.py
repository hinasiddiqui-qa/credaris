"""Credaris ZPA home page."""

from __future__ import annotations

from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class HomePage(BasePage):
    APP_SHELL = (By.CSS_SELECTOR, "app-root, body")
    HOME_ROUTE_MARKER = (By.CSS_SELECTOR, "[routerlink*='home'], .home, #home, main")
    PAGE_TITLE = (By.CSS_SELECTOR, "h1, .page-title, .navbar-brand, .app-title")

    def open(self) -> HomePage:
        super().open(self.config.home_path)
        self.wait_until_loaded()
        return self

    def wait_until_loaded(self) -> HomePage:
        self.wait_for_page_ready()
        self.wait.until_present(self.APP_SHELL)
        current_url = self.driver.current_url
        if "/home" not in current_url and "login.microsoftonline.com" not in current_url:
            self.wait_for_url_contains("/home")
        return self

    def is_loaded(self) -> bool:
        try:
            self.wait_until_loaded()
            return True
        except Exception:
            return False

    def is_sso_login_redirect(self) -> bool:
        return "login.microsoftonline.com" in self.driver.current_url

    def is_on_authenticated_home_url(self) -> bool:
        url = self.driver.current_url
        return (
            self.config.base_url.rstrip("/") in url
            and "/home" in url
            and not self.is_sso_login_redirect()
        )

    def is_authenticated_home(self) -> bool:
        if not self.is_on_authenticated_home_url():
            return False
        try:
            self.wait.until_document_ready()
            return True
        except Exception:
            return False

    def is_dashboard_visible(self) -> bool:
        if self.is_sso_login_redirect():
            return False
        return self.is_authenticated_home() and (
            self.is_visible_quick(self.HOME_ROUTE_MARKER)
            or self.is_visible_quick(self.PAGE_TITLE)
        )

    def get_current_url(self) -> str:
        return self.driver.current_url

    def get_title(self) -> str:
        return self.driver.title
