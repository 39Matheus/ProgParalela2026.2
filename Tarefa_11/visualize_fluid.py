import glob
import os
import sys

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


FRAME_DIR = "frames"
METADATA_FILE = "metadata.txt"


def read_metadata(filename):
    """Lê os parâmetros da simulação armazenados em metadata.txt."""
    meta = {}

    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            key, value = line.split()
            meta[key] = value

    return meta


def load_frame(filename, nx, ny):
    """Carrega um frame CSV e reconstrói os campos de velocidade u e v."""
    data = np.loadtxt(
        filename,
        delimiter=",",
        skiprows=1
    )

    u = data[:, 2].reshape(nx, ny)
    v = data[:, 3].reshape(nx, ny)

    return u, v


def progress_callback(current_frame, total_frames):
    """
    Exibe o progresso da geração do GIF no terminal.

    current_frame começa em 0, por isso é necessário somar 1
    para mostrar a numeração do frame de forma intuitiva.
    """
    frame = current_frame + 1
    percent = 100.0 * frame / total_frames

    print(
        f"\rGerando GIF: frame {frame}/{total_frames} "
        f"({percent:5.1f}%)",
        end="",
        flush=True
    )

    if frame == total_frames:
        print()


def main():
    # Permite informar uma pasta diferente para os frames pela linha de comando.
    frame_dir = os.path.normpath(
        sys.argv[1]
        if len(sys.argv) > 1
        else FRAME_DIR
    )

    # O arquivo metadata.txt fica no mesmo diretório da pasta de frames.
    metadata_path = os.path.join(
        os.path.dirname(frame_dir) or ".",
        METADATA_FILE
    )

    if not os.path.exists(metadata_path):
        raise FileNotFoundError(
            f"Arquivo '{metadata_path}' não encontrado. "
            "Execute primeiro o programa em C."
        )

    # Lê os parâmetros da simulação.
    meta = read_metadata(metadata_path)

    nx = int(meta["NX"])
    ny = int(meta["NY"])
    lx = float(meta["LX"])
    ly = float(meta["LY"])
    dt = float(meta["DT"])
    save_every = int(meta["SAVE_EVERY"])
    nu = float(meta["NU"])
    mode = int(meta["MODE"])
    steps = int(meta["STEPS"])

    # Localiza todos os arquivos CSV gerados pelo programa em C.
    files = sorted(
        glob.glob(
            os.path.join(
                frame_dir,
                "frame_*.csv"
            )
        )
    )
    # Ignora sobras de uma execucao anterior com mais passos.
    files = [file for file in files
             if int(os.path.splitext(os.path.basename(file))[0].split("_")[-1])
             <= steps // save_every]

    if not files:
        raise FileNotFoundError(
            f"Nenhum frame encontrado em '{frame_dir}'. "
            "Execute primeiro o programa em C."
        )

    print(f"{len(files)} frames encontrados.")

    # Carrega os frames para a animação e para a análise da perturbação.
    frames = [
        load_frame(file, nx, ny)
        for file in files
    ]

    # Calcula a magnitude da velocidade em cada frame.
    speeds = [
        np.hypot(u, v)
        for u, v in frames
    ]

    # Calcula as coordenadas dos centros das células da malha.
    x = (
        np.arange(nx) + 0.5
    ) * lx / nx

    y = (
        np.arange(ny) + 0.5
    ) * ly / ny

    X, Y = np.meshgrid(
        x,
        y,
        indexing="ij"
    )

    # Determina a maior magnitude de velocidade para manter
    # a mesma escala de cores durante toda a animação.
    vmax = max(
        float(np.max(speed))
        for speed in speeds
    )

    vmax = max(vmax, 1e-12)

    # Cria uma figura com o campo de velocidade e o gráfico da perturbação.
    fig, (ax_field, ax_decay) = plt.subplots(
        1,
        2,
        figsize=(13, 5)
    )

    # Mostra a magnitude da velocidade como imagem de fundo.
    image = ax_field.imshow(
        speeds[0].T,
        origin="lower",
        extent=[0, lx, 0, ly],
        aspect="equal",
        vmin=0,
        vmax=vmax,
        interpolation="nearest"
    )

    fig.colorbar(
        image,
        ax=ax_field,
        label="|v| (magnitude da velocidade)"
    )

    # Reduz a quantidade de setas para manter o campo vetorial legível.
    skip = max(1, nx // 20)

    quiver = ax_field.quiver(
        X[::skip, ::skip],
        Y[::skip, ::skip],
        frames[0][0][::skip, ::skip],
        frames[0][1][::skip, ::skip],
        angles="xy",
        scale_units="xy",
        scale=max(vmax / 0.15, 1.0)
    )

    ax_field.set_xlabel("x")
    ax_field.set_ylabel("y")
    ax_field.set_title("Campo de velocidade")

    # Define o campo uniforme de referência utilizado para medir
    # a intensidade da perturbação.
    background_u = 1.0 if mode >= 1 else 0.0

    # Calcula o instante correspondente a cada frame.
    times = (
        np.array([int(os.path.splitext(os.path.basename(file))[0].split("_")[-1])
                  for file in files])
        * save_every
        * dt
    )

    rms = []
    max_pert = []

    # Calcula o RMS e o valor máximo da perturbação em cada frame.
    for u, v in frames:
        du = u - background_u
        dv = v

        rms.append(
            float(
                np.sqrt(
                    np.mean(
                        du**2 + dv**2
                    )
                )
            )
        )

        max_pert.append(
            float(
                np.max(
                    np.hypot(
                        du,
                        dv
                    )
                )
            )
        )

    # Inicializa o gráfico do decaimento da perturbação.
    ax_decay.plot(
        times,
        rms,
        label="RMS da perturbação"
    )

    ax_decay.plot(
        times,
        max_pert,
        label="Máximo da perturbação"
    )

    # Marcadores que indicam a posição atual durante a animação.
    marker_rms, = ax_decay.plot(
        [times[0]],
        [rms[0]],
        marker="o",
        linestyle="None"
    )

    marker_max, = ax_decay.plot(
        [times[0]],
        [max_pert[0]],
        marker="o",
        linestyle="None"
    )

    ax_decay.set_xlabel("Tempo")
    ax_decay.set_ylabel("Amplitude da perturbação")
    ax_decay.set_title("Difusão da perturbação")
    ax_decay.grid(True, alpha=0.3)
    ax_decay.legend()

    # Define o texto correspondente ao modo da simulação.
    if mode == 0:
        mode_text = "fluido parado"
    elif mode == 1:
        mode_text = "velocidade uniforme"
    else:
        mode_text = "velocidade uniforme + perturbação"

    fig.suptitle(
        f"Difusão viscosa | nu={nu:g} | {mode_text}"
    )

    plt.tight_layout()

    def update(frame_number):
        """Atualiza o campo de velocidade e o gráfico da perturbação."""
        u, v = frames[frame_number]
        speed = speeds[frame_number]

        # Atualiza a imagem da magnitude da velocidade.
        image.set_data(speed.T)

        # Atualiza as setas do campo vetorial.
        quiver.set_UVC(
            u[::skip, ::skip],
            v[::skip, ::skip]
        )

        ax_field.set_title(
            f"Campo de velocidade | "
            f"frame {frame_number + 1}/{len(frames)}"
        )

        # Atualiza os marcadores do gráfico da perturbação.
        marker_rms.set_data(
            [times[frame_number]],
            [rms[frame_number]]
        )

        marker_max.set_data(
            [times[frame_number]],
            [max_pert[frame_number]]
        )

        return (
            image,
            quiver,
            marker_rms,
            marker_max
        )

    # Cria a animação usando todos os frames disponíveis.
    animation = FuncAnimation(
        fig,
        update,
        frames=len(frames),
        interval=60,
        blit=False,
        repeat=True
    )

    print(
        f"\nIniciando geração do GIF com "
        f"{len(frames)} frames..."
    )

    # Salva a animação e exibe o progresso no terminal.
    animation.save(
        "fluid_simulation.gif",
        writer="pillow",
        fps=15,
        progress_callback=progress_callback
    )

    print(
        "GIF salvo em: fluid_simulation.gif"
    )

    plt.close(fig)


if __name__ == "__main__":
    main()
