"""Manage authenticated browser sessions across test runs."""

from __future__ import annotations

import os

from selenium.webdriver.remote.webdriver import WebDriver

from core.config_loader import AppConfig
from core.session_orchestrator import SessionOrchestrator
from pages.application_page import ApplicationPage
from utils.logger import get_logger
from utils.session_storage import SessionStorage

logger = get_logger(__name__)


class SessionManager:
    def __init__(self, driver: WebDriver, config: AppConfig, mfa_timeout: int | None = None):
        self.driver = driver
        self.config = config
        self.mfa_timeout = mfa_timeout or int(os.getenv("MFA_WAIT_TIMEOUT", "600"))
        self.storage = SessionStorage(config)
        self.orchestrator = SessionOrchestrator(driver, config, mfa_timeout=self.mfa_timeout)

    def ensure_authenticated(self, user: dict) -> ApplicationPage:
        return self.orchestrator.run(user)

    def clear_session(self) -> None:
        self.storage.delete_cookies()
        logger.info("Saved cookie file removed. Delete the Chrome profile folder to fully reset.")
