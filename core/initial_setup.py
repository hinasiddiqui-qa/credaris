"""
Initial Setup workflow — delegates to SessionOrchestrator for Scenario 1 / 2 routing.
"""

from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver

from core.config_loader import AppConfig
from core.session_orchestrator import SessionOrchestrator
from pages.application_page import ApplicationPage
from utils.logger import get_logger

logger = get_logger(__name__)


class InitialSetup:
    def __init__(self, driver: WebDriver, config: AppConfig):
        self.driver = driver
        self.config = config
        self.orchestrator = SessionOrchestrator(driver, config)

    def run(self, user: dict | None = None) -> ApplicationPage:
        return self.orchestrator.run(user)

    def prepare_browser_environment(self) -> None:
        logger.warning(
            "prepare_browser_environment() is deprecated — use run(user) for full Initial Check"
        )
        self.orchestrator.browser_env.dismiss_restore_pages_popup()

    def navigate_and_verify_home(self, user: dict | None = None) -> ApplicationPage:
        return self.run(user)
