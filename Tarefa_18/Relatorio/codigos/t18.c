#include <stdio.h>
#include <stdlib.h>
#include <omp.h>

#include "aux18.c"
#include "somas.c"

int main(int argc, char *argv[])
{
    if (argc != 4) {
        fprintf(stderr, "Uso: %s <N> <TOL> <MODO>\n", argv[0]);
        fprintf(stderr, "  N    = tamanho dos vetores\n");
        fprintf(stderr, "  TOL  = tolerancia\n");
        fprintf(stderr, "  MODO = 0 (CPU) ou 1 (GPU)\n");

        return EXIT_FAILURE;
    }

    // Leitura e validacao dos argumentos
    int N = ler_n(argv[1]);
    float TOL = ler_tol(argv[2]);
    int modo = ler_modo(argv[3]);

    // Alocacao
    float *a = aloca_vetor(N);
    float *b = aloca_vetor(N);
    float *c = aloca_vetor(N);
    float *res = aloca_vetor(N);

    // Inicializacao
    inicializa_vetores(a, b, c, res, N);

    // Execucao
    double inicio = omp_get_wtime();

    if (modo == 0) {
        soma_cpu(a, b, c, N);
    } else {
        soma_gpu(a, b, c, N);
    }

    double fim = omp_get_wtime();

    // Validacao
    int err = verifica_resultado(c, res, N, TOL);

    // Resultado
    printf("====================================\n");
    printf("Soma de vetores\n");
    printf("N      : %d\n", N);
    printf("TOL    : %e\n", TOL);
    printf("MODO   : %s\n", modo == 0 ? "CPU" : "GPU");
    printf("Erros  : %d\n", err);
    printf("Tempo  : %.9f s\n", fim - inicio);
    printf("====================================\n");

    // Liberacao
    libera_vetores(a, b, c, res);

    return EXIT_SUCCESS;
}