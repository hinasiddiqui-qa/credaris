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
    drv = DriverFactory.create_driver(app_config)
    yield drv
    if app_config.keep_browser_open:
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
def application_ready(driver, app_config: AppConfig, test_user):
    """Prerequisite 1 — Initial Setup (see setup/initial_setup_prerequisite.py)."""
    return run_initial_setup(driver, app_config, test_user)


@pytest.fixture(scope="session")
def sugar_crm_ready(driver, app_config: AppConfig, application_ready, sugar_user):
    """Prerequisite 2 — Sugar CRM login (see login/sugar_login_prerequisite.py)."""
    return run_sugar_login_prerequisite(driver, app_config, application_ready, sugar_user)


@pytest.fixture(scope="session")
def suite_contact_page(app_config: AppConfig, sugar_crm_ready):
    """
    Prerequisite 3 — shared suite contact for module tests.

    Create exactly one contact for the whole pytest session.
    Contact and lead tests reuse this record instead of creating duplicates.
    """
    logger.info("Creating suite contact (once per test session)")
    sugar_crm_ready.wait_for_sugar_app_ready(context="before suite contact create")
    sugar_crm_ready.create_contact_and_open_detail()
    return sugar_crm_ready


@pytest.fixture(scope="session")
def initial_setup_complete(application_ready):
    return application_ready


@pytest.fixture(scope="session")
def prepared_app(application_ready):
    return application_ready


@pytest.fixture(scope="session")
def authenticated_session(sugar_crm_ready):
    return sugar_crm_ready


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
