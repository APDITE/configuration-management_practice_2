#!/bin/sh
# Корректные запуски: вывод всех параметров в формате ключ=значение.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

run() {
    echo "\$ depviz $*"
    python3 src/depviz.py "$@"
    echo "exit status: $?"
    echo
}

run --package org.slf4j:slf4j-api:2.0.13 \
    --repo https://repo1.maven.org/maven2
run -p com.google.guava:guava:33.2.1-jre \
    -r https://repo1.maven.org/maven2 -m remote
run -p A -r "repos/simple.txt" -m test
