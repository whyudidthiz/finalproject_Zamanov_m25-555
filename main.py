#!/usr/bin/env python3
from dotenv import load_dotenv

load_dotenv()  # загружаем данные из .env
from valutatrade_hub.cli.interface import main_loop
from valutatrade_hub.logging_config import setup_logging


def main():
    setup_logging()
    main_loop()


if __name__ == "__main__":
    main()
