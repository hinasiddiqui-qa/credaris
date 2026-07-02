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

    - Scenario 2: restore saved session and open Sugar CRM directly
    - Scenario 1: ZPA / Microsoft SSO login, then open Sugar CRM
    - Verify application is ready and browser is on the Sugar CRM host
    """
    try:
        application = SessionOrchestrator(driver, app_config).run(test_user)
    except RuntimeError as exc:
        pytest.skip(str(exc))

    assert application.is_accessible(), (
        "Initial setup did not complete — Sugar CRM is not reachable "
        "(check ZPA/SSO access and application URL)"
    )
    assert app_config.application_host in driver.current_url, (
        f"Expected Sugar CRM host '{app_config.application_host}' in current URL"
    )
    logger.info("Initial setup prerequisite complete")
    return application
