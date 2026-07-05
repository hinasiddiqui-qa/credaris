"""Application create view — opened via 'Create Application' quick action on Lead detail view."""

from __future__ import annotations

import time

from selenium.webdriver.common.by import By

from pages.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class ApplicationCreatePage(BasePage):
    PROVIDER_FIELD_LABEL = "Provider"
    BANK_NOW_ID_FIELD_LABEL = "BANK-now ID"
    CREDIT_AMOUNT_FIELD_LABEL = "Credit Amount"
    CREDIT_DURATION_FIELD_LABEL = "Credit Duration"
    INTEREST_RATE_FIELD_LABEL = "Interest Rate"
    SOKO_FIELD_LABEL = "SOKO"
    EXPLANATION_SOKO_FIELD_LABEL = "Explanation SOKO"
    PROVIDER_STATUS_FIELD_LABEL = "Provider status"
    # Confirmed field 'data-name' attributes from live DOM inspection — exact
    # attribute match, so preferred over label-text matching when available
    # (avoids any label-text ambiguity entirely for these fields).
    FIELD_DATA_NAME = {
        "SOKO": "dotb_soko_c",
        "Explanation SOKO": "explanation_soko_c",
        # Confirmed via DOM inspection — 'Provider status' otherwise shares a
        # text prefix with 'Provider', the exact ambiguity that already
        # caused a false-match bug for that field (see _field_scope_xpath).
        "Provider status": "provider_status_id_c",
    }
    APPLIED_WITH_BANK_SECTION_HEADER = (
        By.XPATH,
        "//*[contains(translate(normalize-space(.), "
        "'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'APPLIED WITH THE BANK')]",
    )
    SAVE_BUTTON_LOCATORS = (
        (By.CSS_SELECTOR, "a[name='save_button'][track='click:save_button']"),
        (By.CSS_SELECTOR, "a.rowaction.btn.btn-primary[name='save_button']"),
        (By.XPATH, "//a[@name='save_button' and @track='click:save_button']"),
        (By.XPATH, "//a[normalize-space()='Save' and contains(@class,'btn-primary')]"),
        (By.XPATH, "//a[normalize-space()='Save']"),
    )
    SELECT2_SEARCH_INPUT_LOCATORS = (
        (By.CSS_SELECTOR, ".select2-drop-active .select2-search input"),
        (By.CSS_SELECTOR, ".select2-drop-active input.select2-input"),
        (By.CSS_SELECTOR, ".select2-drop-active input[type='text']"),
    )

    def wait_until_loaded(self) -> ApplicationCreatePage:
        """
        Wait for the Create Application view to render — the Provider field is the
        first reliable, unique-to-this-form element to check for.
        """
        provider_locator = (By.XPATH, self._field_scope_xpath(self.PROVIDER_FIELD_LABEL))
        logger.info("Waiting for Create Application view to load")
        if self.is_visible_quick(provider_locator):
            logger.info("Create Application view is ready")
            return self

        self.wait_for_sugar_loading_overlay_gone(context="create application view")
        deadline = time.time() + self.config.explicit_wait
        while time.time() < deadline:
            if self.is_visible_quick(provider_locator):
                logger.info("Create Application view is ready")
                return self
            time.sleep(0.1)
        self.wait_for_sugar_app_ready(context="create application view")
        self.wait.until_present(provider_locator)
        return self

    def _field_scope_xpath(self, label: str) -> str:
        """
        XPath scoping to a field's container.

        Prefers the confirmed 'data-name' attribute (exact match — safest, no
        label-text ambiguity at all). Falls back to matching the visible label
        by its EXACT text (a trailing required-field marker, e.g. '*', is
        stripped before comparing) — checking both '<label>' elements and Sugar's
        '<div class="record-label">' field labels, since this form uses the
        latter (a plain '<label>'-only search previously found nothing for
        fields like SOKO and silently failed).

        Must be an exact match, not 'contains' — this form has several labels
        that share a text prefix/substring with 'Provider' ('Provider status',
        'Provider application no', 'Provider Contract Number', etc.). A
        'contains' match previously locked onto one of those instead of the
        real 'Provider' field, and worse, onto a *subpanel table column
        header* (not a form field at all) — which is why this also excludes
        anything under a '<th>'/'<thead>' (list/subpanel headers never belong
        to an editable field).
        """
        data_name = self.FIELD_DATA_NAME.get(label)
        if data_name:
            return f"//div[contains(@class,'record-cell')][@data-name='{data_name}']"

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

    def _expand_collapsed_panels(self) -> None:
        """Some fields (e.g. Applied with the Bank) live in panels that may be collapsed."""
        try:
            toggles = self.driver.find_elements(
                By.CSS_SELECTOR,
                "[data-toggle='collapse'], .panel-heading a, h4.panel-title a",
            )
        except Exception:
            return
        expanded_any = False
        for toggle in toggles:
            try:
                expanded = (toggle.get_attribute("aria-expanded") or "").lower()
                if expanded == "false":
                    self.driver.execute_script("arguments[0].click();", toggle)
                    expanded_any = True
            except Exception:
                continue
        if expanded_any:
            time.sleep(0.3)

    def _scroll_to_locator(self, locator: tuple[str, str]) -> None:
        if self.is_visible_quick(locator):
            self.scroll_to_element(self.driver.find_element(*locator))
            return

        self._expand_collapsed_panels()
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

    def scroll_to_applied_with_bank_section(self) -> ApplicationCreatePage:
        logger.info("Scrolling to 'Applied with the Bank' section")
        self._scroll_to_locator(self.APPLIED_WITH_BANK_SECTION_HEADER)
        return self

    def _open_select2_dropdown(self, scope_xpath: str) -> bool:
        """
        Open a select2 dropdown scoped to the given field XPath. Returns True if an
        inline multi-select input was used directly, False if a floating
        '.select2-drop-active' panel should be used instead.
        """
        inline_xpath = (
            f"{scope_xpath}//ul[contains(@class,'select2-choices')]"
            f"//input[contains(@class,'select2-input')]"
        )
        try:
            inline_input = self.driver.find_element(By.XPATH, inline_xpath)
            self.scroll_to_element(inline_input)
            try:
                inline_input.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", inline_input)
            return True
        except Exception:
            pass

        trigger_xpaths = (
            f"{scope_xpath}//a[contains(@class,'select2-choice')]",
            f"{scope_xpath}//span[contains(@class,'select2-selection')]",
            f"{scope_xpath}//span[contains(@class,'select2-chosen')]",
            f"{scope_xpath}//div[contains(@class,'select2-container')]",
            f"{scope_xpath}//input[contains(@class,'select2-input')]",
            f"{scope_xpath}//a[contains(@class,'dropdown-toggle')]",
        )
        for xpath in trigger_xpaths:
            try:
                element = self.driver.find_element(By.XPATH, xpath)
            except Exception:
                continue
            self.scroll_to_element(element)
            try:
                element.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", element)
            return False
        raise RuntimeError(f"Could not open dropdown for field scope: {scope_xpath}")

    def _type_into_open_dropdown_search(
        self, search_text: str, *, scope_xpath: str | None = None, used_inline: bool = False
    ) -> None:
        if used_inline and scope_xpath:
            inline_xpath = (
                f"{scope_xpath}//ul[contains(@class,'select2-choices')]"
                f"//input[contains(@class,'select2-input')]"
            )
            try:
                inline_input = self.driver.find_element(By.XPATH, inline_xpath)
                inline_input.send_keys(search_text)
                return
            except Exception:
                pass

        try:
            active = self.driver.switch_to.active_element
            tag = (active.tag_name or "").lower()
            input_type = (active.get_attribute("type") or "").lower()
            if tag == "textarea" or (tag == "input" and input_type not in ("hidden", "checkbox", "radio")):
                active.send_keys(search_text)
                return
        except Exception:
            pass

        broadened_locators = self.SELECT2_SEARCH_INPUT_LOCATORS + (
            (By.CSS_SELECTOR, ".select2-drop input[type='text']"),
            (By.CSS_SELECTOR, ".dropdown-menu.open input[type='text']"),
            (By.CSS_SELECTOR, ".open input[placeholder*='Search']"),
            (By.XPATH, "//input[contains(@placeholder,'Search') and not(@type='hidden')]"),
        )
        for locator in broadened_locators:
            if self.is_visible_quick(locator):
                element = self.driver.find_element(*locator)
                element.clear()
                element.send_keys(search_text)
                return

        raise RuntimeError(f"Could not find dropdown search input to type '{search_text}'")

    def _select_open_dropdown_option(self, option_text: str) -> None:
        """
        Click the given option in a currently-open select2/dropdown list.

        Polls for up to explicit_wait rather than checking the locators only
        once — after typing into the search box, select2 filters its result
        list asynchronously, so the matching <li> can briefly not exist yet.
        A single-pass check was intermittently failing here (observed for
        Credit Duration's '24', but this is a generic dropdown timing issue,
        not specific to that field) even though the option renders correctly
        a few hundred ms later.
        """
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
            (
                By.XPATH,
                f"//ul[contains(@class,'dropdown-menu')]"
                f"//*[self::a or self::li][contains(normalize-space(.), '{option_text}')]",
            ),
            (
                By.XPATH,
                f"//*[contains(@class,'dropdown') or contains(@class,'open')]"
                f"//*[self::a or self::li or self::div]"
                f"[contains(normalize-space(.), '{option_text}') "
                f"and not(ancestor::*[contains(@class,'select2-offscreen')])]",
            ),
        )
        deadline = time.time() + self.config.explicit_wait
        while time.time() < deadline:
            for option in option_locators:
                if self.click_if_visible_quick(option):
                    return
                try:
                    self.click_with_fallback(option)
                    return
                except Exception:
                    continue
            time.sleep(0.2)
        raise RuntimeError(f"Could not select option '{option_text}'")

    def _close_any_open_dropdown(self) -> None:
        """
        Defensively blur any select2 dropdown search input left focused from a
        previous field. Without this, a stray still-focused search input from a
        prior field can silently steal keystrokes meant for the next one —
        observed with 'Interest Rate' typing landing inside Credit Duration's
        dropdown because it was never closed after its own selection.

        Deliberately does NOT send an Escape key press here — the Create
        Application view (like the Task quickcreate drawer) treats Escape as
        Cancel for the *whole* view, not just "close this dropdown", which was
        silently cancelling and discarding the entire form right after it
        opened. A plain JS blur() has no such side effect.
        """
        try:
            self.driver.execute_script(
                "if (document.activeElement) { document.activeElement.blur(); }"
            )
        except Exception:
            pass

    def select_provider(self, option_text: str) -> ApplicationCreatePage:
        logger.info("Selecting Provider: %s", option_text)
        self._close_any_open_dropdown()
        scope_xpath = self._field_scope_xpath(self.PROVIDER_FIELD_LABEL)
        self._scroll_to_locator((By.XPATH, scope_xpath))
        used_inline = self._open_select2_dropdown(scope_xpath)
        self._type_into_open_dropdown_search(
            option_text, scope_xpath=scope_xpath, used_inline=used_inline
        )
        self._select_open_dropdown_option(option_text)
        self._close_any_open_dropdown()
        return self

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

    def enter_bank_now_id(self, value: str) -> ApplicationCreatePage:
        logger.info("Entering BANK-now ID: %s", value)
        self._enter_text_field(self.BANK_NOW_ID_FIELD_LABEL, value)
        return self

    def enter_credit_amount(self, value: str) -> ApplicationCreatePage:
        logger.info("Entering Credit Amount: %s", value)
        self._enter_text_field(self.CREDIT_AMOUNT_FIELD_LABEL, value)
        return self

    def select_credit_duration(self, option_text: str) -> ApplicationCreatePage:
        logger.info("Selecting Credit Duration: %s", option_text)
        self._close_any_open_dropdown()
        scope_xpath = self._field_scope_xpath(self.CREDIT_DURATION_FIELD_LABEL)
        self._scroll_to_locator((By.XPATH, scope_xpath))
        used_inline = self._open_select2_dropdown(scope_xpath)
        self._type_into_open_dropdown_search(
            option_text, scope_xpath=scope_xpath, used_inline=used_inline
        )
        self._select_open_dropdown_option(option_text)
        self._close_any_open_dropdown()
        return self

    def select_provider_status(self, option_text: str) -> ApplicationCreatePage:
        """Open the Provider status dropdown and select the given option (e.g. 'Granted')."""
        logger.info("Selecting Provider status: %s", option_text)
        self._close_any_open_dropdown()
        scope_xpath = self._field_scope_xpath(self.PROVIDER_STATUS_FIELD_LABEL)
        self._scroll_to_locator((By.XPATH, scope_xpath))
        used_inline = self._open_select2_dropdown(scope_xpath)
        self._type_into_open_dropdown_search(
            option_text, scope_xpath=scope_xpath, used_inline=used_inline
        )
        self._select_open_dropdown_option(option_text)
        self._close_any_open_dropdown()
        return self

    def select_interest_rate(self, option_text: str) -> ApplicationCreatePage:
        """Open the Interest Rate dropdown and select the given option (e.g. '4.90')."""
        logger.info("Selecting Interest Rate: %s", option_text)
        self._close_any_open_dropdown()
        scope_xpath = self._field_scope_xpath(self.INTEREST_RATE_FIELD_LABEL)
        self._scroll_to_locator((By.XPATH, scope_xpath))
        used_inline = self._open_select2_dropdown(scope_xpath)
        self._type_into_open_dropdown_search(
            option_text, scope_xpath=scope_xpath, used_inline=used_inline
        )
        self._select_open_dropdown_option(option_text)
        self._close_any_open_dropdown()
        return self

    def check_soko(self) -> ApplicationCreatePage:
        """
        Check the SOKO checkbox.

        Scoped via the confirmed 'data-name=dotb_soko_c' container (see
        FIELD_DATA_NAME) — scans all matches and clicks the first *visible*
        checkbox rather than assuming there's only one in the DOM, consistent
        with the rest of this suite's "scan all, click first visible" pattern.
        """
        logger.info("Checking SOKO checkbox")
        scope_xpath = self._field_scope_xpath(self.SOKO_FIELD_LABEL)
        self._scroll_to_locator((By.XPATH, scope_xpath))

        checkbox_xpath = f"{scope_xpath}//input[@type='checkbox']"
        try:
            candidates = self.driver.find_elements(By.XPATH, checkbox_xpath)
        except Exception:
            candidates = []
        visible_checkboxes = [el for el in candidates if self._is_displayed(el)]
        if not visible_checkboxes:
            raise RuntimeError("Could not find SOKO checkbox")

        checkbox = visible_checkboxes[0]
        self.scroll_to_element(checkbox)
        if not checkbox.is_selected():
            try:
                checkbox.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", checkbox)
        return self

    def enter_explanation_soko(self, value: str) -> ApplicationCreatePage:
        """
        Enter text into 'Explanation SOKO' — a required field that only renders
        once the SOKO checkbox is checked, so this must run after check_soko().
        _enter_text_field() already waits for the field to be present, which
        covers this field only appearing after that checkbox toggle.
        """
        logger.info("Entering Explanation SOKO: %s", value)
        self._enter_text_field(self.EXPLANATION_SOKO_FIELD_LABEL, value)
        return self

    def click_save(self) -> ApplicationCreatePage:
        """
        Click Save on the Create Application view.

        Scans all matches per locator and clicks whichever one is actually
        displayed — other views (e.g. the Lead detail header behind this one) can
        contain a hidden button matching the same 'save_button'/'track' attributes.
        """
        logger.info("Clicking Save on Create Application view")
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
                self.wait_for_sugar_loading_overlay_gone(context="after create application save")
                logger.info("Create Application view saved")
                return self
        raise RuntimeError("Could not find a visible Save button on Create Application view")

    def create_application(
        self,
        provider: str,
        bank_now_id: str,
        credit_amount: str,
        credit_duration: str,
        interest_rate: str,
        explanation_soko: str | None = None,
        provider_status: str | None = None,
    ) -> ApplicationCreatePage:
        """
        Create Application flow:
        1. Select Provider
        2. Enter BANK-now ID
        3. Scroll to 'Applied with the Bank' section
        4. Enter Credit Amount
        5. Select Credit Duration
        6. Select Interest Rate
        7. Check SOKO
        8. Enter Explanation SOKO (only rendered once SOKO is checked — required
           before Save will succeed, otherwise the view stays stuck open with a
           client-side validation error)
        9. Select Provider status (if provided) — done last, right before Save
        10. Click Save
        """
        self.select_provider(provider)
        self.enter_bank_now_id(bank_now_id)
        self.scroll_to_applied_with_bank_section()
        self.enter_credit_amount(credit_amount)
        self.select_credit_duration(credit_duration)
        self.select_interest_rate(interest_rate)
        self.check_soko()
        if explanation_soko:
            self.enter_explanation_soko(explanation_soko)
        if provider_status:
            self.select_provider_status(provider_status)
        self.click_save()
        return self
