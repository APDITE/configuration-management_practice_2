"""Описание графа зависимостей на языке диаграмм D2.

Каждый пакет -- узел с коротким идентификатором n0, n1, ... и подписью
из полного имени пакета (части координат Maven выводятся на отдельных
строках). Каждая зависимость -- ребро «пакет -> зависимость».
Короткие идентификаторы не требуют экранирования двоеточий и точек в
именах Maven и сохраняют строки описания короткими.

Оформление: заданный пакет выделен заливкой, пакеты, которые не
удалось загрузить, -- пунктирной рамкой, рёбра циклов -- красным
цветом с подписью cycle.
"""

DIRECTION = "direction: down"
ROOT_STYLE = 'style.fill: "#cfe8ff"'
UNRESOLVED_STYLE = "style.stroke-dash: 3"
CYCLE_EDGE = ": cycle {style.stroke: red}"
NAME_PARTS_SEPARATOR = ":"


def quote(text):
    """Вернуть строку D2 в двойных кавычках с экранированием."""
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return '"' + escaped + '"'


def node_label(package):
    """Вернуть подпись узла: части координат Maven на отдельных строках."""
    return quote(package).replace(NAME_PARTS_SEPARATOR, "\\n")


def cycle_edges(cycles):
    """Вернуть множество рёбер (пакет, зависимость), входящих в циклы."""
    return {edge for cycle in cycles for edge in zip(cycle, cycle[1:])}


def node_lines(graph, root, failures, ids):
    """Вернуть строки D2 с описанием узлов и их оформления."""
    lines = []
    for package in graph:
        node = ids[package]
        lines.append(f"{node}: {node_label(package)}")
        if package == root:
            lines.append(f"{node}.{ROOT_STYLE}")
        if package in failures:
            lines.append(f"{node}.{UNRESOLVED_STYLE}")
    return lines


def edge_lines(graph, cycles, ids):
    """Вернуть строки D2 с описанием рёбер графа."""
    in_cycle = cycle_edges(cycles)
    lines = []
    for package, dependencies in graph.items():
        for dependency in dependencies:
            line = f"{ids[package]} -> {ids[dependency]}"
            if (package, dependency) in in_cycle:
                line += CYCLE_EDGE
            lines.append(line)
    return lines


def to_d2(graph, root, cycles=(), failures=()):
    """Вернуть описание графа на языке D2 в виде списка строк.

    graph -- словарь «пакет -> список зависимостей» (все пакеты графа
    являются его ключами), root -- заданный пакет, cycles -- найденные
    циклы, failures -- пакеты, которые не удалось загрузить.
    """
    ids = {package: f"n{number}" for number, package in enumerate(graph)}
    return ([DIRECTION]
            + node_lines(graph, root, failures, ids)
            + edge_lines(graph, cycles, ids))
