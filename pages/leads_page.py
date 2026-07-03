"""Credaris Sugar CRM leads module page."""

from __future__ import annotations

import time

from selenium.webdriver.common.by import By

from pages.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class LeadsPage(BasePage):
    LISTVIEW_HEADER = (
        By.XPATH,
        "//*[contains(normalize-space(.), 'Leads') and (contains(., 'of') or contains(@class, 'module-title') or contains(@class, 'record-label'))]",
    )
    LISTVIEW_TABLE = (
        By.CSS_SELECTOR,
        ".flex-list-view, .list-view, table.dataTable, .table-responsive",
    )
    # Quick Actions widget on Lead detail view — <a id="lq_create_task" title="Create Task">
    CREATE_TASK_BUTTON_LOCATORS = (
        (By.CSS_SELECTOR, "#lq_create_task"),
        (By.CSS_SELECTOR, "a[title='Create Task']"),
        (By.XPATH, "//a[@id='lq_create_task']"),
        (By.XPATH, "//a[@title='Create Task']"),
        (By.XPATH, "//a[normalize-space()='Create Task']"),
    )
    # Quick Actions widget on Lead detail view — <a id="lq_create_application" title="Create Application">
    CREATE_APPLICATION_BUTTON_LOCATORS = (
        (By.CSS_SELECTOR, "#lq_create_application"),
        (By.CSS_SELECTOR, "a[title='Create Application']"),
        (By.XPATH, "//a[@id='lq_create_application']"),
        (By.XPATH, "//a[@title='Create Application']"),
        (By.XPATH, "//a[normalize-space()='Create Application']"),
    )

    @property
    def leads_listview_url(self) -> str:
        return f"{self.config.application_url.rstrip('/')}#Leads"

    def _current_hash(self) -> str:
        return self.driver.execute_script("return location.hash || ''")

    def _is_listview_route(self) -> bool:
        route_hash = self._current_hash()
        if route_hash in ("#Leads", "#Leads/"):
            return True
        if not route_hash.startswith("#Leads"):
            return False
        if "create" in route_hash.lower():
            return False
        remainder = route_hash[len("#Leads") :].strip("/")
        return remainder == ""

    def _is_detail_route(self) -> bool:
        route_hash = self._current_hash()
        if not route_hash.startswith("#Leads/"):
            return False
        if "create" in route_hash.lower():
            return False
        remainder = route_hash[len("#Leads/") :].strip("/")
        return bool(remainder)

    def _is_listview_ready(self) -> bool:
        return (
            self._is_listview_route()
            and self.is_visible_quick(self.LISTVIEW_HEADER)
            and self.is_visible_quick(self.LISTVIEW_TABLE)
        )

    def open_leads_listview(self) -> LeadsPage:
        """Navigate directly to Leads listview."""
        logger.info("Opening Leads listview via URL: %s", self.leads_listview_url)
        self.wait_for_sugar_loading_overlay_gone()

        if self._is_listview_ready():
            logger.info("Leads listview already open")
            return self

        if self.config.application_host in self.driver.current_url:
            self.driver.execute_script(
                "window.location.href = arguments[0];",
                self.leads_listview_url,
            )
        else:
            self.driver.get(self.leads_listview_url)

        self.wait_for_sugar_loading_overlay_gone()
        self.wait_until_listview_loaded()
        return self

    def wait_until_listview_loaded(self) -> LeadsPage:
        logger.info("Waiting for Leads listview to load")
        if self._is_listview_ready():
            logger.info("Leads listview already loaded")
            return self

        self.wait_for_page_ready()
        deadline = time.time() + self.config.explicit_wait
        while time.time() < deadline:
            if self._is_listview_route():
                break
            time.sleep(0.15)

        self.wait.until_visible(self.LISTVIEW_HEADER)
        self.wait.until_visible(self.LISTVIEW_TABLE)
        return self

    def _latest_lead_link_locators(
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
                f"//a[contains(@href,'#Leads/')])[1]",
            ),
            (
                By.XPATH,
                f"(//div[contains(@class,'flex-list-view')]//a[contains(@href,'#Leads/')"
                f" and contains(normalize-space(.), '{first_name}')])[1]",
            ),
            (
                By.XPATH,
                f"(//table//tbody/{row_match}//a[contains(@href,'#Leads/')])[1]",
            ),
            (
                By.XPATH,
                f"(//div[contains(@class,'flex-list-view')]//tr[1]"
                f"//a[contains(@href,'#Leads/')])[1]",
            ),
            (
                By.XPATH,
                f"(//div[contains(@class,'list-view')]//a[contains(@href,'#Leads/')"
                f" and contains(normalize-space(.), '{first_name}')])[1]",
            ),
            (
                By.XPATH,
                f"(//tr[1]//a[contains(@href,'#Leads/')"
                f" and contains(normalize-space(.), '{first_name}')])[1]",
            ),
            (
                By.XPATH,
                f"(//a[contains(@href,'#Leads/')"
                f" and contains(normalize-space(.), '{first_name}')])[1]",
            ),
        )

    def _is_lead_row_visible(self, first_name: str, last_name: str) -> bool:
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
                const links = [...document.querySelectorAll("a[href*='#Leads/']")];
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

    def _click_lead_row_via_js(self, first_name: str, last_name: str) -> bool:
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
              const link = row.querySelector("a[href*='#Leads/']");
              if (link) {
                link.scrollIntoView({ block: 'center', inline: 'nearest' });
                link.click();
                return true;
              }
              row.scrollIntoView({ block: 'center', inline: 'nearest' });
              row.click();
              return true;
            }
            const links = [...document.querySelectorAll("a[href*='#Leads/']")];
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

    def _wait_for_lead_link_clickable(self, first_name: str, last_name: str) -> None:
        self.wait_for_sugar_loading_overlay_gone()
        deadline = time.time() + self.config.explicit_wait
        while time.time() < deadline:
            if self._is_lead_row_visible(first_name, last_name):
                return
            for locator in self._latest_lead_link_locators(first_name, last_name):
                if self.is_visible_quick(locator):
                    return
            time.sleep(0.15)
        raise TimeoutError(
            f"Lead link for '{first_name} {last_name}' did not appear in listview"
        )

    def _click_latest_lead_link(self, first_name: str, last_name: str) -> None:
        self.wait_for_sugar_loading_overlay_gone()
        if self._click_lead_row_via_js(first_name, last_name):
            logger.info("Clicked latest lead row via JavaScript")
            return

        for locator in self._latest_lead_link_locators(first_name, last_name):
            if self.click_if_visible_quick(locator):
                logger.info("Clicked latest lead link using locator: %s", locator)
                return
            try:
                self.click_with_fallback(locator)
                logger.info("Clicked latest lead link using locator: %s", locator)
                return
            except Exception:
                continue
        raise RuntimeError(
            f"Could not click latest lead link for '{first_name} {last_name}'"
        )

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

    def wait_until_detail_view_loaded(self, first_name: str, last_name: str) -> LeadsPage:
        logger.info("Waiting for Lead detail view: %s %s", first_name, last_name)
        deadline = time.time() + self.config.explicit_wait
        while time.time() < deadline:
            if self.is_detail_view_loaded(first_name, last_name, quick=True):
                return self
            if self.is_detail_view_loaded(first_name, last_name):
                return self
            time.sleep(0.15)
        raise TimeoutError(
            f"Lead detail view did not load for {first_name} {last_name}"
        )

    def open_latest_lead_detail(self, first_name: str, last_name: str) -> LeadsPage:
        """Open detail view for the converted lead from the Leads listview."""
        if self.is_detail_view_loaded(first_name, last_name, quick=True):
            logger.info("Lead detail view already open for %s %s", first_name, last_name)
            return self

        logger.info("Opening latest lead detail from listview: %s %s", first_name, last_name)
        self.wait_for_sugar_loading_overlay_gone()
        if not self._is_listview_ready():
            self.wait_until_listview_loaded()
        self._wait_for_lead_link_clickable(first_name, last_name)
        self._click_latest_lead_link(first_name, last_name)
        return self.wait_until_detail_view_loaded(first_name, last_name)

    def open_leads_listview_and_open_latest_lead_detail(
        self, first_name: str, last_name: str
    ) -> LeadsPage:
        self.open_leads_listview()
        self.open_latest_lead_detail(first_name, last_name)
        return self

    def click_create_task(self):
        """Click the 'Create Task' quick action on the Lead detail view."""
        from pages.task_create_page import TaskCreatePage

        logger.info("Clicking Create Task quick action on lead detail view")
        self.wait_for_sugar_loading_overlay_gone(context="lead detail quick actions")

        for locator in self.CREATE_TASK_BUTTON_LOCATORS:
            if self.click_if_visible_quick(locator):
                logger.info("Clicked Create Task using locator: %s", locator)
                break
            try:
                self.click_with_fallback(locator)
                logger.info("Clicked Create Task using locator: %s", locator)
                break
            except Exception:
                continue
        else:
            raise RuntimeError("Could not find Create Task quick action on lead detail view")

        task_page = TaskCreatePage(self.driver, self.config)
        task_page.wait_until_loaded()
        return task_page

    def click_create_application(self) -> LeadsPage:
        """
        Scroll up to and click the 'Create Application' quick action on the Lead detail view.

        Uses find_elements (plural) and clicks the first *visible* match rather than
        relying on find_element/EC locators (which only ever look at the first DOM
        match) — Sugar can render a hidden duplicate of this same quick action
        elsewhere in the DOM, and clicking that silently does nothing.
        """
        logger.info("Clicking Create Application quick action on lead detail view")
        self.wait_for_sugar_loading_overlay_gone(context="lead detail quick actions")

        for by, selector in self.CREATE_APPLICATION_BUTTON_LOCATORS:
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
                logger.info("Clicked Create Application using locator: %s", (by, selector))
                self.wait_for_sugar_loading_overlay_gone(context="after create application click")
                return self

        raise RuntimeError(
            "Could not find a visible Create Application quick action on lead detail view"
        )
