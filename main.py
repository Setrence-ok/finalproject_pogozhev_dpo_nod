#!/usr/bin/env python3
"""Точка входа в приложение Валютный кошелёк"""

from valutatrade_hub.cli.interface import CLIInterface


def main():
    """Основная функция запуска"""
    cli = CLIInterface()
    cli.run()


if __name__ == "__main__":
    main()
