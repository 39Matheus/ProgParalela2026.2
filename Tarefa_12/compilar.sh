#!/usr/bin/env bash
set -euo pipefail
PASTA=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
CC="${CC:-gcc}"
command -v "$CC" >/dev/null || { echo "Compilador nao encontrado: $CC" >&2; exit 1; }
mkdir -p "$PASTA/bin"
for versao in 0 1 2; do
    echo "$CC -std=c11 -O2 -Wall -Wextra -fopenmp -DVERSAO=$versao"
    "$CC" -std=c11 -O2 -Wall -Wextra -fopenmp "-DVERSAO=$versao" \
        "$PASTA/fluid_sim.c" "$PASTA/fluid.c" -lm -o "$PASTA/bin/v$versao"
done
