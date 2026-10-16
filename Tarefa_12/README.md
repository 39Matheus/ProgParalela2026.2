# Tarefa 12 — avaliação de escalabilidade

Preparação da avaliação do código de difusão viscosa da Tarefa 11 em **um nó
de computação do NPAD**. A Tarefa 11 e seu relatório foram preservados.
As medições no NPAD ainda serão feitas; esta pasta não contém resultados
atribuídos ao supercomputador.

O material de referência está em [`../SlidesAulas.pdf`](../SlidesAulas.pdf).
O limite de conteúdo adotado é a **página 55 do PDF, slide numerado 57**, onde
aparece a definição da Tarefa 12. As mudanças usam laços, índices, `parallel`,
`for`, `single` e suas barreiras, todos apresentados antes desse ponto.

## Começo rápido no Ubuntu

Na pasta `Tarefa_12`:

```bash
bash compilar.sh
python3 validar.py

# Uma execução manual: nx, ny, passos, modo (opcional, padrão 2).
OMP_DYNAMIC=FALSE OMP_NUM_THREADS=2 OMP_SCHEDULE=static \
    ./bin/v2 200 200 2000 2
```

Requisitos: GCC com OpenMP, Bash e Python 3. A compilação e a análise de CSVs
não precisam de NumPy ou Matplotlib. Não é necessário criar `.env` nem `.venv`
para esses passos.

Para verificar todo o fluxo com uma carga pequena, **no computador local**:

```bash
TAMANHOS="40 80" THREADS="1 4" PASSOS=100 REPETICOES=1 \
    bash executar_testes.sh
```

Esse exemplo pressupõe pelo menos quatro CPUs disponíveis. Se seu ambiente
disponibilizar menos, use `THREADS="1 2"`; a análise forte funciona, mas faltará
o ponto de quatro threads para a diagonal fraca desse exemplo. Uma repetição
serve para conferir o fluxo, não para concluir sobre desempenho.

## Versões sucessivas

Os mesmos três fontes produzem `bin/v0`, `bin/v1` e `bin/v2`. O compilador
seleciona o trecho correspondente por `-DVERSAO=0`, `1` ou `2`.

| Versão | Mudança acumulada | Gargalo que permite investigar |
| --- | --- | --- |
| `v0` | Kernel da Tarefa 11, sem `collapse`, com uma região paralela por passo. | Referência para a evolução. |
| `v1` | Calcula as posições das linhas vizinhas uma vez por linha, fora do laço interno. | Repetição de cálculos de índices. |
| `v2` | Usa o kernel de `v1` dentro de uma única região paralela que envolve todos os passos. | Entrada e saída repetidas de regiões paralelas. |

`v0` preserva a ordem das operações numéricas da Tarefa 11. O código foi
separado da visualização para esta avaliação: aceita a carga pela linha de
comando e não gera frames a cada intervalo. Para visualizar a simulação,
continue usando a Tarefa 11.

Em `v2`, todas as threads chamam o `omp for` em cada passo. A barreira no final
do `for` garante que os campos novos estejam prontos. Apenas uma thread troca
os ponteiros, em `single`, e a barreira de `single` protege o início do próximo
passo. Retirar essas barreiras mudaria a correção do programa.

Não se presume que `v1` e `v2` sempre serão mais rápidas. O GCC pode já eliminar
parte do trabalho repetido em `v0`, e a região persistente mantém custos de
barreiras. Os resultados do nó devem mostrar se houve ganho e em quais cargas.

## Como os testes são organizados

Os valores padrão de `executar_testes.sh` são:

```text
TAMANHOS="200 400 800"    # Cada N produz uma malha N x N.
THREADS="1 2 4"          # No modelo SLURM: potências de 2 até a alocação.
PASSOS=2000
MODO=2
REPETICOES=3
AQUECIMENTOS=1
```

A campanha mede todas as combinações de versão, tamanho e equipe. Todos usam
`-O2`, `schedule(runtime)`, `OMP_SCHEDULE=static` e `OMP_DYNAMIC=FALSE`. Assim,
a mudança de schedule não se mistura às mudanças entre versões. O trabalho
por célula é uniforme e a Tarefa 11 já mostrou o custo de blocos pequenos com
distribuição dinâmica.

Há uma execução de aquecimento por configuração, guardada em log e excluída
dos tempos brutos. As versões se alternam entre repetições: `v0/v1/v2`, depois
`v1/v2/v0`, depois `v2/v0/v1`. Tamanhos e equipes ainda têm ordem fixa. Não há
remoção automática de amostras nem garantia de eliminar efeitos de frequência
ou de outros processos.

