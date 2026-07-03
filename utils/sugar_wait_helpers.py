"""Shared Sugar CRM loading wait helpers."""

from __future__ import annotations

import time

from selenium.common.exceptions import TimeoutException

from core.config_loader import AppConfig
from utils.logger import get_logger

logger = get_logger(__name__)

def _sugar_loading_debug(driver) -> str:
    """Return a short description of visible loading indicators (for timeout logs)."""
    try:
        return driver.execute_script(
            """
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
            ];
            const hits = [];
            for (const node of document.querySelectorAll(loadingSelectors.join(','))) {
              if (!node || node.offsetParent === null) continue;
              const style = window.getComputedStyle(node);
              if (style.display === 'none' || style.visibility === 'hidden' || Number(style.opacity) === 0) {
                continue;
              }
              const text = (node.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 80);
              hits.push(`${node.tagName}.${node.className || node.id || '?'} "${text}"`);
            }
            return hits.length ? hits.join('; ') : 'none detected';
            """
        )
    except Exception as exc:
        return f"debug unavailable: {exc}"


def _is_sugar_loading(driver) -> bool:
    return driver.execute_script(
        """
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
        return false;
        """
    )


def wait_for_sugar_loading_overlay_gone(driver, config: AppConfig, *, context: str = "") -> None:
    """Wait until Sugar CRM blocking loaders and pending AJAX requests finish."""
    label = f" ({context})" if context else ""
    timeout = config.sugar_load_timeout
    logger.info(
        "Waiting for Sugar CRM loading to complete%s on %s (timeout=%ss)",
        label,
        driver.current_url,
        timeout,
    )
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not _is_sugar_loading(driver):
            logger.info("Sugar CRM loading complete%s", label)
            return
        time.sleep(0.2)

    debug = _sugar_loading_debug(driver)
    raise TimeoutException(
        f"Sugar CRM did not finish loading within {timeout}s{label}. "
        f"Blocking indicators: {debug}. "
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
    if shell_present:
        logger.info("Sugar CRM app is ready%s", label)
        return

    on_sugar_login = driver.execute_script(
        """
        return !!(
          document.querySelector("form[name='login'] input[name='username']") ||
          document.querySelector("input[name='username']")
        );
        """
    )
    if on_sugar_login:
        logger.info(
            "Sugar CRM login page is visible%s — Microsoft SSO complete, Sugar login can proceed",
            label,
        )
        return

    if config.application_host in driver.current_url:
        logger.info(
            "On sugar-test with loading complete%s — app shell/login will be handled by next step",
            label,
        )
        return

    raise TimeoutException(f"Sugar CRM shell did not become visible{label}")
