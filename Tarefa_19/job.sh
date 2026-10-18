#!/bin/bash

# ============================================================
# Job GPU - Tarefa 19
# Heat equation + OpenMP offload + Nsight Systems
# ============================================================

sbatch <<'EOF'
#!/bin/bash

#SBATCH --partition=gpu-8-v100
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --gres-flags=enforce-binding
#SBATCH --time=00:10:00
#SBATCH --job-name=heat_gpu
#SBATCH --output=resultado_heat_%j.out

# ============================================================
# Configuração OpenMP
# ============================================================

export OMP_TARGET_OFFLOAD=MANDATORY

# ============================================================
# Compilador NVC
# ============================================================

NVC=$(find /opt/npad/shared/compilers/nvidia_hpc_sdk/Linux_x86_64 \
    -type f \
    -name nvc \
    -perm -111 \
    2>/dev/null | head -n 1)

if [ -z "$NVC" ]; then
    echo "ERRO: nvc nao encontrado."
    exit 1
fi

# ============================================================
# Compilação
# ============================================================

echo "======================================"
echo "COMPILACAO"
echo "======================================"

echo "Compilador: $NVC"
echo

"$NVC" -O3 -mp=gpu -std=c11 heat_t18.c -o heat_gpu -lm

if [ $? -ne 0 ]; then
    echo "ERRO: compilacao falhou."
    exit 1
fi

echo "Compilacao concluida."
echo

# ============================================================
# Execução normal
# ============================================================

echo "======================================"
echo "EXECUCAO GPU"
echo "======================================"

echo "----- Warm-up -----"
./heat_gpu 1000 10
echo

for i in {1..5}; do
    echo "----- Execucao $i -----"
    ./heat_gpu 1000 10
    echo
done

# ============================================================
# Profiling com Nsight Systems
# ============================================================

echo "======================================"
echo "NSYS - PROFILING"
echo "======================================"

rm -f heat_1000.nsys-rep
rm -f heat_1000.sqlite

nsys profile \
    --trace=cuda,openmp \
    --cuda-memory-usage=true \
    -o heat_1000 \
    ./heat_gpu 1000 10

if [ $? -eq 0 ]; then
    echo
    echo "Profiling concluido com sucesso."
    echo "Arquivo: heat_1000.nsys-rep"
else
    echo
    echo "ERRO: o profiling com nsys falhou."
    exit 1
fi

echo

# ============================================================
# Estatísticas do profiling
# ============================================================

echo "======================================"
echo "NSYS - ESTATISTICAS"
echo "======================================"

nsys stats heat_1000.nsys-rep

echo
echo "======================================"
echo "FIM"
echo "======================================"

EOF