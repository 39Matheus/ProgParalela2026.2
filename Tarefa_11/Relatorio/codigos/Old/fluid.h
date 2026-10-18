#ifndef FLUID_H
#define FLUID_H

#include <stddef.h>

#define NX 80
#define NY 80

#define LX 1.0
#define LY 1.0

#define NU 0.01
#define ALPHA 0.20

#define STEPS 1000
#define SAVE_EVERY 10

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
    int save_every;
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