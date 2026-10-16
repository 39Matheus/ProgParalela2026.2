#include "fluid.h"

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <sys/stat.h>
#include <errno.h>
#include <string.h>
#include <omp.h>


// Retorna o índice linear correspondente à posição (i,j).
static inline int index_of(const Simulation *sim, int i, int j)
{
    return i * sim->ny + j;
}


// Aplica condições de contorno periódicas.
static inline int periodic(int value, int size)
{
    if (value < 0)
        return value + size;

    if (value >= size)
        return value - size;

    return value;
}


// Libera toda a memória usada pela simulação.
void free_simulation(Simulation *sim)
{
    free(sim->u);
    free(sim->v);
    free(sim->u_new);
    free(sim->v_new);

    sim->u = NULL;
    sim->v = NULL;
    sim->u_new = NULL;
    sim->v_new = NULL;
}


// Aloca os campos de velocidade.
static int allocate_fields(Simulation *sim)
{
    size_t total =
        (size_t) sim->nx * sim->ny;

    sim->u = calloc(
        total,
        sizeof(double)
    );

    sim->v = calloc(
        total,
        sizeof(double)
    );

    sim->u_new = calloc(
        total,
        sizeof(double)
    );

    sim->v_new = calloc(
        total,
        sizeof(double)
    );

    if (!sim->u || !sim->v ||
        !sim->u_new || !sim->v_new)
    {
        fprintf(
            stderr,
            "Falha na alocacao de memoria.\n"
        );

        free_simulation(sim);

        return 0;
    }

    return 1;
}


// Inicializa os parâmetros da simulação.
int init_simulation(Simulation *sim, int mode)
{
    sim->nx = NX;
    sim->ny = NY;

    sim->lx = LX;
    sim->ly = LY;

    sim->nu = NU;
    sim->alpha = ALPHA;

    sim->steps = STEPS;
    sim->save_every = SAVE_EVERY;
    sim->mode = mode;

    sim->dx = sim->lx / sim->nx;
    sim->dy = sim->ly / sim->ny;

    sim->dt =
        sim->alpha *
        fmin(sim->dx * sim->dx, sim->dy * sim->dy) /
        sim->nu;

    sim->u = NULL;
    sim->v = NULL;
    sim->u_new = NULL;
    sim->v_new = NULL;

    return allocate_fields(sim);
}


// Define as condições iniciais.
void initialize_velocity(Simulation *sim)
{
    const double cx = 0.5;
    const double cy = 0.5;
    const double sigma = 0.08;

    for (int i = 0; i < sim->nx; ++i)
    {
        double x =
            (i + 0.5) * sim->dx;

        for (int j = 0; j < sim->ny; ++j)
        {
            double y =
                (j + 0.5) * sim->dy;

            int current =
                index_of(sim, i, j);

            // Inicialmente o fluido está parado.
            sim->u[current] = 0.0;
            sim->v[current] = 0.0;

            // Os modos 1 e 2 possuem velocidade uniforme.
            if (sim->mode >= 1)
            {
                sim->u[current] = 1.0;
            }

            // O modo 2 adiciona uma perturbação gaussiana.
            if (sim->mode == 2)
            {
                double dx = x - cx;
                double dy = y - cy;

                double r2 =
                    dx * dx +
                    dy * dy;

                double perturbation =
                    0.5 *
                    exp(
                        -r2 /
                        (2.0 * sigma * sigma)
                    );

                sim->u[current] +=
                    perturbation;
            }
        }
    }
}


// Cria o diretório dos frames.
int create_frames_directory(void)
{
    if (mkdir("frames", 0755) != 0 &&
        errno != EEXIST)
    {
        fprintf(
            stderr,
            "Erro ao criar diretorio frames: %s\n",
            strerror(errno)
        );

        return 0;
    }

    return 1;
}


// Salva os parâmetros usados pelo Python.
int save_metadata(const Simulation *sim)
{
    FILE *file =
        fopen("metadata.txt", "w");

    if (!file)
    {
        fprintf(
            stderr,
            "Erro ao criar metadata.txt: %s\n",
            strerror(errno)
        );

        return 0;
    }

    fprintf(
        file,
        "NX %d\n",
        sim->nx
    );

    fprintf(
        file,
        "NY %d\n",
        sim->ny
    );

    fprintf(
        file,
        "LX %.12e\n",
        sim->lx
    );

    fprintf(
        file,
        "LY %.12e\n",
        sim->ly
    );

    fprintf(
        file,
        "NU %.12e\n",
        sim->nu
    );

    fprintf(
        file,
        "DT %.12e\n",
        sim->dt
    );

    fprintf(
        file,
        "STEPS %d\n",
        sim->steps
    );

    fprintf(
        file,
        "SAVE_EVERY %d\n",
        sim->save_every
    );

    fprintf(
        file,
        "MODE %d\n",
        sim->mode
    );

    fprintf(
        file,
        "TFINAL %.12e\n",
        sim->steps * sim->dt
    );

    fclose(file);

    return 1;
}


// Salva o campo atual em um arquivo CSV.
int save_frame(
    const Simulation *sim,
    int step
)
{
    char filename[256];

    snprintf(
        filename,
        sizeof(filename),
        "frames/frame_%05d.csv",
        step / sim->save_every
    );

    FILE *file =
        fopen(filename, "w");

    if (!file)
    {
        fprintf(
            stderr,
            "Erro ao abrir %s: %s\n",
            filename,
            strerror(errno)
        );

        return 0;
    }

    fprintf(
        file,
        "i,j,u,v\n"
    );

    for (int i = 0; i < sim->nx; ++i)
    {
        for (int j = 0; j < sim->ny; ++j)
        {
            int current =
                index_of(sim, i, j);

            fprintf(
                file,
                "%d,%d,%.12e,%.12e\n",
                i,
                j,
                sim->u[current],
                sim->v[current]
            );
        }
    }

    fclose(file);

    return 1;
}


