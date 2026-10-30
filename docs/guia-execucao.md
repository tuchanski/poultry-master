# Guia de execução

O ponto de entrada atual é `analyze_sequence.py`. Instale as dependências do seu
sistema conforme o [README](../README.md), disponibilize `models/detector.pt` e
`models/detector.json` e confira o ambiente:

```bash
.venv/bin/python scripts/check_environment.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python analyze_sequence.py --images-dir "/caminho/para/capturas" --output outputs/sequencia-001 --device cpu
```

No Windows, substitua `.venv/bin/python` por `.venv/Scripts/python.exe`.
Use `--device 0` quando houver uma GPU CUDA disponível. No macOS, use CPU.

A pasta deve conter capturas de uma câmera fixa com nomes
`screenshot_<timestamp_ms>_<contador>.png` ou `.jpg`. Para outros nomes,
use `--manifest` com um CSV de caminhos e horários com fuso. As opções de ROI,
tempo e visualização estão em [análise sequencial](analise-sequencial.md).

Cada execução exige uma pasta de saída nova e gera `frames/`, `tracks.csv` e
`report.json`. Os candidatos indicam imobilidade aparente e exigem revisão humana.

| Problema | Ação |
| --- | --- |
| Saída já existe | Escolha outro `--output`. |
| Peso ausente | Confira o caminho em `config.json` e os arquivos em `models/`. |
| Hash incompatível | Disponibilize o peso e o JSON do mesmo treinamento. |
| Capturas não reconhecidas | Confira os nomes ou forneça um manifesto. |
| Horário sem fuso ou repetido | Corrija o manifesto. |
| Dimensões diferentes | Use capturas com a mesma resolução e enquadramento. |
| GPU indisponível | Use `--device cpu`. |
