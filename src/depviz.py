"""Точка входа визуализатора графа зависимостей.

Этап 2: вывод прямых зависимостей заданного пакета из реального
репозитория Maven (режим remote) или из тестового репозитория (test).
"""

import sys

from config import MODE_TEST, PROG, parse_args
from errors import RepositoryError
from maven import MavenRepository
from testrepo import FileRepository

EXIT_OK = 0
EXIT_FAILURE = 1


def open_repository(config):
    """Создать источник зависимостей в соответствии с режимом работы."""
    if config.mode == MODE_TEST:
        return FileRepository(config.repo)
    return MavenRepository(config.repo)


def print_dependencies(package, dependencies, out):
    """Вывести прямые зависимости пакета, по одной в строке."""
    if not dependencies:
        print(f"{package}: no direct dependencies", file=out)
        return
    for dependency in dependencies:
        print(dependency, file=out)


def main(argv=None, out=None, err=None):
    """Вывести прямые зависимости пакета; вернуть код завершения."""
    config = parse_args(argv)
    try:
        repository = open_repository(config)
        dependencies = repository.direct_dependencies(config.package)
    except RepositoryError as error:
        print(f"{PROG}: error: {error}", file=err or sys.stderr)
        return EXIT_FAILURE
    print_dependencies(config.package, dependencies, out or sys.stdout)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
