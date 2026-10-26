"""Тесты разбора POM и подстановки свойств."""

import unittest

from maven import interpolate
from pom import Coordinates, Dependency, PomError, parse_pom

NAMESPACED_POM = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <parent>
    <groupId>org.example</groupId>
    <artifactId>parent</artifactId>
    <version>1.0</version>
  </parent>
  <artifactId>child</artifactId>
  <properties>
    <x.version>2.0</x.version>
  </properties>
  <dependencyManagement>
    <dependencies>
      <dependency>
        <groupId>org.example</groupId>
        <artifactId>bom</artifactId>
        <version>1.0</version>
        <type>pom</type>
        <scope>import</scope>
      </dependency>
    </dependencies>
  </dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>org.example</groupId>
      <artifactId>x</artifactId>
      <version>${x.version}</version>
      <scope>test</scope>
      <optional>true</optional>
    </dependency>
  </dependencies>
</project>
"""


class CoordinatesTest(unittest.TestCase):
    """Координаты пакета Maven."""

    def test_parse_and_str(self):
        """Разбор строки и обратное преобразование."""
        coords = Coordinates.parse("org.slf4j:slf4j-api:2.0.13")
        self.assertEqual(coords.group, "org.slf4j")
        self.assertEqual(coords.artifact, "slf4j-api")
        self.assertEqual(coords.version, "2.0.13")
        self.assertEqual(str(coords), "org.slf4j:slf4j-api:2.0.13")

    def test_pom_path(self):
        """Путь к POM строится по правилам репозитория Maven."""
        coords = Coordinates.parse("org.slf4j:slf4j-api:2.0.13")
        self.assertEqual(
            coords.pom_path(),
            "org/slf4j/slf4j-api/2.0.13/slf4j-api-2.0.13.pom")


class ParsePomTest(unittest.TestCase):
    """Разбор XML файла POM."""

    def test_namespaced_pom(self):
        """POM с пространством имён и наследованием координат."""
        pom = parse_pom(NAMESPACED_POM)
        self.assertEqual(
            (pom.group, pom.artifact, pom.version),
            ("org.example", "child", "1.0"))
        self.assertEqual(
            pom.parent, Coordinates.parse("org.example:parent:1.0"))
        self.assertEqual(pom.properties, {"x.version": "2.0"})
        self.assertEqual(pom.dependencies, [Dependency(
            "org.example", "x", "${x.version}", "test", "true")])
        self.assertTrue(pom.dependencies[0].is_optional)
        self.assertTrue(pom.managed[0].is_bom_import)

    def test_minimal_pom(self):
        """POM без пространства имён, родителя и зависимостей."""
        pom = parse_pom(
            "<project><groupId>g</groupId><artifactId>a</artifactId>"
            "<version>1</version></project>")
        self.assertIsNone(pom.parent)
        self.assertEqual(pom.dependencies, [])
        self.assertEqual(pom.managed, [])

    def test_malformed_xml(self):
        """Некорректный XML."""
        with self.assertRaisesRegex(PomError, "malformed POM"):
            parse_pom("<project><groupId>g</project>")

    def test_wrong_root(self):
        """Корневой элемент не project."""
        with self.assertRaisesRegex(PomError, "not <project>"):
            parse_pom("<settings/>")


class DependencyStrTest(unittest.TestCase):
    """Строковое представление зависимости."""

    def test_default_scope(self):
        """Без scope выводится compile."""
        self.assertEqual(str(Dependency("g", "a", "1")), "g:a:1 [compile]")

    def test_optional_and_unknown_version(self):
        """Необязательная зависимость без версии."""
        dependency = Dependency("g", "a", scope="test", optional="true")
        self.assertEqual(str(dependency), "g:a:? [test] (optional)")


class TransitiveTest(unittest.TestCase):
    """Какие зависимости передаются потребителю пакета."""

    def test_transitive_scopes(self):
        """compile (по умолчанию) и runtime передаются."""
        for scope in ("", "compile", "runtime"):
            with self.subTest(scope=scope):
                self.assertTrue(Dependency("g", "a", "1", scope).is_transitive)

    def test_not_transitive(self):
        """test, provided, system и optional не передаются."""
        for scope in ("test", "provided", "system"):
            with self.subTest(scope=scope):
                self.assertFalse(
                    Dependency("g", "a", "1", scope).is_transitive)
        optional = Dependency("g", "a", "1", optional="true")
        self.assertFalse(optional.is_transitive)

    def test_coordinates(self):
        """Координаты зависимости; неизвестная версия -- «?»."""
        self.assertEqual(Dependency("g", "a", "1").coordinates, "g:a:1")
        self.assertEqual(Dependency("g", "a").coordinates, "g:a:?")


class InterpolateTest(unittest.TestCase):
    """Подстановка свойств ${name}."""

    def test_simple_and_nested(self):
        """Простая и вложенная подстановка."""
        properties = {"a": "1", "b": "${a}.2", "c": "${b}"}
        self.assertEqual(interpolate("v${c}-${a}", properties), "v1.2-1")

    def test_unknown_property(self):
        """Неизвестное свойство остаётся без изменений."""
        self.assertEqual(interpolate("${nope}", {}), "${nope}")

    def test_cyclic_properties(self):
        """Циклические ссылки не приводят к зацикливанию."""
        result = interpolate("${a}", {"a": "${b}", "b": "${a}"})
        self.assertIn(result, ("${a}", "${b}"))


if __name__ == "__main__":
    unittest.main()
