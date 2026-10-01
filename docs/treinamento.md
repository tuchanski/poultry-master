# Treinamento — etapa 3

Os dois modelos reais estão disponíveis em `models/detector.pt` e `models/classifier.pt`. A revisão das 80 imagens foi concluída, os recortes estão em `data/prepared/health-binary-reviewed` e o classificador foi treinado por 15 épocas. A avaliação independente permanece pendente. A integração está disponível em `analyze.py`; consulte o [guia de análise](analise.md).

Os passos abaixo documentam a reprodução do treinamento. Neste workspace, não é necessário refazer a revisão ou o treino; os scripts recusam sobrescrever pastas de preparação ou execuções existentes.

## Revisar e preparar os recortes

1. Abra `data/review/binary-manual/health.html`: são **80 imagens, 40 de cada classe**. A revisão original de 600 imagens continua preservada.
2. Desenhe uma caixa envolvendo uma única ave e confira se o rótulo da foto se aplica a ela. Exclua imagens ambíguas, anotando o motivo.
3. Se não conhecer o animal/sessão, deixe o grupo vazio e registre nas observações `Grupo desconhecido; uso demonstrativo`. Não invente grupos.
4. Baixe o CSV periodicamente. Para retomar, importe a última cópia na página. Ao concluir, substitua `data/review/binary-manual/health.csv` pelo arquivo baixado.

Todas as 80 decisões precisam estar resolvidas, com exemplos aceitos das duas classes. A preparação rejeita linhas pendentes, caixas inválidas e alterações de identidade. Não é necessário revisar as imagens fora dessa seleção.

Como não há informação confiável sobre sessões, o caminho disponível é o treinamento demonstrativo:

```powershell
.venv/Scripts/python.exe scripts/prepare_data.py health --mode demonstration
.venv/Scripts/python.exe scripts/train_classifier.py --allow-demonstration
```

Esse modo gera somente `train/{dead,healthy}`, treina por 15 épocas e exporta a última época para `models/classifier.pt`, com metadados em `models/classifier.json`. Não cria validação/teste artificiais nem métricas de generalização. A avaliação independente permanece pendente.

Se houver grupos reais suficientes no futuro, use `prepare_data.py health --mode grouped` em uma pasta nova e passe esse dataset a `train_classifier.py --dataset CAMINHO`, sem a opção demonstrativa. O modo agrupado seleciona o checkpoint pela validação e reserva o teste.

## Reproduzir o detector

Os checkpoints iniciais já estão em `models/pretrained`. Em outra instalação, obtenha [yolo11n.pt](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt) e [yolo11n-cls.pt](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n-cls.pt) e salve-os nessa pasta. Instale o ambiente e prepare o PIO conforme o [guia de preparação](preparacao-dados.md).

```powershell
.venv/Scripts/python.exe scripts/train_detector.py --epochs 15 --batch 8 --device 0 --name detector-v2
```

O treino usa imagens de 640 pixels, semente 42, paciência de cinco épocas e limite de 1.500 detecções para as cenas densas do PIO. Seleciona o melhor checkpoint pela validação e exporta `models/detector.pt` e `models/detector.json`. O teste não participa dessa seleção.

Os scripts recusam repetir um nome de execução existente. Para outro treino, use um novo `--name`. Os pesos exportados em `models` são substituídos; os checkpoints anteriores permanecem em `outputs/training/NOME/weights`. No classificador, `--output` permite escolher outro destino. Use `--device cpu` para execução sem GPU.

## Sugestões de caixas

```powershell
# Nova fila com sugestões do detector, todas pendentes de revisão.
.venv/Scripts/python.exe scripts/suggest_health_boxes.py --output data/review/binary-v2/health.csv

# Nova fila para marcação manual, sem executar o detector.
.venv/Scripts/python.exe scripts/suggest_health_boxes.py --manual --output data/review/manual-v2/health.csv
```

Cada fila tem CSV, HTML, `selection.json` e `suggestions.json`. A seleção padrão usa 40 imagens únicas por classe e semente 42. Decisões correspondentes da revisão original são preservadas. Para continuar outra revisão, informe seu CSV em `--prior-review`. Quando houver várias sugestões, selecione explicitamente uma caixa e ajuste-a antes de aceitar.

As sugestões inspecionadas no dataset de saúde incluíam fundo e partes da ave; por isso, a configuração atual usa a fila **binary-manual**. O resultado de validação no PIO não demonstra boa detecção nesse outro ambiente. Para usar outra fila, atualize `health_review` e `health_selection` em `config.json`.

## Verificação realizada

O detector foi treinado em dados reais. Os testes automatizados verificam a preparação, e treinos de uma época com imagens sintéticas verificaram os modos agrupado e demonstrativo do classificador. Esses artefatos estão separados em `outputs/classifier-smoke`. Depois, foi executado o treino real `classifier-reviewed`, seguido de inferência em CPU com os dois pesos reais. O registro `outputs/classifier-reviewed-inference.json` usa fotos de treinamento e verifica execução, não generalização. Os resultados e limitações estão em [experimentos](experimentos.md).
