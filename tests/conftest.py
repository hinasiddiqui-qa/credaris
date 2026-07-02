"""Pytest fixtures, session reuse, and reporting hooks."""

from __future__ import annotations

import sys

# Avoid creating __pycache__ under tests/ during pytest runs.
sys.dont_write_bytecode = True

from pathlib import Path

import pytest

try:
    import allure
except ImportError:  # pragma: no cover - optional at runtime before install
    allure = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config_loader import AppConfig, load_config
from core.driver_factory import DriverFactory
from login.sugar_login_prerequisite import run_sugar_login_prerequisite
from setup.initial_setup_prerequisite import run_initial_setup
from utils.console_progress import announce
from utils.data_loader import load_json
from utils.logger import get_logger
from utils.screenshot_helper import capture_screenshot

logger = get_logger("credaris.tests")

# Flat Allure suite layout: one module folder -> one readable test name.
ALLURE_SUITE_LAYOUT = {
    "contacts": {
        "parent_suite": "Contacts",
        "title": "Create contact and open detail view",
    },
    "leads": {
        "parent_suite": "Leads",
        "title": "Create lead from contact and open detail view",
    },
}


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    if allure is None:
        return
    for marker_name, labels in ALLURE_SUITE_LAYOUT.items():
        if item.get_closest_marker(marker_name):
            allure.dynamic.parent_suite(labels["parent_suite"])
            allure.dynamic.suite(labels["title"])
            allure.dynamic.title(labels["title"])
            allure.dynamic.feature(labels["parent_suite"])
            return


@pytest.fixture(scope="session")
def app_config() -> AppConfig:
    return load_config()


@pytest.fixture(scope="session")
def driver(app_config: AppConfig):
    announce(
        "Launching Chrome for Credaris automation "
        f"(profile: {app_config.resolved_user_data_dir})"
    )
    announce("If this hangs, close any open Chrome window using the same profile and retry.")
    drv = DriverFactory.create_driver(app_config)
    announce("Chrome launched successfully.")
    yield drv
    if app_config.keep_browser_open:
        announce("KEEP_BROWSER_OPEN is enabled — close Chrome manually when finished.")
        logger.info(
            "KEEP_BROWSER_OPEN is enabled — browser was not closed automatically. "
            "Close the Chrome window manually when finished."
        )
    else:
        drv.quit()


@pytest.fixture(scope="session")
def test_user(app_config: AppConfig):
    """Microsoft SSO credentials — loaded from config/config.properties."""
    return {
        "username": app_config.microsoft_username,
        "password": app_config.microsoft_password,
    }


@pytest.fixture(scope="session")
def sugar_user(app_config: AppConfig):
    """Sugar CRM credentials — loaded from config/config.properties."""
    return {
        "username": app_config.sugar_username,
        "password": app_config.sugar_password,
    }


@pytest.fixture
def sample_contact():
    return load_json("contacts.json")[0]


@pytest.fixture(scope="session")
def session_prerequisites(driver, app_config: AppConfig, test_user, sugar_user):
    """
    Run all prerequisites once before any test:
    1. Initial setup (ZPA / Microsoft SSO)
    2. Sugar CRM login
    3. Shared suite contact create
    """
    announce("Step 1/3 — Initial setup: ZPA / Microsoft SSO / open Sugar CRM")
    application_ready = run_initial_setup(driver, app_config, test_user)

    announce("Step 2/3 — Sugar CRM login")
    contacts_page = run_sugar_login_prerequisite(
        driver, app_config, application_ready, sugar_user
    )

    announce("Step 3/3 — Create shared suite contact (once per session)")
    contacts_page.wait_for_sugar_app_ready(context="before suite contact create")
    contacts_page.create_contact_and_open_detail()
    announce("Session prerequisites complete — starting tests.")
    return contacts_page


@pytest.fixture(scope="session")
def application_ready(session_prerequisites):
    return session_prerequisites


@pytest.fixture(scope="session")
def sugar_crm_ready(session_prerequisites):
    return session_prerequisites


@pytest.fixture(scope="session")
def suite_contact_page(session_prerequisites):
    """Shared Contacts page with suite contact detail already open."""
    return session_prerequisites


@pytest.fixture(scope="session")
def initial_setup_complete(session_prerequisites):
    return session_prerequisites


@pytest.fixture(scope="session")
def prepared_app(session_prerequisites):
    return session_prerequisites


@pytest.fixture(scope="session")
def authenticated_session(session_prerequisites):
    return session_prerequisites


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


@pytest.fixture(autouse=True)
def screenshot_on_failure(request, driver, app_config: AppConfig):
    yield
    report = getattr(request.node, "rep_call", None)
    if report and report.failed and app_config.screenshot_on_failure:
        path = capture_screenshot(driver, request.node.name)
        logger.error("Saved failure screenshot: %s", path)
        if allure is not None:
            allure.attach.file(
                str(path),
                name="Failure screenshot",
                attachment_type=allure.attachment_type.PNG,
            )
