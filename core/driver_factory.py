"""WebDriver factory for Chrome, Firefox, and Edge."""

from __future__ import annotations

from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService

from core.config_loader import AppConfig


class DriverFactory:
    @staticmethod
    def _clean_profile_locks(profile_dir: Path) -> None:
        # Do not delete DevToolsActivePort — Chrome creates it during startup.
        for name in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
            lock_path = profile_dir / name
            if lock_path.exists():
                try:
                    lock_path.unlink()
                except OSError:
                    pass

    @staticmethod
    def create_driver(config: AppConfig):
        browser = config.browser

        if browser == "firefox":
            return DriverFactory._create_firefox(config)
        if browser == "edge":
            return DriverFactory._create_edge(config)
        return DriverFactory._create_chrome(config)

    @staticmethod
    def _apply_common_options(options, config: AppConfig) -> None:
        if config.headless:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
        else:
            options.add_argument("--start-maximized")

        options.add_argument("--disable-notifications")
        options.add_argument("--no-first-run")
        options.add_argument("--disable-popup-blocking")

        if config.reuse_session and hasattr(options, "add_argument"):
            profile_dir = config.resolved_user_data_dir
            profile_dir.mkdir(parents=True, exist_ok=True)
            DriverFactory._clean_profile_locks(profile_dir)
            options.add_argument(f"--user-data-dir={profile_dir.resolve()}")
            if config.chrome_profile_directory:
                options.add_argument(f"--profile-directory={config.chrome_profile_directory}")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--remote-debugging-port=0")

        if config.keep_browser_open and hasattr(options, "add_experimental_option"):
            options.add_experimental_option("detach", True)

    @staticmethod
    def _create_chrome(config: AppConfig):
        options = ChromeOptions()
        DriverFactory._apply_common_options(options, config)
        driver = webdriver.Chrome(service=ChromeService(), options=options)
        DriverFactory._finalize_driver(driver, config)
        return driver

    @staticmethod
    def _create_firefox(config: AppConfig):
        options = FirefoxOptions()
        if config.headless:
            options.add_argument("-headless")
        driver = webdriver.Firefox(service=FirefoxService(), options=options)
        DriverFactory._finalize_driver(driver, config)
        return driver

    @staticmethod
    def _create_edge(config: AppConfig):
        options = EdgeOptions()
        DriverFactory._apply_common_options(options, config)
        driver = webdriver.Edge(service=EdgeService(), options=options)
        DriverFactory._finalize_driver(driver, config)
        return driver

    @staticmethod
    def _finalize_driver(driver, config: AppConfig) -> None:
        driver.implicitly_wait(config.implicit_wait)
        if not config.headless:
            try:
                driver.maximize_window()
            except Exception:
                pass
