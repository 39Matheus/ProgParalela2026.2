#!/usr/bin/env bash
# Tarefa 11: compara schedule e collapse(2) usando OpenMP.
# Uso: ./executar_testes.sh [modo] [repeticoes]
# Exemplo: ./executar_testes.sh 2 3

set -euo pipefail

PASTA=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
RESULTADOS="$PASTA/resultados_openmp"
MODO="${1:-2}"
REPETICOES="${2:-1}"

if [[ ! "$MODO" =~ ^[012]$ ]]; then
    echo "Modo invalido. Use 0 (parado), 1 (uniforme) ou 2 (perturbacao)." >&2
    exit 1
fi
if [[ ! "$REPETICOES" =~ ^[1-9][0-9]*$ ]]; then
    echo "Quantidade de repeticoes invalida. Use um inteiro positivo." >&2
    exit 1
fi
if ! command -v gcc >/dev/null 2>&1; then
    echo "GCC nao encontrado. Instale o compilador antes de executar." >&2
    exit 1
fi

mkdir -p "$RESULTADOS"

# Compila as duas versoes a partir dos mesmos arquivos-fonte.
echo "Compilando as versoes..."
gcc -O2 -fopenmp "$PASTA/fluid_sim.c" "$PASTA/fluid.c" -lm -o "$PASTA/fluid_normal"
gcc -O2 -fopenmp -DUSE_COLLAPSE "$PASTA/fluid_sim.c" "$PASTA/fluid.c" -lm -o "$PASTA/fluid_collapse"

# Isola os CSVs dos frames: as execucoes nao sobrescrevem os frames existentes.
TEMP_DIR=$(mktemp -d)
trap 'rm -rf -- "$TEMP_DIR"' EXIT

ARQUIVO_TEMPOS="$RESULTADOS/tempos.csv"
ARQUIVO_RESUMO="$RESULTADOS/resumo.csv"
printf 'versao;threads;schedule;repeticao;tempo_segundos\n' > "$ARQUIVO_TEMPOS"

THREADS=(1 2 4)
SCHEDULES=("static" "dynamic,8" "guided,8")
VERSOES=("normal" "collapse")

# O OpenMP deve respeitar a quantidade solicitada de threads.
export OMP_DYNAMIC=FALSE

echo "Modo: $MODO | Repeticoes por configuracao: $REPETICOES"
for versao in "${VERSOES[@]}"; do
    for threads in "${THREADS[@]}"; do
        for schedule in "${SCHEDULES[@]}"; do
            for ((r = 1; r <= REPETICOES; r++)); do
                # Executa dentro da pasta temporaria por causa dos frames e metadata.
                (
                    cd "$TEMP_DIR"
                    OMP_NUM_THREADS="$threads" OMP_SCHEDULE="$schedule" \
                        "$PASTA/fluid_$versao" "$MODO" > "$TEMP_DIR/saida.log"
                )

                # O programa ja mede apenas compute_next_state + swap_fields.
                tempo=$(awk '/^Tempo de calculo:/ {print $(NF-1); exit}' "$TEMP_DIR/saida.log")
                if [[ -z "$tempo" ]]; then
                    echo "Nao foi possivel ler o tempo da execucao." >&2
                    exit 1
                fi

                printf '%s;%s;%s;%s;%s\n' \
                    "$versao" "$threads" "$schedule" "$r" "$tempo" >> "$ARQUIVO_TEMPOS"
                printf '%-8s | %s threads | %-10s | repeticao %d | %s s\n' \
                    "$versao" "$threads" "$schedule" "$r" "$tempo"
            done
        done
    done
 done

# Media dos tempos e speedup relativo a 1 thread, static, sem collapse.
awk -F';' '
    NR == 1 { next }
    {
        chave = $1 SUBSEP $2 SUBSEP $3
        if (!(chave in contagem)) {
            ordem[++total] = chave
            versao[chave] = $1
            threads[chave] = $2
            schedule[chave] = $3
        }
        soma[chave] += $5
        contagem[chave]++
    }
    END {
        print "versao;threads;schedule;tempo_medio_segundos;speedup"
        base = "normal" SUBSEP "1" SUBSEP "static"
        tempo_base = soma[base] / contagem[base]
        for (i = 1; i <= total; i++) {
            chave = ordem[i]
            media = soma[chave] / contagem[chave]
            printf "%s;%s;%s;%.6f;%.3f\n", \
                versao[chave], threads[chave], schedule[chave], \
                media, tempo_base / media
        }
    }
' "$ARQUIVO_TEMPOS" > "$ARQUIVO_RESUMO"

echo
echo "Testes concluidos. Resultados:"
echo "  $ARQUIVO_TEMPOS"
echo "  $ARQUIVO_RESUMO"
echo "Os frames temporarios dos testes foram descartados."
