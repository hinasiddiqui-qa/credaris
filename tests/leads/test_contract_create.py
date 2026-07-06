"""Lead module — create contract from lead detail view."""

from __future__ import annotations

import pytest

from core.base_test import BaseTest


@pytest.mark.contracts
@pytest.mark.smoke
class TestCreateContract(BaseTest):
    def test_create_contract_from_lead_detail(self, suite_contract_page):
        """
        1. Reuse the suite lead detail view (application already saved —
           'suite_application_page' waits for the save round-trip and redirect
           back to the lead detail view before handing back control)
        2. Click the 'Create Contract' quick action on the lead detail view
        3. On the Create Contract view:
           - Enter Provider Contract Number: 1122098
           - Enter Credit Amount: 45000
           - Enter Interest Rate: 4.5
           - Enter Credit Duration: 48
           - Click Save

        The actual flow is performed once per session by the shared
        'suite_contract_page' fixture — this test exercises it. Depends on
        'suite_application_page' (via the fixture chain) so it always runs after
        the Create Application test, regardless of file collection order.
        """
