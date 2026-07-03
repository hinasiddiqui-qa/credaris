"""Browser environment preparation before test execution (not a test case)."""

from __future__ import annotations

from selenium.webdriver.common.by import By

from pages.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class BrowserEnvironmentPage(BasePage):
    """Chrome and sugar-test environment steps for Initial Setup."""

    RESTORE_PAGES_NO_THANKS = (
        By.XPATH,
        "//button[contains(translate(., 'THANKS', 'thanks'), 'no thanks')]",
    )
    RESTORE_PAGES_CLOSE = (
        By.XPATH,
        "//button[@aria-label='Close' or @title='Close' or contains(@class, 'close')]",
    )
    PRIVACY_ADVANCED = (By.ID, "details-button")
    PRIVACY_PROCEED = (By.ID, "proceed-link")
    PRIVACY_PROCEED_TEXT = (
        By.XPATH,
        "//a[contains(., 'Proceed to') and contains(., 'unsafe')]",
    )

    def dismiss_restore_pages_popup(self) -> None:
        logger.info("Initial setup: checking for 'Restore pages?' popup")
        if self.click_if_visible_quick(self.RESTORE_PAGES_NO_THANKS):
            logger.info("Initial setup: dismissed 'Restore pages?' via No Thanks")
            return
        if self.click_if_visible_quick(self.RESTORE_PAGES_CLOSE):
            logger.info("Initial setup: dismissed 'Restore pages?' via Close")
            return
        logger.info("Initial setup: no 'Restore pages?' popup detected")

    def dismiss_chrome_restore_infobar(self) -> None:
        """Dismiss Chrome's native 'Restore pages?' crash recovery infobar if shown."""
        chrome_restore_locators = (
            (
                By.XPATH,
                "//*[contains(normalize-space(.), 'Restore pages')]"
                "/ancestor::*[contains(@class,'infobar') or @role='alert'][1]"
                "//button[@aria-label='Close' or contains(@class,'close')]",
            ),
            (
                By.XPATH,
                "//*[contains(normalize-space(.), 'didn't shut down correctly')]"
                "/ancestor::*[1]//button[@aria-label='Close']",
            ),
            (By.XPATH, "//*[@id='infobar-container']//button"),
        )
        for locator in chrome_restore_locators:
            if self.click_if_visible_quick(locator):
                logger.info("Initial setup: dismissed Chrome 'Restore pages?' infobar")
                return
        logger.debug("Initial setup: no Chrome restore infobar detected")

    def navigate_to_application(self) -> None:
        url = self.config.application_url.rstrip("/") + "/"
        logger.info("Initial setup: navigating to application URL %s", url)
        self.driver.get(url)

    def bypass_privacy_error_if_present(self) -> None:
        page_source = self.driver.page_source
        title = self.driver.title
        privacy_indicators = (
            "Privacy error",
            "Your connection is not private",
            "NET::ERR_CERT",
            "ERR_CERT_AUTHORITY_INVALID",
        )
        is_privacy_page = any(
            indicator in page_source or indicator in title for indicator in privacy_indicators
        )
        if not is_privacy_page:
            logger.info("Initial setup: no privacy error page detected")
            return

        host = self.config.application_host
        logger.info("Initial setup: privacy error detected — clicking Advanced")
        self.click_if_visible_quick(self.PRIVACY_ADVANCED)

        logger.info("Initial setup: proceeding to %s (unsafe)", host)
        for locator in (
            self.PRIVACY_PROCEED,
            (By.PARTIAL_LINK_TEXT, f"Proceed to {host}"),
            self.PRIVACY_PROCEED_TEXT,
        ):
            if self.click_if_visible_quick(locator):
                logger.info("Initial setup: bypassed privacy warning")
                return

        logger.warning("Initial setup: could not locate proceed link on privacy error page")

    def open_sugar_test_and_wait(self, *, context: str = "initial application open") -> None:
        """
        Open sugar-test when needed and wait until elements finish loading.

        Does not navigate to the zpa-ba auth portal. Skips the load wait when still on
        Microsoft SSO — call MicrosoftSSOPage.login first, then invoke this again.
        """
        on_microsoft_sso = "login.microsoftonline.com" in self.driver.current_url
        if on_microsoft_sso:
            logger.info("Initial setup: on Microsoft SSO page — skipping sugar load wait until login completes")
            return

        if self.config.application_host in self.driver.current_url:
            logger.info("Initial setup: staying on sugar-test while the application finishes loading")
        else:
            self.navigate_to_application()

        self.bypass_privacy_error_if_present()
        logger.info("Initial setup: waiting for sugar-test elements to load (%s)", context)
        self.wait_for_page_ready()
        self.wait_for_sugar_app_ready(context=context)

    def wait_for_application_ready(self) -> None:
        logger.info("Initial setup: waiting for application to fully load")
        self.open_sugar_test_and_wait(context="initial application open")

    def run_pre_test_initialization(self) -> None:
        """Legacy helper — prefer SessionOrchestrator for sugar-test-only routing."""
        self.dismiss_restore_pages_popup()
        self.open_sugar_test_and_wait()