O cronômetro envolve a evolução completa, do primeiro ao último passo, em
todas as versões. Inclui escalonamento, sincronização e entrada/saída das
regiões paralelas. Exclui alocação, inicialização, diagnósticos finais e a
gravação opcional do campo. Esse intervalo comum evita misturar a redução de
chamadas ao cronômetro com a otimização de uma das versões.

O programa registra as threads efetivamente usadas e interrompe se diferirem
das solicitadas. O script também recusa equipes acima de `SLURM_CPUS_PER_TASK`
quando houver uma alocação, ou de `nproc` em execução local. Threads de software
não devem ser chamadas automaticamente de núcleos físicos; consulte o
`lscpu` gravado na campanha.

## Escalabilidade forte, fraca e a matriz dos slides

Para passos fixos, a quantidade de trabalho é proporcional a
`W = nx * ny * passos`. Cada atualização de célula calcula as componentes `u`
e `v`.

### Forte: coluna fixa da matriz

Mantenha a mesma malha e os mesmos passos, variando apenas as threads `p`.
Para **cada versão e cada tamanho**, a referência é sua própria execução com
uma thread:

```text
S(p,N) = T(1,N) / T(p,N)
E(p,N) = S(p,N) / p
```

Isso está em `resumo.csv` e nas matrizes `eficiencia_v0.csv`, `v1` e `v2`.
As matrizes têm threads nas linhas e tamanhos nas colunas, como nos slides.
Observe também se aumentar a malha recupera a eficiência perdida com mais
threads: essa é a comparação geral de escalabilidade proposta na aula.

### Fraca: diagonal com trabalho por thread constante

Para a malha quadrada, aumente `N` proporcionalmente a `sqrt(p)`, mantendo os
passos. A carga por thread fica constante:

| Threads `p` | Malha | Atualizações por thread, com 2.000 passos |
| ---: | --- | ---: |
| 1 | 200 × 200 | 80.000.000 |
| 4 | 400 × 400 | 80.000.000 |
| 16 | 800 × 800 | 80.000.000 |

Essa diagonal é extraída automaticamente da matriz em `fraca.csv`, quando os
pontos estiverem presentes. A eficiência fraca usa:

```text
E_fraca(p) = T(1,N_base) / T(p,N_base*sqrt(p))
```

O ideal dessa comparação é manter o tempo constante. O script usa apenas
pontos exatos da relação `N² = N_base² * p`, sem arredondar malhas. Com quatro
threads há dois pontos (`p=1,4`); com 16, há três (`p=1,4,16`).

**Leitura dos slides:** é importante distinguir o lado da malha `N` do trabalho
`W`. O lado cresce menos que `p` (`sqrt(p)`), enquanto o total de células cresce
na mesma proporção de `p`. Essa distinção permite relacionar a observação de
crescimento menor do tamanho nos slides com o teste de carga por recurso
constante, sem confundir `N` com `N²`.

O domínio continua `[0,1) x [0,1)`, e `dt` diminui ao refinar a malha para
manter a estabilidade. Com passos fixos, essas cargas **não representam o
mesmo tempo físico final**. Aqui a fraca controla atualizações de células por
thread. Fixar o tempo físico exigiria aumentar também os passos e redefinir
o crescimento do trabalho; não se deve misturar os dois experimentos.

### Comparar evolução com escalabilidade

`ganho_sobre_v0` compara `T_v0(p,N) / T_versao(p,N)`, com mesma carga e equipe.
Isso mede o progresso entre versões. Já `speedup_versao` compara uma versão
consigo mesma, usando uma thread como referência. Uma versão pode reduzir o
tempo absoluto sem apresentar um speedup proporcionalmente maior.

As referências de uma thread ainda usam OpenMP; não são um executável
sequencial independente. Não extrapole as conclusões além das equipes e cargas
efetivamente medidas.

## Arquivos gerados por uma campanha

Cada execução cria uma pasta nova em `resultados/execucao_DATA_UTC_PID/`:

