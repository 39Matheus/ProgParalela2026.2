#include <stdlib.h>
#include <stdio.h>
#include <math.h>

#include <omp.h>

// Constantes
#define PI acos(-1.0) // Pi
#define LINE "--------------------\n" // linha decorativa

// Definição das funções
void initial_value(const int n, const double dx, const double length, double * restrict u);
void zero(const int n, double * restrict u);

// Função que calcula o próximo passo de tempo, dado o passo de tempo atual (alvo da paralelização)
  void solve(const int n, const double alpha, const double dx, const double dt, const double * restrict u, double * restrict u_tmp);

double solution(const double t, const double x, const double y, const double alpha, const double length);
double l2norm(const int n, const double * restrict u, const int nsteps, const double dt, const double alpha, const double dx, const double length);

// Main function
int main(int argc, char *argv[]) {

  // Start the total program runtime timer
  double start = omp_get_wtime();

  // Problem size, forms an nxn grid
  int n = 1000;

  // Number of timesteps
  int nsteps = 10;


  // Check for the correct number of arguments
  // Print usage and exits if not correct
  if (argc == 3) {

    // Set problem size from first argument
    n = atoi(argv[1]);
    if (n < 0) {
      fprintf(stderr, "Error: n must be positive\n");
      exit(EXIT_FAILURE);
    }

    // Set number of timesteps from second argument
    nsteps = atoi(argv[2]);
    if (nsteps < 0) {
      fprintf(stderr, "Error: nsteps must be positive\n");
      exit(EXIT_FAILURE);
    }
  }


  //
  // Set problem definition
  //
  double alpha = 0.1;          // heat equation coefficient
  double length = 1000.0;      // physical size of domain: length x length square
  double dx = length / (n+1);  // physical size of each cell (+1 as don't simulate boundaries as they are given)
  double dt = 0.5 / nsteps;    // time interval (total time of 0.5s)


  // Stability requires that dt/(dx^2) <= 0.5,
  double r = alpha * dt / (dx * dx);

  // Print message detailing runtime configuration
  printf("\n");
  printf(" MMS heat equation\n\n");
  printf(LINE);
  printf("Problem input\n\n");
  printf(" Grid size: %d x %d\n", n, n);
  printf(" Cell width: %E\n", dx);
  printf(" Grid length: %lf x %lf\n", length, length);
  printf("\n");
  printf(" Alpha: %E\n", alpha);
  printf("\n");
  printf(" Steps: %d\n", nsteps);
  printf(" Total time: %E\n", dt*(double)nsteps);
  printf(" Time step: %E\n", dt);
  printf(LINE);

  // Stability check
  printf("Stability\n\n");
  printf(" r value: %lf\n", r);
  if (r > 0.5)
    printf(" Warning: unstable\n");
  printf(LINE);


  // Allocate two nxn grids
  double *u     = malloc(sizeof(double)*n*n);
  double *u_tmp = malloc(sizeof(double)*n*n);
  double *tmp;

  // Set the initial value of the grid under the MMS scheme
  initial_value(n, dx, length, u);
  zero(n, u_tmp);

  //
  // Run through timesteps under the explicit scheme
  //

  // Start the solve timer
  double tic = omp_get_wtime();
  for (int t = 0; t < nsteps; ++t) {

    // Call the solve kernel
    // Computes u_tmp at the next timestep
    // given the value of u at the current timestep
    solve(n, alpha, dx, dt, u, u_tmp);

    // Pointer swap
    tmp = u;
    u = u_tmp;
    u_tmp = tmp;
  }
  // Stop solve timer
  double toc = omp_get_wtime();

  //
  // Check the L2-norm of the computed solution
  // against the *known* solution from the MMS scheme
  //
  double norm = l2norm(n, u, nsteps, dt, alpha, dx, length);

  // Stop total timer
  double stop = omp_get_wtime();

  // Print results
  printf("Results\n\n");
  printf("Error (L2norm): %E\n", norm);
  printf("Solve time (s): %lf\n", toc-tic);
  printf("Total time (s): %lf\n", stop-start);
  printf(LINE);

  // Free the memory
  free(u);
  free(u_tmp);

}


// Sets the mesh to an initial value, determined by the MMS scheme
void initial_value(const int n, const double dx, const double length, double * restrict u) {

  double y = dx;
  for (int j = 0; j < n; ++j) {
    double x = dx; // Physical x position
    for (int i = 0; i < n; ++i) {
      u[i+j*n] = sin(PI * x / length) * sin(PI * y / length);
      x += dx;
    }
    y += dx; // Physical y position
  }

}


// Zero the array u
void zero(const int n, double * restrict u) {

  for (int i = 0; i < n; ++i) {
    for (int j = 0; j < n; ++j) {
      u[i+j*n] = 0.0;
    }
  }

}


