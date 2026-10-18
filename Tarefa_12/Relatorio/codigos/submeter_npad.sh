#!/usr/bin/env bash
# Baseado no job CPU remoto da Tarefa 18; conferir a disponibilidade ao submeter.
#SBATCH --partition=intel-128
#SBATCH --job-name=tarefa12
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --time=01:00:00
#SBATCH --output=tarefa12-%j.out
#SBATCH --error=tarefa12-%j.err

set -euo pipefail
: "${SLURM_JOB_ID:?Use sbatch para executar este modelo no no de computacao.}"
: "${SLURM_CPUS_PER_TASK:?Alocacao sem cpus-per-task.}"
cd "$SLURM_SUBMIT_DIR"
[[ -f executar_testes.sh ]] || { echo "Submeta a partir da pasta Tarefa_12." >&2; exit 1; }

# O exemplo remoto usa gcc diretamente no PATH, sem module load.
# Se o ambiente mudar, carregue aqui o modulo apropriado.
export CC="${CC:-gcc}"
command -v "$CC" >/dev/null || { echo "Compilador nao encontrado: $CC" >&2; exit 1; }
command -v python3 >/dev/null || { echo "Python 3 nao encontrado." >&2; exit 1; }
if [[ -z "${THREADS:-}" ]]; then
    THREADS="1"
    for (( p=2; p<=SLURM_CPUS_PER_TASK; p*=2 )); do THREADS+=" $p"; done
    export THREADS
fi
# Como no job CPU remoto: os executaveis herdam a alocacao do batch.
bash executar_testes.sh
