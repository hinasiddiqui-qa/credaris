"""Contract create view — opened via 'Create Contract' quick action on Lead detail view."""

from __future__ import annotations

import time

from selenium.webdriver.common.by import By

from pages.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class ContractCreatePage(BasePage):
    PROVIDER_CONTRACT_NUMBER_FIELD_LABEL = "Provider Contract Number"
    CREDIT_AMOUNT_FIELD_LABEL = "Credit Amount"
    INTEREST_RATE_FIELD_LABEL = "Interest Rate"
    CREDIT_DURATION_FIELD_LABEL = "Credit Duration"
    SAVE_BUTTON_LOCATORS = (
        (By.CSS_SELECTOR, "a[name='save_button'][track='click:save_button']"),
        (By.CSS_SELECTOR, "a.rowaction.btn.btn-primary[name='save_button']"),
        (By.XPATH, "//a[@name='save_button' and @track='click:save_button']"),
        (By.XPATH, "//a[normalize-space()='Save' and contains(@class,'btn-primary')]"),
        (By.XPATH, "//a[normalize-space()='Save']"),
    )

    def wait_until_loaded(self) -> ContractCreatePage:
        """
        Wait for the Create Contract view — 'Provider Contract Number' is the
        first reliable, unique-to-this-form field to check for.
        """
        field_locator = (
            By.XPATH,
            self._field_scope_xpath(self.PROVIDER_CONTRACT_NUMBER_FIELD_LABEL),
        )
        logger.info("Waiting for Create Contract view to load")
        if self.is_visible_quick(field_locator):
            logger.info("Create Contract view is ready")
            return self

        self.wait_for_sugar_loading_overlay_gone(context="create contract view")
        deadline = time.time() + self.config.explicit_wait
        while time.time() < deadline:
            if self.is_visible_quick(field_locator):
                logger.info("Create Contract view is ready")
                return self
            time.sleep(0.1)
        self.wait_for_sugar_app_ready(context="create contract view")
        self.wait.until_present(field_locator)
        return self

    def _field_scope_xpath(self, label: str) -> str:
        """
        XPath scoping to a field's container.

        Uses EXACT label text (required-field '*' stripped) — this form has
        several labels sharing a 'Provider' prefix ('Provider Contract Number',
        'Provider', etc.), so 'contains' matching must not be used here.
        """
        exact_label_test = f"normalize-space(translate(., '*', '')) = '{label}'"
        return (
            f"(//label[{exact_label_test}][not(ancestor::th) and not(ancestor::thead)] | "
            f"//div[contains(@class,'record-label')][{exact_label_test}]"
            f"[not(ancestor::th) and not(ancestor::thead)])[1]"
            f"/ancestor::div[contains(@class,'record-cell') or contains(@class,'field') "
            f"or contains(@class,'form-group')][1]"
        )

    def _is_displayed(self, element) -> bool:
        try:
            return bool(element.is_displayed())
        except Exception:
            return False

    def _scroll_to_locator(self, locator: tuple[str, str]) -> None:
        if self.is_visible_quick(locator):
            self.scroll_to_element(self.driver.find_element(*locator))
            return

        try:
            self.driver.execute_script(
                """
                const candidates = document.querySelectorAll(
                    '.edit-view, .record-view, .detail-view, .quickcreate, .drawer, .modal-body'
                );
                candidates.forEach((el) => {
                    if (el.scrollHeight > el.clientHeight) { el.scrollTop = el.scrollHeight; }
                });
                """
            )
        except Exception:
            pass
        try:
            element = self.wait.until_present(locator)
            self.scroll_to_element(element)
        except Exception:
            logger.warning("Could not find/scroll to locator: %s", locator)

    def _enter_text_field(self, label: str, value: str) -> None:
        scope_xpath = self._field_scope_xpath(label)
        self._scroll_to_locator((By.XPATH, scope_xpath))
        input_xpath = (
            f"{scope_xpath}//input[(@type='text' or not(@type)) and not(contains(@class,'select2'))]"
        )
        element = self.wait.until_present((By.XPATH, input_xpath))
        self.scroll_to_element(element)
        try:
            element.clear()
        except Exception:
            pass
        element.send_keys(value)

    def enter_provider_contract_number(self, value: str) -> ContractCreatePage:
        logger.info("Entering Provider Contract Number: %s", value)
        self._enter_text_field(self.PROVIDER_CONTRACT_NUMBER_FIELD_LABEL, value)
        return self

    def enter_credit_amount(self, value: str) -> ContractCreatePage:
        logger.info("Entering Credit Amount: %s", value)
        self._enter_text_field(self.CREDIT_AMOUNT_FIELD_LABEL, value)
        return self

    def enter_interest_rate(self, value: str) -> ContractCreatePage:
        logger.info("Entering Interest Rate: %s", value)
        self._enter_text_field(self.INTEREST_RATE_FIELD_LABEL, value)
        return self

    def enter_credit_duration(self, value: str) -> ContractCreatePage:
        logger.info("Entering Credit Duration: %s", value)
        self._enter_text_field(self.CREDIT_DURATION_FIELD_LABEL, value)
        return self

    def click_save(self) -> ContractCreatePage:
        """Click Save on the Create Contract view."""
        logger.info("Clicking Save on Create Contract view")
        for by, selector in self.SAVE_BUTTON_LOCATORS:
            try:
                candidates = self.driver.find_elements(by, selector)
            except Exception:
                continue
            for element in candidates:
                if not self._is_displayed(element):
                    continue
                self.scroll_to_element(element)
                try:
                    element.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", element)
                self.wait_for_sugar_loading_overlay_gone(context="after create contract save")
                logger.info("Create Contract view saved")
                return self
        raise RuntimeError("Could not find a visible Save button on Create Contract view")

    def create_contract(
        self,
        provider_contract_number: str,
        credit_amount: str,
        interest_rate: str,
        credit_duration: str,
    ) -> ContractCreatePage:
        """
        Create Contract flow:
        1. Enter Provider Contract Number
        2. Enter Credit Amount
        3. Enter Interest Rate
        4. Enter Credit Duration
        5. Click Save
        """
        self.enter_provider_contract_number(provider_contract_number)
        self.enter_credit_amount(credit_amount)
        self.enter_interest_rate(interest_rate)
        self.enter_credit_duration(credit_duration)
        self.click_save()
        return self
