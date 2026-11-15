"""Точка входа визуализатора графа зависимостей.

Строит граф зависимостей заданного пакета с учётом транзитивности
(обход в глубину без рекурсии) и находит циклические зависимости в
реальном репозитории Maven (режим remote) или в тестовом репозитории
из файла (режим test). Выводит граф в текстовом виде, порядок
загрузки зависимостей (параметр --load-order, этап 4) или описание
графа на языке диаграмм D2 (параметр --d2, этап 5).
"""

import sys

from config import MODE_TEST, PROG, parse_args
from d2 import to_d2
from errors import RepositoryError
from graph import build_graph, find_cycles, load_order
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


def format_load_order(order, failures):
    """Вернуть пронумерованные строки порядка загрузки «1. пакет»."""
    lines = []
    for number, package in enumerate(order, start=1):
        line = f"{number}. {package}"
        if package in failures:
            line += " (not resolved)"
        lines.append(line)
    return lines


def render(config, graph, failures):
    """Вернуть строки вывода в формате, выбранном параметрами.

    Описание D2 содержит циклы в виде выделенных рёбер; в текстовых
    форматах циклы выводятся после графа или порядка загрузки.
    """
    root = config.package
    cycles = find_cycles(graph, root)
    if config.d2:
        return to_d2(graph, root, cycles, failures)
    if config.load_order:
        lines = format_load_order(load_order(graph, root), failures)
    else:
        lines = format_graph(graph, failures)
    return lines + format_cycles(cycles)


def main(argv=None, out=None, err=None):
    """Построить граф и вывести результат; вернуть код завершения."""
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
    for line in render(config, graph, source.failures):
        print(line, file=out)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
