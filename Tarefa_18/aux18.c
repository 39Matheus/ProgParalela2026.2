#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <limits.h>
#include <math.h>

int ler_n(const char *arg)
{
    char *end;
    long valor;

    errno = 0;
    valor = strtol(arg, &end, 10);

    if (end == arg || *end != '\0') {
        fprintf(stderr, "Erro: N invalido: '%s'\n", arg);
        exit(EXIT_FAILURE);
    }

    if (errno == ERANGE || valor > INT_MAX || valor < INT_MIN) {
        fprintf(stderr, "Erro: N fora do intervalo permitido: '%s'\n", arg);
        exit(EXIT_FAILURE);
    }

    if (valor <= 0) {
        fprintf(stderr, "Erro: N deve ser maior que zero.\n");
        exit(EXIT_FAILURE);
    }

    return (int)valor;
}


float ler_tol(const char *arg)
{
    char *end;
    float valor;

    errno = 0;
    valor = strtof(arg, &end);

    if (end == arg || *end != '\0') {
        fprintf(stderr, "Erro: TOL invalida: '%s'\n", arg);
        exit(EXIT_FAILURE);
    }

    if (errno == ERANGE) {
        fprintf(stderr, "Erro: TOL fora do intervalo permitido: '%s'\n", arg);
        exit(EXIT_FAILURE);
    }

    if (!isfinite(valor) || valor < 0.0f) {
        fprintf(stderr, "Erro: TOL deve ser um valor finito maior ou igual a zero.\n");
        exit(EXIT_FAILURE);
    }

    return valor;
}


int ler_modo(const char *arg)
{
    char *end;
    long valor;

    errno = 0;
    valor = strtol(arg, &end, 10);

    if (end == arg || *end != '\0') {
        fprintf(stderr, "Erro: MODO invalido: '%s'\n", arg);
        exit(EXIT_FAILURE);
    }

    if (errno == ERANGE || valor < INT_MIN || valor > INT_MAX) {
        fprintf(stderr, "Erro: MODO invalido: '%s'\n", arg);
        exit(EXIT_FAILURE);
    }

    if (valor != 0 && valor != 1) {
        fprintf(stderr, "Erro: MODO deve ser 0 (CPU) ou 1 (GPU).\n");
        exit(EXIT_FAILURE);
    }

    return (int)valor;
}


float *aloca_vetor(int N)
{
    float *vetor = malloc((size_t)N * sizeof(float));

    if (vetor == NULL) {
        fprintf(stderr, "Erro: falha na alocacao de memoria.\n");
        exit(EXIT_FAILURE);
    }

    return vetor;
}


void inicializa_vetores(float *a, float *b, float *c, float *res, int N)
{
    for (int i = 0; i < N; i++) {
        a[i] = (float)i;
        b[i] = 2.0f * (float)i;
        c[i] = 0.0f;
        res[i] = a[i] + b[i];
    }
}


int verifica_resultado(float *c, float *res, int N, float TOL)
{
    int err = 0;

    #pragma omp parallel for reduction(+:err)
    for (int i = 0; i < N; i++) {
        float diff = c[i] - res[i];

        if (fabsf(diff) > TOL) {
            err++;
        }
    }

    return err;
}


void libera_vetores(float *a, float *b, float *c, float *res)
{
    free(a);
    free(b);
    free(c);
    free(res);
}
