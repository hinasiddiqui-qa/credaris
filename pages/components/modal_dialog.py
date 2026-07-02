"""Reusable modal dialog component."""

from __future__ import annotations

import time

from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class ModalDialog(BasePage):
    MODAL = (By.CSS_SELECTOR, ".modal, .dialog, [role='dialog']")

    def is_open(self) -> bool:
        return self.is_visible_quick(self.MODAL)

    def wait_until_closed(self) -> None:
        deadline = time.time() + self.config.quick_poll_timeout
        while time.time() < deadline:
            if not self.is_visible_quick(self.MODAL):
                return
            time.sleep(0.05)
