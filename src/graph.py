"""Построение графа зависимостей и операции над ним.

Граф хранится как словарь: пакет -> список его зависимостей. Порядок
ключей совпадает с порядком посещения пакетов при обходе в глубину.
Все обходы выполняются без рекурсии, с явным стеком, поэтому глубина
графа не ограничена глубиной стека вызовов Python.
"""

WHITE = 0
GRAY = 1
BLACK = 2


def build_graph(root, get_dependencies):
    """Построить граф зависимостей пакета root обходом в глубину (DFS).

    get_dependencies(package) возвращает список прямых зависимостей
    пакета. Каждый пакет запрашивается ровно один раз, поэтому
    циклические зависимости не приводят к зацикливанию.
    """
    graph = {}
    stack = [root]
    while stack:
        package = stack.pop()
        if package in graph:
            continue
        dependencies = list(dict.fromkeys(get_dependencies(package)))
        graph[package] = dependencies
        for dependency in reversed(dependencies):
            if dependency not in graph:
                stack.append(dependency)
    return graph


def find_cycles(graph, root):
    """Найти циклы, достижимые из root, обходом в глубину без рекурсии.

    Возвращает список циклов; каждый цикл -- список пакетов, в котором
    первый и последний элементы совпадают, например [A, B, A].
    Цикл обнаруживается по обратному ребру -- ребру в пакет, который
    сейчас находится на пути обхода (цвет GRAY).
    """
    color = {root: GRAY}
    path = [root]
    stack = [iter(graph.get(root, []))]
    cycles = []
    while stack:
        dependency = next(stack[-1], None)
        if dependency is None:
            color[path.pop()] = BLACK
            stack.pop()
        elif color.get(dependency, WHITE) == GRAY:
            start = path.index(dependency)
            cycles.append(path[start:] + [dependency])
        elif color.get(dependency, WHITE) == WHITE:
            color[dependency] = GRAY
            path.append(dependency)
            stack.append(iter(graph.get(dependency, [])))
    return cycles


def load_order(graph, root):
    """Вернуть порядок загрузки пакетов, достижимых из root.

    Каждый пакет идёт после всех своих зависимостей, root -- последним.
    Это обратный порядок обхода в глубину (post-order): пакет
    добавляется в результат, когда обработаны все его зависимости.
    Обход выполняется без рекурсии. Ребро в пакет, находящийся на
    текущем пути (цикл), пропускается: внутри цикла порядок загрузки
    определяется тем, с какого пакета цикл был достигнут.
    """
    order = []
    color = {root: GRAY}
    stack = [(root, iter(graph.get(root, [])))]
    while stack:
        package, dependencies = stack[-1]
        dependency = next(dependencies, None)
        if dependency is None:
            stack.pop()
            color[package] = BLACK
            order.append(package)
        elif color.get(dependency, WHITE) == WHITE:
            color[dependency] = GRAY
            stack.append((dependency, iter(graph.get(dependency, []))))
    return order
