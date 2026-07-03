"""Lead module — Credit Request panel: Legal terms customer date + Credit usage."""

from __future__ import annotations

import pytest

from core.base_test import BaseTest


@pytest.mark.credit_request
@pytest.mark.smoke
class TestCreditRequestPanel(BaseTest):
    def test_set_legal_terms_and_credit_usage(self, suite_credit_request_page):
        """
        1. Reuse the suite lead detail view (opened after the suite task was created)
        2. Scroll to and click the 'Credit Request' tab
        3. Scroll to 'Legal terms customer', click it to open the calendar, select a date
        4. Click 'Credit usage' and select 'Vehicle'
        5. Save the panel

        The actual flow is performed once per session by the shared
        'suite_credit_request_page' fixture (in tests/conftest.py) — this test
        exercises it, so other tests (e.g. Create Application) can safely depend
        on the same fixture without repeating the work or caring about file order.
        """
