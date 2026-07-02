"""Bootstrap a reusable authenticated session (run once, or when session expires)."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.config_loader import load_config
from core.driver_factory import DriverFactory
from core.session_orchestrator import SessionOrchestrator
from utils.logger import get_logger

logger = get_logger("credaris.bootstrap")


def main() -> int:
    config = load_config()

    if not config.microsoft_username or not config.microsoft_password:
        print("Set microsoft.username and microsoft.password in config/config.properties first.")
        return 1

    print("Bootstrapping session (Initial Check → Scenario 1 or 2)...")
    print(f"  Auth portal:  {config.auth_home_url}")
    print(f"  Application:  {config.application_url}")
    print(f"  Sugar login:  {config.application_login_url}")
    print(f"  Profile:      {config.resolved_user_data_dir}\n")

    driver = DriverFactory.create_driver(config)
    try:
        app = SessionOrchestrator(driver, config).run()
        print("\nSession ready.")
        print(f"  URL:   {app.driver.current_url}")
        print(f"  Title: {app.get_title()}")
        print("\nFuture runs will use Scenario 2 when the saved session is still valid.")
        return 0
    except Exception as exc:
        logger.exception("Bootstrap failed: %s", exc)
        return 1
    finally:
        if config.keep_browser_open:
            print("\nBrowser left open. Close Chrome manually when finished.")
        else:
            driver.quit()


if __name__ == "__main__":
    raise SystemExit(main())
