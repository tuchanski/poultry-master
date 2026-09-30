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
