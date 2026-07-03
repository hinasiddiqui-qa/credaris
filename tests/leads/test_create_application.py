"""Lead module — click Create Application quick action from lead detail view."""

from __future__ import annotations

import pytest

from core.base_test import BaseTest
from pages.leads_page import LeadsPage


@pytest.mark.applications
@pytest.mark.smoke
class TestCreateApplication(BaseTest):
    def test_click_create_application(self, suite_credit_request_page):
        """
        1. Reuse the suite lead detail view (Credit Request panel already saved)
        2. Scroll up to the 'Create Application' quick action button
        3. Click it
        4. Scroll up to the 'Create Application' button again and click it once more

        Depends on 'suite_credit_request_page' so this always runs after the
        Credit Request panel test, regardless of test file collection order.
        """
        leads_page = LeadsPage(self.driver, self.config)
        leads_page.click_create_application()
        leads_page.click_create_application()
