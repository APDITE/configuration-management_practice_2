"""Тесты параметров командной строки и их проверки."""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr

from config import MODE_REMOTE, MODE_TEST, parse_args

ROOT = os.path.join(os.path.dirname(__file__), "..")
TEST_REPO = os.path.join(ROOT, "repos", "simple.txt")
MAVEN_URL = "https://repo1.maven.org/maven2"
MAVEN_PACKAGE = "org.slf4j:slf4j-api:2.0.13"
EXIT_USAGE = 2
ROOT_UID = 0
IS_ROOT = getattr(os, "geteuid", lambda: None)() == ROOT_UID


def run_error(test, argv):
    """Запустить разбор с ошибкой и вернуть текст сообщения."""
    err = io.StringIO()
    with redirect_stderr(err), test.assertRaises(SystemExit) as caught:
        parse_args(argv)
    test.assertEqual(caught.exception.code, EXIT_USAGE)
    return err.getvalue()


class ValidParamsTest(unittest.TestCase):
    """Корректные наборы параметров."""

    def test_remote_mode(self):
        """Режим remote: пакет Maven и URL репозитория."""
        config = parse_args(["-p", MAVEN_PACKAGE, "-r", MAVEN_URL])
        self.assertEqual(config.package, MAVEN_PACKAGE)
        self.assertEqual(config.repo, MAVEN_URL)
        self.assertEqual(config.mode, MODE_REMOTE)

    def test_test_mode(self):
        """Режим test: пакет из больших букв и файл репозитория."""
        config = parse_args(
            ["--package", "AB", "--repo", TEST_REPO, "--mode", "test"])
        self.assertEqual(config.package, "AB")
        self.assertEqual(config.mode, MODE_TEST)
        self.assertFalse(config.load_order)

    def test_load_order_flag(self):
        """Параметр -l/--load-order включает вывод порядка загрузки."""
        for flag in ("-l", "--load-order"):
            with self.subTest(flag=flag):
                config = parse_args(
                    ["-p", "A", "-r", TEST_REPO, "-m", "test", flag])
                self.assertTrue(config.load_order)


class PackageErrorTest(unittest.TestCase):
    """Ошибки параметра --package."""

    def test_missing(self):
        """Параметр не указан."""
        msg = run_error(self, ["-r", MAVEN_URL])
        self.assertIn("-p/--package", msg)

    def test_empty(self):
        """Пустое имя пакета."""
        msg = run_error(self, ["-p", " ", "-r", MAVEN_URL])
        self.assertIn("empty package name", msg)

    def test_not_maven(self):
        """В режиме remote нужен groupId:artifactId:version."""
        for name in ("slf4j", "org.slf4j:slf4j-api", "a:b:c:d", "a b:c:d",
                     "..:..:..", "org:-a:1", "org:a:1 "):
            with self.subTest(name=name):
                msg = run_error(self, ["-p", name, "-r", MAVEN_URL])
                self.assertIn("groupId:artifactId:version", msg)

    def test_not_capital_letters(self):
        """В режиме test имя пакета — большие латинские буквы."""
        for name in ("a", "A1", "Ж", MAVEN_PACKAGE):
            with self.subTest(name=name):
                msg = run_error(
                    self, ["-p", name, "-r", TEST_REPO, "-m", "test"])
                self.assertIn("capital Latin letters", msg)


class RepoErrorTest(unittest.TestCase):
    """Ошибки параметра --repo."""

    def test_missing(self):
        """Параметр не указан."""
        msg = run_error(self, ["-p", MAVEN_PACKAGE])
        self.assertIn("-r/--repo", msg)

    def test_empty(self):
        """Пустое значение."""
        msg = run_error(self, ["-p", MAVEN_PACKAGE, "-r", ""])
        self.assertIn("empty repository location", msg)

    def test_bad_url(self):
        """В режиме remote допустим только http(s) URL."""
        for repo in ("ftp://host/maven2", "repo1.maven.org", "repos/simple.txt",
                     "https://"):
            with self.subTest(repo=repo):
                msg = run_error(self, ["-p", MAVEN_PACKAGE, "-r", repo])
                self.assertIn("expected an http(s) URL", msg)

    def test_url_whitespace(self):
        """URL-адрес не может содержать пробельные символы."""
        for repo in (" " + MAVEN_URL, MAVEN_URL + " extra", MAVEN_URL + "\t"):
            with self.subTest(repo=repo):
                msg = run_error(self, ["-p", MAVEN_PACKAGE, "-r", repo])
                self.assertIn("must not contain whitespace", msg)

    def test_file_not_found(self):
        """В режиме test файл должен существовать."""
        msg = run_error(self, ["-p", "A", "-r", MAVEN_URL, "-m", "test"])
        self.assertIn("no such test repository file", msg)

    def test_directory(self):
        """В режиме test путь должен вести к файлу, а не к каталогу."""
        with tempfile.TemporaryDirectory() as path:
            msg = run_error(self, ["-p", "A", "-r", path, "-m", "test"])
        self.assertIn("not a file", msg)

    @unittest.skipIf(IS_ROOT, "root может читать любой файл")
    def test_permission_denied(self):
        """В режиме test файл должен быть доступен для чтения."""
        with tempfile.TemporaryDirectory() as path:
            repo = os.path.join(path, "repo.txt")
            with open(repo, "w", encoding="utf-8") as file:
                file.write("A:\n")
            os.chmod(repo, 0)
            msg = run_error(self, ["-p", "A", "-r", repo, "-m", "test"])
        self.assertIn("permission denied", msg)


class ModeErrorTest(unittest.TestCase):
    """Ошибки параметра --mode."""

    def test_invalid_choice(self):
        """Недопустимое значение режима."""
        msg = run_error(
            self, ["-p", MAVEN_PACKAGE, "-r", MAVEN_URL, "-m", "prod"])
        self.assertIn("invalid choice: 'prod'", msg)


class UnknownOptionTest(unittest.TestCase):
    """Неизвестные и сокращённые параметры."""

    def test_unknown_option(self):
        """Неизвестный параметр командной строки."""
        msg = run_error(
            self, ["-p", MAVEN_PACKAGE, "-r", MAVEN_URL, "--depth", "3"])
        self.assertIn("unrecognized arguments", msg)

    def test_no_abbreviations(self):
        """Сокращённые имена параметров не принимаются."""
        msg = run_error(self, ["--pack", MAVEN_PACKAGE, "-r", MAVEN_URL])
        self.assertIn("-p/--package", msg)


if __name__ == "__main__":
    unittest.main()
