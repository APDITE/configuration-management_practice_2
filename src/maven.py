"""Получение прямых зависимостей пакета из удалённого репозитория Maven.

Файлы POM скачиваются по HTTP(S) средствами стандартной библиотеки и
разбираются модулем pom. Перед выдачей зависимостей выполняются те же
шаги, что и в Maven при построении эффективной модели:

1. загрузка цепочки родительских POM (элемент parent);
2. объединение свойств (properties) от предков к потомку и подстановка
   значений вида ${name}, включая ${project.version} и аналоги;
3. наследование зависимостей и dependencyManagement от родителей;
4. импорт BOM (scope import, type pom) в dependencyManagement;
5. заполнение отсутствующих version и scope из dependencyManagement.
"""

import re
import urllib.error
import urllib.request
from dataclasses import replace

from errors import RepositoryError
from pom import Coordinates, PomError, parse_pom

TIMEOUT_SECONDS = 30
MAX_PARENTS = 32
MAX_PASSES = 10
HTTP_NOT_FOUND = 404
USER_AGENT = "depviz/0.2 (educational dependency visualizer)"
PROPERTY = re.compile(r"\$\{([^}]+)\}")
BUILTIN_PREFIXES = ("project.", "pom.")


def interpolate(value, properties):
    """Подставить значения свойств вместо ${name} в строке value.

    Подстановка повторяется, пока значение меняется (свойства могут
    ссылаться друг на друга), но не более MAX_PASSES раз, что защищает
    от циклических ссылок. Неизвестные свойства остаются как есть.
    """
    for _ in range(MAX_PASSES):
        result = PROPERTY.sub(
            lambda match: properties.get(match.group(1), match.group(0)),
            value)
        if result == value:
            break
        value = result
    return value


def builtin_properties(pom):
    """Вернуть встроенные свойства project.* для данного POM."""
    values = {
        "groupId": pom.group,
        "artifactId": pom.artifact,
        "version": pom.version,
    }
    if pom.parent is not None:
        values["parent.groupId"] = pom.parent.group
        values["parent.artifactId"] = pom.parent.artifact
        values["parent.version"] = pom.parent.version
    return {prefix + name: value
            for prefix in BUILTIN_PREFIXES
            for name, value in values.items()}


def collect_properties(chain):
    """Объединить свойства цепочки POM (потомок переопределяет предка)."""
    properties = {}
    for pom in reversed(chain):
        properties.update(pom.properties)
    properties.update(builtin_properties(chain[0]))
    return properties


def collect_dependencies(chain, properties):
    """Собрать зависимости цепочки POM с учётом наследования.

    Зависимость потомка заменяет одноимённую зависимость предка.
    """
    result = {}
    for pom in chain:
        for dependency in pom.dependencies:
            item = dependency.map_values(
                lambda value: interpolate(value, properties))
            result.setdefault(item.key, item)
    return list(result.values())


def apply_management(dependency, managed):
    """Заполнить version и scope зависимости из dependencyManagement."""
    rule = managed.get(dependency.key)
    if rule is None:
        return dependency
    return replace(
        dependency,
        version=dependency.version or rule.version,
        scope=dependency.scope or rule.scope,
    )


class MavenRepository:
    """Удалённый репозиторий Maven, доступный по URL-адресу."""

    def __init__(self, url):
        """Создать репозиторий с корнем по адресу url."""
        self.url = url.rstrip("/")
        self._cache = {}

    def pom_url(self, coords):
        """Вернуть URL-адрес файла POM для координат coords."""
        return f"{self.url}/{coords.pom_path()}"

    def download(self, url):
        """Скачать файл по адресу url и вернуть его содержимое."""
        request = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(
                    request, timeout=TIMEOUT_SECONDS) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code == HTTP_NOT_FOUND:
                raise RepositoryError(
                    f"package not found in repository: {url}") from error
            raise RepositoryError(
                f"HTTP error {error.code} {error.reason}: {url}") from error
        except urllib.error.URLError as error:
            raise RepositoryError(
                f"cannot reach repository: {error.reason}") from error
        except OSError as error:
            raise RepositoryError(f"network error: {error}") from error

    def load(self, coords):
        """Скачать и разобрать POM пакета (с кэшированием)."""
        if coords not in self._cache:
            url = self.pom_url(coords)
            try:
                self._cache[coords] = parse_pom(self.download(url))
            except PomError as error:
                raise RepositoryError(f"{url}: {error}") from error
        return self._cache[coords]

    def lineage(self, coords):
        """Вернуть цепочку POM: сам пакет, его родитель, ... до корня."""
        chain = [self.load(coords)]
        seen = {coords}
        while chain[-1].parent is not None:
            parent = chain[-1].parent
            if parent in seen:
                raise RepositoryError(f"cyclic parent POM: {parent}")
            if len(chain) > MAX_PARENTS:
                raise RepositoryError(f"too many parent POMs for {coords}")
            seen.add(parent)
            chain.append(self.load_parent(parent, chain[-1]))
        return chain

    def load_parent(self, parent, pom):
        """Загрузить родительский POM, уточнив сообщение об ошибке."""
        try:
            return self.load(parent)
        except RepositoryError as error:
            raise RepositoryError(
                f"cannot load parent POM {parent} of "
                f"{pom.group}:{pom.artifact}:{pom.version}: {error}"
            ) from error

    def managed_versions(self, chain, properties, imported):
        """Построить dependencyManagement цепочки POM.

        Возвращает словарь (groupId, artifactId) -> Dependency. Записи
        потомка важнее записей предка, явно объявленные записи важнее
        импортированных из BOM. imported -- координаты уже
        импортируемых BOM (защита от циклического импорта).
        """
        managed = {}
        boms = []
        for pom in chain:
            for declared in pom.managed:
                rule = declared.map_values(
                    lambda value: interpolate(value, properties))
                if rule.is_bom_import:
                    boms.append(rule)
                else:
                    managed.setdefault(rule.key, rule)
        for bom in boms:
            for key, rule in self.import_bom(bom, imported).items():
                managed.setdefault(key, rule)
        return managed

    def import_bom(self, bom, imported):
        """Вернуть dependencyManagement импортируемого BOM."""
        coords = Coordinates(bom.group, bom.artifact, bom.version)
        if coords in imported:
            return {}
        chain = self.lineage(coords)
        return self.managed_versions(
            chain, collect_properties(chain), imported | {coords})

    def direct_dependencies(self, package):
        """Вернуть прямые зависимости пакета groupId:artifactId:version."""
        coords = Coordinates.parse(package)
        chain = self.lineage(coords)
        properties = collect_properties(chain)
        managed = self.managed_versions(
            chain, properties, frozenset({coords}))
        return [apply_management(dependency, managed)
                for dependency in collect_dependencies(chain, properties)]
