# Preparação dos dados — etapas 2 e 3

O ambiente, o PIO e os 80 recortes binários aprovados estão preparados. Os recortes estão em `data/prepared/health-binary-reviewed`, somente para treino demonstrativo, pois os grupos de captura são desconhecidos. Os dois modelos foram treinados na etapa 3; veja o [guia de treinamento](treinamento.md).

## Ambiente

Neste workspace, o Python 3.12.11 está instalado em `.tools/python` e o ambiente virtual em `.venv`. Não é necessário ativar o ambiente nem alterar o Python do sistema:

```powershell
.venv/Scripts/python.exe scripts/check_environment.py
```

A verificação importa as bibliotecas, executa uma operação em CPU e outra em GPU quando disponível e salva `outputs/environment.json`. Foram confirmados PyTorch 2.8.0 com CUDA 12.8 e a RTX 4070 Ti SUPER de 16 GB.

`requirements.in` lista as dependências diretas; `requirements.txt` fixa também as indiretas. A combinação de PyTorch e torchvision segue a [matriz oficial do PyTorch](https://pytorch.org/get-started/previous-versions/#v280). Este arquivo de dependências foi validado no Windows x64 com Python 3.12 e suporte NVIDIA; não é uma configuração universal para todos os sistemas.

Para recriar o ambiente em outra instalação que já tenha Python 3.12:

```powershell
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe scripts/check_environment.py
```

A instalação local foi realizada com uv 0.8.22, sem modificar o PATH do sistema. `.python-version` fixa a versão exata do interpretador. Pesos iniciais escolhidos em `config.json`: `yolo11n.pt` e `yolo11n-cls.pt`; os checkpoints já foram baixados neste workspace.

## Comandos de preparação

Os arquivos originais precisam estar extraídos em `pio/data` e `kaggle/extracted/Multimodal Chicken Datasets`, como descrito na [auditoria](experimentos.md). Os caminhos de entrada, saída, semente e proporções ficam em `config.json`; caminhos relativos são resolvidos a partir da pasta desse arquivo.

```powershell
# Preparar o detector.
.venv/Scripts/python.exe scripts/prepare_data.py pio

# Criar outra seleção em uma pasta nova (a atual já existe).
.venv/Scripts/python.exe scripts/suggest_health_boxes.py --manual --output data/review/manual-v2/health.csv

# Preparar o classificador somente depois de concluir a revisão.
.venv/Scripts/python.exe scripts/prepare_data.py health --mode demonstration
```

O PIO e a fila de revisão **já foram gerados neste workspace**. Os comandos recusam sobrescrever saídas existentes. Para repetir uma preparação em outra pasta:

```powershell
.venv/Scripts/python.exe scripts/prepare_data.py pio --output data/prepared/pio-v2
```

Uma execução interrompida pode deixar uma pasta parcial. Somente uma saída com `summary.json` e `status: ready` deve ser utilizada. Prefira uma pasta nova ao repetir a execução; os scripts não apagam pastas automaticamente.

## PIO preparado

Resultado em `data/prepared/pio`:

| Divisão | Imagens | Percentual |
| --- | ---: | ---: |
| Treino | 870 | 70,79% |
| Validação | 171 | 13,91% |
| Teste | 188 | 15,30% |
| Total | 1.229 | 100% |

Foram preservadas 280.655 caixas. A classe `0: Pollo` foi exportada como `0: chicken`. O formato segue a [estrutura YOLO da Ultralytics](https://docs.ultralytics.com/datasets/detect/): `images/{train,val,test}`, `labels/{train,val,test}` e `dataset.yaml`.

Decisões aplicadas:

- Descartar as cinco caixas sem área durante a leitura, registrando arquivo e linha.
- Comparar as caixas numericamente e sem depender da ordem das linhas. Excluir as 229 imagens pertencentes aos 112 grupos de duplicatas com anotações conflitantes, para posterior revisão.
- Remover dez cópias exatas restantes com anotações equivalentes.
- Excluir 19 imagens `K-*.jpg`, pois o arquivo de prefixos do PIO não informa seu grupo de captura.
- Agrupar por instalação/semana e unir grupos ligados por imagens idênticas antes de excluir cópias. Assim, ligações conhecidas não desaparecem durante a limpeza.
- Buscar uma divisão próxima de 70/15/15 com semente 42, priorizando grupos inteiros e representação das classes. Não fazer aumentos de dados nesta etapa.

O total de exclusões é 258 imagens. Os originais permanecem intactos. A saída contém:

- `manifest.csv`: origem, hashes de imagem e rótulo, grupo, divisão e quantidade de caixas.
- `excluded.csv`: cada imagem excluída e seu motivo.
- `discarded_boxes.csv`: as linhas descartadas por área zero.
- `summary.json`: contagens, semente, proporções pretendidas e grupos atribuídos.
- `dataset.yaml`: caminhos locais para o treinamento. Regenerar a preparação caso a pasta do projeto seja movida.

Não há grupos conhecidos ou hashes de imagem compartilhados entre as divisões geradas. Essa verificação não identifica frames quase iguais nem comprova que os animais são diferentes entre semanas. O teste foi reservado; a leitura de uma amostra nesta etapa verificou apenas compatibilidade do carregador, sem avaliação de desempenho.

## Revisão manual do classificador

Abra `data/review/binary-manual/health.html` no navegador. São 80 imagens únicas, 40 por classe. A fila original de 600 imagens permanece preservada. Ao mudar de fila, atualize `health_review` e `health_selection` em `config.json`. A página usa apenas arquivos locais.

1. Confira a foto e a classe informada pela pasta de origem.
2. Arraste sobre a imagem para delimitar uma única ave. A página registra coordenadas em pixels na resolução original.
3. Informe um **grupo de animal/sessão**. Imagens relacionadas precisam ter o mesmo grupo, mesmo quando estiverem em classes diferentes. Se desconhecido, deixe vazio e anote `Grupo desconhecido; uso demonstrativo`. Isso permite somente treino demonstrativo; não invente grupos.
4. Aceite o recorte apenas quando for possível associar a classe de origem àquela ave. Se houver múltiplas aves com rótulo individual incerto, desfoque excessivo ou ambiguidade, exclua a imagem e registre o motivo.
5. Clique em **Baixar health.csv** periodicamente. A página não grava diretamente no disco e o trabalho não salvo é perdido ao fechá-la. Para retomar, abra a página e importe o CSV mais recente.
6. Ao finalizar, coloque o CSV revisado em `data/review/binary-manual/health.csv`, substituindo o arquivo inicial, e execute o comando `health`.

Nesta versão, há no máximo um recorte aceito por imagem. A revisão mantém o rótulo fornecido pelo dataset; não confirma uma condição clínica e não transfere o rótulo automaticamente para cada animal da foto. As imagens térmicas ficam fora da fila.

O CSV usa estas colunas:

| Colunas | Uso |
| --- | --- |
| `image`, `sha256`, `label` | Identidade e classe originais; não alterar |
| `status` | `pending`, `accepted` ou `excluded` |
| `group` | Animal/sessão de origem; obrigatório no modo agrupado |
| `x1`, `y1`, `x2`, `y2` | Caixa em pixels, com área positiva e dentro da imagem |
| `notes` | Observações; motivo obrigatório nas exclusões e nos aceites sem grupo |

O exportador exige todas as decisões da seleção resolvidas e exemplos aceitos das duas classes. Imagens fora de `selection.json` não precisam ser revisadas. Não remova linhas do CSV para ignorar pendências: marque exclusões com um motivo.

No modo `--mode demonstration`, os recortes vão somente para `train/{healthy,dead}`, sem validação/teste; os metadados registram avaliação independente pendente. No modo padrão `--mode grouped`, são necessários grupos reais suficientes para gerar treino, validação e teste com ambas as classes, sem grupos ou hashes compartilhados. Grupos compartilhados podem impedir uma divisão válida mesmo quando há três por classe.

A atribuição de divisão ocorre antes dos recortes PNG RGB. O manifesto conserva origem, grupo, caixa, classe e hashes. O código verifica consistência, mas a confiança nos rótulos e a independência dos grupos dependem da revisão. Imagens térmicas e `sick` ficam fora do treinamento.

## Organização do código e verificações

O ponto de entrada é `scripts/prepare_data.py`. As responsabilidades estão separadas em `src/preparation/pio.py`, `health.py` e `review.py`. `common.py` reúne apenas escrita de manifestos, hashes, grupos e divisões. A página de revisão fica em `scripts/health_review.html`.

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

Os testes cobrem ligação transitiva de grupos, reprodutibilidade, vazamento por hash, grupos insuficientes, caixas inválidas, conflitos de anotações, preservação dos originais e exportação de recortes revisados com dados sintéticos. Também foram conferidos os 1.229 pares de arquivos reais e carregada uma amostra de cada divisão com `YOLODataset`; nenhum arquivo foi marcado como corrompido. A página foi testada no Edge, incluindo desenho, aceite, exportação e reimportação de CSV com vírgulas, aspas e quebras de linha.

Os dados, o CSV de revisão e os artefatos locais ficam fora do Git. Preserve uma cópia do CSV revisado; a semente e o script não conseguem reconstruir decisões manuais perdidas.
