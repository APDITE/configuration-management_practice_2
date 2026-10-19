"""Тесты тестового репозитория из текстового файла."""

import os
import tempfile
import unittest

from errors import RepositoryError
from testrepo import FileRepository, parse_test_repo

ROOT = os.path.join(os.path.dirname(__file__), "..")
SIMPLE_REPO = os.path.join(ROOT, "repos", "simple.txt")


class ParseTestRepoTest(unittest.TestCase):
    """Разбор текста тестового репозитория."""

    def test_valid(self):
        """Пустые строки, пробелы и повторы зависимостей."""
        graph = parse_test_repo("A: B  C B\n\n  B :D\nD:\n", "t")
        self.assertEqual(graph, {"A": ["B", "C"], "B": ["D"], "D": []})

    def test_bad_lines(self):
        """Строки неверного формата."""
        for line in ("A B", "a: B", "A: b", "A: B1", "AB: C,D", ": A"):
            with self.subTest(line=line):
                with self.assertRaisesRegex(RepositoryError, "t:2:"):
                    parse_test_repo("X:\n" + line, "t")

    def test_duplicate(self):
        """Пакет описан дважды."""
        with self.assertRaisesRegex(RepositoryError, "already defined"):
            parse_test_repo("A: B\nA: C\n", "t")


class FileRepositoryTest(unittest.TestCase):
    """Прямые зависимости из файла тестового репозитория."""

    def test_direct_dependencies(self):
        """Зависимости пакетов из repos/simple.txt."""
        repository = FileRepository(SIMPLE_REPO)
        self.assertEqual(repository.direct_dependencies("A"), ["B", "C"])
        self.assertEqual(repository.direct_dependencies("D"), [])

    def test_package_only_as_dependency(self):
        """Пакет без своей строки не имеет зависимостей."""
        with tempfile.TemporaryDirectory() as path:
            repo = os.path.join(path, "repo.txt")
            with open(repo, "w", encoding="utf-8") as file:
                file.write("A: B\n")
            repository = FileRepository(repo)
        self.assertEqual(repository.direct_dependencies("B"), [])

    def test_unknown_package(self):
        """Пакет отсутствует в тестовом репозитории."""
        repository = FileRepository(SIMPLE_REPO)
        with self.assertRaisesRegex(RepositoryError, "'Z' not found"):
            repository.direct_dependencies("Z")

    def test_unreadable_file(self):
        """Файл не удаётся прочитать как текст UTF-8."""
        with tempfile.TemporaryDirectory() as path:
            repo = os.path.join(path, "repo.txt")
            with open(repo, "wb") as file:
                file.write(b"\xff\xfe\x00")
            with self.assertRaisesRegex(RepositoryError, "cannot read"):
                FileRepository(repo)


if __name__ == "__main__":
    unittest.main()
