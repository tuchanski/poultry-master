# Experimentos e auditoria dos dados

## Etapa 1 — Inspeção inicial em 30/09/2026

**Resultado:** requisitos alinhados ao fluxo de múltiplas aves; arquivos acessíveis, extraídos e inspecionados; licenças confirmadas. A auditoria identificou pendências de preparação que impedem considerar os dados prontos para treinamento, especialmente o uso de imagens de saúde como recortes individuais.

Nenhum modelo foi treinado, nenhuma nova divisão foi criada e os arquivos originais foram preservados. Os diretórios locais de dados e resultados estão excluídos do Git.

## 1. Origem, acesso e condições de uso

| Dataset | Arquivo local | Tamanho em bytes | MD5 local |
| --- | --- | --- | --- |
| PIO | `pio/data.rar` | 1.523.257.163 | `c207661257123da12df2ea700fe4c2d1` |
| Chicken Health | `kaggle/archive.zip` | 93.513.772 | `9131fdc1c12966911f3227fc96291c85` |

- **PIO:** o MD5 corresponde ao informado pelo usuário e ao publicado na [API do registro Zenodo](https://zenodo.org/api/records/16686320). O registro declara acesso aberto e licença **CC BY 4.0**. Manter atribuição à fonte e aos autores Keyla Boniche e Edmanuel Cruz e identificar alterações nos dados derivados. [Página do dataset](https://zenodo.org/records/16686320).
- **Chicken Health:** a [API pública do Kaggle](https://www.kaggle.com/api/v1/datasets/list?search=chicken-health-images-dataset-rgb-and-thermal) informa **CC0: Public Domain**, autor Eko Supriyanto e versão atual 2. O tamanho publicado corresponde ao ZIP local, mas não foi obtido checksum remoto para comprovar sua versão. O MD5 acima serve como identificação do arquivo inspecionado. [Página do dataset](https://www.kaggle.com/datasets/ekosupriyanto/chicken-health-images-dataset-rgb-and-thermal).
- Os arquivos compactados não contêm arquivos de licença. Os metadados consultados foram salvos localmente em `outputs/inspection/pio-metadata.json` e `kaggle-metadata.json`.
- Foram obtidos também os pequenos documentos `pio/Readme.txt` e `pio/FilePrefixCode.xlsx` do Zenodo, para conferir a nomenclatura dos dados. Não foi necessário baixar vídeos.

## 2. PIO — detecção

Estrutura extraída em `pio/data/`:

```text
classes.txt
dataset.yaml
images/train/*.jpg
images/val/*.jpg
labels/train/*.txt
labels/val/*.txt
labels/train/classes.txt
labels/train.cache
labels/val.cache
```

| Divisão original | Imagens | Linhas de anotação não vazias |
| --- | ---: | ---: |
| Treino | 1.035 | 253.429 |
| Validação | 452 | 73.859 |
| Total | 1.487 | 327.288 |

As 1.487 imagens possuem arquivo de anotação correspondente, sem anotações órfãs. Há 1.452 imagens em 1920 × 1080 e 35 em 1920 × 1088. Todas abriram para leitura das dimensões; isso não substitui a avaliação visual integral do dataset.

As anotações usam cinco campos YOLO: `classe centro_x centro_y largura altura`. A única classe encontrada foi `0`, denominada **`Pollo`** em `classes.txt` e `dataset.yaml`. A preparação deverá mapear esse nome para `chicken`, preservando o índice.

O YAML original contém caminhos absolutos `/app/data/images/train` e `/app/data/images/val`, que não correspondem à instalação local. Gerar configuração própria na etapa 2. Os arquivos `.cache` e o `classes.txt` dentro de `labels/train` não são anotações de imagens e devem ser excluídos da preparação.

### Problemas encontrados

1. **Cinco caixas com largura zero:** três no treino e duas na validação. As demais 327.283 linhas passaram nas verificações de formato, classe, valores finitos, dimensões positivas e coordenadas normalizadas. Não foram encontradas caixas válidas extrapolando a imagem além da tolerância de 0,00001.
2. **122 grupos de imagens idênticas por SHA-256**, envolvendo 249 arquivos, ou 127 cópias excedentes. **57 desses grupos atravessam treino e validação**, comprovando vazamento na divisão original.
3. Em **112 grupos de imagens idênticas**, os arquivos de anotação diferem em bytes. É necessário comparar semanticamente as caixas antes de escolher uma versão; diferença de bytes, isoladamente, não comprova conflito entre as caixas. Não foram encontradas linhas de anotação exatamente repetidas dentro de um mesmo arquivo.
4. O total local de 327.288 linhas difere em uma unidade das 327.289 instâncias citadas no README. O MD5 do arquivo está correto; usar o inventário local como referência da preparação e registrar os descartes posteriores.
5. Há de 1 a **1.151 caixas por imagem** antes da limpeza. O exemplo com maior contagem é `train/C-W1-0061.jpg`. A contagem de anotações não é confirmação de igual número de animais distintos; revisar os casos extremos e evitar truncamento silencioso pelo limite de detecções do modelo.

Caixas inválidas identificadas, com linhas numeradas a partir de 1:

| Arquivo em `pio/data/labels/` | Linha | Problema |
| --- | ---: | --- |
| `train/C-W3-0016.txt` | 332 | Largura 0 |
| `train/C-W3-0063.txt` | 334 | Largura 0 |
| `train/C-W6-0128.txt` | 149 | Largura 0 |
| `val/C-W3-V0038.txt` | 301 | Largura 0 |
| `val/P-W2-V0014.txt` | 86 | Largura 0 |

### Inspeção visual

Foram sobrepostas as caixas em quatro imagens: `train/C-W1-0001.jpg`, `train/C-W3-0001.jpg`, `train/P-W6-0025.jpg` e `val/C-W1-V0001.jpg`. A amostra inclui alta densidade, iluminação desigual, aves pequenas, oclusões e animais cortados pelas bordas. As caixas examinadas localizam aves, mas esta amostra não valida todas as anotações. A montagem local está em `outputs/inspection/pio-boxes.jpg`.

Os documentos de origem identificam `C` como instalação comercial, `P` como protótipo e `W1` a `W6` como semanas de crescimento. Esses prefixos ajudam a agrupar capturas, mas não identificam cada animal nem garantem independência. Duplicatas exatas aparecem inclusive entre prefixos diferentes; agrupar apenas pelo nome não basta.

O pacote `data.rar` não contém uma divisão de teste. O registro do Zenodo oferece separadamente `Test 2025.rar`, ainda não baixado nem inspecionado; sua adequação pode ser avaliada depois. O PIO possui rótulos de detecção, sem rótulos de saúde, portanto não permite quantificar a cobertura da classe `dead`.

## 3. Chicken Health — classificação

Arquivos extraídos em `kaggle/extracted/Multimodal Chicken Datasets/`, com as pastas `healthy`, `sick` e `dead`. O ZIP contém somente 1.200 JPGs, todos em 640 × 480, sem bounding boxes, metadados de animais/sessões, documentação ou divisão de treino/validação/teste.

| Classe | Prefixo RGB | RGB | Térmicas | RGB únicos por SHA-256 |
| --- | --- | ---: | ---: | ---: |
| `healthy` | `sehat_rgb_` | 200 | 200 | 198 |
| `sick` | `sakit_rgb_` | 200 | 200 | 200 |
| `dead` | `mati_rgb_` | 200 | 200 | 200 |
| Total | — | 600 | 600 | 598 |

O nome `_rgb_` identifica a seleção inicial para o MVP; `_inframerah_` identifica a modalidade térmica, que fica fora do treinamento inicial. Foram gerados manifestos separados `outputs/inspection/health-rgb.csv` e `health-thermal.csv`, sem mover nem modificar os originais. As três pastas correspondem às classes previstas, mas os rótulos são da imagem inteira.

Duplicatas exatas encontradas:

- `healthy/sehat_rgb_113.jpg` e `healthy/sehat_rgb_135.jpg`.
- `healthy/sehat_rgb_136.jpg` e `healthy/sehat_rgb_141.jpg`.
- `sick/sakit_inframerah_155.jpg` e `sick/sakit_inframerah_156.jpg`.

Não foram encontradas imagens de bytes idênticos em classes diferentes. Isso não exclui imagens quase idênticas nem frames do mesmo animal.

### Inspeção visual e adequação dos rótulos

Foram examinadas 12 imagens RGB: números 1, 70, 140 e 200 de cada classe. A montagem está em `outputs/inspection/health-rgb.jpg`. Também foi aberta `dead/mati_inframerah_1.jpg` para confirmar visualmente a distinção entre as modalidades na amostra.

**A suposição de uma única ave por imagem não é válida para todo o conjunto:** `dead/mati_rgb_200.jpg` contém duas aves, e `healthy/sehat_rgb_140.jpg` inclui outra ave parcialmente visível na borda. Há ainda imagens com ave pequena em relação ao fundo, desfoque e enquadramentos muito diferentes dos recortes do detector.

Não há anotações individuais para extrair automaticamente recortes com rótulos confiáveis. Portanto, **as 600 imagens RGB não equivalem a 600 exemplos prontos para o classificador por ave**. Não atribuir o rótulo da pasta a todas as aves visíveis. A aparência observada também não comprova por si só a condição clínica atribuída pelo dataset.

Será necessário revisar a seleção RGB e produzir um manifesto de recortes por ave: caminho da imagem de origem, caixa, rótulo revisado e grupo de captura quando identificável. Imagens ambíguas devem ser excluídas da seleção inicial, com registro do motivo. A contagem final por classe será recalculada após essa revisão. A revisão completa e a criação desses recortes ainda não foram realizadas.

O fundo e a distância da câmera variam na amostra e podem influenciar o aprendizado. O balanceamento de arquivos não comprova diversidade de animais, nem garante generalização para granjas ou para aves saudáveis descansando.

## 4. Decisões para a preparação dos dados

| Pendência | Tratamento proposto antes do treinamento |
| --- | --- |
| Cinco caixas sem área no PIO | Descartar apenas na cópia preparada e registrar arquivo/linha; preservar originais |
| Duplicatas e divisões do PIO | Revisar anotações das cópias, deduplicar e refazer divisões mantendo imagens relacionadas juntas |
| Sequências e aves repetidas | Combinar hashes, informações de captura e revisão visual; não confiar apenas em sorteio por arquivo |
| Classificação por ave sem caixas de saúde | Revisar e anotar recortes individuais; excluir casos ambíguos e preservar o vínculo com a imagem de origem |
| Mistura de modalidades | Utilizar o manifesto RGB; manter térmicas fora do MVP |
| Configuração e caches do PIO | Criar YAML local e não reutilizar caches fornecidos |
| Teste independente | Reservar grupos antes de gerar recortes/aumentos; avaliar separadamente a possibilidade do pacote de teste adicional |
| Generalização para `dead` | Avaliar o detector e o fluxo integrado com exemplos revisados; não inferir cobertura de mortalidade a partir da classe `Pollo` |

**Condição de avanço:** é possível iniciar a preparação do ambiente e a limpeza do detector na etapa 2. O treinamento deve aguardar a correção das divisões e a preparação das anotações; para o classificador, falta resolver a seleção de recortes e seus rótulos. Não há evidência suficiente para considerar a identificação de mortalidade validada.

## 5. Como reproduzir a auditoria

Foi usado Windows PowerShell com bibliotecas .NET disponíveis no sistema. `python` aponta para o atalho da Microsoft Store e não executou um interpretador; o ambiente Python será tratado na etapa 2.

Com os arquivos extraídos nas pastas descritas acima, executar na raiz do projeto:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/inspect-data.ps1
```

O script não modifica imagens ou anotações. Ele verifica correspondência imagem/rótulo, campos YOLO, leitura das dimensões, hashes SHA-256, duplicatas e MD5 dos arquivos compactados. Os resultados ficam em `outputs/inspection/inventory.csv`, `summary.json` e nos dois manifestos de modalidade. A inspeção visual descrita acima foi realizada separadamente; o script não gera as montagens e não determina a condição de saúde dos animais.

A auditoria não fez análise de similaridade perceptual, revisão de todas as caixas ou comprovação clínica dos rótulos. Os resultados aqui descritos se referem aos arquivos originais, antes de qualquer limpeza ou divisão nova.

## Etapa 2 — Preparação em 01/10/2026

O [guia de preparação](preparacao-dados.md) documenta os comandos e as decisões. O usuário informou não possuir anotações adicionais de saúde ou grupos de captura e optou pela preparação de uma revisão manual.

### Ambiente verificado

- Python 3.12.11 local, ambiente `.venv`, 39 dependências fixadas em `requirements.txt`.
- PyTorch 2.8.0+cu128, torchvision 0.23.0+cu128, Ultralytics 8.3.203, Pillow 11.3.0, NumPy 2.2.6, scikit-learn 1.7.2 e PyYAML 6.0.2.
- CPU e GPU testadas com operação de tensor; CUDA disponível na NVIDIA GeForce RTX 4070 Ti SUPER, com 16 GB.
- Checkpoints iniciais definidos: `yolo11n.pt` e `yolo11n-cls.pt`. Nenhum treinamento ou download de pesos executado.

### Resultado do PIO

As diferenças nos arquivos de anotação de 112 grupos de duplicatas também existem após comparação numérica e ordenação das caixas. Foram excluídas da cópia preparada as 229 imagens desses grupos, dez cópias equivalentes e 19 imagens com prefixo `K`, não explicado no documento de nomenclatura. As cinco caixas sem área foram descartadas durante a leitura dos originais. Os registros completos estão em `data/prepared/pio`.

| Divisão | Imagens |
| --- | ---: |
| Treino | 870 |
| Validação | 171 |
| Teste | 188 |
| Total | 1.229 |

Restaram 280.655 caixas. A semente é 42; a meta 70/15/15 é aproximada para preservar os grupos de captura. Os grupos foram unidos transitivamente quando ligados por imagens idênticas, inclusive antes das exclusões. Não há interseção de hashes ou grupos entre divisões. A independência de animais entre semanas e a ausência de frames quase iguais não foram comprovadas.

Foram verificados os hashes e as anotações de todos os arquivos preparados. O carregador `YOLODataset` verificou as três divisões e retornou uma amostra `3 × 640 × 640` de cada uma, sem arquivos corrompidos. Isso é uma verificação de leitura, não uma avaliação de desempenho no teste.

### Classificador e testes

O CSV `data/review/health.csv` contém 600 imagens RGB: duas cópias exatas marcadas como excluídas e 598 imagens pendentes. A página `data/review/health.html` permite marcar um recorte por foto, informar o grupo e exportar o CSV. Imagens térmicas não entram na fila. Os rótulos originais não foram alterados e nenhum recorte real foi aprovado automaticamente.

A execução de `prepare_data.py health` recusa a revisão incompleta, como esperado. O exportador foi testado com imagens sintéticas revisadas; a geração real do dataset de classificação aguarda as decisões do usuário. Caso a revisão não consiga identificar sessões suficientes, ainda será necessário resolver essa limitação antes de afirmar que existe teste independente.

Passaram nove testes automatizados, a verificação das dependências instaladas e o teste da ferramenta de revisão no navegador Edge. A preparação não aplica aumentos de dados nem altera os arquivos originais.


## Etapa 3 — treinamento e revisão binária (01/10/2026)

YOLO11n ajustado no PIO preparado: 870 imagens de treino, 171 de validação e 188 de teste reservado. Execução `outputs/training/detector-baseline`, origem `models/pretrained/yolo11n.pt`, semente 42, entrada 640, lote 8, máximo de 15 épocas, paciência 5, limite de 1.500 detecções, RTX 4070 Ti SUPER. Concluídas 13 épocas em aproximadamente 565 segundos. Melhor checkpoint da validação exportado para `models/detector.pt`; hashes, versões e parâmetros em `models/detector.json`.

| Métrica na validação do PIO | Resultado |
| --- | ---: |
| Precisão | 0,8286 |
| Recall | 0,7278 |
| mAP@50 | 0,8154 |
| mAP@50–95 | 0,5082 |

Não são métricas de teste nem comprovam identificação de aves mortas. No dataset de saúde, a inspeção mostrou caixas no fundo e recortes parciais. A fila `data/review/binary`, com entrada 640 e confiança 0,15, atingiu o limite de 20 sugestões em todas as 80 imagens. Uma amostra de oito imagens com entrada 320 e confiança 0,4 melhorou alguns casos `dead`, mas ainda apresentou erros em `healthy`. Nenhuma caixa foi aprovada automaticamente.

Aplicado o fallback do plano: `data/review/binary-manual/health.html`, 40 imagens únicas por classe, semente 42, todas pendentes. Sugestões anteriores e revisão original preservadas. A configuração seleciona explicitamente essas 80 imagens e exclui `sick` do treinamento.

Preparação e treinador binários implementados: divisão por grupos conhecidos ou demonstração somente com treino. O modo demonstrativo exige opção explícita, usa orçamento fixo e exporta a última época, sem selecionar por validação nem fabricar métricas independentes. Grupos desconhecidos permanecem vazios com observações.

Testes unitários e dois treinos de uma época com oito imagens sintéticas verificaram o código, um por modo, em `outputs/classifier-smoke`. Esses pesos não foram exportados como `models/classifier.pt` e não substituem treino real. Treinamento real do classificador, integração e avaliação independente permanecem pendentes.


### Conclusão do treinamento binário — 01/10/2026

O usuário concluiu e aprovou os 80 recortes (40 `dead`, 40 `healthy`). A observação de grupo desconhecido foi normalizada para o campo de notas, mantendo grupos vazios, caixas e aprovações; o CSV anterior foi preservado em backup. Dataset final: `data/prepared/health-binary-reviewed`, configurado em `config.json`, somente treino demonstrativo.

Treinamento real `classifier-reviewed`: YOLO11n-cls, semente 42, entrada 224, lote 16, 15 épocas fixas, GPU RTX 4070 Ti SUPER, aproximadamente 16,69 segundos incluindo preparação do treino. Última época exportada para `models/classifier.pt`; mapeamento `0: dead`, `1: healthy`. Metadados em `models/classifier.json`, com métricas de validação nulas e avaliação independente pendente. SHA-256 dos pesos: `830358f8bd8ecc993eec32109ca430d13494cb4d972e33e2ea0e9bdddc18e4af`.

A primeira tentativa `classifier-baseline` foi interrompida por restrição de acesso do sandbox; foi preservada e substituída por uma nova execução autorizada, sem reutilizar artefatos parciais.

Verificação funcional em CPU com os dois pesos reais: fotos `dead/mati_rgb_109.jpg` e `healthy/sehat_rgb_10.jpg`, ambas usadas no treinamento. Detector com entrada 320, confiança 0,4 e limite 20 produziu respectivamente 5 e 20 recortes, classificados com sucesso. Resultado em `outputs/classifier-reviewed-inference.json`. Isso confirma compatibilidade e execução, não qualidade das caixas nem generalização; permanecem os erros de detecção neste domínio. Não foram calculadas métricas de teste sobre essas imagens. Próxima etapa: integração em CLI, imagem anotada e relatório JSON.


## Etapa 4 — integração em CLI (01/10/2026)

Implementados `analyze.py`, `src/pipeline.py` e `src/reporting.py`. Os pesos e metadados são validados por tarefa, classes e hash. CPU por padrão; detecção 640, confiança 0,25, IoU 0,7, máximo 1.500; classificação 224 em lotes de 32. Limiares iniciais, sem ajuste no teste reservado. A saída registra parâmetros, versões por hash, horário com fuso, dimensões, caixas, confianças separadas, contagens, percentuais e candidatos à verificação.

Verificação: 16 testes unitários passaram, cobrindo também ausência de detecções, recortes nas bordas, descarte de caixas vazias, preservação da associação caixa/classe com mapeamento invertido, falha de classificação e limite de detecções. Testes da CLI com pesos reais confirmaram saída zerada para uma imagem branca com confiança configurada em 1, erro para entrada inválida, peso ausente e pasta existente. Esses cenários são controles funcionais, não avaliação dos modelos.

Execuções reais em CPU, com tempo incluindo carregamento dos modelos, inferência e gravação da imagem:

| Foto | Uso prévio | Tempo | Caixas | healthy | dead |
| --- | --- | ---: | ---: | ---: | ---: |
| `dead/mati_rgb_109.jpg` (640×480) | Treino do classificador | 3,156 s | 13 | 6 | 7 |
| `C-W1-0001.jpg` (1920×1080) | Treino do detector | 6,062 s | 868 | 370 | 498 |

Artefatos: `outputs/analysis-stage4` e `outputs/analysis-stage4-pio`, cada um com `annotated.jpg` e `report.json`. A inspeção visual da foto de saúde identificou caixas no chão e partes de aves. Na cena densa do PIO há sobreposição de textos, e o grande número de previsões `dead` evidencia a necessidade de avaliar a transferência do classificador para esse domínio. Não há rótulos individuais de saúde no PIO para medir esses erros. Essas contagens não são mortalidade confirmada, e os exemplos não constituem teste independente. A etapa 5 deve avaliar e registrar essas limitações; não foram usados dados de teste para ajustar parâmetros.
