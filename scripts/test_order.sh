#!/bin/sh
# Порядок загрузки зависимостей (этап 4).
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

show() {
    echo "--- repos/$1.txt ---"
    cat "repos/$1.txt"
    echo
}

echo "=== test: общая зависимость (ромб) ==="
show simple
run -p A -r repos/simple.txt -m test --load-order

echo "=== test: цикл через корневой пакет ==="
show cycle
run -p A -r repos/cycle.txt -m test --load-order

echo "=== test: пакет зависит сам от себя ==="
show self
run -p A -r repos/self.txt -m test --load-order

echo "=== test: несколько циклов ==="
show complex
run -p A -r repos/complex.txt -m test --load-order

echo "=== test: пакет без зависимостей ==="
run -p D -r repos/simple.txt -m test --load-order

echo "=== remote: Maven Central ==="
run -p com.google.guava:guava:33.2.1-jre -r "$URL" --load-order
run -p com.fasterxml.jackson.core:jackson-databind:2.17.1 -r "$URL" \
    --load-order
