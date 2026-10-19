# Визуализатор графа зависимостей Maven (вариант 17)

Практическая работа № 2 по дисциплине «Конфигурационное управление».

## Общее описание

Консольное приложение (CLI) на Python 3 для построения и визуализации
графа зависимостей пакетов Java (Maven). Готовые менеджеры пакетов и
библиотеки для получения зависимостей не используются.

Текущее состояние — **этап 1**: минимальный прототип с конфигурацией.
Приложение принимает параметры командной строки, проверяет их и выводит
в формате `ключ=значение`.

Сторонние зависимости не требуются — только стандартная библиотека
Python 3.8+.

## Структура репозитория

```
src/
  depviz.py   точка входа: разбор параметров и их вывод
  config.py   параметры командной строки и их проверка
repos/        тестовые репозитории для режима test
scripts/      скрипты ОС для демонстрации работы
tests/        модульные тесты (unittest)
run.sh        запуск приложения и тестов
```

## Настройки

Все параметры задаются опциями командной строки:

- `-p`, `--package NAME` — имя анализируемого пакета (обязательный):
  - в режиме `remote` — координаты Maven `groupId:artifactId:version`,
    например `org.slf4j:slf4j-api:2.0.13`;
  - в режиме `test` — большие латинские буквы, например `A`.
- `-r`, `--repo URL_OR_PATH` — где искать пакеты (обязательный):
  - в режиме `remote` — URL-адрес Maven-репозитория (`http` или
    `https`), например `https://repo1.maven.org/maven2`;
  - в режиме `test` — путь к файлу тестового репозитория.
- `-m`, `--mode {remote,test}` — режим работы с тестовым репозиторием:
  `remote` (по умолчанию) — реальный репозиторий по URL, `test` —
  тестовый репозиторий из файла.
- `-h`, `--help` — справка по параметрам.

Тестовый репозиторий — текстовый файл, в каждой строке которого указан
пакет и через двоеточие его прямые зависимости (пример —
`repos/simple.txt`):

```
A: B C
B: D
C: D
D:
```

## Функции

При запуске все параметры выводятся в формате `ключ=значение`
(порядок: `package`, `repo`, `mode`), код завершения — 0.

### Обработка ошибок

При ошибке выводятся краткая справка и причина, код завершения — 2.

- `--package`:
  - не указан: `the following arguments are required: -p/--package`;
  - пустой: `--package: empty package name`;
  - в режиме `remote` не в формате Maven (три непустые части через
    двоеточие, каждая начинается с буквы или цифры):
    `--package: 'slf4j-api': expected groupId:artifactId:version`;
  - в режиме `test` не из больших латинских букв:
    `--package: 'a': in test mode the package name must consist of
    capital Latin letters`.
- `--repo`:
  - не указан: `the following arguments are required: -r/--repo`;
  - пустой: `--repo: empty repository location`;
  - в режиме `remote` не http(s) URL:
    `--repo: 'ftp://...': expected an http(s) URL of a Maven repository`;
  - в режиме `remote` URL содержит пробельные символы:
    `--repo: '...': URL must not contain whitespace`;
  - в режиме `test` файл не найден, это каталог или нет прав на
    чтение: `no such test repository file`, `not a file`,
    `permission denied`.
- `--mode`: недопустимое значение —
  `argument -m/--mode: invalid choice: 'prod' (choose from 'remote',
  'test')`.
- Неизвестный параметр: `unrecognized arguments: --depth 3`.
- Сокращённые имена параметров (например, `--pack`) не принимаются.

## Сборка и запуск

Сборка не требуется.

```sh
./run.sh -p org.slf4j:slf4j-api:2.0.13 -r https://repo1.maven.org/maven2
./run.sh -p A -r repos/simple.txt -m test
./run.sh test                     # запуск тестов
```

Без `run.sh`:

```sh
python3 src/depviz.py -p A -r repos/simple.txt -m test
python3 -m unittest discover -s tests -t . -v
```

Скрипты ОС (`scripts/`):

- `test_params.sh` — корректные запуски в режимах `remote` и `test`;
- `test_errors.sh` — ошибки каждого параметра и неизвестный параметр
  (ошибка `permission denied` не воспроизводится при запуске от root).

## Примеры использования

Реальный репозиторий Maven:

```
$ ./run.sh --package org.slf4j:slf4j-api:2.0.13 \
    --repo https://repo1.maven.org/maven2
package=org.slf4j:slf4j-api:2.0.13
repo=https://repo1.maven.org/maven2
mode=remote
```

Тестовый репозиторий:

```
$ ./run.sh -p A -r repos/simple.txt -m test
package=A
repo=repos/simple.txt
mode=test
```

Ошибки:

```
$ ./run.sh -p slf4j-api -r https://repo1.maven.org/maven2
usage: depviz [-h] -p NAME -r URL_OR_PATH [-m {remote,test}]
depviz: error: --package: 'slf4j-api': expected groupId:artifactId:version
$ ./run.sh -p A -r repos/missing.txt -m test
usage: depviz [-h] -p NAME -r URL_OR_PATH [-m {remote,test}]
depviz: error: --repo: 'repos/missing.txt': no such test repository file
$ ./run.sh -p A -r repos/simple.txt -m prod
usage: depviz [-h] -p NAME -r URL_OR_PATH [-m {remote,test}]
depviz: error: argument -m/--mode: invalid choice: 'prod' (choose from 'remote', 'test')
```
