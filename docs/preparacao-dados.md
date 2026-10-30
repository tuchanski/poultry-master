# Preparação do detector PIO

Instale o ambiente conforme o [README](../README.md). O clone não inclui datasets,
pesos nem resultados de treinamento.

Extraia o PIO em `data/pio/data`, com imagens em `images/<divisão>/*.jpg` e
anotações correspondentes em `labels/<divisão>/*.txt`. Ajuste `pio_source` em
`config.json` se os originais estiverem em outro local. Os caminhos relativos da
configuração são resolvidos a partir da pasta do JSON.

```bash
.venv/bin/python scripts/prepare_data.py pio
```

Por padrão, a saída é `data/prepared/pio`. Para outra pasta, use `--output`.
A saída deve ser nova e separada dos originais. No Windows, use
`.venv/Scripts/python.exe`.

A preparação mantém a classe 0 como `chicken`, descarta caixas sem área e rejeita
anotações inválidas. Imagens idênticas são deduplicadas; anotações conflitantes
e grupos de captura desconhecidos são excluídos. Grupos ligados por hashes
idênticos permanecem juntos antes da divisão em treino, validação e teste.

A semente e as proporções vêm de `config.json`. Cada divisão recebe imagens,
rótulos e registros no `manifest.csv`. A saída também contém `dataset.yaml`,
`summary.json`, `excluded.csv` e `discarded_boxes.csv`.

A separação por galpão/semana e hash evita vazamentos conhecidos, mas não comprova
independência entre animais nem elimina todas as imagens quase iguais.
Veja [treinamento](treinamento.md) e [avaliação](avaliacao.md).
