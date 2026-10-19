"""Разбор файлов описания пакетов Maven (POM).

Модуль читает из XML только то, что нужно для получения зависимостей:
координаты пакета и родителя, свойства, зависимости и управляемые
версии (dependencyManagement). Значения не интерпретируются: подстановка
свойств и наследование выполняются в модуле maven.
"""

from xml.etree import ElementTree
from dataclasses import dataclass, field, replace

DEFAULT_SCOPE = "compile"
IMPORT_SCOPE = "import"
POM_TYPE = "pom"
TRUE = "true"


class PomError(Exception):
    """Файл POM не удаётся разобрать."""


@dataclass(frozen=True)
class Coordinates:
    """Координаты пакета Maven: groupId, artifactId и version."""

    group: str
    artifact: str
    version: str

    @classmethod
    def parse(cls, text):
        """Создать координаты из строки groupId:artifactId:version."""
        group, artifact, version = text.split(":")
        return cls(group, artifact, version)

    def pom_path(self):
        """Вернуть путь к файлу POM относительно корня репозитория."""
        name = f"{self.artifact}-{self.version}.pom"
        return "/".join([
            self.group.replace(".", "/"), self.artifact, self.version, name,
        ])

    def __str__(self):
        """Вернуть координаты в виде groupId:artifactId:version."""
        return f"{self.group}:{self.artifact}:{self.version}"


@dataclass(frozen=True)
class Dependency:
    """Зависимость в том виде, в котором она записана в POM.

    Пустая строка в version или scope означает, что значение не задано
    и должно быть взято из dependencyManagement или по умолчанию.
    """

    group: str
    artifact: str
    version: str = ""
    scope: str = ""
    optional: str = ""
    kind: str = ""

    @property
    def key(self):
        """Ключ зависимости для поиска управляемой версии."""
        return (self.group, self.artifact)

    @property
    def is_optional(self):
        """Помечена ли зависимость как необязательная."""
        return self.optional.strip().lower() == TRUE

    @property
    def is_bom_import(self):
        """Является ли запись импортом BOM в dependencyManagement."""
        return self.scope == IMPORT_SCOPE and self.kind == POM_TYPE

    def map_values(self, func):
        """Вернуть копию, применив func ко всем строковым полям."""
        return replace(
            self, group=func(self.group), artifact=func(self.artifact),
            version=func(self.version), scope=func(self.scope),
            optional=func(self.optional), kind=func(self.kind),
        )

    def __str__(self):
        """Вернуть строку вида groupId:artifactId:version [scope]."""
        version = self.version or "?"
        text = f"{self.group}:{self.artifact}:{version}"
        text += f" [{self.scope or DEFAULT_SCOPE}]"
        if self.is_optional:
            text += " (optional)"
        return text


@dataclass
class Pom:
    """Содержимое одного файла POM без учёта наследования."""

    group: str
    artifact: str
    version: str
    parent: Coordinates = None
    properties: dict = field(default_factory=dict)
    dependencies: list = field(default_factory=list)
    managed: list = field(default_factory=list)


def local_name(tag):
    """Вернуть имя тега без пространства имён XML."""
    return tag.rsplit("}", 1)[-1]


def child(element, name):
    """Вернуть дочерний элемент с именем name или None."""
    if element is None:
        return None
    for item in element:
        if local_name(item.tag) == name:
            return item
    return None


def text_of(element, name):
    """Вернуть текст дочернего элемента name (пустая строка, если нет)."""
    item = child(element, name)
    if item is None or item.text is None:
        return ""
    return item.text.strip()


def parse_dependency(element):
    """Разобрать элемент dependency."""
    return Dependency(
        group=text_of(element, "groupId"),
        artifact=text_of(element, "artifactId"),
        version=text_of(element, "version"),
        scope=text_of(element, "scope"),
        optional=text_of(element, "optional"),
        kind=text_of(element, "type"),
    )


def parse_dependencies(element):
    """Разобрать все элементы dependency внутри element."""
    container = child(element, "dependencies")
    if container is None:
        return []
    return [parse_dependency(item) for item in container
            if local_name(item.tag) == "dependency"]


def parse_parent(project):
    """Разобрать координаты родительского POM или вернуть None."""
    element = child(project, "parent")
    if element is None:
        return None
    return Coordinates(
        text_of(element, "groupId"),
        text_of(element, "artifactId"),
        text_of(element, "version"),
    )


def parse_properties(project):
    """Разобрать раздел properties в словарь."""
    element = child(project, "properties")
    if element is None:
        return {}
    return {local_name(item.tag): (item.text or "").strip()
            for item in element}


def parse_pom(data):
    """Разобрать содержимое файла POM (bytes или str) в объект Pom."""
    try:
        project = ElementTree.fromstring(data)
    except ElementTree.ParseError as error:
        raise PomError(f"malformed POM: {error}") from error
    if local_name(project.tag) != "project":
        raise PomError("malformed POM: root element is not <project>")
    parent = parse_parent(project) or Coordinates("", "", "")
    return Pom(
        group=text_of(project, "groupId") or parent.group,
        artifact=text_of(project, "artifactId"),
        version=text_of(project, "version") or parent.version,
        parent=parent if parent.artifact else None,
        properties=parse_properties(project),
        dependencies=parse_dependencies(project),
        managed=parse_dependencies(child(project, "dependencyManagement")),
    )
