#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CC="${CC:-gcc}"
CFLAGS="${CFLAGS:--O2 -Wall -Wextra -std=c11}"

cd "$ROOT"
mkdir -p bin

"$CC" $CFLAGS -o bin/benchmark src/benchmark.c -lm
"$CC" $CFLAGS -o bin/interference src/interference.c

echo "Built: $ROOT/bin/benchmark $ROOT/bin/interference"