"""Dump sidebar DOM for Contacts locator debugging."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.config_loader import load_config
from core.driver_factory import DriverFactory
from pages.sugar_login_page import SugarLoginPage
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def main() -> int:
    config = load_config()
    driver = DriverFactory.create_driver(config)
    try:
        driver.get(config.application_url.rstrip("/") + "/")
        wait = WebDriverWait(driver, 30)

        sugar = SugarLoginPage(driver, config)
        if sugar.is_displayed():
            sugar.login(config.sugar_username, config.sugar_password)

        # Wait for SPA shell / sidebar links to render
        time.sleep(5)
        for locator in (
            (By.CSS_SELECTOR, "a[href='#Contacts']"),
            (By.CSS_SELECTOR, "a.sidebar-nav-item-btn"),
            (By.XPATH, "//*[contains(text(),'My Dashboard')]"),
        ):
            try:
                wait.until(EC.presence_of_element_located(locator))
                break
            except Exception:
                continue

        script = """
        const allAnchors = [...document.querySelectorAll('a')];
        const contactAnchors = allAnchors.filter(a => {
          const href = (a.getAttribute('href') || '').toLowerCase();
          const aria = (a.getAttribute('aria-label') || '').toLowerCase();
          const cls = (a.className || '').toLowerCase();
          return href.includes('contact') || aria.includes('contact') || cls.includes('sidebar-nav');
        });
        const sidebars = [...document.querySelectorAll('[class*="sidebar"], nav, aside')].slice(0, 5);
        return {
          url: location.href,
          hash: location.hash,
          title: document.title,
          sidebars: sidebars.map(el => ({
            tag: el.tagName,
            class: el.className,
            id: el.id,
            snippet: el.outerHTML.slice(0, 1500),
          })),
          contactAnchors: contactAnchors.map(a => ({
            href: a.getAttribute('href'),
            aria: a.getAttribute('aria-label'),
            class: a.className,
            text: (a.textContent || '').trim(),
            visible: !!(a.offsetWidth || a.offsetHeight || a.getClientRects().length),
            rect: a.getBoundingClientRect(),
            html: a.outerHTML.slice(0, 800),
          })),
          allSidebarNavBtns: [...document.querySelectorAll('a.sidebar-nav-item-btn')].map(a => ({
            href: a.getAttribute('href'),
            aria: a.getAttribute('aria-label'),
            visible: !!(a.offsetWidth || a.offsetHeight || a.getClientRects().length),
          })),
        };
        """
        data = driver.execute_script(script)
        out = PROJECT_ROOT / "reports" / "sidebar-inspect.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(json.dumps(data, indent=2))
        return 0
    finally:
        if not config.keep_browser_open:
            driver.quit()


if __name__ == "__main__":
    raise SystemExit(main())
