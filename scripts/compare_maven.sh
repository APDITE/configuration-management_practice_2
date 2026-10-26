#!/bin/sh
# Сравнение порядка загрузки depviz с реальным менеджером пакетов Maven.
# Нужны Maven (команда mvn) и доступ в интернет.
# Запуск: sh scripts/compare_maven.sh [groupId:artifactId:version]
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
URL=https://repo1.maven.org/maven2
PLUGIN=org.apache.maven.plugins:maven-dependency-plugin:3.6.1
PKG="${1:-com.google.guava:guava:33.2.1-jre}"

if ! command -v mvn >/dev/null 2>&1; then
    echo "mvn not found: install Maven (macOS: brew install maven)"
    exit 1
fi

GROUP="$(echo "$PKG" | cut -d: -f1)"
ARTIFACT="$(echo "$PKG" | cut -d: -f2)"
VERSION="$(echo "$PKG" | cut -d: -f3)"
WORK="$(mktemp -d)"

cat > "$WORK/pom.xml" <<POM
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>depviz.compare</groupId>
  <artifactId>consumer</artifactId>
  <version>1.0</version>
  <dependencies>
    <dependency>
      <groupId>$GROUP</groupId>
      <artifactId>$ARTIFACT</artifactId>
      <version>$VERSION</version>
    </dependency>
  </dependencies>
</project>
POM

echo "=== depviz: порядок загрузки $PKG ==="
python3 src/depviz.py -p "$PKG" -r "$URL" --load-order
echo

echo "=== Maven: дерево зависимостей (dependency:tree) ==="
mvn -q -f "$WORK/pom.xml" "$PLUGIN:tree" -DoutputFile="$WORK/tree.txt" \
    && cat "$WORK/tree.txt"
echo

echo "=== Maven: порядок в classpath (dependency:build-classpath) ==="
mvn -q -f "$WORK/pom.xml" "$PLUGIN:build-classpath" \
    -Dmdep.outputFile="$WORK/classpath.txt" -Dmdep.includeScope=runtime \
    && tr ':' '\n' < "$WORK/classpath.txt" | sed 's|.*/repository/||' \
    | awk -F/ '{g = $1; for (i = 2; i <= NF - 3; i++) g = g "." $i;
                print NR ". " g ":" $(NF - 2) ":" $(NF - 1)}'

rm -rf "$WORK"
