"""Contact detail view actions — lead creation entry point."""

from __future__ import annotations

import time

from selenium.webdriver.common.by import By

from pages.base_page import BasePage
from pages.choosing_document_page import ChoosingDocumentPage
from utils.data_loader import load_json
from utils.logger import get_logger

logger = get_logger(__name__)


class ContactDetailPage(BasePage):
    ACTIONS_BUTTON = (
        By.CSS_SELECTOR,
        "[title='Actions']",
    )
    ACTIONS_BUTTON_LOCATORS = (
        ACTIONS_BUTTON,
        (By.CSS_SELECTOR, "a.btn.dropdown-toggle[title='Actions']"),
        (By.CSS_SELECTOR, "button[title='Actions']"),
        (
            By.XPATH,
            "//*[(@title='Actions' or normalize-space()='Actions') "
            "and (self::a or self::button or @role='button')]",
        ),
    )
    CREATE_LEAD_LOCATORS = (
        (By.CSS_SELECTOR, "a.rowaction[name='create_lead']"),
        (By.CSS_SELECTOR, "a[name='create_lead'][track='click:create_lead']"),
        (By.CSS_SELECTOR, "a[name='create_lead']"),
        (By.XPATH, "//a[@name='create_lead']"),
        (
            By.XPATH,
            "//li[contains(@class,'dropdown') and contains(@class,'open')]"
            "//a[@name='create_lead']",
        ),
        (
            By.XPATH,
            "//*[contains(@class,'dropdown-menu') and contains(@class,'open')]"
            "//a[@name='create_lead']",
        ),
        (By.XPATH, "//a[normalize-space()='Create Lead']"),
    )

    def click_actions(self) -> ContactDetailPage:
        logger.info("Clicking Actions button on contact detail view")
        self.wait_for_sugar_loading_overlay_gone()
        for locator in self.ACTIONS_BUTTON_LOCATORS:
            try:
                element = self.wait.until_clickable(locator)
                self.scroll_to_element(element)
                try:
                    element.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", element)
                self._wait_for_create_lead_visible()
                return self
            except Exception:
                continue
        raise RuntimeError("Could not find Actions button on contact detail view")

    def _wait_for_create_lead_visible(self) -> None:
        deadline = time.time() + self.config.explicit_wait
        while time.time() < deadline:
            self.wait_for_sugar_loading_overlay_gone()
            for locator in self.CREATE_LEAD_LOCATORS:
                if self.is_visible_quick(locator):
                    return
            time.sleep(0.05)
        raise RuntimeError("Create Lead option did not appear after opening Actions")

    def click_create_lead(self) -> ContactDetailPage:
        logger.info("Clicking Create Lead from Actions menu")
        self.wait_for_sugar_loading_overlay_gone()
        for locator in self.CREATE_LEAD_LOCATORS:
            if not self.is_visible_quick(locator):
                continue
            element = self.driver.find_element(*locator)
            self.scroll_to_element(element)
            self.driver.execute_script("arguments[0].click();", element)
            logger.info("Clicked Create Lead using locator: %s", locator)
            return self
        raise RuntimeError("Could not click Create Lead option in Actions menu")

    def open_create_lead_from_actions(self) -> ChoosingDocumentPage:
        self.click_actions()
        self.click_create_lead()
        choosing_document = ChoosingDocumentPage(self.driver, self.config)
        choosing_document.wait_until_loaded()
        return choosing_document

    def create_lead_from_contact(self, lead: dict | None = None) -> ChoosingDocumentPage:
        """
        From contact detail: Actions → Create Lead → complete Choosing Document screen.
        Lead data defaults to test_data/leads.json.
        """
        lead_data = lead or load_json("leads.json")[0]
        choosing_document = self.open_create_lead_from_actions()
        choosing_document.complete_lead_creation(lead_data)
        return choosing_document