/*
anotações pra esclarecer o solve()

visualização da matriz 3x3 (exemplo)
as atualizações ocorrem considerando os vizinhos de cada célula, 
formando um "stencil 5 pontos" (cima, baixo, esquerda, direita e o próprio ponto central).
basicamente um "+".
┌────┬────┬────┐
│ 01 │*02*│ 03 │
├────┼────┼────┤
│*04*│*05*│*06*│
├────┼────┼────┤
│ 07 │*08*│ 09 │
└────┴────┴────┘

u --> estado atual da temperatura (AGORA)
u_tmp --> estado da temperatura no próximo passo de tempo (DEPOIS)

restrict: 
é uma palavra-chave do C99 que indica que o ponteiro é o ÚNICO meio de acessar o objeto apontado. (uma promessa)
Isso permite ao compilador otimizar melhor o código, assumindo que não há aliasing 
(ou seja, não há outros ponteiros que possam modificar o mesmo objeto). 

Isso pode levar a melhorias significativas de desempenho em certos casos, 
especialmente em loops intensivos de computação.


updates:

r2 * u[i+j*n] +                         // ponto central
r * ((i < n-1) ? u[i+1+j*n] : 0.0) +    // vizinho da direita
r * ((i > 0)   ? u[i-1+j*n] : 0.0) +    // vizinho da esquerda
r * ((j < n-1) ? u[i+(j+1)*n] : 0.0) +  // vizinho de baixo
r * ((j > 0)   ? u[i+(j-1)*n] : 0.0);   // vizinho de cima

o zero é usado para lidar com as condições de contorno, garantindo que as células na 
borda da matriz não acessem índices fora dos limites.

constantemente, o valor de cada célula é atualizado com base em uma combinação 
ponderada de seu próprio valor e dos valores de seus vizinhos,
onde r é um fator de ponderação que depende do coeficiente de difusão (alpha),
do tamanho do passo de tempo (dt) e do tamanho da célula (dx).


Movimentação dos dados com map:

          ┌─────GPU─────┐
  u  ---->│             │ map(to: u[0:n*n]) // envia u para o dispositivo
          │   solve()   │
u_tmp <---│             │ map(from: u_tmp[0:n*n]) // recebe u_tmp do dispositivo
          └─────────────┘

*/

// Compute the next timestep, given the current timestep
void solve(const int n, const double alpha,                     //n = matriz nxn. //alpha = coef. da eq. do calor
          const double dx, const double dt,                     //dx = tamanho de cada célula. //dt = intervalo de tempo
          const double * restrict u, double * restrict u_tmp) {

  // Finite difference constant multiplier
  const double r = alpha * dt / (dx * dx);  // Constante de multiplicação para diferenças finitas
  const double r2 = 1.0 - 4.0*r;            // Constante de multiplicação para o ponto central

  // Loop paralelizavel
  #pragma omp target map(to: u[0:n*n]) map(from: u_tmp[0:n*n]) // Mapeamento de dados para o dispositivo
  {
    #pragma omp loop collapse(2) // Distribuição de equipes e paral
    for (int i = 0; i < n; ++i) {
      for (int j = 0; j < n; ++j) {


        u_tmp[i+j*n] =  r2 * u[i+j*n] +         // central
        r * ((i < n-1) ? u[i+1+j*n] : 0.0) +    // direita
        r * ((i > 0)   ? u[i-1+j*n] : 0.0) +    // esquerda
        r * ((j < n-1) ? u[i+(j+1)*n] : 0.0) +  // baixo
        r * ((j > 0)   ? u[i+(j-1)*n] : 0.0);   // cima
      }
    }
  }
}


// True answer given by the manufactured solution
double solution(const double t, const double x, const double y, const double alpha, const double length) {

  return exp(-2.0*alpha*PI*PI*t/(length*length)) * sin(PI*x/length) * sin(PI*y/length);

}


// Computes the L2-norm of the computed grid and the MMS known solution
// The known solution is the same as the boundary function.
double l2norm(const int n, const double * restrict u, const int nsteps, const double dt, const double alpha, const double dx, const double length) {

  // Final (real) time simulated
  double time = dt * (double)nsteps;

  // L2-norm error
  double l2norm = 0.0;

  // Loop over the grid and compute difference of computed and known solutions as an L2-norm
  double y = dx;
  for (int j = 0; j < n; ++j) {
    double x = dx;
    for (int i = 0; i < n; ++i) {
      double answer = solution(time, x, y, alpha, length);
      l2norm += (u[i+j*n] - answer) * (u[i+j*n] - answer);

      x += dx;
    }
    y += dx;
  }

  return sqrt(l2norm);

}