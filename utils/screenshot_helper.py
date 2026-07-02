"""Screenshot capture helpers."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from selenium.webdriver.remote.webdriver import WebDriver

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCREENSHOT_DIR = PROJECT_ROOT / "screenshots"


def capture_screenshot(driver: WebDriver, name: str = "failure") -> Path:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = SCREENSHOT_DIR / f"{name}_{timestamp}.png"
    driver.save_screenshot(str(path))
    return path
