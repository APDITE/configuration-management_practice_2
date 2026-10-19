"""Точка входа визуализатора графа зависимостей."""

import sys

from config import parse_args

EXIT_OK = 0


def print_config(config, out):
    """Вывести параметры в формате ключ=значение."""
    for key, value in config.items():
        print(f"{key}={value}", file=out)


def main(argv=None, out=None):
    """Разобрать параметры и вывести их; вернуть код завершения."""
    config = parse_args(argv)
    print_config(config, out or sys.stdout)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
