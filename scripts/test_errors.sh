#!/bin/sh
# Обработка ошибок параметров командной строки и получения зависимостей.
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
run -p ..:..:.. -r "$URL"
run -p a -r "$TEST_REPO" -m test

echo "=== --repo ==="
run -p "$PKG"
run -p "$PKG" -r ""
run -p "$PKG" -r ftp://repo1.maven.org/maven2
run -p "$PKG" -r "$URL extra"
run -p "$PKG" -r "$TEST_REPO"
run -p A -r "repos/missing.txt" -m test
run -p A -r repos -m test
NO_READ="$(mktemp)"
chmod 000 "$NO_READ"
run -p A -r "$NO_READ" -m test
rm -f "$NO_READ"

echo "=== --mode ==="
run -p "$PKG" -r "$URL" -m prod

echo "=== неизвестные параметры ==="
run -p "$PKG" -r "$URL" --depth 3
run --pack "$PKG" -r "$URL"

echo "=== получение зависимостей ==="
run -p org.example:no-such-package:1.0 -r "$URL"
run -p "$PKG" -r http://127.0.0.1:9
run -p Z -r "$TEST_REPO" -m test
cat repos/broken.txt
run -p A -r repos/broken.txt -m test
