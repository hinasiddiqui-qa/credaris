"""Shared Sugar CRM loading wait helpers."""

from __future__ import annotations

import time

from selenium.common.exceptions import TimeoutException

from core.config_loader import AppConfig
from utils.logger import get_logger

logger = get_logger(__name__)

_IS_SUGAR_LOADING_SCRIPT = """
const loadingSelectors = [
  '.loading',
  '.mask',
  '.block-ui',
  '.blockOverlay',
  '.blockUI',
  '.alert-loading',
  '.drawer.loading',
  '#overlay',
  '#nprogress',
  '[class*="loading"]',
  '[class*="spinner"]',
];
for (const node of document.querySelectorAll(loadingSelectors.join(','))) {
  if (!node || node.offsetParent === null) continue;
  const style = window.getComputedStyle(node);
  if (style.display === 'none' || style.visibility === 'hidden' || Number(style.opacity) === 0) {
    continue;
  }
  const text = (node.textContent || '').replace(/\\s+/g, ' ').trim();
  if (
    text.includes('Loading') ||
    node.classList.contains('loading') ||
    node.classList.contains('mask') ||
    node.id === 'nprogress'
  ) {
    return true;
  }
}
if (window.jQuery && window.jQuery.active > 0) {
  return true;
}
return false;
"""


def wait_for_sugar_loading_overlay_gone(driver, config: AppConfig, *, context: str = "") -> None:
    """Wait until Sugar CRM blocking loaders and pending AJAX requests finish."""
    label = f" ({context})" if context else ""
    timeout = config.sugar_load_timeout
    logger.info("Waiting for Sugar CRM loading to complete%s (timeout=%ss)", label, timeout)
    deadline = time.time() + timeout
    while time.time() < deadline:
        loading = driver.execute_script(f"return ({_IS_SUGAR_LOADING_SCRIPT});")
        if not loading:
            logger.info("Sugar CRM loading complete%s", label)
            return
        time.sleep(0.2)

    raise TimeoutException(
        f"Sugar CRM did not finish loading within {timeout}s{label}. "
        "The page may still be showing a Loading overlay or pending requests."
    )


def wait_for_sugar_app_ready(driver, config: AppConfig, *, context: str = "") -> None:
    """Wait for document readiness, SPA stability, and Sugar loading overlays."""
    label = f" ({context})" if context else ""
    logger.info("Waiting for Sugar CRM app to be ready%s", label)

    ready_deadline = time.time() + config.sugar_load_timeout
    while time.time() < ready_deadline:
        if driver.execute_script("return document.readyState") == "complete":
            break
        time.sleep(0.1)
    else:
        raise TimeoutException(f"Document did not reach readyState=complete within {config.sugar_load_timeout}s{label}")

    try:
        driver.execute_script(
            """
            if (typeof window.getAllAngularTestabilities === 'function') {
              const stable = window.getAllAngularTestabilities().every((t) => t.isStable());
              if (!stable) return false;
            }
            return true;
            """
        )
    except Exception:
        pass

    wait_for_sugar_loading_overlay_gone(driver, config, context=context or "app ready")

    shell_present = driver.execute_script(
        """
        const shell = document.querySelector('app-root, #content, .navbar, .sidebar, .main');
        return !!(shell && shell.offsetParent !== null);
        """
    )
    if not shell_present:
        raise TimeoutException(f"Sugar CRM shell did not become visible{label}")

    logger.info("Sugar CRM app is ready%s", label)