// Calcula e imprime as medidas da perturbação.
void print_diagnostics(
    const Simulation *sim,
    int step
)
{
    double max_perturbation = 0.0;
    double sum_squared = 0.0;

    double reference_u =
        sim->mode >= 1 ? 1.0 : 0.0;

    for (int i = 0; i < sim->nx; ++i)
    {
        for (int j = 0; j < sim->ny; ++j)
        {
            int current =
                index_of(sim, i, j);

            double du =
                sim->u[current] -
                reference_u;

            double dv =
                sim->v[current];

            double amplitude =
                sqrt(
                    du * du +
                    dv * dv
                );

            if (amplitude >
                max_perturbation)
            {
                max_perturbation =
                    amplitude;
            }

            sum_squared +=
                du * du +
                dv * dv;
        }
    }

    double rms =
        sqrt(
            sum_squared /
            ((double) sim->nx *
             sim->ny)
        );

    double time =
        step * sim->dt;

    printf(
        "step=%4d | "
        "t=%8.4f | "
        "max_pert=%10.6e | "
        "RMS_pert=%10.6e\n",
        step,
        time,
        max_perturbation,
        rms
    );
}


// Calcula o próximo estado por diferenças finitas. (Ponto Chave)
void compute_next_state(Simulation *sim)
{
    double dx2 = sim->dx * sim->dx;
    double dy2 = sim->dy * sim->dy;

    // Permite comparar a paralelizacao com e sem collapse(2).
#ifdef USE_COLLAPSE
    #pragma omp parallel for collapse(2) schedule(runtime)
#else
    #pragma omp parallel for schedule(runtime)
#endif
    for (int i = 0; i < sim->nx; ++i) // Loop sobre a dimensão x
    {
        for (int j = 0; j < sim->ny; ++j) // Loop sobre a dimensão y
        {
            int previous_i = periodic(i - 1, sim->nx);
            int next_i = periodic(i + 1, sim->nx);
            int previous_j = periodic(j - 1, sim->ny);
            int next_j = periodic(j + 1, sim->ny);

            int current = index_of(sim, i, j);
            int left = index_of(sim, previous_i, j);
            int right = index_of(sim, next_i, j);
            int down = index_of(sim, i, previous_j);
            int up = index_of(sim, i, next_j);

            // Calcula o Laplaciano da componente u.
            double laplacian_u = (
                (sim->u[right] - 2.0 * sim->u[current] + sim->u[left]) / dx2
                + (sim->u[up] - 2.0 * sim->u[current] + sim->u[down]) / dy2
            );

            // Calcula o Laplaciano da componente v.
            double laplacian_v = (
                (sim->v[right] - 2.0 * sim->v[current] + sim->v[left]) / dx2
                + (sim->v[up] - 2.0 * sim->v[current] + sim->v[down]) / dy2
            );

            // Aplica Euler explícito à componente u.
            sim->u_new[current] = sim->u[current] + sim->nu * sim->dt * laplacian_u;

            // Aplica Euler explícito à componente v.
            sim->v_new[current] = sim->v[current] + sim->nu * sim->dt * laplacian_v;
        }
    }
}


// Troca os campos atual e novo.
void swap_fields(Simulation *sim)
{
    double *temp;

    temp = sim->u;
    sim->u = sim->u_new;
    sim->u_new = temp;

    temp = sim->v;
    sim->v = sim->v_new;
    sim->v_new = temp;
}


// Executa a evolução temporal.
int run_simulation(Simulation *sim)
{
    double tempo_calculo = 0.0;

    for (int step = 0;
         step <= sim->steps;
         ++step)
    {
        // Salva um frame nos intervalos definidos.
        if (sim->save_every > 0 && step % sim->save_every == 0)
        {
            if (!save_frame(sim, step))
                return 0;

            print_diagnostics(
                sim,
                step
            );
        }

        // Evita calcular um passo após o estado final.
        if (step == sim->steps)
            break;

        // Mede somente o calculo, sem incluir a gravacao dos CSVs.
        double inicio = omp_get_wtime();

        // Calcula o próximo estado.
        compute_next_state(sim);

        // Torna o novo estado o estado atual.
        swap_fields(sim);

        tempo_calculo += omp_get_wtime() - inicio;
    }

    printf("Tempo de calculo: %.6f segundos\n", tempo_calculo);

    return 1;
}


// Imprime as configurações da simulação.
void print_simulation_info(
    const Simulation *sim
)
{
    printf(
        "Modo: %d\n",
        sim->mode
    );

    printf(
        "NX=%d NY=%d | "
        "nu=%.5f | "
        "dt=%.8f | "
        "alpha=%.3f\n",
        sim->nx,
        sim->ny,
        sim->nu,
        sim->dt,
        sim->alpha
    );

    printf(
        "Tempo final: %.5f\n",
        sim->steps * sim->dt
    );

    if (sim->save_every > 0)
        printf("Arquivos salvos em ./frames/\n\n");
    else
        printf("Teste de desempenho: sem gravacao de frames.\n\n");
}


// Retorna uma descrição do modo utilizado.
const char *get_mode_name(int mode)
{
    switch (mode)
    {
        case 0:
            return "fluido parado";

        case 1:
            return "velocidade uniforme";

        case 2:
            return "velocidade uniforme + perturbacao";

        default:
            return "modo desconhecido";
    }
}
