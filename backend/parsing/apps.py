import atexit
import logging
import os
import sys

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class ParsingConfig(AppConfig):
    name = "parsing"

    # def ready(self):
    #     is_runserver = (
    #         len(sys.argv) >= 2
    #         and sys.argv[1] == "runserver"
    #         and os.environ.get("RUN_MAIN") == "true"
    #     )

    #     if not is_runserver:
    #         return

    #     from parsing.drivers.manager import driver_context, quit_all_drivers

    #     # Прогреваем один драйвер заранее — он вернётся в пул
    #     # и будет готов к первому запросу без задержки холодного старта
    #     try:
    #         with driver_context() as driver:
    #             logger.info("[Driver] Прогрет при старте: %s", driver.session_id)
    #     except Exception as exc:
    #         logger.error("[Driver] Не удалось прогреть: %s", exc)

    #     atexit.register(quit_all_drivers)  # quit_driver → quit_all_drivers