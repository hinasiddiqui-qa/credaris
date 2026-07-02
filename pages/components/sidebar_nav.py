"""Sugar CRM left sidebar module navigation."""

from __future__ import annotations

import time

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

from pages.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class SidebarNav(BasePage):
    """
    Credaris Sugar sidebar structure (from live DOM):

    a.sidebar-nav-item-btn[href='#Contacts'][aria-label='Contacts']
      └── span[title='Contacts']
            └── span.sicon.sicon-contact-lg
    """

    CONTACTS_LINK = (
        By.CSS_SELECTOR,
        "a.sidebar-nav-item-btn[href='#Contacts'][aria-label='Contacts']",
    )
    CONTACTS_LINK_LOCATORS = (
        CONTACTS_LINK,
        (By.XPATH, "//a[@href='#Contacts' and @aria-label='Contacts']"),
        (
            By.XPATH,
            "//a[@href='#Contacts']//span[@title='Contacts']/ancestor::a[1]",
        ),
        (
            By.XPATH,
            "//span[contains(@class,'sicon-contact-lg')]/ancestor::a[@href='#Contacts'][1]",
        ),
        (By.CSS_SELECTOR, "a[href='#Contacts']"),
    )

    def is_contacts_link_present(self) -> bool:
        count = self.driver.execute_script(
            """
            return document.querySelectorAll(
              "a.sidebar-nav-item-btn[href='#Contacts'], a[href='#Contacts']"
            ).length;
            """
        )
        return bool(count)

    def wait_until_contacts_link_present(self) -> None:
        """Wait for Sugar SPA to render the Contacts sidebar anchor."""
        self.wait_for_sugar_loading_overlay_gone()
        self.wait_for_page_ready()
        deadline = time.time() + self.config.explicit_wait

        while time.time() < deadline:
            if self.is_contacts_link_present():
                logger.info("Contacts sidebar link rendered")
                return
            time.sleep(0.3)

        raise TimeoutError(
            "Contacts sidebar link was not rendered. "
            "Confirm Sugar CRM login completed and dashboard is visible."
        )

    def _find_contacts_element(self):
        for locator in self.CONTACTS_LINK_LOCATORS:
            try:
                return self.wait.until_present(locator)
            except Exception:
                continue
        raise RuntimeError("Could not locate Contacts sidebar link in DOM")

    def _wait_for_contacts_route(self) -> None:
        deadline = time.time() + self.config.explicit_wait
        while time.time() < deadline:
            current_hash = self.driver.execute_script("return location.hash || ''")
            current_url = self.driver.current_url
            if "#Contacts" in current_url or current_hash.startswith("#Contacts"):
                logger.info("Contacts route active: hash=%s", current_hash)
                self.wait_for_page_ready()
                return
            time.sleep(0.3)

        logger.warning("Hash route not detected after click — navigating to #Contacts directly")
        self.driver.execute_script("window.location.hash = '#Contacts';")
        self.wait_for_page_ready()

    def open_contacts(self) -> None:
        """Click the Contacts icon in the left sidebar."""
        logger.info("Opening Contacts module from sidebar")
        self.wait_until_contacts_link_present()

        element = self._find_contacts_element()
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
            element,
        )

        try:
            ActionChains(self.driver).move_to_element(element).pause(0.2).click(element).perform()
            logger.info("Clicked Contacts sidebar link via ActionChains")
        except Exception as exc:
            logger.debug("ActionChains click failed (%s) — using JavaScript click", exc)
            self.driver.execute_script("arguments[0].click();", element)
            logger.info("Clicked Contacts sidebar link via JavaScript")

        self._wait_for_contacts_route()

    def wait_until_sidebar_loaded(self) -> None:
        """Backward-compatible alias."""
        self.wait_until_contacts_link_present()
