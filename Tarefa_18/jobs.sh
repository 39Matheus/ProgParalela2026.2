#!/bin/bash

# ============================================================
# Job CPU
# ============================================================

sbatch <<'EOF'
#!/bin/bash

#SBATCH --partition=intel-128
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:02:00
#SBATCH --job-name=ppCPU_job
#SBATCH --output=resultado_cpu_%j.out

cd "$SLURM_SUBMIT_DIR"

gcc -O3 -fopenmp -std=c11 t18.c -o t18_cpu -lm

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export OMP_PLACES=cores
export OMP_PROC_BIND=close

echo "======================================"
echo "EXECUCAO CPU"
echo "Hostname: $(hostname)"
echo "Threads OpenMP: $OMP_NUM_THREADS"
echo "======================================"
echo

for i in {1..5}; do
    echo "----- Execucao $i -----"
    ./t18_cpu 10000000 1e-9 0
    echo
done
EOF


# ============================================================
# Job GPU
# ============================================================

sbatch <<'EOF'
#!/bin/bash

#SBATCH --partition=gpu-8-v100
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:4
#SBATCH --gres-flags=enforce-binding
#SBATCH --time=00:02:00
#SBATCH --job-name=ppGPU_job
#SBATCH --output=resultado_gpu_%j.out

cd "$SLURM_SUBMIT_DIR"

export OMP_TARGET_OFFLOAD=MANDATORY

gcc -O3 -fopenmp -std=c11 t18.c -o t18_gpu -lm

echo "======================================"
echo "EXECUCAO GPU"
echo "Hostname: $(hostname)"
echo "======================================"

nvidia-smi --query-gpu=name --format=csv,noheader
echo

echo "----- Warm-up -----"
./t18_gpu 10000000 1e-9 1
echo

for i in {1..5}; do
    echo "----- Execucao $i -----"
    ./t18_gpu 10000000 1e-9 1
    echo
done
EOF