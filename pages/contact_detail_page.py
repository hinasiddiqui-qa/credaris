"""Contact detail view actions — lead creation entry point."""

from __future__ import annotations

import re
import time

from selenium.webdriver.common.by import By

from pages.base_page import BasePage
from pages.choosing_document_page import ChoosingDocumentPage
from utils.data_loader import load_json
from utils.logger import get_logger

logger = get_logger(__name__)


class ContactDetailPage(BasePage):
    DETAIL_HEADER = (By.CSS_SELECTOR, "div.headerpane, div.record-header, .headerpane")
    EDIT_BUTTON_LOCATORS = (
        (By.CSS_SELECTOR, "div.headerpane a[name='edit_button']"),
        (By.CSS_SELECTOR, "div.headerpane a[title='Edit']"),
        (By.XPATH, "//div[contains(@class,'headerpane')]//a[@name='edit_button']"),
        (By.XPATH, "//div[contains(@class,'headerpane')]//a[@title='Edit']"),
        (By.XPATH, "//div[contains(@class,'headerpane')]//a[normalize-space()='Edit']"),
    )
    # Actions lives in a span.fieldset.actions.btn-group, NOT inside .headerpane .btn-toolbar.
    ACTIONS_BUTTON_LOCATORS = (
        (By.CSS_SELECTOR, "a[track='click:actiondropdown']"),
        (By.CSS_SELECTOR, "span.fieldset.actions a.dropdown-toggle[title='Actions']"),
        (By.CSS_SELECTOR, "a.dropdown-toggle.btn-primary[title='Actions']"),
        (By.CSS_SELECTOR, "a[aria-label='Actions'][title='Actions']"),
        (By.XPATH, "//a[@track='click:actiondropdown']"),
        (By.XPATH, "//span[contains(@class,'actions') and contains(@class,'btn-group')]//a[@title='Actions']"),
        (By.XPATH, "//a[@title='Actions' and contains(@class,'dropdown-toggle')]"),
        (By.XPATH, "//*[@title='Actions' and (self::a or self::button)]"),
    )
    CREATE_LEAD_LOCATORS = (
        (By.CSS_SELECTOR, "ul.leads-submenu a[name='create_lead']"),
        (By.CSS_SELECTOR, "a.rowaction[name='create_lead']"),
        (By.CSS_SELECTOR, "a[name='create_lead'][track='click:create_lead']"),
        (By.CSS_SELECTOR, "a[name='create_lead']"),
        (By.XPATH, "//ul[contains(@class,'leads-submenu')]//a[@name='create_lead']"),
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

    def _ensure_detail_view_route(self) -> None:
        route_hash = self.driver.execute_script("return location.hash || ''")
        if "/edit" not in route_hash.lower():
            return

        match = re.search(r"#Contacts/([^/]+)", route_hash, re.IGNORECASE)
        contact_id = match.group(1) if match else ""
        if not contact_id:
            return

        detail_url = f"{self.config.application_url.rstrip('/')}#Contacts/{contact_id}"
        logger.info("On contact edit route — returning to detail view: %s", detail_url)
        self.driver.get(detail_url)
        self.wait_for_sugar_loading_overlay_gone(context="return to contact detail")
        self.wait_for_detail_toolbar_ready()

    def wait_for_detail_toolbar_ready(self) -> ContactDetailPage:
        """
        Wait until the contact detail header toolbar (Edit, Actions) is visible.

        Chrome's 'Restore pages?' popup/infobar is only handled once, during
        Initial Setup (see SessionOrchestrator) — re-checking it here on every
        toolbar wait added several seconds of dead time per call for no benefit.
        """
        logger.info("Waiting for contact detail toolbar (Edit / Actions)")
        self.wait_for_sugar_loading_overlay_gone(context="contact detail toolbar")
        deadline = time.time() + self.config.explicit_wait
        while time.time() < deadline:
            if self._toolbar_button_visible("Edit") and self._toolbar_button_visible("Actions"):
                logger.info("Contact detail toolbar is ready")
                return self
            self.wait_for_sugar_loading_overlay_gone(context="contact detail toolbar")
            time.sleep(0.1)
        raise RuntimeError(
            "Contact detail toolbar did not become ready — Edit/Actions buttons not visible"
        )

    def _toolbar_button_visible(self, label: str) -> bool:
        if label.lower() == "edit":
            locators = self.EDIT_BUTTON_LOCATORS
        else:
            locators = self.ACTIONS_BUTTON_LOCATORS
        return any(self.is_visible_quick(locator) for locator in locators) or bool(
            self.driver.execute_script(
                """
                const label = arguments[0];
                for (const node of document.querySelectorAll('a[title], button[title], a[aria-label], button[aria-label]')) {
                  const title = (node.getAttribute('title') || node.getAttribute('aria-label') || node.textContent || '').trim();
                  if (title === label) {
                    const style = window.getComputedStyle(node);
                    return style.display !== 'none' && style.visibility !== 'hidden' && node.offsetParent !== null;
                  }
                }
                return false;
                """,
                label,
            )
        )

    def _click_toolbar_button(self, label: str) -> None:
        locators = self.EDIT_BUTTON_LOCATORS if label == "Edit" else self.ACTIONS_BUTTON_LOCATORS
        for locator in locators:
            try:
                element = self.wait.until_clickable(locator)
                self.scroll_to_element(element)
                try:
                    element.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", element)
                logger.info("Clicked %s on contact detail toolbar using locator: %s", label, locator)
                return
            except Exception:
                continue

        clicked = self.driver.execute_script(
            """
            const label = arguments[0];
            for (const node of document.querySelectorAll('a[title], button[title], a[aria-label], button[aria-label]')) {
              const title = (node.getAttribute('title') || node.getAttribute('aria-label') || '').trim();
              if (title !== label) continue;
              node.scrollIntoView({block: 'center', inline: 'nearest'});
              node.click();
              return true;
            }
            return false;
            """,
            label,
        )
        if clicked:
            logger.info("Clicked %s on contact detail toolbar via JavaScript", label)
            return
        raise RuntimeError(f"Could not click {label} button on contact detail view")

    def click_edit(self) -> ContactDetailPage:
        logger.info("Clicking Edit button on contact detail view")
        self.wait_for_detail_toolbar_ready()
        self._click_toolbar_button("Edit")
        self.wait_for_sugar_loading_overlay_gone(context="after Edit click")
        return self

    def _actions_dropdown_open(self) -> bool:
        return bool(
            self.driver.execute_script(
                """
                for (const node of document.querySelectorAll("a[track='click:actiondropdown'], a[title='Actions']")) {
                  if (node.getAttribute('aria-expanded') === 'true') return true;
                }
                return false;
                """
            )
        )

    def close_actions_dropdown(self) -> None:
        """Close the Actions dropdown if it is currently open (toggle button)."""
        if self._actions_dropdown_open():
            self._click_toolbar_button("Actions")
            logger.info("Closed Actions dropdown")

    def click_actions(self) -> ContactDetailPage:
        logger.info("Clicking Actions button on contact detail view")
        self._ensure_detail_view_route()
        self.wait_for_detail_toolbar_ready()
        if self._actions_dropdown_open():
            logger.info("Actions dropdown already open — skipping click")
        else:
            self._click_toolbar_button("Actions")
        self._wait_for_create_lead_visible()
        return self

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
