"""Точка входа визуализатора графа зависимостей.

Этап 3: построение графа зависимостей заданного пакета с учётом
транзитивности (обход в глубину без рекурсии) и поиск циклических
зависимостей в реальном репозитории Maven (режим remote) или в
тестовом репозитории из файла (режим test).
"""

import sys

from config import MODE_TEST, PROG, parse_args
from errors import RepositoryError
from graph import build_graph, find_cycles
from maven import MavenRepository
from testrepo import FileRepository

EXIT_OK = 0
EXIT_FAILURE = 1


class DependencySource:
    """Источник зависимостей для обхода графа.

    Ошибка загрузки корневого пакета прерывает работу. Ошибки загрузки
    остальных пакетов запоминаются в failures, а такой пакет считается
    пакетом без зависимостей, чтобы построить остальную часть графа.
    """

    def __init__(self, repository, root):
        """Создать источник для пакета root из репозитория repository."""
        self.repository = repository
        self.root = root
        self.failures = {}

    def __call__(self, package):
        """Вернуть зависимости пакета, передаваемые транзитивно."""
        try:
            return self.repository.dependency_names(package)
        except RepositoryError as error:
            if package == self.root:
                raise
            self.failures[package] = str(error)
            return []


def open_repository(config):
    """Создать источник зависимостей в соответствии с режимом работы."""
    if config.mode == MODE_TEST:
        return FileRepository(config.repo)
    return MavenRepository(config.repo)


def format_graph(graph, failures):
    """Вернуть строки вида «пакет -> зависимость, ...» для всего графа."""
    lines = []
    for package, dependencies in graph.items():
        line = package
        if dependencies:
            line += " -> " + ", ".join(dependencies)
        if package in failures:
            line += " (not resolved)"
        lines.append(line)
    return lines


def format_cycles(cycles):
    """Вернуть строки вида «cycle: A -> B -> A»."""
    return ["cycle: " + " -> ".join(cycle) for cycle in cycles]


def main(argv=None, out=None, err=None):
    """Построить и вывести граф зависимостей; вернуть код завершения."""
    config = parse_args(argv)
    out = out or sys.stdout
    err = err or sys.stderr
    try:
        source = DependencySource(open_repository(config), config.package)
        graph = build_graph(config.package, source)
    except RepositoryError as error:
        print(f"{PROG}: error: {error}", file=err)
        return EXIT_FAILURE
    for package, reason in source.failures.items():
        print(f"{PROG}: warning: {package}: {reason}", file=err)
    cycles = find_cycles(graph, config.package)
    for line in format_graph(graph, source.failures) + format_cycles(cycles):
        print(line, file=out)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
