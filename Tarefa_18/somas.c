#include <stdlib.h>
#include <omp.h>

void soma_cpu(float *a, float *b, float *c, int N)
{
    #pragma omp parallel for
    for (int i = 0; i < N; i++) {
        c[i] = a[i] + b[i];
    }
}

void soma_gpu(float *a, float *b, float *c, int N)
{
    #pragma omp target
    #pragma omp loop
    for (int i = 0; i < N; i++) {
        c[i] = a[i] + b[i];
    }
}
