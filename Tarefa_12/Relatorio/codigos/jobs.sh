#!/usr/bin/env bash
# Entrada curta para submissao; argumentos sao opcoes adicionais do sbatch.
set -euo pipefail
PASTA=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$PASTA"
command -v sbatch >/dev/null || { echo "Execute este script no NPAD, onde ha sbatch." >&2; exit 1; }
sbatch "$@" submeter_npad.sh
