"""Lead module — create an application from the lead detail view."""

from __future__ import annotations

import pytest

from core.base_test import BaseTest
from pages.leads_page import LeadsPage
from utils.data_loader import load_json


@pytest.mark.applications
@pytest.mark.smoke
class TestCreateApplication(BaseTest):
    def test_create_application_from_lead_detail(self, suite_credit_request_page):
        """
        1. Reuse the suite lead detail view (Credit Request panel already saved —
           'suite_credit_request_page' waits for the save round-trip to actually
           finish before handing back control, so the toolbar is guaranteed to be
           back in its normal Edit/Actions state here)
        2. Scroll up to the 'Create Application' quick action button and click it
        3. On the Create Application view:
           - Select Provider
           - Enter BANK-now ID
           - Scroll to the 'Applied with the Bank' section
           - Enter Credit Amount
           - Select Credit Duration
           - Select Interest Rate
           - Check the SOKO checkbox
           - Enter Explanation SOKO (only appears once SOKO is checked)
           - Click Save

        Depends on 'suite_credit_request_page' so this always runs after the
        Credit Request panel test, regardless of test file collection order.
        """
        application_data = load_json("applications.json")[0]
        leads_page = LeadsPage(self.driver, self.config)
        application_page = leads_page.click_create_application()
        application_page.create_application(
            provider=application_data["provider"],
            bank_now_id=application_data["bank_now_id"],
            credit_amount=application_data["credit_amount"],
            credit_duration=application_data["credit_duration"],
            interest_rate=application_data["interest_rate"],
            explanation_soko=application_data.get("explanation_soko"),
        )
