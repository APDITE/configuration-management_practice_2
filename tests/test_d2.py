"""Тесты описания графа на языке диаграмм D2."""

import os
import shutil
import subprocess
import tempfile
import unittest

from d2 import cycle_edges, node_label, quote, to_d2
from graph import build_graph, find_cycles
from testrepo import FileRepository

ROOT = os.path.join(os.path.dirname(__file__), "..")
D2 = shutil.which("d2")


def describe(name, root="A"):
    """Вернуть описание D2 графа из repos/<name>.txt."""
    repository = FileRepository(os.path.join(ROOT, "repos", name + ".txt"))
    graph = build_graph(root, repository.dependency_names)
    return to_d2(graph, root, find_cycles(graph, root))


class QuoteTest(unittest.TestCase):
    """Строки и подписи узлов D2."""

    def test_quote(self):
        """Кавычки и обратная косая черта экранируются."""
        self.assertEqual(quote('a"b\\c'), '"a\\"b\\\\c"')

    def test_maven_label(self):
        """Части координат Maven выводятся на отдельных строках."""
        self.assertEqual(
            node_label("org.slf4j:slf4j-api:2.0.13"),
            '"org.slf4j\\nslf4j-api\\n2.0.13"')

    def test_test_label(self):
        """Имя пакета тестового репозитория выводится как есть."""
        self.assertEqual(node_label("A"), '"A"')


class ToD2Test(unittest.TestCase):
    """Описание графа на языке D2."""

    def test_diamond(self):
        """Узлы, выделение заданного пакета и рёбра ромба."""
        self.assertEqual(describe("simple"), [
            "direction: down",
            'n0: "A"', 'n0.style.fill: "#cfe8ff"',
            'n1: "B"', 'n2: "D"', 'n3: "C"',
            "n0 -> n1", "n0 -> n3", "n1 -> n2", "n3 -> n2",
        ])

    def test_cycle_edges_highlighted(self):
        """Рёбра цикла выделяются, остальные -- нет."""
        lines = describe("cycle")
        self.assertIn("n2 -> n0: cycle {style.stroke: red}", lines)
        self.assertIn("n2 -> n3", lines)

    def test_self_loop(self):
        """Петля -- ребро из узла в себя."""
        self.assertIn("n0 -> n0: cycle {style.stroke: red}", describe("self"))

    def test_unresolved_package(self):
        """Недоступный пакет обводится пунктиром."""
        lines = to_d2({"A": ["B"], "B": []}, "A", failures={"B"})
        self.assertIn("n1.style.stroke-dash: 3", lines)

    def test_cycle_edges(self):
        """Рёбра циклов, включая петлю."""
        self.assertEqual(
            cycle_edges([["A", "B", "A"], ["C", "C"]]),
            {("A", "B"), ("B", "A"), ("C", "C")})

    @unittest.skipIf(D2 is None, "компилятор d2 не установлен")
    def test_compiles_with_d2(self):
        """Описание компилируется утилитой d2 без ошибок."""
        for name in ("simple", "cycle", "self", "complex"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as path:
                source = os.path.join(path, "graph.d2")
                with open(source, "w", encoding="utf-8") as file:
                    file.write("\n".join(describe(name)) + "\n")
                result = subprocess.run(
                    [D2, source, os.path.join(path, "graph.svg")],
                    capture_output=True, text=True, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
