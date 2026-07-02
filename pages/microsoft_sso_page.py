"""Microsoft Azure AD / Entra ID SSO login page."""

from __future__ import annotations

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from pages.auth_portal_page import AuthPortalPage
from pages.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class MicrosoftSSOPage(BasePage):
    EMAIL = (By.CSS_SELECTOR, "input[name='loginfmt'], input#i0116")
    PASSWORD = (By.CSS_SELECTOR, "input[name='passwd'], input#i0118")
    SUBMIT = (By.CSS_SELECTOR, "input[type='submit']#idSIButton9")
    PICK_ACCOUNT_HEADER = (By.XPATH, "//*[contains(text(), 'Pick an account')]")
    MFA_TITLE = (
        By.CSS_SELECTOR,
        "#idDiv_SAOTCAS_Title, #idRichContext_DisplaySign, .row.text-title",
    )
    ERROR_MESSAGE = (By.CSS_SELECTOR, "#usernameError, #passwordError, div[role='alert']")

    def is_displayed(self) -> bool:
        return "login.microsoftonline.com" in self.driver.current_url

    def is_pick_an_account_page(self) -> bool:
        if not self.is_displayed():
            return False
        page = self.driver.page_source
        return "Pick an account" in page or self.is_visible_quick(self.PICK_ACCOUNT_HEADER)

    def select_account(self, username: str) -> MicrosoftSSOPage:
        logger.info("Pick an account page detected — selecting user %s", username)
        account_locators = (
            (By.XPATH, f"//div[@role='button' and contains(normalize-space(.), '{username}')]"),
            (By.XPATH, f"//div[contains(@class, 'table-cell') and contains(., '{username}')]"),
            (By.XPATH, f"//*[contains(text(), '{username}')]/ancestor::div[@role='button'][1]"),
            (By.XPATH, f"//small[contains(text(), '{username}')]/ancestor::div[@role='button'][1]"),
        )
        for locator in account_locators:
            if self.click_if_visible_quick(locator):
                logger.info("Selected account tile for %s", username)
                return self

        raise RuntimeError(f"Could not select account '{username}' on Pick an account page")

    def enter_username_and_next(self, username: str) -> MicrosoftSSOPage:
        logger.info("Entering Microsoft SSO username")
        self.type_text(self.EMAIL, username)
        self.click(self.SUBMIT)
        return self

    def enter_password_and_sign_in(self, password: str) -> MicrosoftSSOPage:
        logger.info("Entering password and submitting sign-in")
        self.wait.until_visible(self.PASSWORD)
        self.type_text(self.PASSWORD, password)
        self.click(self.SUBMIT)
        return self

    def is_mfa_prompt_visible(self) -> bool:
        if self.is_pick_an_account_page():
            return False
        try:
            page_source = self.driver.page_source.lower()
            mfa_keywords = (
                "approve sign in request",
                "microsoft authenticator",
                "enter the number",
                "verify your identity",
            )
            return any(keyword in page_source for keyword in mfa_keywords) and self.is_displayed()
        except Exception:
            return False

    def wait_for_mfa_approval(self, timeout: int = 600) -> None:
        logger.info(
            "Waiting up to %s seconds for Microsoft Authenticator approval on your mobile device...",
            timeout,
        )
        print("\n>>> Please approve the sign-in request in Microsoft Authenticator on your phone.\n")

        end_time = time.time() + timeout
        while time.time() < end_time:
            if not self.is_displayed():
                logger.info("Left Microsoft login — authentication appears complete.")
                return

            current_url = self.driver.current_url
            if self.config.auth_base_url.rstrip("/") in current_url:
                logger.info("Redirected back to Credaris auth portal.")
                return
            if self.config.application_host in current_url:
                logger.info("Redirected back to Credaris application.")
                return

            time.sleep(0.5)

        raise TimeoutError(
            f"Timed out after {timeout}s waiting for Authenticator approval. "
            "Please approve the request on your mobile device and retry."
        )

    def handle_stay_signed_in_prompt(self) -> None:
        try:
            if "Stay signed in?" in self.driver.page_source:
                logger.info("Handling 'Stay signed in?' prompt")
                self.click(self.SUBMIT)
        except Exception:
            pass

    def login(self, username: str, password: str, mfa_timeout: int = 600) -> AuthPortalPage:
        if self.is_pick_an_account_page():
            self.select_account(username)
        elif self.is_visible_quick(self.EMAIL):
            self.enter_username_and_next(username)
        elif self.is_visible_quick(self.PASSWORD):
            logger.info("Microsoft SSO: email step skipped, password field already visible")
        else:
            self.wait.until_visible(self.EMAIL)
            self.enter_username_and_next(username)

        self.enter_password_and_sign_in(password)

        if self.is_mfa_prompt_visible() or self.is_displayed():
            self.wait_for_mfa_approval(timeout=mfa_timeout)

        self.handle_stay_signed_in_prompt()

        auth_root = self.config.auth_base_url.rstrip("/")
        app_host = self.config.application_host
        wait = WebDriverWait(self.driver, 60)
        wait.until(
            lambda d: "login.microsoftonline.com" not in d.current_url
            and (auth_root in d.current_url or app_host in d.current_url)
        )
        return AuthPortalPage(self.driver, self.config)
