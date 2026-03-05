"""
parsing/drivers/manager.py

Потокобезопасный пул Selenium WebDriver-ов.
Вместо синглтона используется пул из MAX_DRIVERS драйверов.
"""

from __future__ import annotations

import logging
import os
import threading
from contextlib import contextmanager
from typing import Generator

from django.conf import settings
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)

_pool: list[webdriver.Chrome] = []
_pool_lock = threading.Lock()
MAX_DRIVERS = 3


def _build_options() -> Options:
    cfg = settings.SELENIUM_DRIVER_OPTIONS
    opts = Options()

    w, h = cfg.get("window_size", (1920, 1080))

    # Обязательные флаги для Docker/headless
    opts.add_argument("--headless=new")  # современный headless (Chrome 112+)
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--single-process")
    opts.add_argument("--remote-debugging-port=0")
    opts.add_argument(f"--window-size={w},{h}")  # один раз, не дважды

    # Антибот
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)

    if ua := cfg.get("user_agent"):
        opts.add_argument(f"user-agent={ua}")

    return opts


def _create_driver() -> webdriver.Chrome:
    cfg = settings.SELENIUM_DRIVER_OPTIONS
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH")

    if chromedriver_path:
        service = Service(executable_path=chromedriver_path)
    else:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=_build_options())
    driver.set_page_load_timeout(cfg.get("page_load_timeout", 30))
    driver.implicitly_wait(cfg.get("implicit_wait", 5))
    logger.info("[Driver] Новый WebDriver создан.")
    return driver


def _is_alive(driver: webdriver.Chrome) -> bool:
    try:
        _ = driver.current_url
        return True
    except Exception:
        return False


def _try_quit(driver: webdriver.Chrome) -> None:
    try:
        driver.quit()
    except Exception:
        pass


@contextmanager
def driver_context() -> Generator[webdriver.Chrome, None, None]:
    """
    Потокобезопасный контекстный менеджер.
    Берёт живой драйвер из пула или создаёт новый,
    возвращает обратно в пул после использования.

    Пример::

        with driver_context() as driver:
            driver.get(url)
            html = driver.page_source
    """
    driver: webdriver.Chrome | None = None

    with _pool_lock:
        while _pool:
            candidate = _pool.pop()
            if _is_alive(candidate):
                driver = candidate
                break
            _try_quit(candidate)

    if driver is None:
        driver = _create_driver()

    try:
        yield driver
    except Exception:
        # Драйвер мог сломаться после исключения — не возвращаем в пул
        _try_quit(driver)
        driver = None
        raise
    finally:
        if driver is not None:
            with _pool_lock:
                if len(_pool) < MAX_DRIVERS:
                    try:
                        driver.delete_all_cookies()
                    except Exception:
                        pass
                    _pool.append(driver)
                else:
                    _try_quit(driver)


def quit_all_drivers() -> None:
    """Завершить все драйверы в пуле (вызывать при shutdown приложения)."""
    with _pool_lock:
        for driver in _pool:
            _try_quit(driver)
        _pool.clear()
    logger.info("[Driver] Все драйверы остановлены.")