| Arquivo | Conteúdo |
| --- | --- |
| `tempos.csv` | Cada repetição, threads solicitadas/reais e diagnósticos finais. |
| `resumo.csv` | Média, desvio padrão amostral, CV, speedup, eficiência e ganho sobre `v0`. |
| `eficiencia_v*.csv` | Matriz de eficiência para cada versão. |
| `fraca.csv` | Diagonal de trabalho por thread constante. |
| `configuracao.json` | Carga, equipes, repetições, aquecimento e indicação local/SLURM. |
| `ambiente.txt` | Hostname, hardware, compilador, data UTC e alocação SLURM. |
| `fontes.sha256` | Identificação exata dos fontes e scripts medidos. |
| `compilacao.log`, `logs/` | Compilação, aquecimentos e todas as saídas das execuções. |
| `observacoes.txt` | Limites da campanha e avisos sobre duração e variabilidade. |

A análise rejeita matriz incompleta, repetições duplicadas, tempos inválidos,
threads divergentes e diagnósticos finais incompatíveis entre versões/equipes.
O desvio padrão é **amostral**. Com uma repetição, o zero na coluna de desvio
não representa estabilidade demonstrada; o aviso fica em `observacoes.txt`.

Para analisar novamente e, opcionalmente, gerar os gráficos:

```bash
python3 analisar_resultados.py resultados/execucao_DATA_PID

# Só os gráficos precisam de Matplotlib. Pode usar o .venv da Tarefa 11.
source ../Tarefa_11/.venv/bin/activate
python analisar_resultados.py resultados/execucao_DATA_PID --graficos
```

Os gráficos ficam na própria campanha, em `graficos/`. Não é necessário
instalar dependências gráficas no nó do NPAD: eles podem ser gerados no Ubuntu
depois de trazer os resultados.

## Preparação para o NPAD — execução em uma próxima etapa

`submeter_npad.sh` é um **modelo ajustável**, não uma confirmação da fila e dos
módulos da sua conta. Reserva um único nó, uma tarefa e 16 CPUs por tarefa.
Não fixa partição nem nome de módulo. Os recursos, a fila e a duração serão
conferidos quando formos trabalhar no acesso ao NPAD.

Quando essa etapa chegar, na pasta `Tarefa_12` do supercomputador:

```bash
# Depois de confirmar a partição e carregar o GCC apropriado:
sbatch submeter_npad.sh
```

A compilação é refeita dentro da alocação, e o `srun` inicia a campanha no nó
de computação. Todas as versões e equipes dessa campanha usam a mesma alocação.
Os testes de desempenho não devem ser executados diretamente no nó de login.
O modelo verifica que está dentro de um job SLURM.

A carga padrão pode ser ajustada sem editar os fontes, por exemplo:

```bash
PASSOS=5000 REPETICOES=5 sbatch submeter_npad.sh
```

Antes da campanha final, faça uma submissão pequena para estimar os tempos e
a memória. Aumente `PASSOS` se as medições forem muito curtas. Para mais pontos
fracos além de `p=16`, será necessário incluir também a malha correspondente
e verificar se existem recursos suficientes na alocação.

O material oficial do NPAD confirma o uso de `sbatch`, `--cpus-per-task` e
OpenMP em um nó. As instruções desta pasta não dependem de acessar conteúdos
de programação posteriores à Tarefa 12 nos slides:

- [NPAD: OpenMP e submissão](https://npad.ufrn.br/tutorials/advanced/openmp/)
- [NPAD: comandos SLURM](https://npad.ufrn.br/tutorials/intermediate/slurm_commands/)

## Correção e próximos passos

`python3 validar.py` verifica os campos completos das três versões em malhas
retangulares pequenas, com passos pares e ímpares, três modos e 1/2/4 threads.
Também verifica conservação da média, limites dos campos, estados constantes
e argumentos inválidos. Os arquivos ficam em uma pasta temporária e são
removidos. As equipes de quatro threads são apenas verificações curtas de
correção, podendo se sobrepor a menos CPUs disponíveis; o script de desempenho
não permite isso.

O diagnóstico final e o CSV opcional ficam fora da medição. Para inspecionar
um campo, forneça o nome do arquivo após o modo:

```bash
OMP_DYNAMIC=FALSE OMP_NUM_THREADS=2 OMP_SCHEDULE=static \
    ./bin/v2 80 80 1000 2 final.csv
```

Depois das medições reais, a análise deve discutir: ganho por versão; queda
de eficiência com a carga fixa; recuperação ao aumentar a malha; diagonal
fraca; dispersão; custo de regiões/barreiras; e possíveis limites de memória.
Sem contadores ou medições adicionais, limites de cache e largura de banda
devem ser tratados como hipóteses, não como causas quantitativamente provadas.
O relatório da Tarefa 12 será feito com esses dados reais.
