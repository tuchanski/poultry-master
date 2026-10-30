# MVP sequencial: escopo e próximas verificações

O fluxo atual recebe fotos de uma câmera fixa, detecta aves com o detector
existente e associa caixas entre capturas para sinalizar imobilidade aparente.
As entradas, parâmetros e saídas estão em [análise sequencial](analise-sequencial.md)
e o comportamento detalhado em [fluxo atual](fluxo-atual-mvp-sequencial.md).

## Escopo implementado

- Pasta de capturas com timestamps ou manifesto CSV com fuso horário.
- Detecção por foto, filtro opcional por ROI e associação um a um de caixas.
- IDs temporários e estados `tracking`, `stationary_candidate` e `lost`.
- Tempo observado limitado por intervalo, tolerância de capturas ausentes e
  separação de sessões após pausas longas.
- Fotos anotadas, `tracks.csv` e `report.json` para revisão humana.

Os padrões temporais estão no comando `analyze_sequence.py --help`.
O classificador de saúde foi removido. Captura automática, vídeo em tempo real,
múltiplas câmeras, identificação permanente e alertas automáticos ficam fora
do escopo atual.

## Próximas verificações

1. Revisar caixas associadas nas capturas de granja e registrar trocas de identidade,
   oclusões e erros de detecção.
2. Conferir candidatos e duração acumulada com as fotos e observações em `tracks.csv`.
3. Obter sequências representativas com revisão humana antes de escolher novos
   limiares ou afirmar desempenho em campo.
4. Avaliar falsos candidatos e trajetórias perdidas sem usar o teste reservado
   do detector para ajustar parâmetros.

Imobilidade aparente pode corresponder a descanso, oclusão ou falhas do sistema.
Nenhum candidato confirma óbito; a verificação humana permanece necessária.
