"""Тесты получения прямых зависимостей из репозитория Maven."""

import unittest

from errors import RepositoryError
from maven import MavenRepository
from tests.maven_server import MavenServer

CLOSED_PORT_URL = "http://127.0.0.1:9"


class MavenRepositoryTest(unittest.TestCase):
    """Прямые зависимости пакетов из локального тестового репозитория."""

    @classmethod
    def setUpClass(cls):
        """Запустить HTTP-сервер с тестовыми POM."""
        cls.server = MavenServer()
        cls.server.start()

    @classmethod
    def tearDownClass(cls):
        """Остановить HTTP-сервер."""
        cls.server.stop()

    def dependencies(self, package):
        """Вернуть прямые зависимости пакета строками."""
        repository = MavenRepository(self.server.url + "/")
        return [str(item) for item in repository.direct_dependencies(package)]

    def test_effective_dependencies(self):
        """Наследование, свойства, dependencyManagement и импорт BOM."""
        self.assertEqual(self.dependencies("org.example:app:1.2.3"), [
            "org.slf4j:slf4j-api:2.0.13 [compile]",
            "com.google.guava:guava:33.2.1-jre [runtime]",
            "org.example:core:1.2.3 [compile]",
            "org.apache.commons:commons-lang3:3.14.0 [compile] (optional)",
            "javax.servlet:javax.servlet-api:4.0.1 [provided]",
            "junit:junit:4.13.2 [test]",
        ])

    def test_no_dependencies(self):
        """POM без зависимостей и без пространства имён."""
        self.assertEqual(self.dependencies("org.example:core:1.2.3"), [])

    def test_self_import_and_cyclic_properties(self):
        """Циклический импорт BOM и циклические свойства."""
        self.assertEqual(self.dependencies("org.example:self-import:1.0"), [
            "org.example:unmanaged:? [compile]",
            "org.example:looped:${a} [compile]",
        ])

    def test_not_found(self):
        """Пакет отсутствует в репозитории."""
        with self.assertRaisesRegex(RepositoryError, "not found.*nope"):
            self.dependencies("org.example:nope:1.0")

    def test_missing_parent(self):
        """Родительский POM отсутствует в репозитории."""
        with self.assertRaisesRegex(
                RepositoryError, "cannot load parent POM .*missing-parent"):
            self.dependencies("org.example:orphan:1.0")

    def test_cyclic_parent(self):
        """Циклическая цепочка родительских POM."""
        with self.assertRaisesRegex(RepositoryError, "cyclic parent POM"):
            self.dependencies("org.example:cycle-a:1.0")

    def test_malformed_pom(self):
        """Некорректный XML в файле POM."""
        with self.assertRaisesRegex(RepositoryError, "malformed POM"):
            self.dependencies("org.example:broken:1.0")

    def test_unreachable_repository(self):
        """Репозиторий недоступен."""
        repository = MavenRepository(CLOSED_PORT_URL)
        with self.assertRaisesRegex(RepositoryError, "cannot reach"):
            repository.direct_dependencies("org.example:app:1.2.3")


if __name__ == "__main__":
    unittest.main()
