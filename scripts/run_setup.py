"""Run one-time Credaris app setup and verify home page load."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.app_setup import AppSetup
from core.config_loader import load_config
from core.driver_factory import DriverFactory
from utils.logger import get_logger

logger = get_logger("credaris.setup")


def main() -> int:
    config = load_config()
    driver = DriverFactory.create_driver(config)

    try:
        setup = AppSetup(driver, config)
        home = setup.launch_and_verify_home()

        print("Setup completed successfully.")
        print(f"  URL:   {home.get_current_url()}")
        print(f"  Title: {home.get_title()}")
        return 0
    except Exception as exc:
        logger.exception("Setup failed: %s", exc)
        return 1
    finally:
        input("Press Enter to close the browser...")
        driver.quit()


if __name__ == "__main__":
    raise SystemExit(main())
