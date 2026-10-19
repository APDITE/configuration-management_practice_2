"""Тесты точки входа: вывод прямых зависимостей и коды завершения."""

import io
import os
import unittest

from depviz import EXIT_FAILURE, EXIT_OK, main
from tests.maven_server import MavenServer

ROOT = os.path.join(os.path.dirname(__file__), "..")
SIMPLE_REPO = os.path.join(ROOT, "repos", "simple.txt")
BROKEN_REPO = os.path.join(ROOT, "repos", "broken.txt")


def run_main(argv):
    """Запустить main и вернуть (код, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    code = main(argv, out=out, err=err)
    return code, out.getvalue().splitlines(), err.getvalue()


class TestModeTest(unittest.TestCase):
    """Режим test."""

    def test_dependencies(self):
        """Вывод прямых зависимостей по одной в строке."""
        code, out, _ = run_main(["-p", "A", "-r", SIMPLE_REPO, "-m", "test"])
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out, ["B", "C"])

    def test_no_dependencies(self):
        """Пакет без зависимостей."""
        code, out, _ = run_main(["-p", "D", "-r", SIMPLE_REPO, "-m", "test"])
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out, ["D: no direct dependencies"])

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

    def test_dependencies_and_error(self):
        """Вывод зависимостей и ошибка для отсутствующего пакета."""
        server = MavenServer()
        server.start()
        try:
            code, out, _ = run_main(
                ["-p", "org.example:app:1.2.3", "-r", server.url])
            failed, _, err = run_main(
                ["-p", "org.example:nope:1.0", "-r", server.url])
        finally:
            server.stop()
        self.assertEqual(code, EXIT_OK)
        self.assertIn("org.example:core:1.2.3 [compile]", out)
        self.assertEqual(failed, EXIT_FAILURE)
        self.assertIn("package not found", err)


if __name__ == "__main__":
    unittest.main()
