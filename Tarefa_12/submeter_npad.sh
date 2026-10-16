#!/usr/bin/env bash
# Modelo: confirmar particao, modulos e recursos antes da primeira submissao.
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

# Se necessario, inserir aqui o module load do GCC disponivel na sua conta.
# Nao ha nome de particao ou modulo presumido neste modelo.
if [[ -z "${THREADS:-}" ]]; then
    THREADS="1"
    for (( p=2; p<=SLURM_CPUS_PER_TASK; p*=2 )); do THREADS+=" $p"; done
    export THREADS
fi
srun --ntasks=1 --cpus-per-task="$SLURM_CPUS_PER_TASK" bash executar_testes.sh
