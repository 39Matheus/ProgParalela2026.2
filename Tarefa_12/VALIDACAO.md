# Verificações da preparação

Estas são verificações de desenvolvimento, não resultados de escalabilidade
do NPAD. Nenhum job foi submetido ao supercomputador nesta etapa.

- Compilação inicial de `v0`, `v1` e `v2` com GCC, OpenMP, `-O2` e avisos
  adicionais tratados como erro: sem erros.
- `validar.py`: 54 execuções curtas; campos completos idênticos entre versões
  e equipes nos três modos, em duas malhas retangulares, com passos pares e
  ímpares. Conservação da média, estados constantes, redução do pico e limites
  dos valores conferidos.
- Comparação adicional do campo de `v0` com o código da Tarefa 11: valores
  compatíveis dentro da precisão dos CSVs da tarefa anterior.
- Fluxo completo de coleta: uma matriz pequena com 18 configurações e duas
  repetições, com aquecimentos, logs, metadados e resumos. Arquivos mantidos
  fora do repositório por serem verificações locais.
- Fórmulas da análise conferidas com dados sintéticos de tempo conhecido:
  eficiência forte, diagonal fraca e ganho entre versões. Os dados sintéticos
  ficaram fora do repositório.
- Campanha incompleta rejeitada pelo analisador; geração opcional dos quatro
  gráficos conferida; sintaxe dos scripts Bash verificada.

O conteúdo de `Tarefa_11`, inclusive o relatório final, foi preservado.
O próximo passo é conferir a alocação e os módulos da conta do NPAD e realizar
as medições em um nó de computação.

## Adaptação ao ZIP remoto

A configuração passou a usar `-O3`, cinco repetições e `intel-128`, conforme
o exemplo remoto de CPU da Tarefa 18. A correção das três versões foi novamente
verificada com `-O3`. O fluxo local de coleta/análise também foi conferido com
binários separados por campanha. O script `jobs.sh` foi verificado com uma
substituição local de `sbatch`, sem enviar um job real.
