# Tarefa 11 — difusão viscosa com OpenMP

Os fontes principais estão nesta pasta. `Old/` mantém a versão sequencial
original. A versão atual preserva os três modos, os frames CSV, o GIF e os
diagnósticos, com OpenMP, `schedule(runtime)`, comparação de `collapse(2)` e
medição apenas de `compute_next_state` + `swap_fields`.

## Simulação e GIF

Execute nesta pasta:

```bash
gcc -O2 -fopenmp fluid_sim.c fluid.c -lm -o fluid_sim
OMP_NUM_THREADS=4 OMP_SCHEDULE=static ./fluid_sim 2
python3 visualize_fluid.py
```

Modos: `0` = parado; `1` = velocidade uniforme; `2` = uniforme + perturbação
gaussiana. O modo padrão é `2`. O Python usa NumPy, Matplotlib e Pillow
(`python3 -m pip install numpy matplotlib pillow`).

A simulação grava `metadata.txt` e `frames/frame_*.csv` no diretório de execução.
O visualizador grava `fluid_simulation.gif` no diretório de execução e também
aceita o caminho de outra pasta de frames, inclusive com `/` no final:

```bash
python3 visualize_fluid.py Old/frames/
```

## Testes de desempenho

```bash
# Carga original: 80 x 80, 1.000 passos, três repetições por configuração.
bash executar_testes.sh 2 3

# Mais carga: 400 x 400, 5.000 passos, três repetições por configuração.
bash executar_testes.sh 2 3 400 400 5000
```

Argumentos: `[modo] [repeticoes] [nx] [ny] [passos]`. O script recompila as duas
versões e compara 1, 2 e 4 threads com `static`, `dynamic,8` e `guided,8`.
São 18 configurações por repetição, ou 54 execuções com três repetições.

O script usa `--benchmark`: não grava frames, metadados de visualização nem
diagnósticos a cada intervalo. A evolução numérica continua igual, e o tempo
inclui a criação e sincronização das threads dentro do cálculo. Os resultados
ficam em `resultados_openmp/tempos.csv`, `resumo.csv` e `configuracao.txt`.
Cada nova execução substitui esses três arquivos; os CSVs antigos em
`Resultados/` são preservados. O speedup usa como referência a média de
`normal`, 1 thread, `static`.

A carga maior do exemplo faz aproximadamente 125 vezes mais atualizações de
células. Comece com ela e ajuste conforme o tempo no seu computador. Mais
repetições ajudam a avaliar variação, mas não aumentam o trabalho de cada
execução. As medições antigas de aproximadamente 0,04 s são possíveis para a
malha pequena; custos de paralelismo e variação do sistema têm maior influência
nessa duração. Mais carga permite uma comparação mais representativa, sem
garantir que todas as configurações terão speedup.

Para ajustar a carga manualmente, os parâmetros também aceitam `-D`:

```bash
gcc -O2 -fopenmp -DNX=400 -DNY=400 -DSTEPS=5000 \
    fluid_sim.c fluid.c -lm -o fluid_sim
OMP_NUM_THREADS=4 OMP_SCHEDULE=static ./fluid_sim 2 --benchmark
```

Adicione `-DUSE_COLLAPSE` para a versão com `collapse(2)`. Para gerar um GIF
com essa carga, omita `--benchmark`; `-DSAVE_EVERY=100` reduz a quantidade de
frames gravados. O padrão continua sendo um frame a cada 10 passos.

Ao refinar a malha, o passo de tempo diminui para manter a estabilidade do
método explícito. Portanto, comparar desempenho com a mesma carga não equivale
necessariamente a simular o mesmo tempo físico. Para malhas retangulares,
o cálculo de `dt` usa o menor espaçamento entre `dx` e `dy`.
