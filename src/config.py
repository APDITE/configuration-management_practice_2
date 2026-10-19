"""Параметры командной строки визуализатора зависимостей."""

import argparse
from dataclasses import dataclass

PROG = "depviz"
MODE_REMOTE = "remote"
MODE_TEST = "test"
MODES = (MODE_REMOTE, MODE_TEST)


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


def parse_args(argv=None):
    """Разобрать параметры командной строки и вернуть Config."""
    args = build_parser().parse_args(argv)
    return Config(package=args.package, repo=args.repo, mode=args.mode)
