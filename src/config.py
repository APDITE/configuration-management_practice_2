"""Параметры командной строки визуализатора зависимостей."""

import argparse
import os
import re
from dataclasses import dataclass
from urllib.parse import urlparse

PROG = "depviz"
MODE_REMOTE = "remote"
MODE_TEST = "test"
MODES = (MODE_REMOTE, MODE_TEST)
URL_SCHEMES = ("http", "https")
MAVEN_PART = r"[A-Za-z0-9_.-]+"
MAVEN_PACKAGE = re.compile(
    rf"^{MAVEN_PART}:{MAVEN_PART}:{MAVEN_PART}$")
TEST_PACKAGE = re.compile(r"^[A-Z]+$")


class ConfigError(Exception):
    """Ошибка в значении параметра командной строки."""


@dataclass(frozen=True)
class Config:
    """Настройки, заданные пользователем.

    package -- имя анализируемого пакета;
    repo -- URL-адрес репозитория или путь к файлу тестового репозитория;
    mode -- режим работы: remote (реальный репозиторий) или test
    (тестовый репозиторий из файла).
    """

    package: str
    repo: str
    mode: str = MODE_REMOTE

    def items(self):
        """Вернуть параметры как список пар (ключ, значение)."""
        return [
            ("package", self.package),
            ("repo", self.repo),
            ("mode", self.mode),
        ]


def build_parser():
    """Создать парсер параметров командной строки."""
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Визуализатор графа зависимостей пакетов Maven.",
    )
    parser.add_argument(
        "-p", "--package", required=True, metavar="NAME",
        help="имя пакета: groupId:artifactId:version "
             "или большие латинские буквы в режиме test",
    )
    parser.add_argument(
        "-r", "--repo", required=True, metavar="URL_OR_PATH",
        help="URL-адрес репозитория или путь к файлу тестового "
             "репозитория",
    )
    parser.add_argument(
        "-m", "--mode", choices=MODES, default=MODE_REMOTE,
        help="режим работы с репозиторием (по умолчанию remote)",
    )
    return parser


def validate_package(package, mode):
    """Проверить имя пакета с учётом режима работы."""
    if not package.strip():
        raise ConfigError("--package: empty package name")
    if mode == MODE_TEST:
        if not TEST_PACKAGE.match(package):
            raise ConfigError(
                f"--package: '{package}': in test mode the package "
                "name must consist of capital Latin letters")
    elif not MAVEN_PACKAGE.match(package):
        raise ConfigError(
            f"--package: '{package}': expected "
            "groupId:artifactId:version")


def validate_url(repo):
    """Проверить URL-адрес реального репозитория."""
    parts = urlparse(repo)
    if parts.scheme not in URL_SCHEMES or not parts.netloc:
        raise ConfigError(
            f"--repo: '{repo}': expected an http(s) URL "
            "of a Maven repository")


def validate_repo_file(repo):
    """Проверить путь к файлу тестового репозитория."""
    if not os.path.exists(repo):
        raise ConfigError(
            f"--repo: '{repo}': no such test repository file")
    if not os.path.isfile(repo):
        raise ConfigError(f"--repo: '{repo}': not a file")
    if not os.access(repo, os.R_OK):
        raise ConfigError(f"--repo: '{repo}': permission denied")


def validate(config):
    """Проверить все параметры; при ошибке бросить ConfigError."""
    validate_package(config.package, config.mode)
    if not config.repo.strip():
        raise ConfigError("--repo: empty repository location")
    if config.mode == MODE_TEST:
        validate_repo_file(config.repo)
    else:
        validate_url(config.repo)


def parse_args(argv=None):
    """Разобрать и проверить параметры командной строки.

    При ошибке выводит сообщение и завершает работу с кодом 2.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    config = Config(package=args.package, repo=args.repo, mode=args.mode)
    try:
        validate(config)
    except ConfigError as error:
        parser.error(str(error))
    return config
