#!/bin/sh
# Описание графа зависимостей на языке диаграмм D2 (этап 5).
# Режим remote обращается к Maven Central и требует доступа в интернет.
# Если установлена утилита d2 (macOS: brew install d2), описания
# дополнительно преобразуются в изображения out/<имя>.svg.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
URL=https://repo1.maven.org/maven2
OUT=out

draw() {
    name="$1"
    shift
    echo "\$ depviz $* --d2"
    python3 src/depviz.py "$@" --d2 > "$OUT/$name.d2"
    status=$?
    cat "$OUT/$name.d2"
    echo "exit status: $status"
    if command -v d2 >/dev/null 2>&1; then
        d2 "$OUT/$name.d2" "$OUT/$name.svg" >/dev/null 2>&1 \
            && echo "image: $OUT/$name.svg"
    fi
    echo
}

mkdir -p "$OUT"

echo "=== test: общая зависимость и циклы ==="
draw simple -p A -r repos/simple.txt -m test
draw cycle -p A -r repos/cycle.txt -m test
draw complex -p A -r repos/complex.txt -m test

echo "=== remote: три пакета из Maven Central ==="
draw guava -p com.google.guava:guava:33.2.1-jre -r "$URL"
draw jackson-databind \
    -p com.fasterxml.jackson.core:jackson-databind:2.17.1 -r "$URL"
draw spring-context -p org.springframework:spring-context:6.1.8 -r "$URL"

if ! command -v d2 >/dev/null 2>&1; then
    echo "d2 not found: install it to render images (brew install d2)"
fi
