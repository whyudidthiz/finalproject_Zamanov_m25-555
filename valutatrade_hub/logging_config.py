import logging
import os
from logging.handlers import RotatingFileHandler
from valutatrade_hub.infra.settings import SettingsLoader

settings = SettingsLoader()

def setup_logging():
    """Настраивает корневой логгер для приложения."""
    log_file = settings.get('log_file', 'logs/trade.log')
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # Формат лога: время, уровень, сообщение
    formatter = logging.Formatter(
        fmt='%(asctime)s.%(msecs)03d %(levelname)s %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )

    # Ротация по размеру (5 MB, хранить 3 файла)
    handler = RotatingFileHandler(
        log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
    )
    handler.setFormatter(formatter)

    # Корневой логгер
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Можно позже менять через конфиг
    logger.addHandler(handler)

    # Также можно добавить вывод в консоль (опционально)
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)