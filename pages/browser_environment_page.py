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

    def wait_for_application_ready(self) -> None:
        logger.info("Initial setup: waiting for application to fully load")
        self.wait.until_document_ready()

    def run_pre_test_initialization(self) -> None:
        """Legacy helper — prefer SessionOrchestrator for full Scenario routing."""
        self.dismiss_restore_pages_popup()
        self.navigate_to_application()
        self.bypass_privacy_error_if_present()
        self.wait_for_application_ready()
