#include "fluid.h"
#include <math.h>
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>

static inline int index_of(const Simulation *sim, int i, int j)
{
    return i * sim->ny + j;
}

static inline int periodic(int value, int size)
{
    if (value < 0)
        return value + size;
    if (value >= size)
        return value - size;
    return value;
}

void free_simulation(Simulation *sim)
{
    free(sim->u);
    free(sim->v);
    free(sim->u_new);
    free(sim->v_new);
    sim->u = sim->v = sim->u_new = sim->v_new = NULL;
}

int init_simulation(Simulation *sim, int nx, int ny, int steps, int mode)
{
    sim->nx = nx;
    sim->ny = ny;
    sim->steps = steps;
    sim->mode = mode;
    sim->threads_reais = 0;
    sim->nu = NU;
    sim->dx = LX / nx;
    sim->dy = LY / ny;
    sim->dt = ALPHA * fmin(sim->dx * sim->dx, sim->dy * sim->dy) / sim->nu;
    size_t total = (size_t)nx * ny;
    sim->u = calloc(total, sizeof(double));
    sim->v = calloc(total, sizeof(double));
    sim->u_new = calloc(total, sizeof(double));
    sim->v_new = calloc(total, sizeof(double));
    if (!sim->u || !sim->v || !sim->u_new || !sim->v_new)
    {
        fprintf(stderr, "Falha na alocacao de memoria.\n");
        free_simulation(sim);
        return 0;
    }
    return 1;
}

/* Mesma gaussiana e mesmos tres modos da Tarefa 11. */
void initialize_velocity(Simulation *sim)
{
    const double cx = 0.5, cy = 0.5, sigma = 0.08;
    for (int i = 0; i < sim->nx; ++i)
    {
        double x = (i + 0.5) * sim->dx;
        for (int j = 0; j < sim->ny; ++j)
        {
            double y = (j + 0.5) * sim->dy;
            int current = index_of(sim, i, j);
            sim->u[current] = sim->mode >= 1 ? 1.0 : 0.0;
            sim->v[current] = 0.0;
            if (sim->mode == 2)
            {
                double dx = x - cx, dy = y - cy;
                double r2 = dx * dx + dy * dy;
                double perturbation = 0.5 * exp(-r2 / (2.0 * sigma * sigma));
                sim->u[current] += perturbation;
            }
        }
    }
}

/*
 * v0: kernel da Tarefa 11 sem collapse, com a mesma ordem das operacoes.
 * v1: calcula os indices das linhas uma vez por i, fora do laco em j.
 * v2: mesmo kernel de v1, chamado por uma equipe paralela persistente.
 */
void compute_next_state(Simulation *sim)
{
    double dx2 = sim->dx * sim->dx;
    double dy2 = sim->dy * sim->dy;
#if VERSAO == 2
    /* Todas as threads de run_simulation chegam a este omp for. */
    #pragma omp for schedule(runtime)
#else
    #pragma omp parallel for schedule(runtime)
#endif
    for (int i = 0; i < sim->nx; ++i)
    {
        /* Somente i=0 escreve; a barreira do for protege a leitura. */
        if (i == 0)
            sim->threads_reais = omp_get_num_threads();
#if VERSAO >= 1
        int row = i * sim->ny;
        int previous_row = periodic(i - 1, sim->nx) * sim->ny;
        int next_row = periodic(i + 1, sim->nx) * sim->ny;
#endif
        for (int j = 0; j < sim->ny; ++j)
        {
#if VERSAO == 0
            int previous_i = periodic(i - 1, sim->nx);
            int next_i = periodic(i + 1, sim->nx);
#endif
            int previous_j = periodic(j - 1, sim->ny);
            int next_j = periodic(j + 1, sim->ny);
#if VERSAO == 0
            int current = index_of(sim, i, j);
            int left = index_of(sim, previous_i, j);
            int right = index_of(sim, next_i, j);
            int down = index_of(sim, i, previous_j);
            int up = index_of(sim, i, next_j);
#else
            int current = row + j;
            int left = previous_row + j;
            int right = next_row + j;
            int down = row + previous_j;
            int up = row + next_j;
#endif
            double laplacian_u = (
                (sim->u[right] - 2.0 * sim->u[current] + sim->u[left]) / dx2
                + (sim->u[up] - 2.0 * sim->u[current] + sim->u[down]) / dy2
            );
            double laplacian_v = (
                (sim->v[right] - 2.0 * sim->v[current] + sim->v[left]) / dx2
                + (sim->v[up] - 2.0 * sim->v[current] + sim->v[down]) / dy2
            );
            sim->u_new[current] = sim->u[current] + sim->nu * sim->dt * laplacian_u;
            sim->v_new[current] = sim->v[current] + sim->nu * sim->dt * laplacian_v;
        }
    }
}

void swap_fields(Simulation *sim)
{
    double *temp = sim->u;
    sim->u = sim->u_new;
    sim->u_new = temp;
    temp = sim->v;
    sim->v = sim->v_new;
    sim->v_new = temp;
}

void run_simulation(Simulation *sim)
{
#if VERSAO == 2
    #pragma omp parallel shared(sim)
    {
        for (int step = 0; step < sim->steps; ++step)
        {
            /* O omp for termina com barreira antes da troca dos ponteiros. */
            compute_next_state(sim);
            #pragma omp single
            {
                swap_fields(sim);
            }
            /* A barreira de single protege a entrada no proximo passo. */
        }
    }
#else
    for (int step = 0; step < sim->steps; ++step)
    {
        compute_next_state(sim);
        swap_fields(sim);
    }
#endif
}

/* Verificacao final fora da regiao cronometrada. */
int diagnostics(const Simulation *sim, Diagnostics *result)
{
    size_t total = (size_t)sim->nx * sim->ny;
    double reference = sim->mode >= 1 ? 1.0 : 0.0;
    double sum_u = 0.0, sum_v = 0.0, sum_squared = 0.0, maximum = 0.0;
    for (size_t k = 0; k < total; ++k)
    {
        if (!isfinite(sim->u[k]) || !isfinite(sim->v[k]))
            return 0;
        double du = sim->u[k] - reference;
        double squared = du * du + sim->v[k] * sim->v[k];
        if (squared > maximum)
            maximum = squared;
        sum_u += sim->u[k];
        sum_v += sim->v[k];
        sum_squared += squared;
    }
    result->media_u = sum_u / total;
    result->media_v = sum_v / total;
    result->max_pert = sqrt(maximum);
    result->rms_pert = sqrt(sum_squared / total);
    return 1;
}

int save_final(const Simulation *sim, const char *filename)
{
    FILE *file = fopen(filename, "w");
    if (!file)
    {
        perror(filename);
        return 0;
    }
    int ok = fprintf(file, "i,j,u,v\n") >= 0;
    for (int i = 0; i < sim->nx && ok; ++i)
        for (int j = 0; j < sim->ny && ok; ++j)
        {
            int k = index_of(sim, i, j);
            ok = fprintf(file, "%d,%d,%.17g,%.17g\n", i, j,
                         sim->u[k], sim->v[k]) >= 0;
        }
    if (fclose(file) != 0)
        ok = 0;
    return ok;
}
