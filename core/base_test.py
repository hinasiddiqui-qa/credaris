"""Shared pytest base class for all test classes."""

from __future__ import annotations

import pytest

from core.config_loader import AppConfig


class BaseTest:
    driver = None
    config: AppConfig | None = None

    @pytest.fixture(autouse=True)
    def _inject_driver(self, driver, app_config):
        self.driver = driver
        self.config = app_config

    def login_to_sugar_crm(self, sugar_user: dict) -> None:
        """
        Sugar CRM login steps (credentials from config/config.properties):
        1. Enter username
        2. Enter password
        3. Click Login button
        4. Open Contacts listview directly via #Contacts URL
        """
        from login.sugar_login_prerequisite import login_to_sugar_crm

        login_to_sugar_crm(self.driver, self.config, sugar_user)
