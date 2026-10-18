#!/usr/bin/env bash
set -euo pipefail
PASTA=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
CC="${CC:-gcc}"
BIN_DIR="${BIN_DIR:-$PASTA/bin}"
command -v "$CC" >/dev/null || { echo "Compilador nao encontrado: $CC" >&2; exit 1; }
mkdir -p "$BIN_DIR"
for versao in 0 1 2; do
    echo "$CC -std=c11 -O3 -Wall -Wextra -fopenmp -DVERSAO=$versao"
    "$CC" -std=c11 -O3 -Wall -Wextra -fopenmp "-DVERSAO=$versao" \
        "$PASTA/fluid_sim.c" "$PASTA/fluid.c" -lm -o "$BIN_DIR/v$versao"
done
