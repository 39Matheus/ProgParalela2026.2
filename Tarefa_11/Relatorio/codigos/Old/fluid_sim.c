#include "fluid.h"

#include <stdio.h>
#include <stdlib.h>


int main(int argc, char **argv)
{
    int mode = 2;

    if (argc > 1)
        mode = atoi(argv[1]);

    if (mode < 0 || mode > 2)
    {
        fprintf(
            stderr,
            "Modo invalido. Use 0, 1 ou 2.\n"
        );

        return EXIT_FAILURE;
    }

    // Inicializa a simulação.
    Simulation sim;
    if (!init_simulation(&sim, mode))
        return EXIT_FAILURE;

    // Define o estado inicial do fluido.
    initialize_velocity(&sim);

    // Cria o diretório dos frames.
    if (!create_frames_directory())
    {
        free_simulation(&sim);
        return EXIT_FAILURE;
    }

    // Salva os parâmetros para o visualizador Python.
    if (!save_metadata(&sim))
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