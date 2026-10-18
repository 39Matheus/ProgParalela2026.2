#ifndef FLUID_H
#define FLUID_H
#ifndef VERSAO
#define VERSAO 0
#endif
#if VERSAO < 0 || VERSAO > 2
#error "Use VERSAO=0, 1 ou 2."
#endif
#define LX 1.0
#define LY 1.0
#define NU 0.01
#define ALPHA 0.20

typedef struct
{
    int nx, ny, steps, mode;
    int threads_reais;
    double dx, dy, dt, nu;
    double *u, *v, *u_new, *v_new;
} Simulation;

typedef struct
{
    double media_u, media_v, max_pert, rms_pert;
} Diagnostics;

int init_simulation(Simulation *sim, int nx, int ny, int steps, int mode);
void free_simulation(Simulation *sim);
void initialize_velocity(Simulation *sim);
void compute_next_state(Simulation *sim);
void swap_fields(Simulation *sim);
void run_simulation(Simulation *sim);
int diagnostics(const Simulation *sim, Diagnostics *result);
int save_final(const Simulation *sim, const char *filename);
#endif
