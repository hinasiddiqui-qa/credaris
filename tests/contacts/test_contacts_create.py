"""Contacts module — single end-to-end contact create test."""

from __future__ import annotations

import pytest

from core.base_test import BaseTest
from utils.data_loader import load_json


@pytest.mark.contacts
@pytest.mark.smoke
class TestContactsCreate(BaseTest):
    def test_open_contacts_listview_and_click_create(self, suite_contact_page):
        """
        1. Log into Sugar CRM
        2. Open Contacts listview and click Create
        3. Fill contact form from test data
        4. Save the record
        5. Open the created contact detail view

        Contact is created once per suite via the suite_contact_page fixture.
        The Actions button is exercised once, in the leads test, to avoid a
        redundant open/close cycle on the toggle dropdown.
        """
        contact = load_json("contacts.json")[0]
        suite_contact_page.ensure_contact_detail_open(
            contact["first_name"],
            contact["last_name"],
        )
