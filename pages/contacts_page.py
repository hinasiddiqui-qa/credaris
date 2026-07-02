"""Credaris Sugar CRM contacts module page."""

from __future__ import annotations

import time

from selenium.webdriver.common.by import By

from pages.base_page import BasePage
from pages.components.modal_dialog import ModalDialog
from utils.data_loader import load_json
from utils.logger import get_logger

logger = get_logger(__name__)


class ContactsPage(BasePage):
    LISTVIEW_HEADER = (
        By.XPATH,
        "//*[contains(normalize-space(.), 'Contacts') and (contains(., 'of') or contains(@class, 'module-title') or contains(@class, 'record-label'))]",
    )
    LISTVIEW_TABLE = (
        By.CSS_SELECTOR,
        ".flex-list-view, .list-view, table.dataTable, .table-responsive",
    )
    CREATE_BUTTON_LOCATORS = (
        (By.CSS_SELECTOR, "a[name='create_button'][href='#Contacts/create']"),
        (By.CSS_SELECTOR, "a.btn.btn-primary[name='create_button']"),
        (By.CSS_SELECTOR, "span.list-headerpane a[name='create_button']"),
        (By.XPATH, "//a[@name='create_button' and @href='#Contacts/create']"),
        (By.CSS_SELECTOR, "a[name='create_button']"),
    )
    FIRST_NAME = (
        By.CSS_SELECTOR,
        "input[name='first_name'], #first_name, input[data-fieldname='first_name']",
    )
    LAST_NAME = (
        By.CSS_SELECTOR,
        "input[name='last_name'], #last_name, input[data-fieldname='last_name']",
    )
    EMAIL = (
        By.XPATH,
        "//*[contains(normalize-space(.),'Email Address')]"
        "/ancestor::div[contains(@class,'field') or contains(@class,'record-cell')][1]"
        "//input[not(@type='hidden')]",
    )
    # Record header toolbar — a[name='save_button'][track='click:save_button']
    SAVE_BUTTON = (
        By.CSS_SELECTOR,
        "a[name='save_button'].btn.btn-primary",
    )
    SAVE_BUTTON_LOCATORS = (
        SAVE_BUTTON,
        (By.CSS_SELECTOR, "a.btn.btn-primary[name='save_button']"),
        (By.CSS_SELECTOR, "div.btn-toolbar.pull-right a[name='save_button']"),
        (By.XPATH, "//a[@name='save_button' and @track='click:save_button']"),
        (By.XPATH, "//div[contains(@class,'btn-toolbar')]//a[@name='save_button']"),
        (By.XPATH, "//a[normalize-space()='Save' and contains(@class,'btn-primary')]"),
        (By.CSS_SELECTOR, "a[name='Save'].btn-primary"),
        (By.CSS_SELECTOR, "input[name='Save'], button[name='Save']"),
    )
    IGNORE_DUPLICATE_SAVE_BUTTON = (
        By.CSS_SELECTOR,
        "a[name='duplicate_button'].btn.btn-primary",
    )
    IGNORE_DUPLICATE_SAVE_LOCATORS = (
        IGNORE_DUPLICATE_SAVE_BUTTON,
        (By.CSS_SELECTOR, "a[name='duplicate_button']"),
        (By.XPATH, "//a[@name='duplicate_button' and @track='click:duplicate_button']"),
        (
            By.XPATH,
            "//a[normalize-space()='Ignore Duplicate and Save' and contains(@class,'btn-primary')]",
        ),
    )

    @property
    def contacts_create_url(self) -> str:
        return f"{self.config.application_url.rstrip('/')}#Contacts/create"

    @property
    def contacts_listview_url(self) -> str:
        return f"{self.config.application_url.rstrip('/')}#Contacts"

    def open_contacts_listview(self) -> ContactsPage:
        """Navigate directly to Contacts listview (bypasses sidebar click)."""
        logger.info("Opening Contacts listview via URL: %s", self.contacts_listview_url)
        self.wait_for_sugar_loading_overlay_gone()

        if self._is_listview_ready():
            logger.info("Contacts listview already open")
            return self

        if self.config.application_host in self.driver.current_url:
            self.driver.execute_script(
                "window.location.href = arguments[0];",
                self.contacts_listview_url,
            )
        else:
            self.driver.get(self.contacts_listview_url)

        self.wait_for_sugar_loading_overlay_gone()
        self.wait_until_listview_loaded()
        return self

    def open_contacts_from_sidebar(self) -> ContactsPage:
        """Backward-compatible alias for direct Contacts listview navigation."""
        return self.open_contacts_listview()

    def wait_until_listview_loaded(self) -> ContactsPage:
        logger.info("Waiting for Contacts listview to load")
        if self._is_listview_ready():
            logger.info("Contacts listview already loaded")
            return self

        deadline = time.time() + self.config.sugar_load_timeout
        while time.time() < deadline:
            if self._is_listview_ready():
                logger.info("Contacts listview ready")
                return self
            if self._is_listview_route() and self.is_visible_quick(self.CREATE_BUTTON_LOCATORS[0]):
                logger.info("Contacts listview route ready with Create button")
                return self
            self.wait_for_sugar_loading_overlay_gone(context="contacts listview")
            time.sleep(0.1)

        self.wait_for_sugar_app_ready(context="contacts listview")
        self.wait.until_visible(self.LISTVIEW_HEADER)
        self.wait.until_visible(self.LISTVIEW_TABLE)
        self.wait.until_clickable(self.CREATE_BUTTON_LOCATORS[0])
        return self

    def open_create_form_direct(self) -> ContactsPage:
        """Navigate directly to Contact create form (skips listview + Create click)."""
        logger.info("Opening Contact create form via URL: %s", self.contacts_create_url)

        current_hash = self._current_hash().lower()
        if "contacts/create" in current_hash and self.is_visible_quick(self.FIRST_NAME):
            logger.info("Contact create form already open")
            return self

        self._navigate_to_url(self.contacts_create_url)
        self.wait_for_sugar_app_ready(context="contact create form")
        return self.wait_until_create_form_loaded()

    def _is_listview_ready(self) -> bool:
        return (
            self._is_listview_route()
            and self.is_visible_quick(self.LISTVIEW_HEADER)
            and self.is_visible_quick(self.LISTVIEW_TABLE)
        )

    def wait_until_create_form_loaded(self) -> ContactsPage:
        logger.info("Waiting for Contact create form to load")
        deadline = time.time() + self.config.sugar_load_timeout
        while time.time() < deadline:
            current_hash = self.driver.execute_script("return location.hash || ''").lower()
            if "contacts/create" in current_hash and self.is_visible_quick(self.FIRST_NAME):
                return self
            self.wait_for_sugar_loading_overlay_gone(context="contact create form fields")
            time.sleep(0.1)
        self.wait_for_sugar_app_ready(context="contact create form fields")
        self.wait.until_visible(self.FIRST_NAME)
        return self

    def click_create(self) -> ContactsPage:
        logger.info("Clicking Create on Contacts listview")
        for locator in self.CREATE_BUTTON_LOCATORS:
            if self.click_if_visible_quick(locator):
                logger.info("Clicked Create using locator: %s", locator)
                self.wait_until_create_form_loaded()
                return self

        for locator in self.CREATE_BUTTON_LOCATORS:
            try:
                self.click_with_fallback(locator)
                logger.info("Clicked Create using locator: %s", locator)
                self.wait_until_create_form_loaded()
                return self
            except Exception:
                continue

        raise RuntimeError("Could not find Create button on Contacts listview")

    def open_create_form(self) -> ContactsPage:
        self.open_contacts_listview()
        self.click_create()
        return self

    def _field_by_label(self, label: str) -> tuple[str, str]:
        xpath = (
            f"//*[contains(normalize-space(.), '{label}')]"
            f"/ancestor::div[contains(@class,'field') or contains(@class,'record-cell')][1]"
        )
        return (By.XPATH, xpath)

    def scroll_to_field_by_label(self, label: str) -> None:
        locator = self._field_by_label(label)
        element = self.wait.until_present(locator)
        self.scroll_to_element(element)

    def select_dropdown_by_label(self, label: str, option_text: str) -> None:
        logger.info("Selecting '%s' for '%s'", option_text, label)
        self.scroll_to_field_by_label(label)
        field_xpath = self._field_by_label(label)[1]

        trigger_locators = (
            (By.XPATH, f"{field_xpath}//a[contains(@class,'select2-choice')]"),
            (By.XPATH, f"{field_xpath}//span[contains(@class,'select2-chosen')]"),
            (By.XPATH, f"{field_xpath}//select"),
            (By.XPATH, f"{field_xpath}//div[contains(@class,'dropdown')]"),
            (By.XPATH, f"{field_xpath}//input[contains(@class,'select2-input')]"),
        )
        opened = False
        for trigger in trigger_locators:
            try:
                self.click_with_fallback(trigger)
                opened = True
                break
            except Exception:
                continue

        if not opened:
            raise RuntimeError(f"Could not open dropdown for field '{label}'")

        option_locators = (
            (By.XPATH, f"//div[contains(@class,'select2-drop')]//li[contains(normalize-space(.), '{option_text}')]"),
            (
                By.XPATH,
                f"//li[contains(@class,'select2-result') and contains(normalize-space(.), '{option_text}')]",
            ),
            (By.XPATH, f"//option[normalize-space()='{option_text}']"),
            (By.XPATH, f"//*[contains(@class,'dropdown-menu')]//a[contains(normalize-space(.), '{option_text}')]"),
        )
        for option in option_locators:
            if self.click_if_visible_quick(option):
                return
            try:
                self.click_with_fallback(option)
                return
            except Exception:
                continue

        raise RuntimeError(f"Could not select '{option_text}' for field '{label}'")

    def enter_first_name(self, value: str) -> ContactsPage:
        logger.info("Entering First name: %s", value)
        self.type_text(self.FIRST_NAME, value)
        return self

    def enter_last_name(self, value: str) -> ContactsPage:
        logger.info("Entering Last name: %s", value)
        self.type_text(self.LAST_NAME, value)
        return self

    def enter_email_address(self, value: str) -> ContactsPage:
        logger.info("Entering Email Address: %s", value)
        self.scroll_to_field_by_label("Email Address")
        self.type_text(self.EMAIL, value)
        return self

    def fill_create_form(self, contact: dict) -> ContactsPage:
        self.enter_first_name(contact["first_name"])
        self.enter_last_name(contact["last_name"])
        self.select_dropdown_by_label(
            "Correspondence Language",
            contact["correspondence_language"],
        )
        self.enter_email_address(contact["email"])
        self.scroll_to_field_by_label("Gender")
        self.select_dropdown_by_label("Gender", contact["gender"])
        return self

    def fill_contact_details(self, contact: dict) -> ContactsPage:
        return self.fill_create_form(contact)

    def create_contact_and_open_detail(self, contact: dict | None = None) -> ContactsPage:
        """
        End-to-end contact create flow:
        open listview → create → fill form → save → open detail view.
        Contact data is loaded from test_data/contacts.json when not provided.
        """
        contact_data = contact or load_json("contacts.json")[0]
        logger.info(
            "Running contact create flow for %s %s",
            contact_data.get("first_name"),
            contact_data.get("last_name"),
        )

        if not (
            "contacts/create" in self._current_hash().lower()
            and self.is_visible_quick(self.FIRST_NAME)
        ):
            self.open_create_form_direct()
        self.fill_create_form(contact_data)
        self.save()
        self._open_detail_after_save(
            contact_data["first_name"],
            contact_data["last_name"],
        )
        return self

    def ensure_contact_detail_open(
        self, first_name: str, last_name: str
    ) -> ContactsPage:
        """Open contact detail view without creating a new record."""
        if self.is_detail_view_loaded(first_name, last_name, quick=True):
            logger.info("Contact detail view already open for %s %s", first_name, last_name)
            return self
        return self.open_latest_contact_detail(
            first_name,
            last_name,
            post_save_done=True,
        )

    def click_save(self) -> ContactsPage:
        logger.info("Clicking Save on Contact create form")
        self.wait_for_page_ready()

        try:
            save_button = self.wait.until_clickable(self.SAVE_BUTTON)
            self.scroll_to_element(save_button)
            try:
                save_button.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", save_button)
            logger.info("Clicked Save using locator: %s", self.SAVE_BUTTON)
            self.wait_for_page_ready()
            return self
        except Exception:
            logger.debug("Primary Save locator failed — trying fallbacks")

        for locator in self.SAVE_BUTTON_LOCATORS[1:]:
            try:
                self.click_with_fallback(locator)
                logger.info("Clicked Save using locator: %s", locator)
                self.wait_for_page_ready()
                return self
            except Exception:
                continue

        raise RuntimeError("Could not find Save button on Contact create form")

    def _click_ignore_duplicate_and_save_if_present(self) -> None:
        """Click duplicate override when Sugar shows it after the first Save."""
        logger.info("Checking for 'Ignore Duplicate and Save' button")
        duplicate_wait = min(self.config.explicit_wait, 4)
        deadline = time.time() + duplicate_wait
        while time.time() < deadline:
            for locator in self.IGNORE_DUPLICATE_SAVE_LOCATORS:
                if self.is_visible_quick(locator):
                    self.click_with_fallback(locator)
                    logger.info("Clicked 'Ignore Duplicate and Save' using locator: %s", locator)
                    self.wait_for_sugar_loading_overlay_gone()
                    return

            if "contacts/create" not in self._current_hash().lower():
                logger.info("Save completed without duplicate prompt")
                return

            time.sleep(0.05)

        logger.info("'Ignore Duplicate and Save' button not shown — continuing")

    def save(self) -> ContactsPage:
        self.click_save()
        self._click_ignore_duplicate_and_save_if_present()
        ModalDialog(self.driver, self.config).wait_until_closed()
        self._wait_for_post_save_navigation()
        return self

    def _wait_for_post_save_navigation(self) -> str | None:
        """Wait until Sugar leaves the create route after save. Returns contact ID if seen."""
        route_hash = self._current_hash().lower()
        if "contacts/create" not in route_hash:
            return self._extract_contact_id_from_hash()

        logger.info("Waiting for post-save navigation")
        contact_id: str | None = None
        deadline = time.time() + self.config.explicit_wait
        while time.time() < deadline:
            contact_id = self._extract_contact_id_from_hash() or contact_id
            route_hash = self._current_hash().lower()
            if "contacts/create" not in route_hash:
                self.wait_for_sugar_loading_overlay_gone()
                return contact_id or self._extract_contact_id_from_hash()
            time.sleep(0.05)
        raise TimeoutError("Contact save did not complete — still on create route")

    def _open_detail_after_save(self, first_name: str, last_name: str) -> ContactsPage:
        """Open saved contact detail after save (handles Home redirect and Contacts listview)."""
        logger.info("Opening contact detail after save: %s %s", first_name, last_name)
        contact_id = self._extract_contact_id_from_hash()
        deadline = time.time() + self.config.explicit_wait

        while time.time() < deadline:
            self.wait_for_sugar_loading_overlay_gone()
            contact_id = self._extract_contact_id_from_hash() or contact_id

            if contact_id:
                return self._open_contact_detail_by_id(contact_id, first_name, last_name)

            if self.is_detail_view_loaded(first_name, last_name, quick=True):
                return self

            if self._is_detail_route():
                return self.wait_until_detail_view_loaded(first_name, last_name)

            if self._is_listview_route():
                if self._is_contact_row_visible(first_name, last_name):
                    self._click_latest_contact_link(first_name, last_name)
                    return self.wait_until_detail_view_loaded(first_name, last_name)
                time.sleep(0.05)
                continue

            if self._is_home_route() or not self._current_hash().startswith("#Contacts"):
                logger.info(
                    "Post-save redirect detected on %s — opening Contacts listview",
                    self._current_hash() or "(empty hash)",
                )
                self._navigate_to_contacts_listview_fast()
                continue

            time.sleep(0.05)

        raise TimeoutError(
            f"Contact detail view did not open after save for {first_name} {last_name}"
        )

    def _navigate_to_url(self, url: str) -> None:
        if self.config.application_host in self.driver.current_url:
            self.driver.execute_script("window.location.href = arguments[0];", url)
        else:
            self.driver.get(url)

    def _is_home_route(self) -> bool:
        return self._current_hash().startswith("#Home")

    def _extract_contact_id_from_hash(self) -> str | None:
        route_hash = self._current_hash()
        if not route_hash.startswith("#Contacts/"):
            return None
        if "create" in route_hash.lower():
            return None
        remainder = route_hash[len("#Contacts/") :].strip("/").split("/")[0]
        return remainder or None

    def _navigate_to_contacts_listview_fast(self) -> ContactsPage:
        """Open Contacts listview when Sugar redirects elsewhere (e.g. Home) after save."""
        if self._is_listview_ready():
            return self

        logger.info("Navigating to Contacts listview: %s", self.contacts_listview_url)
        self._navigate_to_url(self.contacts_listview_url)
        self.wait_for_sugar_loading_overlay_gone()

        deadline = time.time() + self.config.explicit_wait
        while time.time() < deadline:
            if self._is_listview_ready():
                return self
            if self._is_listview_route() and self.is_visible_quick(self.CREATE_BUTTON_LOCATORS[0]):
                return self
            time.sleep(0.05)

        return self.wait_until_listview_loaded()

    def _open_contact_detail_by_id(
        self, contact_id: str, first_name: str, last_name: str
    ) -> ContactsPage:
        detail_url = f"{self.config.application_url.rstrip('/')}#Contacts/{contact_id}"
        logger.info("Opening contact detail by ID: %s", contact_id)
        self._navigate_to_url(detail_url)
        self.wait_for_sugar_loading_overlay_gone()
        return self.wait_until_detail_view_loaded(first_name, last_name)

    def _current_hash(self) -> str:
        return self.driver.execute_script("return location.hash || ''")

    def _is_listview_route(self) -> bool:
        route_hash = self._current_hash()
        if route_hash in ("#Contacts", "#Contacts/"):
            return True
        if not route_hash.startswith("#Contacts"):
            return False
        if "create" in route_hash.lower():
            return False
        remainder = route_hash[len("#Contacts") :].strip("/")
        return remainder == ""

    def _is_detail_route(self) -> bool:
        route_hash = self._current_hash()
        if not route_hash.startswith("#Contacts/"):
            return False
        if "create" in route_hash.lower():
            return False
        remainder = route_hash[len("#Contacts/") :].strip("/")
        return bool(remainder)

    def _latest_contact_link_locators(
        self, first_name: str, last_name: str
    ) -> tuple[tuple[str, str], ...]:
        row_match = (
            f"*[(self::tr or contains(@class,'row'))"
            f"][.//*[contains(normalize-space(.), '{first_name}')] "
            f"and .//*[contains(normalize-space(.), '{last_name}')]]"
        )
        return (
            (
                By.XPATH,
                f"(//div[contains(@class,'flex-list-view')]//{row_match}"
                f"//a[contains(@href,'#Contacts/')])[1]",
            ),
            (
                By.XPATH,
                f"(//div[contains(@class,'flex-list-view')]//a[contains(@href,'#Contacts/')"
                f" and contains(normalize-space(.), '{first_name}')])[1]",
            ),
            (
                By.XPATH,
                f"(//table//tbody/{row_match}//a[contains(@href,'#Contacts/')])[1]",
            ),
            (
                By.XPATH,
                f"(//div[contains(@class,'flex-list-view')]//tr[1]"
                f"//a[contains(@href,'#Contacts/')])[1]",
            ),
            (
                By.XPATH,
                f"(//div[contains(@class,'list-view')]//a[contains(@href,'#Contacts/')"
                f" and contains(normalize-space(.), '{first_name}')])[1]",
            ),
            (
                By.XPATH,
                f"(//tr[1]//a[contains(@href,'#Contacts/')"
                f" and contains(normalize-space(.), '{first_name}')])[1]",
            ),
            (
                By.XPATH,
                f"(//a[contains(@href,'#Contacts/')"
                f" and contains(normalize-space(.), '{first_name}')])[1]",
            ),
        )

    def _is_contact_row_visible(self, first_name: str, last_name: str) -> bool:
        return bool(
            self.driver.execute_script(
                """
                const firstName = arguments[0];
                const lastName = arguments[1];
                const rowSelectors = [
                  '.flex-list-view tr',
                  '.flex-list-view .flex-list-view-row',
                  '.flex-list-view [class*="row"]',
                  '.list-view tr',
                  'table.dataTable tbody tr',
                ];
                const rows = rowSelectors.flatMap((selector) => [...document.querySelectorAll(selector)]);
                for (const row of rows) {
                  const text = (row.textContent || '').replace(/\\s+/g, ' ').trim();
                  if (!text.includes(firstName)) continue;
                  if (lastName && !text.includes(lastName)) continue;
                  if (row.offsetParent !== null) return true;
                }
                const links = [...document.querySelectorAll("a[href*='#Contacts/']")];
                return links.some(
                  (link) =>
                    link.offsetParent !== null &&
                    (link.textContent || '').includes(firstName)
                );
                """,
                first_name,
                last_name,
            )
        )

    def _click_contact_row_via_js(self, first_name: str, last_name: str) -> bool:
        clicked = self.driver.execute_script(
            """
            const firstName = arguments[0];
            const lastName = arguments[1];
            const rowSelectors = [
              '.flex-list-view tr',
              '.flex-list-view .flex-list-view-row',
              '.flex-list-view [class*="row"]',
              '.list-view tr',
              'table.dataTable tbody tr',
            ];
            const rows = rowSelectors.flatMap((selector) => [...document.querySelectorAll(selector)]);
            for (const row of rows) {
              const text = (row.textContent || '').replace(/\\s+/g, ' ').trim();
              if (!text.includes(firstName)) continue;
              if (lastName && !text.includes(lastName)) continue;
              const link = row.querySelector("a[href*='#Contacts/']");
              if (link) {
                link.scrollIntoView({ block: 'center', inline: 'nearest' });
                link.click();
                return true;
              }
              row.scrollIntoView({ block: 'center', inline: 'nearest' });
              row.click();
              return true;
            }
            const links = [...document.querySelectorAll("a[href*='#Contacts/']")];
            const match = links.find((link) => (link.textContent || '').includes(firstName));
            if (match) {
              match.scrollIntoView({ block: 'center', inline: 'nearest' });
              match.click();
              return true;
            }
            return false;
            """,
            first_name,
            last_name,
        )
        return bool(clicked)

    def _wait_for_contact_link_clickable(self, first_name: str, last_name: str) -> None:
        """Wait until a listview contact row/link is ready to click."""
        self.wait_for_sugar_loading_overlay_gone()
        deadline = time.time() + self.config.explicit_wait
        while time.time() < deadline:
            if self._is_contact_row_visible(first_name, last_name):
                return
            for locator in self._latest_contact_link_locators(first_name, last_name):
                if self.is_visible_quick(locator):
                    return
            time.sleep(0.05)
        raise TimeoutError(
            f"Contact link for '{first_name} {last_name}' did not appear in listview"
        )

    def _click_latest_contact_link(self, first_name: str, last_name: str) -> None:
        self.wait_for_sugar_loading_overlay_gone()
        if self._click_contact_row_via_js(first_name, last_name):
            logger.info("Clicked latest contact row via JavaScript")
            return

        for locator in self._latest_contact_link_locators(first_name, last_name):
            if self.click_if_visible_quick(locator):
                logger.info("Clicked latest contact link using locator: %s", locator)
                return
            try:
                self.click_with_fallback(locator)
                logger.info("Clicked latest contact link using locator: %s", locator)
                return
            except Exception:
                continue
        raise RuntimeError(
            f"Could not click latest contact link for '{first_name} {last_name}'"
        )

    def wait_until_detail_view_loaded(self, first_name: str, last_name: str) -> ContactsPage:
        logger.info("Waiting for Contact detail view: %s %s", first_name, last_name)
        deadline = time.time() + self.config.sugar_load_timeout
        while time.time() < deadline:
            if self.is_detail_view_loaded(first_name, last_name, quick=True):
                return self
            if self.is_detail_view_loaded(first_name, last_name):
                return self
            self.wait_for_sugar_loading_overlay_gone(context="contact detail view")
            time.sleep(0.1)
        raise TimeoutError(
            f"Contact detail view did not load for {first_name} {last_name}"
        )

    def open_latest_contact_detail(
        self,
        first_name: str,
        last_name: str,
        *,
        post_save_done: bool = False,
    ) -> ContactsPage:
        """Open detail view for the saved contact from listview or verify existing detail view."""
        if not post_save_done and "contacts/create" in self._current_hash().lower():
            self._wait_for_post_save_navigation()

        if self.is_detail_view_loaded(first_name, last_name, quick=True):
            logger.info("Contact detail view already open for %s %s", first_name, last_name)
            return self

        if self._is_detail_route():
            logger.info("Detail route detected after save — waiting for header")
            return self.wait_until_detail_view_loaded(first_name, last_name)

        logger.info("Opening latest contact detail from listview: %s %s", first_name, last_name)
        self.wait_for_sugar_loading_overlay_gone()
        if self._is_home_route() or not self._current_hash().startswith("#Contacts"):
            self._navigate_to_contacts_listview_fast()
        elif not self._is_listview_ready():
            self.wait_until_listview_loaded()
        self._wait_for_contact_link_clickable(first_name, last_name)
        self._click_latest_contact_link(first_name, last_name)
        return self.wait_until_detail_view_loaded(first_name, last_name)

    def is_detail_view_loaded(
        self, first_name: str, last_name: str, *, quick: bool = False
    ) -> bool:
        if not self._is_detail_route():
            return False

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
                f"//*[contains(@class,'headerpane') or contains(@class,'record-label') "
                f"or contains(@class,'record-name')]"
                f"//*[contains(normalize-space(.), '{first_name}')]",
            ),
            (
                By.XPATH,
                f"//*[contains(normalize-space(.), '{first_name}') "
                f"and contains(normalize-space(.), '{last_name}')]",
            ),
        )
        timeout = self.config.quick_poll_timeout if quick else 3
        return any(self.is_visible(locator, timeout=timeout) for locator in header_locators)

    def is_listview_loaded(self) -> bool:
        return self.is_visible(self.LISTVIEW_HEADER) and self.is_visible(self.LISTVIEW_TABLE)

    def is_create_form_visible(self) -> bool:
        current_hash = self.driver.execute_script("return location.hash || ''").lower()
        if "contacts/create" in current_hash:
            return True
        return self.is_visible(self.FIRST_NAME)

    def is_record_saved(self) -> bool:
        route_hash = self._current_hash().lower()
        if "contacts/create" in route_hash:
            return False
        if route_hash in ("#contacts", "#contacts/"):
            return True
        if route_hash.startswith("#contacts/"):
            remainder = route_hash[len("#contacts/") :].strip("/")
            return bool(remainder) and "create" not in remainder
        return False
