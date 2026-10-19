#!/bin/sh
# Вывод прямых зависимостей пакетов (этап 2).
# Режим remote обращается к Maven Central и требует доступа в интернет.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
URL=https://repo1.maven.org/maven2

run() {
    echo "\$ depviz $*"
    python3 src/depviz.py "$@"
    echo "exit status: $?"
    echo
}

echo "=== remote: Maven Central ==="
run -p org.slf4j:slf4j-api:2.0.13 -r "$URL"
run -p com.google.guava:guava:33.2.1-jre -r "$URL"
run -p com.fasterxml.jackson.core:jackson-databind:2.17.1 -r "$URL"
run -p org.apache.commons:commons-lang3:3.14.0 -r "$URL"

echo "=== test: repos/simple.txt ==="
cat repos/simple.txt
echo
run -p A -r repos/simple.txt -m test
run -p B -r repos/simple.txt -m test
run -p D -r repos/simple.txt -m test
