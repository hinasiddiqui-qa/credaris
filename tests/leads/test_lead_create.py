"""Lead module — create lead from contact detail view."""

from __future__ import annotations

import pytest

from core.base_test import BaseTest
from pages.contact_detail_page import ContactDetailPage
from pages.leads_page import LeadsPage
from utils.data_loader import load_json


@pytest.mark.leads
@pytest.mark.smoke
class TestLeadCreate(BaseTest):
    def test_create_lead_from_contact_detail(self, suite_contact_page):
        """
        1. Reuse the suite contact detail view (no second contact create)
        2. Click Actions on contact detail
        3. Click Create Lead from the dropdown
        4. On Choosing Document screen, select Status: 01 - New
        5. Click Merge and Create Lead
        6. Wait for redirect to contact detail view
        7. Open Leads listview by URL
        8. Open the newly created lead detail view
        """
        contact = load_json("contacts.json")[0]
        suite_contact_page.ensure_contact_detail_open(
            contact["first_name"],
            contact["last_name"],
        )
        choosing_document = ContactDetailPage(self.driver, self.config).create_lead_from_contact()
        choosing_document.wait_for_contact_detail_redirect(
            contact["first_name"],
            contact["last_name"],
        )
        LeadsPage(self.driver, self.config).open_leads_listview_and_open_latest_lead_detail(
            contact["first_name"],
            contact["last_name"],
        )
