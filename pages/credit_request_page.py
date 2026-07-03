"""Credit Request tab/panel on the Lead detail view."""

from __future__ import annotations

import time
from datetime import date

from selenium.webdriver.common.by import By

from pages.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class CreditRequestPage(BasePage):
    CREDIT_REQUEST_TAB_LOCATORS = (
        (By.XPATH, "//a[normalize-space()='Credit Request']"),
        (By.XPATH, "//li//a[contains(normalize-space(.), 'Credit Request')]"),
        (By.XPATH, "//*[@role='tab'][contains(normalize-space(.), 'Credit Request')]"),
    )
    CREDIT_REQUEST_PANEL_HEADER = (
        By.XPATH,
        "//*[contains(translate(normalize-space(.), "
        "'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'CREDIT REQUEST')]",
    )
    # Confirmed field 'data-name' attributes from DOM inspection — used to target
    # the exact '<div class="record-label" data-name="...">' pill (the '+ Label'
    # element shown when the field is empty in detail view).
    FIELD_DATA_NAME = {
        "Legal terms customer": "legal_terms_accepted_date_c",
        "Credit usage": "credit_usage_type_id_c",
    }
    PANEL_SAVE_BUTTON_LOCATORS = (
        (By.CSS_SELECTOR, "a[name='save_button'][track='click:save_button']"),
        (By.CSS_SELECTOR, "a.rowaction.btn.btn-primary[name='save_button']"),
        (By.XPATH, "//a[@name='save_button' and @track='click:save_button']"),
        (By.XPATH, "//a[normalize-space()='Save' and contains(@class,'btn-primary')]"),
        (By.XPATH, "//a[normalize-space()='Save']"),
    )

    def _field_label_xpath(self, label: str) -> str:
        """XPath for the clickable '+ Label' pill (or resolved value) of a field."""
        data_name = self.FIELD_DATA_NAME.get(label)
        if data_name:
            return f"//div[contains(@class,'record-label')][@data-name='{data_name}']"
        return (
            f"//div[contains(@class,'record-label')]"
            f"[@title='{label}' or @data-original-title='{label}' or normalize-space()='{label}']"
        )

    def _field_scope_xpath(self, label: str) -> str:
        """XPath scoping to a field's outer record-cell container."""
        data_name = self.FIELD_DATA_NAME.get(label)
        if data_name:
            return f"//div[@data-name='{data_name}']"
        return f"({self._field_label_xpath(label)})[1]/ancestor::div[contains(@class,'record-cell')][1]"

    def _click_first_visible(self, locators) -> bool:
        for locator in locators:
            if self.click_if_visible_quick(locator):
                return True
            try:
                self.click_with_fallback(locator)
                return True
            except Exception:
                continue
        return False

    def open_credit_request_tab(self) -> CreditRequestPage:
        logger.info("Opening Credit Request tab on lead detail view")
        self.wait_for_sugar_loading_overlay_gone(context="lead detail tabs")
        for locator in self.CREDIT_REQUEST_TAB_LOCATORS:
            try:
                element = self.driver.find_element(*locator)
            except Exception:
                continue
            self.scroll_to_element(element)
            try:
                element.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", element)
            self.wait_for_sugar_loading_overlay_gone(context="credit request tab")
            self.wait.until_visible(self.CREDIT_REQUEST_PANEL_HEADER)
            logger.info("Credit Request tab is open")
            return self
        raise RuntimeError("Could not find Credit Request tab on lead detail view")

    def _click_field_pill(self, label: str) -> bool:
        """
        Click the '+ Label' pill (data-name based) to switch the field into edit
        mode. Returns False if the pill isn't present (field may already be in
        edit mode, e.g. after another field in the same panel activated it).
        """
        label_xpath = self._field_label_xpath(label)
        try:
            element = self.driver.find_element(By.XPATH, label_xpath)
        except Exception:
            return False
        self.scroll_to_element(element)
        try:
            element.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", element)
        return True

    def _click_visible_calendar_day(self, day_text: str) -> bool:
        """
        Click a visible calendar day cell matching the exact day-of-month text,
        preferring a cell flagged as 'today'/'active'/'selected' and skipping
        muted overflow days from adjacent months (old/new/disabled classes).
        Written generically (by visible text, not fixed widget classes) since
        the exact calendar widget markup wasn't confirmed via DOM inspection.
        """
        script = """
            const dayText = arguments[0];
            const nodes = Array.from(document.querySelectorAll('td, a, span, div'));
            const candidates = nodes.filter((el) => {
                if (el.children.length > 1) return false;
                if (!el.offsetParent) return false;
                const text = (el.textContent || '').trim();
                if (text !== dayText) return false;
                const cls = el.className || '';
                if (typeof cls !== 'string') return false;
                if (/\\b(old|new|disabled|unselectable|muted|out-of-range)\\b/i.test(cls)) return false;
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            });
            if (candidates.length === 0) { return false; }
            const preferred = candidates.find((el) => /today|active|selected|highlight/i.test(el.className))
                || candidates[0];
            const clickable = preferred.querySelector('a') || preferred;
            clickable.click();
            return true;
        """
        try:
            return bool(self.driver.execute_script(script, day_text))
        except Exception:
            return False

    def set_legal_terms_customer_date(self) -> CreditRequestPage:
        logger.info("Setting Legal terms customer date")
        scope_xpath = self._field_scope_xpath("Legal terms customer")
        field_element = self.wait.until_present((By.XPATH, scope_xpath))
        self.scroll_to_element(field_element)

        self._click_field_pill("Legal terms customer")

        deadline = time.time() + self.config.explicit_wait
        today_text = str(date.today().day)
        while time.time() < deadline:
            if self._click_visible_calendar_day(today_text):
                logger.info("Selected date '%s' for Legal terms customer", today_text)
                return self
            time.sleep(0.2)

        raise RuntimeError("Could not select a date for Legal terms customer — calendar did not appear")

    def select_credit_usage(self, option_text: str) -> CreditRequestPage:
        logger.info("Selecting Credit usage: %s", option_text)
        scope_xpath = self._field_scope_xpath("Credit usage")
        field_element = self.wait.until_present((By.XPATH, scope_xpath))
        self.scroll_to_element(field_element)

        already_editable = bool(
            self.driver.find_elements(
                By.XPATH, f"{scope_xpath}//a[contains(@class,'select2-choice')]"
            )
        )
        if not already_editable:
            self._click_field_pill("Credit usage")

        trigger_xpaths = (
            f"{scope_xpath}//a[contains(@class,'select2-choice')]",
            f"{scope_xpath}//span[contains(@class,'select2-chosen')]",
            f"{scope_xpath}//div[contains(@class,'select2-container')]",
        )
        opened = False
        for xpath in trigger_xpaths:
            try:
                trigger = self.wait.until_present((By.XPATH, xpath))
            except Exception:
                continue
            self.scroll_to_element(trigger)
            try:
                trigger.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", trigger)
            opened = True
            break
        if not opened:
            raise RuntimeError("Could not open Credit usage dropdown")

        option_locators = (
            (
                By.XPATH,
                f"//div[contains(@class,'select2-drop-active')]"
                f"//li[contains(normalize-space(.), '{option_text}')]",
            ),
            (
                By.XPATH,
                f"//li[contains(@class,'select2-result') "
                f"and contains(normalize-space(.), '{option_text}')]",
            ),
            (By.XPATH, f"//option[normalize-space()='{option_text}']"),
        )
        if self._click_first_visible(option_locators):
            logger.info("Selected Credit usage: %s", option_text)
            return self
        raise RuntimeError(f"Could not select Credit usage option '{option_text}'")

    def click_save(self) -> CreditRequestPage:
        """Click the panel-level Save button that appears once a field enters edit mode."""
        logger.info("Clicking Save on Credit Request panel")
        for by, selector in self.PANEL_SAVE_BUTTON_LOCATORS:
            try:
                candidates = self.driver.find_elements(by, selector)
            except Exception:
                continue
            for element in candidates:
                try:
                    if not element.is_displayed():
                        continue
                except Exception:
                    continue
                self.scroll_to_element(element)
                try:
                    element.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", element)
                self.wait_for_sugar_loading_overlay_gone(context="after credit request save")
                logger.info("Credit Request panel saved")
                return self
        raise RuntimeError("Could not find a visible Save button on Credit Request panel")
