"""Тесты точки входа: вывод графа зависимостей и коды завершения."""

import io
import os
import unittest

from depviz import EXIT_FAILURE, EXIT_OK, main
from tests.maven_server import MavenServer

ROOT = os.path.join(os.path.dirname(__file__), "..")
SIMPLE_REPO = os.path.join(ROOT, "repos", "simple.txt")
BROKEN_REPO = os.path.join(ROOT, "repos", "broken.txt")
CYCLE_REPO = os.path.join(ROOT, "repos", "cycle.txt")


def run_main(argv):
    """Запустить main и вернуть (код, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    code = main(argv, out=out, err=err)
    return code, out.getvalue().splitlines(), err.getvalue()


class TestModeTest(unittest.TestCase):
    """Режим test."""

    def test_graph(self):
        """Граф с общей зависимостью: каждый пакет выводится один раз."""
        code, out, _ = run_main(["-p", "A", "-r", SIMPLE_REPO, "-m", "test"])
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out, ["A -> B, C", "B -> D", "D", "C -> D"])

    def test_leaf(self):
        """Пакет без зависимостей."""
        code, out, _ = run_main(["-p", "D", "-r", SIMPLE_REPO, "-m", "test"])
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out, ["D"])

    def test_cycle(self):
        """Циклическая зависимость выводится отдельной строкой."""
        code, out, _ = run_main(["-p", "A", "-r", CYCLE_REPO, "-m", "test"])
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out, [
            "A -> B", "B -> C", "C -> A, D", "D",
            "cycle: A -> B -> C -> A",
        ])

    def test_errors(self):
        """Неизвестный пакет и ошибка формата файла."""
        cases = (("Z", SIMPLE_REPO, "'Z' not found"),
                 ("A", BROKEN_REPO, "broken.txt:2:"))
        for package, repo, message in cases:
            with self.subTest(repo=repo):
                code, out, err = run_main(
                    ["-p", package, "-r", repo, "-m", "test"])
                self.assertEqual(code, EXIT_FAILURE)
                self.assertEqual(out, [])
                self.assertIn(message, err)


class RemoteModeTest(unittest.TestCase):
    """Режим remote с локальным HTTP-сервером."""

    def test_graph_and_error(self):
        """Граф пакета и ошибка для отсутствующего корневого пакета."""
        with MavenServer() as server:
            code, out, _ = run_main(
                ["-p", "org.example:rt:1.0", "-r", server.url])
            failed, _, err = run_main(
                ["-p", "org.example:nope:1.0", "-r", server.url])
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out, [
            "org.example:rt:1.0 -> org.example:core:1.2.3",
            "org.example:core:1.2.3",
        ])
        self.assertEqual(failed, EXIT_FAILURE)
        self.assertIn("package not found", err)

    def test_unresolved_dependency(self):
        """Недоступная транзитивная зависимость: предупреждение."""
        with MavenServer() as server:
            code, out, err = run_main(
                ["-p", "org.example:lib:1.0", "-r", server.url])
        self.assertEqual(code, EXIT_OK)
        self.assertIn("org.example:ghost:1.0 (not resolved)", out)
        self.assertIn("warning: org.example:ghost:1.0", err)


if __name__ == "__main__":
    unittest.main()
