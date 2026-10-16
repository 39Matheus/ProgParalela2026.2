#!/usr/bin/env bash
# Matriz tamanho x threads. A mesma matriz permite as duas analises.
set -euo pipefail
PASTA=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TAMANHOS="${TAMANHOS:-200 400 800}"
THREADS="${THREADS:-1 2 4}"
PASSOS="${PASSOS:-2000}"
MODO="${MODO:-2}"
REPETICOES="${REPETICOES:-3}"
AQUECIMENTOS="${AQUECIMENTOS:-1}"
CC="${CC:-gcc}"

inteiro_positivo() {
    local valor="$1" maximo="$2"
    [[ "$valor" =~ ^[1-9][0-9]*$ ]] && (( ${#valor} <= 10 && valor <= maximo ))
}
inteiro_positivo "$PASSOS" 2147483647 || { echo "PASSOS invalido." >&2; exit 1; }
inteiro_positivo "$REPETICOES" 2147483647 || { echo "REPETICOES invalido." >&2; exit 1; }
[[ "$MODO" =~ ^[012]$ && "$AQUECIMENTOS" =~ ^[01]$ ]] || {
    echo "Use MODO=0, 1 ou 2 e AQUECIMENTOS=0 ou 1." >&2; exit 1;
}
read -r -a MALHAS <<< "$TAMANHOS"
read -r -a EQUIPES <<< "$THREADS"
(( ${#MALHAS[@]} > 0 && ${#EQUIPES[@]} > 0 )) || exit 1
declare -A malhas_vistas equipes_vistas
for n in "${MALHAS[@]}"; do
    inteiro_positivo "$n" 46340 && (( n >= 2 )) || { echo "Malha invalida: $n" >&2; exit 1; }
    [[ ! -v malhas_vistas[$n] ]] || { echo "Malha repetida: $n" >&2; exit 1; }
    malhas_vistas[$n]=1
done
LIMITE="${SLURM_CPUS_PER_TASK:-$(nproc)}"
for p in "${EQUIPES[@]}"; do
    inteiro_positivo "$p" "$LIMITE" || { echo "Threads invalidas ou acima dos recursos ($LIMITE): $p" >&2; exit 1; }
    [[ ! -v equipes_vistas[$p] ]] || { echo "Equipe repetida: $p" >&2; exit 1; }
    equipes_vistas[$p]=1
done
[[ -v equipes_vistas[1] ]] || { echo "Inclua 1 em THREADS para a referencia." >&2; exit 1; }
command -v python3 >/dev/null || { echo "Python 3 nao encontrado." >&2; exit 1; }

export OMP_DYNAMIC=FALSE OMP_SCHEDULE=static LC_ALL=C
BASE="${RESULTADOS_BASE:-$PASTA/resultados}"
EXECUCAO="$BASE/execucao_$(date -u +%Y%m%dT%H%M%SZ)_$$"
mkdir -p "$EXECUCAO/logs"
bash "$PASTA/compilar.sh" > "$EXECUCAO/compilacao.log" 2>&1
python3 - "$EXECUCAO/configuracao.json" "$PASSOS" "$MODO" "$REPETICOES" \
    "$AQUECIMENTOS" "$TAMANHOS" "$THREADS" <<'PY'
import json, os, sys
path, steps, mode, repeats, warm, sizes, threads = sys.argv[1:]
data = dict(passos=int(steps), modo=int(mode), repeticoes=int(repeats),
            aquecimentos=int(warm), tamanhos=list(map(int, sizes.split())),
            threads=list(map(int, threads.split())), versoes=['v0', 'v1', 'v2'],
            schedule='static', ambiente='slurm' if os.getenv('SLURM_JOB_ID') else 'local')
with open(path, 'w') as file:
    json.dump(data, file, indent=2)
    file.write('\n')
PY
{
    date -u '+Data UTC: %Y-%m-%d %H:%M:%S'
    hostname
    uname -a
    "$CC" --version
    lscpu
    printf 'SLURM_JOB_ID=%s\nSLURM_JOB_NODELIST=%s\nSLURM_CPUS_PER_TASK=%s\n' \
        "${SLURM_JOB_ID:-local}" "${SLURM_JOB_NODELIST:-local}" "${SLURM_CPUS_PER_TASK:-local}"
    printf 'OMP_DYNAMIC=%s\nOMP_SCHEDULE=%s\n' "$OMP_DYNAMIC" "$OMP_SCHEDULE"
    if command -v module >/dev/null 2>&1; then module list 2>&1; fi
} > "$EXECUCAO/ambiente.txt"
(
    cd "$PASTA"
    sha256sum fluid.c fluid.h fluid_sim.c compilar.sh executar_testes.sh analisar_resultados.py
) > "$EXECUCAO/fontes.sha256"

CSV="$EXECUCAO/tempos.csv"
printf 'versao;nx;ny;passos;modo;threads_solicitadas;threads_reais;repeticao;tempo_segundos;media_u;media_v;max_pert;rms_pert\n' > "$CSV"
executar() {
    local versao="$1" n="$2" p="$3" repeticao="$4" log="$5"
    OMP_NUM_THREADS="$p" "$PASTA/bin/v$versao" "$n" "$n" "$PASSOS" "$MODO" > "$log" 2>&1 || {
        cat "$log" >&2; echo "Execucao interrompida. Logs: $EXECUCAO" >&2; exit 1;
    }
    if (( repeticao > 0 )); then
        awk -F';' -v r="$repeticao" '
            $1 == "RESULTADO" && NF == 13 && $7 == $8 && $9 > 0 {
                printf "%s;%s;%s;%s;%s;%s;%s;%d;%s;%s;%s;%s;%s\n", \
                    $2,$3,$4,$5,$6,$7,$8,r,$9,$10,$11,$12,$13
                ok=1
            }
            END { if (!ok) exit 1 }
        ' "$log" >> "$CSV"
    fi
}

echo "Resultados: $EXECUCAO"
for n in "${MALHAS[@]}"; do
    for p in "${EQUIPES[@]}"; do
        if (( AQUECIMENTOS == 1 )); then
            for v in 0 1 2; do
                executar "$v" "$n" "$p" 0 "$EXECUCAO/logs/v${v}_n${n}_p${p}_aquecimento.log"
            done
        fi
        for (( r=1; r<=REPETICOES; r++ )); do
            # Alterna a ordem das versoes: 0/1/2, 1/2/0, 2/0/1.
            for (( deslocamento=0; deslocamento<3; deslocamento++ )); do
                v=$(( (r - 1 + deslocamento) % 3 ))
                executar "$v" "$n" "$p" "$r" "$EXECUCAO/logs/v${v}_n${n}_p${p}_r${r}.log"
                echo "v$v | $n x $n | $p threads | repeticao $r"
            done
        done
    done
done
python3 "$PASTA/analisar_resultados.py" "$EXECUCAO"
echo "Concluido: $EXECUCAO"
