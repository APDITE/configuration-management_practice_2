"""Тестовый репозиторий: описание графа пакетов в текстовом файле.

Каждая непустая строка файла имеет вид «ПАКЕТ: ЗАВИСИМОСТЬ ...», где
имена пакетов состоят из больших латинских букв. Пакет, который
встречается только в списках зависимостей, не имеет своих зависимостей.
"""

import re

from errors import RepositoryError

LINE = re.compile(r"^\s*([A-Z]+)\s*:\s*([A-Z]+(?:\s+[A-Z]+)*)?\s*$")


def parse_test_repo(text, source):
    """Разобрать текст тестового репозитория в словарь пакет -> список.

    source -- имя файла для сообщений об ошибках.
    """
    graph = {}
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        match = LINE.match(line)
        if match is None:
            raise RepositoryError(
                f"{source}:{number}: expected 'NAME: DEPENDENCY ...' "
                "with capital Latin letters")
        name = match.group(1)
        if name in graph:
            raise RepositoryError(
                f"{source}:{number}: package '{name}' is already defined")
        graph[name] = list(dict.fromkeys((match.group(2) or "").split()))
    return graph


class FileRepository:
    """Тестовый репозиторий, загруженный из файла."""

    def __init__(self, path):
        """Прочитать и разобрать файл тестового репозитория."""
        try:
            with open(path, encoding="utf-8") as file:
                text = file.read()
        except (OSError, UnicodeDecodeError) as error:
            raise RepositoryError(
                f"cannot read test repository '{path}': {error}") from error
        self.graph = parse_test_repo(text, path)

    def packages(self):
        """Вернуть множество всех пакетов, упомянутых в файле."""
        names = set(self.graph)
        for dependencies in self.graph.values():
            names.update(dependencies)
        return names

    def direct_dependencies(self, package):
        """Вернуть список прямых зависимостей пакета."""
        if package not in self.packages():
            raise RepositoryError(
                f"package '{package}' not found in test repository")
        return list(self.graph.get(package, []))

    def dependency_names(self, package):
        """Вернуть имена зависимостей пакета (все передаются транзитивно)."""
        return self.direct_dependencies(package)
