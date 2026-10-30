# Requisitos do MVP sequencial

O sistema processa fotos RGB sucessivas de uma câmera fixa para detectar aves,
associar caixas e indicar imobilidade aparente para revisão humana.

## Entrada e execução

- Execução local por linha de comando, em Python 3.12, com CPU por padrão.
- Pasta de capturas com timestamps no nome ou manifesto CSV com `image` e
  `timestamp`, incluindo fuso horário.
- Ordenação cronológica; rejeição de horários repetidos, imagens ausentes e
  dimensões incompatíveis.
- Detector YOLO com tarefa `detect`, classe `chicken` e metadados validados por hash.
- ROI opcional, incluindo caixas cujo centro esteja dentro da região.

## Associação e resultados

- IDs temporários associados por distância dos centros e IoU, com correspondência
  um a um. Os IDs não identificam permanentemente os animais.
- Estados `tracking`, `stationary_candidate` e `lost`.
- Crédito de tempo limitado pelo intervalo nominal; movimento reinicia a
  acumulação, ausências encerram trajetórias após a tolerância e pausas longas
  iniciam novas sessões.
- Saída nova por execução, com fotos anotadas, `tracks.csv` e `report.json`.
- Preservação das imagens originais e registro dos parâmetros e hash do detector.

## Limites

O MVP não inclui classificação de saúde, diagnóstico de óbito, alertas
automáticos, captura de câmera, serviço contínuo, múltiplas câmeras ou interface
web. Candidatos exigem revisão humana. Os testes controlados e a avaliação do
PIO não comprovam desempenho sequencial em uma granja real.
