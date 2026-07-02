"""One-time application setup before test execution."""

from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver

from core.config_loader import AppConfig
from core.initial_setup import InitialSetup
from pages.application_page import ApplicationPage


class AppSetup:
    def __init__(self, driver: WebDriver, config: AppConfig):
        self.driver = driver
        self.config = config
        self.initial_setup = InitialSetup(driver, config)

    def launch_and_verify_home(self, user: dict | None = None) -> ApplicationPage:
        return self.initial_setup.run(user)
