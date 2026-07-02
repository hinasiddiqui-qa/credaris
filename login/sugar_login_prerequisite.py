"""Sugar CRM login prerequisite — authenticate before module tests."""

from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver

from core.config_loader import AppConfig
from pages.application_page import ApplicationPage
from pages.contacts_page import ContactsPage
from pages.sugar_login_page import SugarLoginPage
from utils.logger import get_logger
from utils.session_storage import SessionStorage

logger = get_logger(__name__)


def login_to_sugar_crm(
    driver: WebDriver,
    app_config: AppConfig,
    sugar_user: dict,
) -> ContactsPage:
    """Enter Sugar credentials when needed, then wait for app load before tests."""
    sugar_login = SugarLoginPage(driver, app_config)
    contacts_page = ContactsPage(driver, app_config)

    if sugar_login.is_login_form_visible() or sugar_login.is_displayed():
        sugar_login.login(sugar_user["username"], sugar_user["password"])
        if app_config.reuse_session:
            SessionStorage(app_config).save_session(driver)
    elif contacts_page._is_home_route():
        logger.info("Already logged in on Home — waiting for Sugar to finish loading")
        contacts_page.wait_for_sugar_app_ready(context="existing Home session")
        contacts_page.open_create_form_direct()
        return contacts_page

    contacts_page.wait_for_sugar_app_ready(context="before contact create flow")
    if contacts_page._is_home_route():
        logger.info("Home dashboard loaded — navigating straight to contact create form")
        contacts_page.open_create_form_direct()

    return contacts_page


def run_sugar_login_prerequisite(
    driver: WebDriver,
    app_config: AppConfig,
    application: ApplicationPage,
    sugar_user: dict,
) -> ContactsPage:
    """
    Prerequisite 2 — Sugar CRM login.

    - Enter Sugar username/password from config when login form is shown
    - Click Log In
    - Verify authenticated Sugar session (no Sugar or Microsoft login screens)
    - Leave Home immediately once the page is ready
    """
    logger.info("Running Sugar CRM login prerequisite")
    contacts_page = login_to_sugar_crm(driver, app_config, sugar_user)

    assert application.is_session_active_quick(), "Sugar CRM session is not active"
    assert not application.requires_microsoft_login(), "Microsoft SSO login is still required"
    logger.info("Sugar CRM login prerequisite complete")
    return contacts_page
