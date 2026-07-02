"""Base page object with shared Selenium actions."""

from __future__ import annotations

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from core.config_loader import AppConfig, load_config
from utils.wait_helpers import WaitHelpers


class BasePage:
    def __init__(self, driver: WebDriver, config: AppConfig | None = None):
        self.driver = driver
        self.config = config or load_config()
        self.wait = WaitHelpers(driver, self.config.explicit_wait)
        self.base_url = self.config.base_url.rstrip("/")

    def open(self, path: str = "/") -> BasePage:
        url = f"{self.base_url}{path}"
        self.driver.get(url)
        return self

    def click(self, locator: tuple[str, str]) -> None:
        self.wait.until_clickable(locator).click()

    def type_text(self, locator: tuple[str, str], value: str) -> None:
        element = self.wait.until_visible(locator)
        element.clear()
        element.send_keys(value)

    def get_text(self, locator: tuple[str, str]) -> str:
        return self.wait.until_visible(locator).text.strip()

    def is_visible(self, locator: tuple[str, str], timeout: int | None = None) -> bool:
        poll = timeout if timeout is not None else self.config.explicit_wait
        return self.wait.is_visible(locator, timeout=poll)

    def is_visible_quick(self, locator: tuple[str, str]) -> bool:
        """Fast check for optional/transient UI (popup, tab) — avoids long timeouts."""
        return self.wait.is_visible(locator, timeout=self.config.quick_poll_timeout)

    def click_if_visible_quick(self, locator: tuple[str, str]) -> bool:
        if self.is_visible_quick(locator):
            self.click(locator)
            return True
        return False

    def scroll_to_element(self, element: WebElement) -> None:
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
            element,
        )

    def click_with_fallback(self, locator: tuple[str, str]) -> None:
        element = self.wait.until_clickable(locator)
        self.scroll_to_element(element)
        try:
            element.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", element)

    def wait_for_url_contains(self, fragment: str) -> bool:
        return self.wait.until_url_contains(fragment)

    def wait_for_page_ready(self) -> None:
        self.wait.until_document_ready()
        try:
            self.wait.until_angular_stable()
        except Exception:
            pass

    def wait_for_sugar_loading_overlay_gone(self) -> None:
        """Wait until Sugar's blocking Loading overlay/modal is dismissed."""
        deadline = time.time() + self.config.explicit_wait
        while time.time() < deadline:
            loading_visible = self.driver.execute_script(
                """
                const nodes = [...document.querySelectorAll(
                  '.loading, .modal, [class*="loading"], .block-ui, .drawer.loading, .alert-loading'
                )];
                return nodes.some((node) => {
                  if (node.offsetParent === null) return false;
                  const text = (node.textContent || '').replace(/\\s+/g, ' ').trim();
                  return text.includes('Loading') || node.classList.contains('loading');
                });
                """
            )
            if not loading_visible:
                return
            time.sleep(0.1)

    def find(self, locator: tuple[str, str]) -> WebElement:
        return self.wait.until_visible(locator)

    @staticmethod
    def by_id(element_id: str) -> tuple[str, str]:
        return (By.ID, element_id)

    @staticmethod
    def by_css(selector: str) -> tuple[str, str]:
        return (By.CSS_SELECTOR, selector)

    @staticmethod
    def by_xpath(xpath: str) -> tuple[str, str]:
        return (By.XPATH, xpath)
