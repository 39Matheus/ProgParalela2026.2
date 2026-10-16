# Adaptação aos arquivos remotos enviados

A referência prioritária foi `ArquivosRemotosNPAD.zip`. Seu conteúdo foi
inspecionado na área de trabalho; os arquivos pessoais do pacote e as outras
tarefas não foram incorporados ao repositório.

O primeiro `ArquivosLocais.zip` excedeu o limite de transferência de 32 MiB.
O autor enviou depois uma versão menor, que foi lida e comparada com o ZIP
remoto. Essa conferência confirmou a configuração já adotada; não exigiu
alterar a implementação da Tarefa 12.

## O que foi aproveitado

| Referência remota | Evidência | Aplicação na Tarefa 12 |
| --- | --- | --- |
| `Tarefa_18/jobs.sh`, bloco CPU | `intel-128`, um nó, uma tarefa e `cpus-per-task`. | Partição padrão e formato do job OpenMP. |
| Mesmo bloco CPU | `gcc -O3 -fopenmp -std=c11 ... -lm`, sem `module load`. | Mesmas opções centrais e GCC encontrado no `PATH`, nas três versões. |
| Mesmo bloco CPU | Compilação e execução dentro do batch, a partir de `SLURM_SUBMIT_DIR`. | Compilação dentro da alocação e execução direta da campanha no batch. |
| Mesmo bloco CPU e arquivos `CPU1a.out`, `CPU1b.out`, `CPU4.out` | Cinco execuções por configuração. | Cinco repetições por padrão, com retenção de todos os tempos. |
| `Tarefa_14/job.sh` | Uso de `intel-512` em outra tarefa do autor. | Exemplo de substituição da partição por opção de `sbatch`; não é uma medição da Tarefa 12. |

O `jobs.sh` da Tarefa 12 é uma entrada curta que chama `sbatch` com o arquivo
de submissão. Ele submete somente a campanha CPU da Tarefa 12. As diretivas
ficam em `submeter_npad.sh`, sem duplicar seu conteúdo.

Os logs antigos de CPU mostram hostname e quantidade de threads, mas não
identificam o job SLURM nem a partição em cada saída. Não foram usados como
prova de desempenho da Tarefa 12. A nova campanha registra também o ID do job,
a lista de nós, a partição, os recursos solicitados e as threads efetivas.

## Limite de conteúdo e escolhas preservadas

Foram aproveitadas as informações de ambiente dos scripts remotos. A lógica
numérica continua sendo a difusão viscosa da Tarefa 11, com as evoluções
`v0`, `v1` e `v2` documentadas no README.

As implementações de MPI, GPU, offload, afinidade e ferramentas de profiling
nas tarefas posteriores não foram transplantadas. O limite continua sendo a
página 55 do PDF dos slides, numerada 57, onde está definida a Tarefa 12.

A otimização `-O3` está dentro desse limite: os níveis de otimização já aparecem
na Tarefa 3. Ela é aplicada igualmente às três versões; a Tarefa 11 e seu
relatório continuam com a configuração original `-O2`.

Foram mantidos os aquecimentos, a alternância da ordem das versões, os
diagnósticos de correção e as análises forte/fraca da preparação anterior.
A duração de uma hora e a solicitação de 16 CPUs são escolhas iniciais para
a matriz da Tarefa 12, não valores que tenham sido testados nessa conta.

Cada campanha agora compila em seu próprio diretório para evitar colisões
caso mais de um job seja submetido. O nome da versão, os hashes dos fontes,
o compilador e a opção `-O3` ficam registrados com os resultados.

## Conferência complementar dos arquivos locais

- `Done/Tarefa_14/job.sh` coincide com o remoto desconsiderando espaços e
  quebras de linha finais; o fonte `tarefa14.c` e o log correspondente também
  coincidem.
- Os três fontes da Tarefa 18 (`aux18.c`, `t18.c` e `somas.c`) coincidem com os
  remotos, assim como `heat.c` e `heat_t18.c` da Tarefa 19.
- O `Tarefa_18/jobs.sh` local difere do remoto: seu bloco CPU solicita
  `intel-512`, usa `ntasks-per-node=8` e define threads por `SLURM_NTASKS`.
  O remoto usa `intel-128`, uma tarefa, `cpus-per-task` e cinco repetições.
  Foi mantida a organização remota de uma tarefa OpenMP com várias threads.
- Os benchmarks locais das tarefas 15 a 17 possuem matrizes de tamanhos e
  equipes, logs completos, repetições e média/desvio amostral. Essas práticas
  já estão presentes na Tarefa 12; seus mecanismos MPI não foram incorporados.
- Os exemplos da Tarefa 4 deixam inicialização e checksum fora do intervalo
  cronometrado. A Tarefa 12 já faz isso com a inicialização e os diagnósticos
  finais; não foi necessário mudar a medição.

Nenhum executável dos pacotes foi executado, e os arquivos das outras tarefas
não foram copiados para a Tarefa 12. Não foram feitos novos testes de desempenho
nem submetidos jobs ao NPAD nesta conferência documental.
