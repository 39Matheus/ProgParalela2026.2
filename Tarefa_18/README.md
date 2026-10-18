# Tarefa 18 — soma de vetores em CPU e GPU com OpenMP

O enunciado está em [`requisitosTarefa18.txt`](requisitosTarefa18.txt).
O [relatório em PDF](Relatorio/relatorio.pdf) explica a implementação, os
conceitos e os resultados, com códigos e logs completos nos apêndices.
O [projeto Overleaf](Relatorio/overleaf.zip) pode ser importado diretamente.
Veja as [instruções do relatório](Relatorio/README.md).

Os arquivos originais foram preservados. A análise considera os sete logs
enviados: 35 medições e quatro aquecimentos. O modo CPU com quatro threads
configuradas apresentou média de aproximadamente 5,379 ms; as referências
de uma thread ficaram em 10,568 ms e 9,975 ms.

Os registros identificam nós com V100 e H200, mas ainda não comprovam que a
região target executou no acelerador. O relatório documenta essa limitação,
o tratamento dos dados e a confirmação necessária. Os tempos do modo declarado
GPU não são apresentados como uma comparação final entre dispositivos.

`jobs.sh` submete dois jobs e compila apenas `t18.c`, pois este inclui
`aux18.c` e `somas.c`. O script atual configura uma thread CPU e a partição
V100; não reproduz sozinho as variações CPU4 e H200 dos logs históricos.

O diagnóstico em [`Relatorio/codigos/diagnostico_offload.c`](Relatorio/codigos/diagnostico_offload.c)
é apoio para uma nova execução, não parte da campanha recebida. As próximas
simulações devem ocorrer dentro de uma alocação no NPAD, com compilação e
dispositivo de execução registrados.
