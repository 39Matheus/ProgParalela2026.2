"""Analisa uma campanha completa. So os graficos opcionais exigem Matplotlib."""
import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, delimiter=";", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def analyze(folder):
    config = json.loads((folder / "configuracao.json").read_text())
    with (folder / "tempos.csv").open() as file:
        raw = list(csv.DictReader(file, delimiter=";"))
    groups = defaultdict(list)
    signatures = {}
    for row in raw:
        n, ny, steps, mode, p, actual, repeat = [
            int(row[name]) for name in ("nx", "ny", "passos", "modo",
                                       "threads_solicitadas", "threads_reais", "repeticao")]
        if (n != ny or p != actual or steps != config["passos"] or
                mode != config["modo"]):
            raise ValueError("Malha, carga ou threads incompatíveis com a configuração.")
        elapsed = float(row["tempo_segundos"])
        signature = tuple(float(row[name]) for name in
                          ("media_u", "media_v", "max_pert", "rms_pert"))
        if elapsed <= 0 or not all(map(math.isfinite, (elapsed,) + signature)):
            raise ValueError("Tempo inválido ou diagnóstico não finito.")
        if n in signatures and not all(math.isclose(a, b, rel_tol=1e-11, abs_tol=1e-12)
                                       for a, b in zip(signature, signatures[n])):
            raise ValueError("Diagnósticos divergentes entre versões, threads ou repetições.")
        signatures[n] = signature
        groups[row["versao"], n, p].append((repeat, elapsed))
    expected = {(v, n, p) for v in config["versoes"]
                for n in config["tamanhos"] for p in config["threads"]}
    if set(groups) != expected:
        raise ValueError("Matriz incompleta ou configurações extras no CSV.")
    stats = {}
    for key, values in groups.items():
        if sorted(r for r, t in values) != list(range(1, config["repeticoes"] + 1)):
            raise ValueError("Repetição ausente, duplicada ou inválida.")
        times = [t for r, t in values]
        stats[key] = mean(times), stdev(times) if len(times) > 1 else 0.0
    if 1 not in config["threads"]:
        raise ValueError("É necessária a referência de uma thread.")

    summary = []
    for version, n, p in sorted(stats):
        avg, sd = stats[version, n, p]
        base = stats[version, n, 1][0]
        speed = base / avg
        summary.append(dict(
            versao=version, nx=n, ny=n, passos=config["passos"], threads=p,
            repeticoes=config["repeticoes"], tempo_medio_segundos=avg,
            desvio_amostral=sd, cv_percentual=100 * sd / avg,
            speedup_versao=speed, eficiencia_versao=speed / p,
            ganho_sobre_v0=stats["v0", n, p][0] / avg,
            celulas_por_segundo=n * n * config["passos"] / avg))
    write_csv(folder / "resumo.csv", list(summary[0]), summary)

    sizes = sorted(config["tamanhos"])
    teams = sorted(config["threads"])
    for version in config["versoes"]:
        pivot = []
        for p in teams:
            row = {"threads": p}
            for n in sizes:
                row["N=" + str(n)] = stats[version, n, 1][0] / (p * stats[version, n, p][0])
            pivot.append(row)
        write_csv(folder / ("eficiencia_" + version + ".csv"), list(pivot[0]), pivot)

    # Diagonal exata: N(p)^2 = N(1)^2 * p, com os mesmos passos.
    base_n = min(sizes)
    weak = []
    for version in config["versoes"]:
        initial = stats[version, base_n, 1][0]
        for p in teams:
            for n in sizes:
                if n * n == base_n * base_n * p:
                    avg, sd = stats[version, n, p]
                    weak.append(dict(
                        versao=version, nx_base=base_n, nx=n, ny=n, threads=p,
                        passos=config["passos"],
                        atualizacoes_por_thread=n * n * config["passos"] // p,
                        tempo_medio_segundos=avg, desvio_amostral=sd,
                        eficiencia_fraca=initial / avg))
    weak_fields = ["versao", "nx_base", "nx", "ny", "threads", "passos",
                   "atualizacoes_por_thread", "tempo_medio_segundos",
                   "desvio_amostral", "eficiencia_fraca"]
    write_csv(folder / "fraca.csv", weak_fields, weak)
    observations = [
        "Campanha registrada como: " + config["ambiente"] + ". Confira o hostname em ambiente.txt.",
        "Speedup e eficiência forte usam T(1,N) da própria versão, sem mudar a carga.",
        "ganho_sobre_v0 compara versões no mesmo N e mesmo p.",
        "Eficiência fraca = T(1,N_base)/T(p,N_base*sqrt(p)), com trabalho/thread constante.",
        "O número de passos é fixo; o tempo físico diminui ao refinar a malha.",
        "Nenhuma amostra foi removida. As versões se alternam, mas tamanhos e equipes têm ordem fixa.",
    ]
    if len({row["threads"] for row in weak}) < 2:
        observations.append("Faltam pontos na diagonal fraca. Inclua N_base, 2*N_base e p=1,4, por exemplo.")
    if config["repeticoes"] < 3:
        observations.append("Menos de três repetições: campanha útil para verificar o fluxo, não para concluir desempenho.")
    if any(row["tempo_medio_segundos"] < .1 for row in summary):
        observations.append("Há médias abaixo de 0,1 s. Considere aumentar PASSOS antes das medições finais.")
    if any(row["cv_percentual"] > 10 for row in summary):
        observations.append("Há CV acima de 10%. Examine os logs e a dispersão antes de comparar pequenas diferenças.")
    (folder / "observacoes.txt").write_text("\n".join(observations) + "\n", encoding="utf-8")
    print("Análise completa: %d medições, %d configurações." % (len(raw), len(stats)))
    return config, stats, weak


