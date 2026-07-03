"""Task create view — opened via 'Create Task' quick action on Lead detail view."""

from __future__ import annotations

import time

from selenium.webdriver.common.by import By

from pages.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class TaskCreatePage(BasePage):
    SUBJECT_FIELD = (
        By.CSS_SELECTOR,
        "input[name='name'], #name, input[data-fieldname='name']",
    )
    SAVE_BUTTON_LOCATORS = (
        (By.CSS_SELECTOR, "a[name='save_button'][track='click:save_button']"),
        (By.CSS_SELECTOR, "a.rowaction.btn.btn-primary[name='save_button']"),
        (By.XPATH, "//a[@name='save_button' and @track='click:save_button']"),
        (By.XPATH, "//a[normalize-space()='Save' and contains(@class,'btn-primary')]"),
    )
    SELECT2_SEARCH_INPUT_LOCATORS = (
        (By.CSS_SELECTOR, ".select2-drop-active .select2-search input"),
        (By.CSS_SELECTOR, ".select2-drop-active input.select2-input"),
        (By.CSS_SELECTOR, ".select2-drop-active input[type='text']"),
    )
    # Confirmed field 'data-name' attributes from DOM inspection — the most reliable
    # way to scope a field, since it's an exact attribute match (no over-matching risk).
    FIELD_DATA_NAME = {
        "Category": "category_c",
        "Teams": "team_name",
    }

    def wait_until_loaded(self) -> TaskCreatePage:
        """
        Wait for the Task quickcreate drawer to render.

        This opens as an in-place drawer on the Lead detail view — the URL hash
        never changes to '#Tasks/create' — so the only reliable signal is the
        Subject field becoming visible. Checking is_visible_quick() first (which
        fast-paths via find_elements when nothing is in the DOM yet) avoids
        looping for the full explicit_wait when the drawer is already there,
        which was previously adding a large fixed delay before every task test.
        """
        logger.info("Waiting for Task create view to load")
        if self.is_visible_quick(self.SUBJECT_FIELD):
            logger.info("Task create view is ready")
            return self

        self.wait_for_sugar_loading_overlay_gone(context="task create view")
        deadline = time.time() + self.config.explicit_wait
        while time.time() < deadline:
            if self.is_visible_quick(self.SUBJECT_FIELD):
                logger.info("Task create view is ready")
                return self
            time.sleep(0.1)
        self.wait_for_sugar_app_ready(context="task create view")
        self.wait.until_visible(self.SUBJECT_FIELD)
        return self

    def _field_scope_xpath(self, label: str) -> str:
        """
        Build an XPath scoping to a single field's container.

        Prefers the confirmed 'data-name' attribute (exact match — safest).
        Falls back to matching the visible label element and climbing to its
        record-cell/field ancestor (still exact-match on the label, not a
        page-wide substring search, to avoid over-matching large containers).
        """
        data_name = self.FIELD_DATA_NAME.get(label)
        if data_name:
            return f"//div[@data-name='{data_name}']"
        return (
            f"(//div[contains(@class,'record-label')]"
            f"[@title='{label}' or @data-original-title='{label}' or normalize-space()='{label}']"
            f")[1]/ancestor::div[contains(@class,'record-cell') or contains(@class,'field')][1]"
        )

    def _expand_collapsed_panels(self) -> None:
        """Some Task fields (e.g. Teams) live in panels that may be collapsed by default."""
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

    def _scroll_field_into_view(self, scope_xpath: str) -> None:
        """
        Scroll a field into view, expanding collapsed panels first if needed.

        Fields near the top (e.g. Category) are already present/visible right
        after the drawer opens — skip the panel-expand + scroll-to-bottom pass
        entirely in that case, since it was adding a needless delay before every
        field interaction. Only fall back to the fuller expand/scroll routine
        for fields that aren't immediately present (e.g. Teams, further down).
        """
        quick_locator = (By.XPATH, scope_xpath)
        if self.is_visible_quick(quick_locator):
            self.scroll_to_element(self.driver.find_element(*quick_locator))
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
            element = self.wait.until_present(quick_locator)
            self.scroll_to_element(element)
        except Exception:
            logger.warning("Could not find/scroll to field scope: %s", scope_xpath)

    def _open_select2_dropdown(self, scope_xpath: str) -> bool:
        """
        Open a select2 dropdown scoped to the given field XPath.

        Handles both variants:
        - single-select (e.g. Category, Teams as seen in DOM): click 'a.select2-choice'
          -> a floating '.select2-drop-active' panel with its own search input appears.
        - multi-select (chip based): the search input lives inline inside
          'ul.select2-choices' — clicking/focusing it both opens the dropdown and is
          the element to type into directly.

        Returns True if the inline multi-select input was used (caller should type
        directly into it), False if a floating '.select2-drop-active' panel should
        be used instead.
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

        # Some fields (e.g. Teams / TeamSetField) open a custom 'Search and Select...'
        # widget rather than a plain select2 popup. Whatever widget it is, opening it
        # almost always auto-focuses its own search input — so type into that directly.
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
            # Custom widgets (e.g. Teams 'Search and Select...') often render results
            # as a bootstrap-style dropdown-menu list rather than select2 markup.
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
        for option in option_locators:
            if self.click_if_visible_quick(option):
                return
            try:
                self.click_with_fallback(option)
                return
            except Exception:
                continue
        raise RuntimeError(f"Could not select option '{option_text}'")

    def select_category(self, option_text: str) -> TaskCreatePage:
        logger.info("Selecting Category: %s", option_text)
        scope_xpath = self._field_scope_xpath("Category")
        self._scroll_field_into_view(scope_xpath)
        self._open_select2_dropdown(scope_xpath)
        self._select_open_dropdown_option(option_text)
        return self

    def select_teams(self, search_text: str, option_text: str) -> TaskCreatePage:
        logger.info("Selecting Teams — search '%s', select '%s'", search_text, option_text)
        scope_xpath = self._field_scope_xpath("Teams")
        self._scroll_field_into_view(scope_xpath)
        used_inline = self._open_select2_dropdown(scope_xpath)
        self._type_into_open_dropdown_search(
            search_text, scope_xpath=scope_xpath, used_inline=used_inline
        )
        self._select_open_dropdown_option(option_text)
        return self

    def click_save(self) -> TaskCreatePage:
        """
        Click the Task drawer's Save button.

        The Lead detail view's own (currently inactive) header can contain a button
        matching the same 'save_button'/'track' attributes, hidden behind the Task
        drawer. Locators like find_element/visibility_of_element_located only ever
        look at the *first* DOM match, so if that happens to be the hidden Lead
        button, the click silently targets the wrong element (or times out). Scan
        *all* matches per locator and click whichever one is actually displayed.
        """
        logger.info("Clicking Save on Task create view")
        for by, selector in self.SAVE_BUTTON_LOCATORS:
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
                self.wait_for_sugar_loading_overlay_gone(context="after task save")
                return self
        raise RuntimeError("Could not find a visible Save button on Task create view")

    def create_task(self, category: str, team_search: str, team_option: str) -> TaskCreatePage:
        """
        Task create flow:
        1. Select Category
        2. Search and select Teams
        3. Click Save
        """
        self.select_category(category)
        self.select_teams(team_search, team_option)
        self.click_save()
        return self

    def click_lead_link(self):
        """Click the related Lead link on the saved Task detail view to navigate back to it."""
        from pages.leads_page import LeadsPage

        logger.info("Clicking Lead link on Task detail view")
        self.wait_for_sugar_loading_overlay_gone(context="task detail view")

        lead_link_locators = (
            (By.CSS_SELECTOR, "a[href*='#Leads/']"),
            (By.XPATH, "//a[contains(@href,'#Leads/')]"),
        )
        for locator in lead_link_locators:
            if self.click_if_visible_quick(locator):
                logger.info("Clicked Lead link using locator: %s", locator)
                break
            try:
                self.click_with_fallback(locator)
                logger.info("Clicked Lead link using locator: %s", locator)
                break
            except Exception:
                continue
        else:
            raise RuntimeError("Could not find Lead link on Task detail view")

        leads_page = LeadsPage(self.driver, self.config)
        leads_page.wait_for_sugar_loading_overlay_gone(context="lead detail after task save")
        return leads_page
