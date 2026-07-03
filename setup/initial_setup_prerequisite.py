"""Initial Setup prerequisite — ZPA/SSO and Sugar CRM application readiness."""

from __future__ import annotations

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from core.config_loader import AppConfig
from core.session_orchestrator import SessionOrchestrator
from pages.application_page import ApplicationPage
from utils.logger import get_logger

logger = get_logger(__name__)


def run_initial_setup(
    driver: WebDriver,
    app_config: AppConfig,
    test_user: dict,
) -> ApplicationPage:
    """
    Prerequisite 1 — Initial Setup.

    - Restore saved session when available
    - Open sugar-test directly and wait for elements to load (never zpa-ba)
    - Skip Microsoft SSO when skip.microsoft.login=true (use saved session only)
    """
    try:
        application = SessionOrchestrator(driver, app_config).run(test_user)
    except RuntimeError as exc:
        pytest.skip(str(exc))

    assert app_config.application_host in driver.current_url, (
        f"Expected Sugar CRM host '{app_config.application_host}' in current URL"
    )
    assert not application.requires_microsoft_login(), (
        "Microsoft SSO is required but skip.microsoft.login=true. "
        "Refresh the saved session with scripts/bootstrap_session.py."
    )
    logger.info("Initial setup prerequisite complete")
    return application
