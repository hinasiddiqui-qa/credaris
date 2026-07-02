"""Sugar CRM application login page (after Microsoft SSO / ZPA)."""

from __future__ import annotations

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from pages.application_page import ApplicationPage
from pages.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class SugarLoginPage(BasePage):
    USERNAME = (
        By.CSS_SELECTOR,
        "form[name='login'] input[name='username'], input[name='username'], input#username, input[name='user_name']",
    )
    PASSWORD = (
        By.CSS_SELECTOR,
        "form[name='login'] input[name='password'], input[name='password'], input#password, input[name='username_password']",
    )
    LOGIN_BUTTON_LOCATORS = (
        (By.CSS_SELECTOR, "a[name='login_button']"),
        (By.CSS_SELECTOR, "form[name='login'] a.btn-primary[name='login_button']"),
        (By.XPATH, "//form[@name='login']//a[@name='login_button']"),
        (By.XPATH, "//a[@name='login_button' and contains(normalize-space(.), 'Log In')]"),
        (By.CSS_SELECTOR, "a.btn.btn-primary[role='button'][name='login_button']"),
        (By.ID, "login_button"),
        (By.CSS_SELECTOR, "button.btn-primary"),
        (
            By.XPATH,
            "//button[contains(translate(normalize-space(.), 'LOG IN', 'log in'), 'log in')]",
        ),
        (By.CSS_SELECTOR, "button[type='submit'], input[type='submit']"),
    )

    def is_displayed(self) -> bool:
        if self.config.application_host not in self.driver.current_url:
            return False
        if "login.microsoftonline.com" in self.driver.current_url:
            return False
        url = self.driver.current_url.lower()
        if "login" in url or "log-in" in url:
            return True
        return self.is_login_form_visible()

    def is_login_form_visible(self) -> bool:
        return self.is_visible(self.USERNAME, timeout=5) and self.is_visible(
            self.PASSWORD, timeout=5
        )

    def is_login_form_visible_quick(self) -> bool:
        return self.is_visible_quick(self.USERNAME) and self.is_visible_quick(self.PASSWORD)

    def _wait_until_logged_in(self) -> None:
        """Minimal wait after Log In — do not wait for Home dashlets to finish loading."""
        deadline = time.time() + self.config.explicit_wait
        while time.time() < deadline:
            if "login.microsoftonline.com" in self.driver.current_url:
                time.sleep(0.05)
                continue
            if self.config.application_host not in self.driver.current_url:
                time.sleep(0.05)
                continue
            if not self.is_login_form_visible_quick():
                document_ready = self.driver.execute_script(
                    "return document.readyState === 'complete'"
                )
                if document_ready:
                    return
            time.sleep(0.05)
        raise TimeoutError("Sugar CRM login did not complete")

    def open_login(self) -> SugarLoginPage:
        self.driver.get(self.config.application_login_url)
        self.wait_for_page_ready()
        return self

    def enter_username(self, username: str) -> None:
        logger.info("Entering Sugar CRM username")
        self.type_text(self.USERNAME, username)

    def enter_password(self, password: str) -> None:
        logger.info("Entering Sugar CRM password")
        self.type_text(self.PASSWORD, password)

    def click_login_button(self) -> None:
        logger.info("Clicking Sugar CRM Log In button")

        for locator in self.LOGIN_BUTTON_LOCATORS:
            if self.click_if_visible_quick(locator):
                logger.info("Clicked Log In button using locator: %s", locator)
                return

        for locator in self.LOGIN_BUTTON_LOCATORS:
            try:
                element = self.wait.until_clickable(locator)
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});",
                    element,
                )
                try:
                    element.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", element)
                logger.info("Clicked Log In button using locator: %s", locator)
                return
            except Exception:
                continue

        logger.warning("Log In button not found — submitting login form via Enter key")
        password_field = self.wait.until_visible(self.PASSWORD)
        password_field.send_keys(Keys.ENTER)

    def login(self, username: str, password: str) -> ApplicationPage:
        logger.info("Logging into Sugar CRM as %s", username)
        if not self.is_login_form_visible_quick() and not self.is_displayed():
            self.open_login()

        self.enter_username(username)
        self.enter_password(password)
        self.click_login_button()
        self._wait_until_logged_in()
        return ApplicationPage(self.driver, self.config)
