#!/usr/bin/env python3
"""Точка входа в приложение Валютный кошелёк"""
import sys
from valutatrade_hub.cli.interface import CLIInterface
from valutatrade_hub.logging_config import setup_logging


def main():
    """Основная функция запуска"""
    setup_logging()
    cli = CLIInterface()
    cli.run()


if __name__ == "__main__":
    main()
