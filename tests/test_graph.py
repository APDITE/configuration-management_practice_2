"""Тесты построения графа зависимостей и поиска циклов."""

import os
import sys
import unittest

from graph import build_graph, find_cycles, load_order
from testrepo import FileRepository

ROOT = os.path.join(os.path.dirname(__file__), "..")
CHAIN_LENGTH = 10000


def load(name):
    """Загрузить тестовый репозиторий repos/<name>.txt."""
    repository = FileRepository(os.path.join(ROOT, "repos", name + ".txt"))
    return repository.dependency_names


def counting(get_dependencies, calls):
    """Обернуть get_dependencies, подсчитывая вызовы в словаре calls."""
    def wrapper(package):
        """Вернуть зависимости пакета и учесть вызов."""
        calls[package] = calls.get(package, 0) + 1
        return get_dependencies(package)
    return wrapper


class BuildGraphTest(unittest.TestCase):
    """Построение графа обходом в глубину без рекурсии."""

    def test_diamond(self):
        """Общая зависимость посещается один раз, порядок -- DFS."""
        calls = {}
        graph = build_graph("A", counting(load("simple"), calls))
        self.assertEqual(graph, {
            "A": ["B", "C"], "B": ["D"], "D": [], "C": ["D"]})
        self.assertEqual(list(graph), ["A", "B", "D", "C"])
        self.assertEqual(set(calls.values()), {1})

    def test_cycle(self):
        """Циклическая зависимость не приводит к зацикливанию."""
        graph = build_graph("A", load("cycle"))
        self.assertEqual(list(graph), ["A", "B", "C", "D"])
        self.assertEqual(graph["C"], ["A", "D"])

    def test_self_loop(self):
        """Пакет, зависящий сам от себя."""
        graph = build_graph("A", load("self"))
        self.assertEqual(graph, {"A": ["A", "B"], "B": []})

    def test_only_reachable(self):
        """В граф попадают только пакеты, достижимые из корня."""
        graph = build_graph("A", load("complex"))
        self.assertEqual(set(graph), set("ABCDEFGH"))
        self.assertNotIn("X", graph)

    def test_duplicate_dependencies(self):
        """Повторы в списке зависимостей отбрасываются."""
        graph = build_graph("A", {"A": ["B", "B"], "B": []}.get)
        self.assertEqual(graph["A"], ["B"])

    def test_deep_chain_without_recursion(self):
        """Цепочка длиннее предела рекурсии Python обходится полностью."""
        self.assertGreater(CHAIN_LENGTH, sys.getrecursionlimit())
        chain = {i: [i + 1] for i in range(CHAIN_LENGTH)}
        chain[CHAIN_LENGTH] = []
        graph = build_graph(0, chain.get)
        self.assertEqual(len(graph), CHAIN_LENGTH + 1)
        self.assertEqual(find_cycles(graph, 0), [])


class FindCyclesTest(unittest.TestCase):
    """Поиск циклических зависимостей."""

    def cycles(self, name, root="A"):
        """Найти циклы в тестовом репозитории, начиная с root."""
        return find_cycles(build_graph(root, load(name)), root)

    def test_no_cycles(self):
        """Ромб без циклов."""
        self.assertEqual(self.cycles("simple"), [])

    def test_simple_cycle(self):
        """Цикл через корневой пакет."""
        self.assertEqual(self.cycles("cycle"), [["A", "B", "C", "A"]])

    def test_self_loop(self):
        """Петля: пакет зависит сам от себя."""
        self.assertEqual(self.cycles("self"), [["A", "A"]])

    def test_several_cycles(self):
        """Несколько циклов, не проходящих через корень."""
        self.assertEqual(self.cycles("complex"), [
            ["B", "E", "H", "B"], ["C", "F", "C"]])

    def test_cycle_before_root(self):
        """Цикл из корня и циклы глубже в графе."""
        self.assertEqual(self.cycles("complex", "X"), [
            ["X", "Y", "X"], ["B", "E", "H", "B"], ["C", "F", "C"]])


class LoadOrderTest(unittest.TestCase):
    """Порядок загрузки зависимостей."""

    def order(self, name, root="A"):
        """Порядок загрузки для тестового репозитория."""
        return load_order(build_graph(root, load(name)), root)

    def test_diamond(self):
        """Зависимости загружаются раньше зависящих от них пакетов."""
        self.assertEqual(self.order("simple"), ["D", "B", "C", "A"])

    def test_each_package_after_dependencies(self):
        """Для графа без циклов каждый пакет идёт после зависимостей."""
        graph = build_graph("A", load("simple"))
        order = load_order(graph, "A")
        for package, dependencies in graph.items():
            for dependency in dependencies:
                with self.subTest(package=package, dependency=dependency):
                    self.assertLess(
                        order.index(dependency), order.index(package))

    def test_all_reachable_once(self):
        """Каждый достижимый пакет загружается ровно один раз."""
        order = self.order("complex")
        self.assertEqual(sorted(order), sorted(set("ABCDEFGH")))
        self.assertEqual(order[-1], "A")

    def test_cycle(self):
        """Цикл не мешает построить порядок; корень -- последний."""
        self.assertEqual(self.order("cycle"), ["D", "C", "B", "A"])
        self.assertEqual(self.order("self"), ["B", "A"])

    def test_leaf(self):
        """Пакет без зависимостей."""
        self.assertEqual(self.order("simple", "D"), ["D"])

    def test_deep_chain_without_recursion(self):
        """Цепочка длиннее предела рекурсии: порядок от конца к началу."""
        chain = {i: [i + 1] for i in range(CHAIN_LENGTH)}
        chain[CHAIN_LENGTH] = []
        order = load_order(build_graph(0, chain.get), 0)
        self.assertEqual(order, list(range(CHAIN_LENGTH, -1, -1)))


if __name__ == "__main__":
    unittest.main()
