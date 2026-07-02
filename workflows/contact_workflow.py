"""Contact module workflows."""

from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver

from core.config_loader import AppConfig, load_config
from pages.contacts_page import ContactsPage
from utils.logger import get_logger

logger = get_logger(__name__)


class ContactWorkflow:
    def __init__(self, driver: WebDriver, config: AppConfig | None = None):
        self.driver = driver
        self.config = config or load_config()

    def open_contacts_and_click_create(self) -> ContactsPage:
        """
        1. Click Contacts (user) icon in sidebar
        2. Wait for Contacts listview to load
        3. Click Create
        """
        logger.info("Workflow: open Contacts listview and click Create")
        page = ContactsPage(self.driver, self.config)
        page.open_contacts_listview()
        page.click_create()
        return page

    def create_contact(self, contact: dict | None = None) -> ContactsPage:
        logger.info("Creating contact via ContactsPage flow")
        page = ContactsPage(self.driver, self.config)
        return page.create_contact_and_open_detail(contact)
