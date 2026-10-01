# Guia rápido para executar o MVP

Execute os comandos no **terminal PowerShell do VS Code, na pasta `poultry-master`**, onde está o `README.md`. Não é necessário ativar o ambiente virtual.

Neste computador, os dados já foram preparados, as 80 imagens foram revisadas e os dois modelos foram treinados. **Para testar o sistema agora, execute os passos 1 a 4.** O passo 5 explica como repetir a preparação e os treinamentos, se desejar.

## 1. Conferir o ambiente e os testes

```powershell
.venv/Scripts/python.exe scripts/check_environment.py
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

Esperado: ambiente sem erros e testes terminando com `OK`. A verificação do ambiente salva `outputs/environment.json`.

Se `.venv` não existir, siga a instalação em [preparação dos dados](preparacao-dados.md). Um clone do Git não inclui datasets, pesos nem CSVs de revisão.

## 2. Executar o fluxo completo em uma foto

Este exemplo usa uma foto local do teste do detector:

```powershell
.venv/Scripts/python.exe analyze.py --image "data/prepared/pio/images/test/C-W3-0001.jpg" --output outputs/meu-teste-01
```

O programa faz automaticamente:

1. Carrega a foto e os dois modelos.
2. Detecta as aves e recorta cada caixa válida.
3. Classifica cada recorte como `healthy` ou `dead`.
4. Mostra as contagens e salva a imagem anotada e o relatório.

Para testar uma foto sua, substitua o caminho após `--image`:

```powershell
.venv/Scripts/python.exe analyze.py --image "C:/caminho/da/sua/foto.jpg" --output outputs/meu-teste-02
```

O padrão é CPU. Para usar a GPU, acrescente `--device 0` ao comando. **Use uma pasta de saída nova a cada execução**, por exemplo `meu-teste-03`, `meu-teste-04`.

## 3. Abrir e conferir os resultados

Para o primeiro exemplo:

```powershell
Invoke-Item outputs/meu-teste-01/annotated.jpg
Get-Content -Encoding UTF8 outputs/meu-teste-01/report.json
```

Também pode abrir esses arquivos pelo Explorador do VS Code.

| Arquivo | O que conferir |
| --- | --- |
| `annotated.jpg` | Caixas, identificadores, classes e confiança; `dead` aparece em vermelho |
| `report.json` | `summary` contém contagens e percentuais; `birds` contém cada caixa e suas duas confianças |

A soma de `healthy` e `dead` deve ser igual ao total detectado. Sem detecções, os totais ficam zerados. A foto original permanece intacta.

**Importante para interpretar:** as caixas e classes são previsões, não confirmações. Já observamos supercontagem e muitas previsões `dead` nas fotos do PIO. Não interprete esse número como quantidade real de aves mortas. O classificador ainda não tem avaliação independente.

## 4. Executar a avaliação do detector

```powershell
.venv/Scripts/python.exe scripts/evaluate.py --device 0 --output outputs/evaluation/meu-teste-01
```

Para CPU, troque `--device 0` por `--device cpu`. Escolha uma pasta nova se repetir.

Esperado na pasta escolhida:

- `summary.json`: precisão, recall, mAP e erros de contagem.
- `counts.csv`: quantidade anotada e detectada em cada imagem.
- `validation/`: gráficos e exemplos visuais. Apesar do nome, a avaliação usa o conjunto **test**.

Este comando avalia **o detector**, não a classificação de saúde. Não use o teste para escolher novos parâmetros. Os resultados já obtidos e suas limitações estão em [avaliação](avaliacao.md).

## 5. Repetir a preparação e os treinamentos — opcional

**Não precisa executar esta parte para testar o sistema pronto.** Os comandos de preparação recusam pastas existentes; os comandos de treinamento recusam nomes de execução já utilizados.

### 5.1. Preparar o PIO novamente

```powershell
.venv/Scripts/python.exe scripts/prepare_data.py pio --output data/prepared/pio-reexecucao
```

Esperado: `summary.json` com `status: ready`, `dataset.yaml` e pastas de imagens e anotações de treino, validação e teste.

Para treinar e avaliar usando essa nova preparação, altere em `config.json`:

```json
"pio_output": "data/prepared/pio-reexecucao"
```

Se usar os dados já preparados, mantenha `data/prepared/pio` e pule esse comando.

### 5.2. Conferir a revisão manual

Abra no Edge ou Chrome o arquivo **`data/review/binary-manual/health.html`**. Não use a página antiga `data/review/health.html`, de 600 imagens.

Na página, use **Retomar revisão** para importar `data/review/binary-manual/health.csv`. O HTML sozinho não reflete automaticamente as decisões salvas no CSV.

A revisão já está concluída. Se fizer alterações: marque uma única ave por foto, deixe Grupo vazio quando desconhecido, registre `Grupo desconhecido; uso demonstrativo` nas notas e clique em **Aceitar recorte**. Para excluir, informe o motivo. Baixe o CSV e substitua `data/review/binary-manual/health.csv`. Todas as decisões precisam estar resolvidas.

### 5.3. Preparar os recortes novamente

```powershell
.venv/Scripts/python.exe scripts/prepare_data.py health --mode demonstration --output data/prepared/health-reexecucao
```

Esperado: recortes em `train/dead` e `train/healthy`, manifesto e `summary.json`. Com a revisão atual, são 40 recortes por classe. Esse modo não cria validação ou teste.

### 5.4. Treinar os dois modelos novamente

Os checkpoints iniciais devem estar em `models/pretrained`. Já existem neste computador; para outra instalação, consulte [treinamento](treinamento.md).

**Estes comandos substituem os pesos finais e seus metadados em `models`.** Antes, faça uma cópia dos quatro arquivos `detector.pt`, `detector.json`, `classifier.pt` e `classifier.json` se quiser preservar a versão atual.

```powershell
.venv/Scripts/python.exe scripts/train_detector.py --epochs 15 --batch 8 --device 0 --name detector-reexecucao
.venv/Scripts/python.exe scripts/train_classifier.py --dataset data/prepared/health-reexecucao --epochs 15 --device 0 --name classifier-reexecucao --allow-demonstration
```

O detector usa `pio_output` de `config.json`. O classificador usa o dataset indicado em `--dataset`. Se pulou a preparação dos recortes, use `data/prepared/health-binary-reviewed` nesse argumento.

Esperado: os pesos e metadados em `models`, além dos registros em `outputs/training`. O detector pode encerrar antes das 15 épocas por parada antecipada; o classificador demonstrativo usa as 15 épocas, sem métricas de validação independente.

Depois, repita os passos **2 e 3** com uma pasta de saída nova. A avaliação do passo 4 registra o desempenho do detector; não transforme sucessivas consultas ao teste em ajuste de modelo.

## Problemas comuns

| Mensagem ou situação | O que fazer |
| --- | --- |
| Pasta de saída ou execução já existe | Escolha outro `--output` ou `--name`; não precisa apagar resultados |
| Peso ausente | Confira os arquivos em `models` e os caminhos em `config.json` |
| Peso não corresponde aos metadados | Use o `.pt` e o `.json` gerados no mesmo treinamento |
| Revisão incompleta | Importe o CSV no HTML, resolva as pendências e salve novamente |
| HTML mostra 600 imagens | Abra `data/review/binary-manual/health.html` |
| Imagem branca no HTML | Abra o arquivo diretamente no navegador, fora da prévia do VS Code |
| GPU indisponível | Use `--device cpu` nos comandos de análise, treino ou avaliação |
