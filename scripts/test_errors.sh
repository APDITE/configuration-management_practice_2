#!/bin/sh
# Обработка ошибок для всех параметров командной строки.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
URL=https://repo1.maven.org/maven2
PKG=org.slf4j:slf4j-api:2.0.13
TEST_REPO="repos/simple.txt"

run() {
    echo "\$ depviz $*"
    python3 src/depviz.py "$@"
    echo "exit status: $?"
    echo
}

echo "=== --package ==="
run -r "$URL"
run -p "" -r "$URL"
run -p slf4j-api -r "$URL"
run -p a -r "$TEST_REPO" -m test

echo "=== --repo ==="
run -p "$PKG"
run -p "$PKG" -r ""
run -p "$PKG" -r ftp://repo1.maven.org/maven2
run -p "$PKG" -r "$TEST_REPO"
run -p A -r "repos/missing.txt" -m test
run -p A -r repos -m test

echo "=== --mode ==="
run -p "$PKG" -r "$URL" -m prod
run -p "$PKG" -r "$URL" --depth 3
