"""Choosing Document screen — lead conversion from contact."""

from __future__ import annotations

import time

from selenium.webdriver.common.by import By

from pages.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class ChoosingDocumentPage(BasePage):
    CHOOSING_DOCUMENT_HEADER = (
        By.XPATH,
        "//*[contains(normalize-space(.),'Choosing Document')]",
    )
    MERGE_AND_CREATE_LEAD = (
        By.CSS_SELECTOR,
        "a[name='leadconvert_merge_button']",
    )
    MERGE_AND_CREATE_LEAD_LOCATORS = (
        MERGE_AND_CREATE_LEAD,
        (By.CSS_SELECTOR, "a.btn.btn-primary[name='leadconvert_merge_button']"),
        (By.XPATH, "//a[@name='leadconvert_merge_button']"),
        (By.XPATH, "//a[normalize-space()='Merge and Create Lead']"),
    )
    # First Select2 on Choosing Document — lead Status (not the tag/chip Status field).
    STATUS_DROPDOWN_SCOPE = (
        "(//*[contains(normalize-space(.),'Choosing Document')]"
        "/following::div[contains(@class,'select2-container')][1])"
    )
    STATUS_TRIGGER_LOCATORS = (
        (
            By.XPATH,
            f"{STATUS_DROPDOWN_SCOPE}//a[contains(@class,'select2-choice')]",
        ),
        (
            By.XPATH,
            f"{STATUS_DROPDOWN_SCOPE}//span[contains(@class,'select2-selection')]",
        ),
        (By.XPATH, STATUS_DROPDOWN_SCOPE),
        (
            By.XPATH,
            "(//div[contains(@class,'field') or contains(@class,'record-cell')]"
            "[.//label[contains(normalize-space(.),'Status')]"
            " and .//div[contains(@class,'select2')]]"
            "//a[contains(@class,'select2-choice')])[1]",
        ),
        (
            By.XPATH,
            "(//div[contains(@class,'field') or contains(@class,'record-cell')]"
            "[.//label[contains(normalize-space(.),'Status')]"
            " and .//div[contains(@class,'select2')]]"
            "//span[contains(@class,'select2-selection')])[1]",
        ),
    )
    STATUS_VALUE_LOCATORS = (
        (
            By.XPATH,
            f"{STATUS_DROPDOWN_SCOPE}//span[contains(@class,'select2-chosen')]",
        ),
        (
            By.XPATH,
            f"{STATUS_DROPDOWN_SCOPE}//span[contains(@class,'select2-selection__rendered')]",
        ),
    )

    def wait_until_loaded(self) -> ChoosingDocumentPage:
        logger.info("Waiting for Choosing Document screen to load")
        self.wait_for_sugar_loading_overlay_gone()
        self.wait.until_visible(self.CHOOSING_DOCUMENT_HEADER)
        return self

    def _status_already_selected(self, option_text: str) -> bool:
        for locator in self.STATUS_VALUE_LOCATORS:
            if not self.is_visible_quick(locator):
                continue
            try:
                current = self.driver.find_element(*locator).text.strip()
                if option_text in current:
                    logger.info("Status already set to '%s' — skipping dropdown", current)
                    return True
            except Exception:
                continue
        return False

    def _open_status_dropdown(self) -> None:
        self.wait_for_sugar_loading_overlay_gone()
        for locator in self.STATUS_TRIGGER_LOCATORS:
            if not self.is_visible_quick(locator):
                continue
            try:
                element = self.driver.find_element(*locator)
                self.scroll_to_element(element)
                try:
                    element.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", element)
                return
            except Exception:
                continue
        raise RuntimeError("Could not open Status dropdown on Choosing Document screen")

    def _select_dropdown_option(self, option_text: str) -> None:
        option_locators = (
            (
                By.XPATH,
                f"//div[contains(@class,'select2-drop-active')]"
                f"//li[contains(normalize-space(.), '{option_text}')]",
            ),
            (
                By.XPATH,
                f"//div[contains(@class,'select2-drop')]"
                f"//li[contains(normalize-space(.), '{option_text}')]",
            ),
            (
                By.XPATH,
                f"//li[contains(@class,'select2-result') "
                f"and contains(normalize-space(.), '{option_text}')]",
            ),
            (By.XPATH, f"//option[normalize-space()='{option_text}']"),
        )
        for option in option_locators:
            if self.click_if_visible_quick(option):
                return
            try:
                self.click_with_fallback(option)
                return
            except Exception:
                continue
        raise RuntimeError(f"Could not select Status option '{option_text}'")

    def select_status(self, option_text: str) -> None:
        logger.info("Selecting Status: %s", option_text)
        if self._status_already_selected(option_text):
            return
        self._open_status_dropdown()
        self._select_dropdown_option(option_text)

    def click_merge_and_create_lead(self) -> ChoosingDocumentPage:
        logger.info("Clicking Merge and Create Lead")
        self.wait_for_sugar_loading_overlay_gone()
        for locator in self.MERGE_AND_CREATE_LEAD_LOCATORS:
            if self.click_if_visible_quick(locator):
                self.wait_for_page_ready()
                return self
            try:
                self.click_with_fallback(locator)
                self.wait_for_page_ready()
                return self
            except Exception:
                continue
        raise RuntimeError("Could not find Merge and Create Lead button")

    def wait_for_contact_detail_redirect(
        self, first_name: str, last_name: str
    ) -> ChoosingDocumentPage:
        """Wait until Sugar redirects to the contact detail view after lead creation."""
        logger.info(
            "Waiting for redirect to contact detail view after lead creation: %s %s",
            first_name,
            last_name,
        )
        self.wait_for_page_ready()
        self.wait_for_sugar_loading_overlay_gone()
        deadline = time.time() + self.config.explicit_wait
        header_locators = (
            (
                By.XPATH,
                f"//div[contains(@class,'headerpane')]"
                f"[.//*[contains(normalize-space(.), '{first_name}')] "
                f"and .//*[contains(normalize-space(.), '{last_name}')]]",
            ),
            (
                By.XPATH,
                f"//*[contains(@class,'record-header') or contains(@class,'headerpane')]"
                f"[.//*[contains(normalize-space(.), '{first_name}')] "
                f"and .//*[contains(normalize-space(.), '{last_name}')]]",
            ),
            (
                By.XPATH,
                f"//*[contains(normalize-space(.), '{first_name}') "
                f"and contains(normalize-space(.), '{last_name}')]",
            ),
        )
        while time.time() < deadline:
            route_hash = self.driver.execute_script("return location.hash || ''")
            if route_hash.startswith("#Contacts/"):
                remainder = route_hash[len("#Contacts/") :].strip("/")
                if remainder and "create" not in remainder.lower():
                    if any(
                        self.is_visible(locator, timeout=self.config.quick_poll_timeout)
                        for locator in header_locators
                    ):
                        self.wait_for_sugar_loading_overlay_gone()
                        return self
            time.sleep(0.15)
        raise TimeoutError(
            f"Lead creation did not redirect to contact detail view for {first_name} {last_name}"
        )

    def complete_lead_creation(self, lead: dict) -> ChoosingDocumentPage:
        self.select_status(lead["status"])
        self.click_merge_and_create_lead()
        return self
