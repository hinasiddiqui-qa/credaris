"""Run Credaris login via Microsoft SSO and wait for Authenticator MFA approval."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.config_loader import load_config
from core.driver_factory import DriverFactory
from utils.logger import get_logger
from workflows.auth_workflow import AuthWorkflow

logger = get_logger("credaris.sso_login")


def main() -> int:
    config = load_config()
    mfa_timeout = int(os.getenv("MFA_WAIT_TIMEOUT", str(config.mfa_wait_timeout)))

    if not config.microsoft_username or not config.microsoft_password:
        print("Set microsoft.username and microsoft.password in config/config.properties first.")
        return 1

    driver = DriverFactory.create_driver(config)

    try:
        user = {
            "username": config.microsoft_username,
            "password": config.microsoft_password,
        }
        home = AuthWorkflow(driver, config, mfa_timeout=mfa_timeout).login(user)

        print("\nLogin completed successfully.")
        print(f"  URL:   {home.get_current_url()}")
        print(f"  Title: {home.get_title()}")
        return 0
    except Exception as exc:
        logger.exception("SSO login failed: %s", exc)
        print(f"\nLogin failed: {exc}")
        return 1
    finally:
        if config.keep_browser_open:
            print("\nBrowser left open. Close Chrome manually when finished.")
        else:
            input("\nPress Enter to close the browser...")
            driver.quit()


if __name__ == "__main__":
    raise SystemExit(main())
