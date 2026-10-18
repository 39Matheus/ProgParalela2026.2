#include "fluid.h"
#include <errno.h>
#include <limits.h>
#include <math.h>
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>

static int parse_integer(const char *text, int minimum, int maximum, int *value)
{
    char *end;
    errno = 0;
    long parsed = strtol(text, &end, 10);
    if (errno || *text == '\0' || *end != '\0' ||
        parsed < minimum || parsed > maximum)
        return 0;
    *value = (int)parsed;
    return 1;
}

int main(int argc, char **argv)
{
    int nx, ny, steps, mode = 2;
    if (argc < 4 || argc > 6 ||
        !parse_integer(argv[1], 2, INT_MAX, &nx) ||
        !parse_integer(argv[2], 2, INT_MAX, &ny) ||
        !parse_integer(argv[3], 1, INT_MAX, &steps) ||
        (argc >= 5 && !parse_integer(argv[4], 0, 2, &mode)))
    {
        fprintf(stderr, "Uso: %s nx ny passos [modo: 0, 1 ou 2] [csv_final]\n", argv[0]);
        return EXIT_FAILURE;
    }
    if (nx > INT_MAX / ny)
    {
        fprintf(stderr, "NX * NY deve caber em um indice int.\n");
        return EXIT_FAILURE;
    }
    Simulation sim = {0};
    if (!init_simulation(&sim, nx, ny, steps, mode))
        return EXIT_FAILURE;
    initialize_velocity(&sim);
    int requested = omp_get_max_threads();
    double start = omp_get_wtime();
    run_simulation(&sim);
    double elapsed = omp_get_wtime() - start;

    Diagnostics result;
    if (!isfinite(elapsed) || elapsed <= 0 || !diagnostics(&sim, &result))
    {
        fprintf(stderr, "Tempo invalido ou campo nao finito.\n");
        free_simulation(&sim);
        return EXIT_FAILURE;
    }
    if (sim.threads_reais != requested)
    {
        fprintf(stderr, "Threads solicitadas: %d; threads reais: %d. Verifique os recursos.\n",
                requested, sim.threads_reais);
        free_simulation(&sim);
        return EXIT_FAILURE;
    }
    if (argc == 6 && !save_final(&sim, argv[5]))
    {
        fprintf(stderr, "Falha ao salvar o estado final.\n");
        free_simulation(&sim);
        return EXIT_FAILURE;
    }
    printf("v%d | NX=%d NY=%d | passos=%d | modo=%d | threads=%d\n",
           VERSAO, nx, ny, steps, mode, sim.threads_reais);
    printf("dt=%.12g | tempo fisico final=%.12g\n", sim.dt, steps * sim.dt);
    printf("Tempo de calculo: %.9f segundos\n", elapsed);
    printf("RESULTADO;v%d;%d;%d;%d;%d;%d;%d;%.9f;%.17g;%.17g;%.17g;%.17g\n",
           VERSAO, nx, ny, steps, mode, requested, sim.threads_reais, elapsed,
           result.media_u, result.media_v, result.max_pert, result.rms_pert);
    free_simulation(&sim);
    return EXIT_SUCCESS;
}
