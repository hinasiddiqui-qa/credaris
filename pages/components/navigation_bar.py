"""Top navigation component (legacy). Prefer SidebarNav for Sugar CRM."""

from __future__ import annotations

from pages.components.sidebar_nav import SidebarNav


class NavigationBar(SidebarNav):
    def go_to_contacts(self) -> None:
        self.open_contacts()