"""Explicit wait helpers."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class WaitHelpers:
    def __init__(self, driver: WebDriver, timeout: int = 30):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)

    def until_visible(self, locator: tuple[str, str]) -> WebElement:
        return self.wait.until(EC.visibility_of_element_located(locator))

    def until_clickable(self, locator: tuple[str, str]) -> WebElement:
        return self.wait.until(EC.element_to_be_clickable(locator))

    def until_present(self, locator: tuple[str, str]) -> WebElement:
        return self.wait.until(EC.presence_of_element_located(locator))

    def is_visible(self, locator: tuple[str, str], timeout: int | None = None) -> bool:
        wait = WebDriverWait(self.driver, timeout if timeout is not None else self.timeout)
        try:
            wait.until(EC.visibility_of_element_located(locator))
            return True
        except Exception:
            return False

    def until_url_contains(self, fragment: str) -> bool:
        return self.wait.until(EC.url_contains(fragment))

    def until_document_ready(self) -> bool:
        return self.wait.until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

    def until_angular_stable(self) -> bool:
        """Best-effort wait for SPA frameworks to finish initial rendering."""
        script = """
        return (
            document.readyState === 'complete' &&
            (typeof window.getAllAngularTestabilities !== 'function' ||
             window.getAllAngularTestabilities().every(t => t.isStable()))
        );
        """
        return self.wait.until(lambda d: d.execute_script(script))

    @staticmethod
    def by_css(selector: str) -> tuple[str, str]:
        return (By.CSS_SELECTOR, selector)
