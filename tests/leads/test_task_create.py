"""Task module — create task from lead detail view."""

from __future__ import annotations

import pytest

from core.base_test import BaseTest


@pytest.mark.tasks
@pytest.mark.smoke
class TestTaskCreate(BaseTest):
    def test_create_task_from_lead_detail(self, suite_task_page):
        """
        1. Reuse the suite lead detail view (contact + lead created once per session)
        2. Click 'Create Task' quick action on the lead detail view
        3. On the Task create view, select Category: Antrag verzichten
        4. Scroll to Teams field, search and select: Callback
        5. Click Save
        6. On the saved Task detail view, click the related Lead link to return to it

        The actual flow is performed once per session by the shared
        'suite_task_page' fixture (in tests/conftest.py) — this test exercises it,
        so other tests (e.g. the Credit Request panel test) can safely depend on
        the same fixture without recreating the task or caring about file order.
        """
