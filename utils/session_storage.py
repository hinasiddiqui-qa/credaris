"""Persist and restore browser cookies as a secondary session mechanism."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

from selenium.webdriver.remote.webdriver import WebDriver

from core.config_loader import AppConfig, PROJECT_ROOT
from utils.logger import get_logger

logger = get_logger(__name__)

SESSIONS_DIR = PROJECT_ROOT / "sessions"

# Domains needed for ZPA + Microsoft SSO + sugar-test reuse.
RELEVANT_DOMAIN_SUFFIXES = (
    "credaris.ch",
    "microsoftonline.com",
    "microsoft.com",
    "live.com",
)


class SessionStorage:
    def __init__(self, config: AppConfig):
        self.config = config
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        self.cookie_file = SESSIONS_DIR / "credaris_cookies.json"

    def has_saved_session(self) -> bool:
        profile_exists = self.config.resolved_user_data_dir.exists()
        cookies_exist = self.cookie_file.exists() and self.cookie_file.stat().st_size > 2
        return profile_exists or cookies_exist

    def save_session(self, driver: WebDriver) -> None:
        cookies = self._collect_cookies(driver)
        filtered = [cookie for cookie in cookies if self._is_relevant_domain(cookie.get("domain", ""))]
        self.cookie_file.write_text(json.dumps(filtered, indent=2), encoding="utf-8")
        logger.info(
            "Saved %s session cookies to %s (Chrome profile: %s)",
            len(filtered),
            self.cookie_file,
            self.config.resolved_user_data_dir,
        )

    save_cookies = save_session

    def restore_session(self, driver: WebDriver) -> bool:
        if not self.cookie_file.exists():
            logger.info("No cookie file to restore — relying on Chrome profile only")
            return False

        cookies = json.loads(self.cookie_file.read_text(encoding="utf-8"))
        if not cookies:
            logger.info("Cookie file is empty — relying on Chrome profile only")
            return False

        loaded = self._inject_cookies(driver, cookies)
        logger.info(
            "Restored %s/%s cookies from %s via CDP (Chrome profile also loaded)",
            loaded,
            len(cookies),
            self.cookie_file,
        )
        return loaded > 0

    load_cookies = restore_session

    def delete_cookies(self) -> None:
        if self.cookie_file.exists():
            self.cookie_file.unlink()

    def _collect_cookies(self, driver: WebDriver) -> list[dict]:
        try:
            driver.execute_cdp_cmd("Network.enable", {})
            return driver.execute_cdp_cmd("Network.getAllCookies", {}).get("cookies", [])
        except Exception as exc:
            logger.warning("CDP cookie export failed (%s) — falling back to per-domain collection", exc)
            return self._collect_cookies_via_navigation(driver)

    def _collect_cookies_via_navigation(self, driver: WebDriver) -> list[dict]:
        collected: dict[tuple[str, str, str], dict] = {}
        for url in self._session_urls():
            driver.get(url)
            for cookie in driver.get_cookies():
                key = (cookie.get("domain", ""), cookie.get("name", ""), cookie.get("path", "/"))
                collected[key] = cookie
        return list(collected.values())

    def _inject_cookies(self, driver: WebDriver, cookies: list[dict]) -> int:
        try:
            driver.execute_cdp_cmd("Network.enable", {})
        except Exception as exc:
            logger.warning("Could not enable CDP Network domain: %s", exc)
            return self._inject_cookies_via_navigation(driver, cookies)

        loaded = 0
        for cookie in cookies:
            if not self._is_relevant_domain(cookie.get("domain", "")):
                continue
            params = self._to_cdp_cookie_params(cookie)
            try:
                result = driver.execute_cdp_cmd("Network.setCookie", params)
                if result.get("success"):
                    loaded += 1
            except Exception as exc:
                logger.debug("Skipped cookie %s: %s", cookie.get("name"), exc)
        return loaded

    def _inject_cookies_via_navigation(self, driver: WebDriver, cookies: list[dict]) -> int:
        loaded = 0
        cookies_by_domain: dict[str, list[dict]] = {}
        for cookie in cookies:
            domain = cookie.get("domain", "").lstrip(".")
            cookies_by_domain.setdefault(domain, []).append(cookie)

        for domain, domain_cookies in cookies_by_domain.items():
            seed_url = self._seed_url_for_domain(domain)
            if not seed_url:
                continue
            driver.get(seed_url)
            for cookie in domain_cookies:
                selenium_cookie = dict(cookie)
                selenium_cookie.pop("sameSite", None)
                try:
                    driver.add_cookie(selenium_cookie)
                    loaded += 1
                except Exception as exc:
                    logger.debug("Skipped cookie %s on %s: %s", cookie.get("name"), domain, exc)
        return loaded

    def _session_urls(self) -> list[str]:
        return [
            self.config.auth_home_url,
            self.config.application_url.rstrip("/") + "/",
        ]

    def _seed_url_for_domain(self, domain: str) -> str | None:
        auth_host = urlparse(self.config.auth_base_url).netloc
        app_host = self.config.application_host
        if domain == auth_host or domain.endswith(f".{auth_host}"):
            return self.config.auth_home_url
        if domain == app_host or domain.endswith(f".{app_host}"):
            return self.config.application_url.rstrip("/") + "/"
        if "microsoftonline.com" in domain:
            return "https://login.microsoftonline.com/"
        return None

    @staticmethod
    def _is_relevant_domain(domain: str) -> bool:
        normalized = domain.lstrip(".").lower()
        return any(normalized == suffix or normalized.endswith(f".{suffix}") for suffix in RELEVANT_DOMAIN_SUFFIXES)

    @staticmethod
    def _to_cdp_cookie_params(cookie: dict) -> dict:
        params: dict = {
            "name": cookie["name"],
            "value": cookie["value"],
            "domain": cookie.get("domain", ""),
            "path": cookie.get("path", "/"),
            "secure": bool(cookie.get("secure", False)),
            "httpOnly": bool(cookie.get("httpOnly", False)),
        }
        expires = cookie.get("expires", cookie.get("expiry"))
        if expires not in (None, -1):
            params["expires"] = expires
        same_site = cookie.get("sameSite")
        if same_site in {"Strict", "Lax", "None"}:
            params["sameSite"] = same_site
        return params
