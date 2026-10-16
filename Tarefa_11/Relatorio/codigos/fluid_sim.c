#include "fluid.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>


int main(int argc, char **argv)
{
    int mode = 2;

    if (argc > 3 ||
        (argc > 1 && (strlen(argv[1]) != 1 || argv[1][0] < '0' || argv[1][0] > '2')) ||
        (argc == 3 && strcmp(argv[2], "--benchmark") != 0))
    {
        fprintf(
            stderr,
            "Uso: %s [modo: 0, 1 ou 2] [--benchmark]\n",
            argv[0]
        );

        return EXIT_FAILURE;
    }

    if (argc > 1)
        mode = argv[1][0] - '0';

    // Inicializa a simulação.
    Simulation sim;
    if (!init_simulation(&sim, mode))
        return EXIT_FAILURE;

    if (argc == 3)
        sim.save_every = 0;

    // Define o estado inicial do fluido.
    initialize_velocity(&sim);

    // Cria o diretório dos frames.
    if (sim.save_every > 0 && !create_frames_directory())
    {
        free_simulation(&sim);
        return EXIT_FAILURE;
    }

    // Salva os parâmetros para o visualizador Python.
    if (sim.save_every > 0 && !save_metadata(&sim))
    {
        free_simulation(&sim);
        return EXIT_FAILURE;
    }

    // Exibe as configurações utilizadas.
    print_simulation_info(&sim);

    printf(
        "Modo selecionado: %s\n\n",
        get_mode_name(sim.mode)
    );

    // Executa a simulação.
    if (!run_simulation(&sim))
    {
        free_simulation(&sim);
        return EXIT_FAILURE;
    }

    // Libera a memória utilizada.
    free_simulation(&sim);

    printf(
        "\nSimulacao concluida.\n"
    );

    return EXIT_SUCCESS;
}
