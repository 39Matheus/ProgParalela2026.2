/* Apoio para uma nova execucao: nao gerou os resultados historicos. */
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>

int main(void)
{
    int devices = omp_get_num_devices();
    int on_host = 1;
    printf("_OPENMP: %d\n", _OPENMP);
    printf("Dispositivos OpenMP: %d\n", devices);
    if (devices < 1) {
        fprintf(stderr, "Nenhum dispositivo OpenMP disponivel.\n");
        return EXIT_FAILURE;
    }

    #pragma omp target map(from:on_host)
    {
        on_host = omp_is_initial_device();
    }
    printf("Executou no host: %d\n", on_host);
    if (on_host) {
        fprintf(stderr, "A regiao target executou no host.\n");
        return EXIT_FAILURE;
    }
    return EXIT_SUCCESS;
}
