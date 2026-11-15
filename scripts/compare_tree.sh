#!/bin/sh
# Сравнение графа depviz со штатным инструментом визуализации Maven
# (mvn dependency:tree) для трёх пакетов. Нужны Maven и интернет.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
URL=https://repo1.maven.org/maven2
PLUGIN=org.apache.maven.plugins:maven-dependency-plugin:3.6.1

if ! command -v mvn >/dev/null 2>&1; then
    echo "mvn not found: install Maven (macOS: brew install maven)"
    exit 1
fi

compare() {
    pkg="$1"
    work="$(mktemp -d)"
    cat > "$work/pom.xml" <<POM
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>depviz.compare</groupId>
  <artifactId>consumer</artifactId>
  <version>1.0</version>
  <dependencies>
    <dependency>
      <groupId>$(echo "$pkg" | cut -d: -f1)</groupId>
      <artifactId>$(echo "$pkg" | cut -d: -f2)</artifactId>
      <version>$(echo "$pkg" | cut -d: -f3)</version>
    </dependency>
  </dependencies>
</project>
POM
    echo "######## $pkg ########"
    echo "=== depviz: граф ==="
    python3 src/depviz.py -p "$pkg" -r "$URL"
    echo
    echo "=== Maven: mvn dependency:tree ==="
    mvn -q -f "$work/pom.xml" "$PLUGIN:tree" -DoutputFile="$work/tree.txt" \
        && cat "$work/tree.txt"
    echo
    echo "=== Maven: mvn dependency:tree -Dverbose ==="
    mvn -q -f "$work/pom.xml" "$PLUGIN:tree" -Dverbose \
        -DoutputFile="$work/verbose.txt" && cat "$work/verbose.txt"
    echo
    rm -rf "$work"
}

compare com.google.guava:guava:33.2.1-jre
compare com.fasterxml.jackson.core:jackson-databind:2.17.1
compare org.springframework:spring-context:6.1.8
