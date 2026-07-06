"""Lead module — create an application from the lead detail view."""

from __future__ import annotations

import pytest

from core.base_test import BaseTest


@pytest.mark.applications
@pytest.mark.smoke
class TestCreateApplication(BaseTest):
    def test_create_application_from_lead_detail(self, suite_application_page):
        """
        1. Reuse the suite lead detail view (Credit Request panel already saved —
           'suite_credit_request_page' waits for the save round-trip to actually
           finish before handing back control)
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
           - Select Provider status: Granted
           - Click Save

        The actual flow is performed once per session by the shared
        'suite_application_page' fixture — this test exercises it, so the
        Create Contract test can safely depend on it without recreating the
        application or caring about file order.
        """
