# Poultry Master

Ferramenta experimental de visão computacional para detectar aves em imagens e
acompanhar suas **bounding boxes** em fotos sucessivas de uma câmera fixa. O
fluxo atual usa as caixas detectadas para estimar trajetórias e sinalizar
imobilidade aparente para revisão humana.

O foco do MVP é a detecção e o acompanhamento espacial/temporal das caixas. O
classificador `healthy/dead` não faz parte do fluxo sequencial atual. Um
candidato de imobilidade não confirma que uma ave morreu: caixas podem sumir,
ser associadas à ave errada ou parecer paradas entre capturas.

## Fluxo atual

```text
Fotos de uma câmera fixa com horários
                 ↓
       Detector YOLO de aves
                 ↓
     Bounding boxes por captura
                 ↓
     Filtro opcional por ROI
                 ↓
 Associação de caixas entre fotos
                 ↓
  Movimento e tempo aparente parado
                 ↓
 Candidatos para revisão humana
                 ↓
 frames/ + tracks.csv + report.json
```

O detector processa cada foto separadamente. O associador atribui IDs
temporários às caixas que parecem corresponder entre capturas; esses IDs não
são uma identificação permanente dos animais. O programa limita a 30 segundos
o tempo creditado entre observações, encerra trajetórias após capturas ausentes
e inicia uma nova sessão depois de uma pausa longa. Detalhes da configuração e
da última execução estão em [fluxo atual do MVP sequencial](docs/fluxo-atual-mvp-sequencial.md).

## Requisitos e instalação

Use Python 3.12 e `uv`. Na raiz do repositório, crie um ambiente virtual e
instale as dependências apropriadas ao sistema.

### macOS (Apple Silicon)

```bash
uv venv --python 3.12 .venv
uv pip sync --python .venv/bin/python requirements-macos.txt
.venv/bin/python scripts/check_environment.py
```

### Windows (PowerShell, NVIDIA CUDA 12.8)

```powershell
uv venv --python 3.12 .venv
uv pip sync --python .venv/Scripts/python.exe requirements.txt
.venv/Scripts/python.exe scripts/check_environment.py
```

CPU é o padrão. No Windows com GPU CUDA disponível, passe `--device 0` ao
comando de análise. No macOS, use CPU.

## Arquivos necessários

O clone não inclui pesos treinados, datasets nem capturas da granja. Para o
fluxo sequencial, disponibilize o peso do detector e o arquivo de metadados
gerado junto dele:

```text
models/detector.pt
models/detector.json
```

Os metadados devem corresponder exatamente ao peso. O caminho padrão está em
`config.json` (`inference.detector`). O detector esperado tem a tarefa `detect`
e a classe `chicken`.

## Executar a análise sequencial

### Opção 1: pasta de capturas com timestamp no nome

Para capturas nomeadas como
`screenshot_<timestamp_em_milissegundos>_<contador>.png` (ou `.jpg`), passe a
pasta diretamente. As imagens são ordenadas pelo timestamp extraído do nome;
arquivos fora do padrão são ignorados.

```bash
.venv/bin/python analyze_sequence.py \
  --images-dir "/caminho/para/capturas" \
  --output outputs/granja-001 \
  --device cpu \
  --roi 0,0.60,1,1 \
  --stationary-minutes 7 \
  --candidates-only \
  --hide-labels
```

No Windows, substitua `.venv/bin/python` por
`.venv/Scripts/python.exe` e use caminhos compatíveis com PowerShell. Passe
`--device 0` para selecionar a GPU CUDA. Escolha uma pasta de saída nova para
cada execução.

O exemplo usa a ROI `0,0.60,1,1`: toda a largura da imagem e os 40% inferiores.
Uma caixa é incluída quando seu centro está dentro da ROI. Remova `--roi` para
considerar todas as detecções. `--stationary-minutes 7` define o limiar
experimental da execução; o padrão do programa é 5 minutos. `--candidates-only`
e `--hide-labels` mudam apenas a visualização gerada.

### Opção 2: manifesto CSV

Use esta opção se os nomes dos arquivos não carregam timestamps. Crie um CSV
UTF-8 com as colunas `image` e `timestamp`; timestamps precisam incluir o fuso
horário e caminhos relativos são resolvidos a partir da pasta do CSV.

```csv
image,timestamp
frames/frame-001.jpg,2026-10-19T10:00:00-03:00
frames/frame-002.jpg,2026-10-19T10:00:30-03:00
```

Execute:

```bash
.venv/bin/python analyze_sequence.py \
  --manifest "/caminho/para/sequence.csv" \
  --output outputs/sequencia-001 \
  --device cpu
```

O programa ordena as linhas cronologicamente e rejeita horários repetidos,
imagens ausentes, dimensões diferentes e timestamps sem fuso. Para mais
parâmetros temporais e exemplos, consulte [análise sequencial](docs/analise-sequencial.md).

## Resultados

Cada execução cria a pasta indicada por `--output` com:

| Arquivo | Conteúdo |
| --- | --- |
| `frames/` | Fotos anotadas com caixas, IDs temporários e candidatos, conforme opções de visualização. |
| `tracks.csv` | Uma linha por observação: timestamp, caixa, trajetória, movimento e estado. |
| `report.json` | Configuração, contagens, trajetórias, eventos candidatos e metadados das imagens/modelo. |

`stationary_candidate` quer dizer que uma trajetória acumulou pouca
movimentação aparente pelo tempo configurado e precisa ser verificada. Não é
um diagnóstico de saúde ou confirmação de óbito. Câmera móvel, mudanças de
iluminação, sobreposição, falhas de detecção e trocas de associação podem
afetar o resultado.

## Desenvolvimento, avaliação e dados

Confira o ambiente e rode a suíte de testes:

```bash
.venv/bin/python scripts/check_environment.py
.venv/bin/python -m unittest discover -s tests -v
```

No Windows, use `.venv/Scripts/python.exe` no lugar de `.venv/bin/python`.
Os testes do associador usam detecções controladas e não validam o desempenho
em uma granja real.

O projeto também contém preparação e avaliação do detector PIO. O detector
atingiu mAP@50 de 93,41% no teste PIO, mas apresentou supercontagem média de
39,81 aves por imagem nessa avaliação. Esse resultado não mede o rastreamento
sequencial. Dados de preparação e treinamento estão documentados em
[preparação dos dados](docs/preparacao-dados.md), [treinamento](docs/treinamento.md)
e [avaliação](docs/avaliacao.md). Os planos do MVP estão em
[MVP sequencial](docs/plano-mvp-sequencial.md) e [MVP inicial](docs/plano-mvp.md).