def plots(folder, config, stats, weak):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        raise ValueError("Para --graficos, instale matplotlib em um ambiente virtual.")
    output = folder / "graficos"
    output.mkdir(exist_ok=True)
    teams = sorted(config["threads"])
    for field in ("tempo", "speedup", "eficiencia"):
        fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), layout="constrained")
        for ax, version in zip(axes, config["versoes"]):
            for n in sorted(config["tamanhos"]):
                times = [stats[version, n, p][0] for p in teams]
                base = stats[version, n, 1][0]
                if field == "tempo":
                    errors = [stats[version, n, p][1] for p in teams]
                    ax.errorbar(teams, times, yerr=errors, fmt="o-", capsize=3,
                                label=str(n) + " x " + str(n))
                else:
                    values = [base / t for t in times]
                    if field == "eficiencia":
                        values = [s / p for s, p in zip(values, teams)]
                    ax.plot(teams, values, "o-", label=str(n) + " x " + str(n))
            if field == "speedup":
                ax.plot(teams, teams, "--", color=".5", label="Ideal")
            if field == "eficiencia":
                ax.axhline(1, ls="--", color=".5")
            ax.set(title=version, xlabel="Threads efetivas")
            ax.set_xticks(teams)
            ax.set_ylim(bottom=0)
            ax.grid(alpha=.2)
            ax.legend(fontsize=8)
        axes[0].set_ylabel(dict(tempo="Tempo de cálculo (s)", speedup="Speedup da própria versão",
                               eficiencia="Eficiência forte S/p")[field])
        fig.savefig(output / (field + ".png"), dpi=170)
        plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.7), layout="constrained")
    for version in config["versoes"]:
        points = [row for row in weak if row["versao"] == version]
        p = [row["threads"] for row in points]
        axes[0].errorbar(p, [row["tempo_medio_segundos"] for row in points],
                         yerr=[row["desvio_amostral"] for row in points],
                         fmt="o-", capsize=3, label=version)
        axes[1].plot(p, [row["eficiencia_fraca"] for row in points], "o-", label=version)
    for ax in axes:
        ax.set_xlabel("Threads efetivas, com trabalho/thread constante")
        ax.set_ylim(bottom=0)
        ax.grid(alpha=.2)
        ax.legend()
    axes[0].set_ylabel("Tempo de cálculo (s)")
    axes[1].set_ylabel("Eficiência fraca")
    axes[1].axhline(1, ls="--", color=".5")
    fig.savefig(output / "fraca.png", dpi=170)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pasta", type=Path)
    parser.add_argument("--graficos", action="store_true")
    args = parser.parse_args()
    try:
        config, stats, weak = analyze(args.pasta)
        if args.graficos:
            plots(args.pasta, config, stats, weak)
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, "Falha na análise: " + str(error) + "\n")


if __name__ == "__main__":
    main()
