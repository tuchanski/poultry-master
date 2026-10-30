# Treinamento do detector

Prepare o PIO conforme [preparação dos dados](preparacao-dados.md) e disponibilize
o checkpoint inicial em `models/pretrained/yolo11n.pt`, correspondente a
`detector_checkpoint` em `config.json`.

```bash
.venv/bin/python scripts/train_detector.py --device cpu --name detector-baseline
```

No Windows com NVIDIA, use `.venv/Scripts/python.exe` e `--device 0`.
Os padrões são 15 épocas, lote 8 e entrada 640. As opções `--epochs`, `--batch`
e `--imgsz` permitem alterar esses parâmetros. Escolha um nome de execução novo.

O treino utiliza somente treino e validação; o teste reservado não seleciona os
pesos. O melhor checkpoint na validação é exportado para `models/detector.pt`,
com classes, hash e parâmetros em `models/detector.json`. Esses arquivos são
sobrescritos ao exportar outro treino; preserve o par anterior se necessário.
O histórico fica em `outputs/training/<nome>`.

A análise sequencial exige o peso e o JSON correspondentes. A tarefa deve ser
`detect` e a única classe deve ser `chicken`. Confira a [avaliação](avaliacao.md)
para reproduzir as métricas do detector; elas não avaliam o associador temporal.
