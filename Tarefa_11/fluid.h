#ifndef FLUID_H
#define FLUID_H

#include <stddef.h>
#include <limits.h>

#ifndef NX
#define NX 80
#endif
#ifndef NY
#define NY 80
#endif

#define LX 1.0
#define LY 1.0

#define NU 0.01
#define ALPHA 0.20

#ifndef STEPS
#define STEPS 1000
#endif
#ifndef SAVE_EVERY
#define SAVE_EVERY 10
#endif

#if NX < 2 || NY < 2 || STEPS < 1 || SAVE_EVERY < 1
#error "Use NX e NY >= 2, STEPS e SAVE_EVERY >= 1."
#endif
#if NY > 0 && NX > INT_MAX / NY
#error "NX * NY deve caber em um indice do tipo int."
#endif

typedef struct
{
    int nx;
    int ny;

    double lx;
    double ly;

    double dx;
    double dy;
    double dt;

    double nu;
    double alpha;

    int steps;
    int save_every; // Zero desativa frames e diagnosticos nos testes de desempenho.
    int mode;

    double *u;
    double *v;

    double *u_new;
    double *v_new;

} Simulation;


// Inicializa os parâmetros e aloca os campos.
int init_simulation(Simulation *sim, int mode);

// Libera a memória utilizada pela simulação.
void free_simulation(Simulation *sim);

// Define as condições iniciais do campo de velocidade.
void initialize_velocity(Simulation *sim);

// Cria o diretório dos frames.
int create_frames_directory(void);

// Salva os parâmetros usados pelo visualizador Python.
int save_metadata(const Simulation *sim);

// Salva o campo de velocidade atual em CSV.
int save_frame(const Simulation *sim, int step);

// Calcula e imprime as medidas da perturbação.
void print_diagnostics(const Simulation *sim, int step);

// Calcula o próximo estado usando diferenças finitas. (Ponto Chave)
void compute_next_state(Simulation *sim);

// Troca os campos atual e novo.
void swap_fields(Simulation *sim);

// Executa a evolução temporal da simulação.
int run_simulation(Simulation *sim);

// Imprime os parâmetros da simulação.
void print_simulation_info(const Simulation *sim);

// Retorna o nome do modo selecionado.
const char *get_mode_name(int mode);

#endif
