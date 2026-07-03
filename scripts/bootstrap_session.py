"""Bootstrap a reusable authenticated session (run once, or when session expires)."""

from __future__ import annotations

import os
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
    import argparse

    parser = argparse.ArgumentParser(description="Bootstrap a reusable authenticated session.")
    parser.add_argument(
        "--force-microsoft-auth",
        action="store_true",
        help="Clear saved cookies and skip restore so Microsoft SSO runs fresh.",
    )
    args = parser.parse_args()

    config = load_config()

    if not config.microsoft_username or not config.microsoft_password:
        print("Set microsoft.username and microsoft.password in config/config.properties first.")
        return 1

    print("Bootstrapping session (open sugar-test, wait for load, save session)...")
    print(f"  Application:  {config.application_url}")
    print(f"  Sugar login:  {config.application_login_url}")
    print(f"  Profile:      {config.resolved_user_data_dir}\n")

    driver = DriverFactory.create_driver(config)
    try:
        if args.force_microsoft_auth:
            print("Force Microsoft auth: clearing saved cookies before opening sugar-test.\n")
            from utils.session_storage import SessionStorage

            storage = SessionStorage(config)
            storage.delete_cookies()
            storage.clear_browser_cookies(driver)
            os.environ["SKIP_SESSION_RESTORE"] = "true"

        app = SessionOrchestrator(driver, config).run()
        print("\nMicrosoft SSO complete — sugar-test is open.")

        if not config.sugar_username or not config.sugar_password:
            print("Set sugar.username and sugar.password in config/config.properties for Sugar CRM login.")
        else:
            from login.sugar_login_prerequisite import login_to_sugar_crm

            print("Completing Sugar CRM login...")
            login_to_sugar_crm(
                driver,
                config,
                {"username": config.sugar_username, "password": config.sugar_password},
            )

        print("\nSession ready.")
        print(f"  URL:   {app.driver.current_url}")
        print(f"  Title: {app.get_title()}")
        print("\nFuture runs will reuse the saved session when it is still valid.")
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
